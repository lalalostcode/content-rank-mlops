package io.contentranking;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.patch;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.time.OffsetDateTime;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.Callable;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfEnvironmentVariable;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.core.env.Environment;
import org.springframework.dao.DataAccessException;
import org.springframework.http.MediaType;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.DriverManagerDataSource;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.ResultActions;

@SpringBootTest(properties = {
    "spring.datasource.hikari.maximum-pool-size=3",
    "spring.datasource.hikari.minimum-idle=0"
})
@AutoConfigureMockMvc
@EnabledIfEnvironmentVariable(named = "RANKING_TEST_DATABASE", matches = "true")
class RankingPostgresTest {
    private static final OffsetDateTime CUTOFF = OffsetDateTime.parse("2025-02-01T00:00:00Z");
    @Autowired MockMvc mvc;
    @Autowired ObjectMapper mapper;
    @Autowired Environment env;
    JdbcTemplate seed;
    String client;
    String otherClient;
    String model;
    String prefix;
    String itemPrefix;

    @BeforeEach
    void createIsolatedClientAndPublishedRun() {
        String url = env.getRequiredProperty("spring.datasource.url");
        String user = env.getProperty("spring.flyway.user", env.getRequiredProperty("spring.datasource.username"));
        String password = env.getProperty("spring.flyway.password", env.getProperty("spring.datasource.password", ""));
        seed = new JdbcTemplate(new DriverManagerDataSource(url, user, password));
        client = "test-" + UUID.randomUUID();
        otherClient = "test-" + UUID.randomUUID();
        model = "test-model-" + UUID.randomUUID();
        prefix = "/api/v1/clients/" + client;
        itemPrefix = prefix + "/items/content-a";
        seed.update("INSERT INTO client (id,label) VALUES (?,?), (?,?)", client, "Integration", otherClient, "Other");
        seed.update("INSERT INTO model_version (id,artifact_sha256,feature_schema_version) VALUES (?,?,?)",
            model, "a".repeat(64), "rank-features-v1");
        seed.update("INSERT INTO content (client_id,id) VALUES (?,?), (?,?)", client, "content-a", client, "content-b");
        publish("run-a", "snapshot-a", CUTOFF, "b");
    }

    private void publish(String run, String snapshot, OffsetDateTime cutoff, String digestByte) {
        String digest = digestByte.repeat(64);
        seed.update("""
            INSERT INTO scoring_run (client_id,id,snapshot_id,input_digest,observation_cutoff,transform_revision,
                model_id,status,input_rows,eligible_rows,started_at,finished_at,published_at)
            VALUES (?,?,?,?,?,?,?,'succeeded',2,2,?,?,?)
            """, client, run, snapshot, digest, cutoff, "snapshot-features-v1", model, cutoff, cutoff, cutoff);
        for (String item : new String[]{"content-a", "content-b"}) {
            seed.update("""
                INSERT INTO observation (client_id,content_id,snapshot_id,cutoff,source_release,input_digest,
                    window_start,window_end,metrics,declining)
                VALUES (?,?,?,?,'unit-fixture',?,?,?,'{"impressions":100,"ctr":1.2}',true)
                """, client, item, snapshot, cutoff, digest, cutoff.minusDays(90), cutoff);
            int position = item.equals("content-a") ? 1 : 2;
            seed.update("""
                INSERT INTO rank_item (client_id,run_id,content_id,snapshot_id,position,score,reason_codes)
                VALUES (?,?,?,?,?,?,'[{"code":"SEARCH_VISIBILITY","metric":"impressions","value":100,"unit":"count"}]')
                """, client, run, item, snapshot, position, 1.0 / position);
        }
        seed.update("UPDATE client SET published_run_id = ? WHERE id = ?", run, client);
    }

    @Test
    void publishedQueueIsScopedAndPaginationStaysOnItsRun() throws Exception {
        mvc.perform(get("/api/v1/health")).andExpect(status().isOk());
        mvc.perform(get(prefix + "/overview")).andExpect(status().isOk())
            .andExpect(jsonPath("$.decliningCount").value(2)).andExpect(jsonPath("$.coverage").value(1.0));
        ResultActions first = mvc.perform(get(prefix + "/rankings").param("limit", "1")).andExpect(status().isOk())
            .andExpect(jsonPath("$.items[0].contentId").value("content-a"));
        String cursor = body(first).get("nextCursor").asText();
        publish("run-b", "snapshot-b", CUTOFF.plusDays(1), "c");
        mvc.perform(get(prefix + "/rankings").param("cursor", cursor)).andExpect(status().isOk())
            .andExpect(jsonPath("$.runId").value("run-a")).andExpect(jsonPath("$.items[0].position").value(2));
        mvc.perform(get(prefix + "/rankings").param("q", "CONTENT-B").param("status", "OPEN"))
            .andExpect(status().isOk()).andExpect(jsonPath("$.items.length()").value(1));
        mvc.perform(get(prefix + "/models/" + model)).andExpect(status().isOk())
            .andExpect(jsonPath("$.artifactSha256").value("a".repeat(64)));
        mvc.perform(get("/api/v1/clients/" + otherClient + "/models/" + model)).andExpect(status().isNotFound());
        mvc.perform(get("/api/v1/clients/" + otherClient + "/runs/run-a")).andExpect(status().isNotFound());
        mvc.perform(get(prefix + "/rankings").param("limit", "101")).andExpect(status().isBadRequest());
    }

    @Test
    void decisionsReplayWithImmutableHistoryAndUnavailableFollowUp() throws Exception {
        JsonNode started = body(start("begin").andExpect(status().isOk()).andExpect(jsonPath("$.version").value(1)));
        String caseId = started.get("caseId").asText();
        assertThat(body(start("begin").andExpect(status().isOk()))).isEqualTo(started);
        Map<String, Object> decision = Map.of("caseId", caseId, "runId", "run-a", "expectedVersion", 1,
            "decision", "act", "note", "Documented synthetic review");
        JsonNode acted = body(decide("act", decision).andExpect(status().isCreated())
            .andExpect(jsonPath("$.status").value("ACTION_TAKEN")));
        assertThat(body(decide("act", decision).andExpect(status().isOk()))).isEqualTo(acted);
        decide("act", Map.of("caseId", caseId, "runId", "run-a", "expectedVersion", 1,
            "decision", "no_action")).andExpect(status().isConflict());
        decide("stale", decision).andExpect(status().isConflict());
        mvc.perform(get(itemPrefix + "/observations").param("caseId", caseId)).andExpect(status().isOk())
            .andExpect(jsonPath("$.followUp.reason").value("NO_LATER_OBSERVATION"))
            .andExpect(jsonPath("$.followUp.deltas").doesNotExist());
        JsonNode page = body(mvc.perform(get(itemPrefix + "/actions").param("limit", "1")).andExpect(status().isOk()));
        assertThat(page.get("items").get(0).get("eventType").asText()).isEqualTo("CASE_OPENED");
        mvc.perform(get(itemPrefix + "/actions").param("cursor", page.get("nextCursor").asText()))
            .andExpect(status().isOk()).andExpect(jsonPath("$.items.length()").value(2))
            .andExpect(jsonPath("$.items[1].eventId").value(acted.get("eventId").asText()));
        assertThatThrownBy(() -> seed.update("UPDATE review_event SET note = 'changed' WHERE id = ?::uuid",
            acted.get("eventId").asText())).isInstanceOf(DataAccessException.class)
            .hasMessageContaining("Review events are immutable");
    }

    @Test
    void terminalStatusSurvivesSameCutoffAndAllowsNewCandidate() throws Exception {
        JsonNode started = body(start("begin").andExpect(status().isOk()));
        decide("close", Map.of("caseId", started.get("caseId").asText(), "runId", "run-a", "expectedVersion", 1,
            "decision", "no_action")).andExpect(status().isCreated());
        publish("run-b", "snapshot-b", CUTOFF, "c");
        mvc.perform(get(prefix + "/rankings/run-b/items/content-a")).andExpect(status().isOk())
            .andExpect(jsonPath("$.reviewStatus").value("NO_ACTION"));
        publish("run-c", "snapshot-c", CUTOFF.plusDays(7), "d");
        mvc.perform(get(prefix + "/rankings/run-c/items/content-a")).andExpect(status().isOk())
            .andExpect(jsonPath("$.reviewStatus").value("OPEN")).andExpect(jsonPath("$.candidateRunId").value("run-c"));
        mvc.perform(get(itemPrefix + "/actions")).andExpect(status().isOk())
            .andExpect(jsonPath("$.items.length()").value(3));
    }

    @Test
    void concurrentCandidateUpdatesPersistOnlyOneCase() throws Exception {
        CountDownLatch ready = new CountDownLatch(2);
        try (var pool = new CloseableExecutor()) {
            Callable<Integer> begin = () -> {
                ready.countDown();
                assertThat(ready.await(5, TimeUnit.SECONDS)).isTrue();
                return start(UUID.randomUUID().toString()).andReturn().getResponse().getStatus();
            };
            var first = pool.executor.submit(begin);
            var second = pool.executor.submit(begin);
            assertThat(first.get(10, TimeUnit.SECONDS)).isIn(200, 409).isNotEqualTo(second.get(10, TimeUnit.SECONDS));
            assertThat(second.get()).isIn(200, 409);
        }
        mvc.perform(get(itemPrefix + "/actions")).andExpect(status().isOk())
            .andExpect(jsonPath("$.items.length()").value(2));
    }

    private ResultActions start(String key) throws Exception {
        return mvc.perform(patch(itemPrefix + "/status").header("Idempotency-Key", key)
            .contentType(MediaType.APPLICATION_JSON).content("""
                {"candidateRunId":"run-a","status":"IN_REVIEW","expectedVersion":0}
                """));
    }

    private ResultActions decide(String key, Map<String, Object> request) throws Exception {
        return mvc.perform(post(itemPrefix + "/actions").header("Idempotency-Key", key)
            .contentType(MediaType.APPLICATION_JSON).content(mapper.writeValueAsString(request)));
    }

    private JsonNode body(ResultActions action) throws Exception {
        return mapper.readTree(action.andReturn().getResponse().getContentAsByteArray());
    }

    private static class CloseableExecutor implements AutoCloseable {
        final java.util.concurrent.ExecutorService executor = Executors.newFixedThreadPool(2);

        @Override
        public void close() {
            executor.shutdownNow();
        }
    }
}
