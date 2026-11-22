package io.contentranking;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.time.Duration;
import java.time.Instant;
import java.time.OffsetDateTime;
import java.util.ArrayList;
import java.util.TreeMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.UUID;
import org.springframework.jdbc.core.simple.JdbcClient;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@Transactional(readOnly = true)
class RankingReadService {
    static final String ISSUE_TYPE = "DECLINE_PRIORITY";
    private static final String RANKS = """
        SELECT i.content_id, i.position, i.score, i.reason_codes, i.snapshot_id,
            o.metrics, o.cutoff, o.window_start, o.window_end,
            coalesce(c.status, 'OPEN') AS review_status, coalesce(c.version, 0) AS version,
            c.id AS case_id
        FROM rank_item i
        JOIN scoring_run r ON r.client_id = i.client_id AND r.id = i.run_id
        JOIN observation o ON o.client_id = i.client_id AND o.content_id = i.content_id
            AND o.snapshot_id = i.snapshot_id
        LEFT JOIN LATERAL (
            SELECT id, status, version FROM review_case
            WHERE client_id = i.client_id AND content_id = i.content_id
            AND issue_type = 'DECLINE_PRIORITY' AND opening_cutoff <= r.observation_cutoff
            AND (terminal_cutoff IS NULL OR terminal_cutoff >= r.observation_cutoff)
            ORDER BY opening_cutoff DESC LIMIT 1
        ) c ON true
        WHERE i.client_id = :client AND i.run_id = :run
        """;

    static final Map<String, Metric> METRIC_DEFINITIONS = Map.ofEntries(
        Map.entry("impressions", new Metric("Search impressions", "count")),
        Map.entry("clicks", new Metric("Search clicks", "count")),
        Map.entry("ctr", new Metric("Search click-through rate", "%")),
        Map.entry("avgPosition", new Metric("Average search position", "position")),
        Map.entry("sessions", new Metric("Sessions", "count")),
        Map.entry("engagementRate", new Metric("Engagement rate", "%")),
        Map.entry("daysSinceLastUpdate", new Metric("Age since last update", "days")),
        Map.entry("trendPercent", new Metric("Observed impression change", "%"))
    );

    record ClientView(String id, String label) {}
    record Overview(String snapshotId, Instant cutoff, long itemCount, Long decliningCount, Double coverage) {}
    record RunView(String runId, String status, String snapshotId, String inputDigest, Instant observationCutoff,
                   String transformRevision, String modelId, int inputRows, int eligibleRows,
                   Instant startedAt, Instant finishedAt, Instant publishedAt) {}
    record ModelView(String modelId, String artifactSha256, String featureSchemaVersion,
                     String registryUri, String registryVersion) {}
    record RankItem(String contentId, int position, double score, JsonNode reasonCodes, String snapshotId,
                    JsonNode metrics, Instant cutoff, Instant observationWindowStart, Instant observationWindowEnd,
                    String issueType, ReviewStatus reviewStatus, long version, UUID caseId, String candidateRunId) {}
    record RankingPage(String runId, List<RankItem> items, String nextCursor, boolean pending) {}
    record Metric(String definition, String unit) {}
    record Observation(String snapshotId, Instant cutoff, String sourceRelease, String inputDigest,
                       Instant windowStart, Instant windowEnd, JsonNode metrics, Map<String, Metric> metricDefinitions) {}
    record ActionAnchor(String snapshotId, Instant occurredAt) {}

    @JsonInclude(JsonInclude.Include.NON_NULL)
    record FollowUp(String status, String reason, Observation baseline, Observation later, Map<String, Double> deltas) {
        static FollowUp unavailable(String reason) {
            return new FollowUp("UNAVAILABLE", reason, null, null, null);
        }
    }

    record ObservationHistory(List<Observation> items, FollowUp followUp) {}
    record EventView(UUID eventId, UUID caseId, long resultingVersion, String actor, Instant occurredAt,
                     String eventType, String runId, String snapshotId, String priorStatus, String newStatus,
                     String decision, String note) {}
    record EventPage(List<EventView> items, String nextCursor) {}

    private final JdbcClient jdbc;
    private final ObjectMapper mapper;

    RankingReadService(JdbcClient jdbc, ObjectMapper mapper) {
        this.jdbc = jdbc;
        this.mapper = mapper;
    }

    List<ClientView> clients() {
        return jdbc.sql("SELECT id, label FROM client ORDER BY label, id").query(ClientView.class).list();
    }

    String currentRun(String client) {
        return jdbc.sql("SELECT published_run_id FROM client WHERE id = :client")
            .param("client", client).query((row, index) -> new String[]{row.getString(1)})
            .optional().orElseThrow(() -> ApiException.missing("Client not found."))[0];
    }

    void requireContent(String client, String item) {
        jdbc.sql("SELECT id FROM content WHERE client_id = :client AND id = :item")
            .param("client", client).param("item", item).query(String.class).optional()
            .orElseThrow(() -> ApiException.missing("Content not found."));
    }

    RunView run(String client, String run) {
        return jdbc.sql("SELECT * FROM scoring_run WHERE client_id = :client AND id = :run")
            .param("client", client).param("run", run)
            .query((row, index) -> new RunView(row.getString("id"), row.getString("status"),
                row.getString("snapshot_id"), row.getString("input_digest"), instant(row, "observation_cutoff"),
                row.getString("transform_revision"), row.getString("model_id"), row.getInt("input_rows"),
                row.getInt("eligible_rows"), instant(row, "started_at"), instant(row, "finished_at"),
                instant(row, "published_at")))
            .optional().orElseThrow(() -> ApiException.missing("Scoring run not found."));
    }

    ModelView model(String client, String model) {
        return jdbc.sql("""
                SELECT m.id, m.artifact_sha256, m.feature_schema_version, m.registry_uri, m.registry_version
                FROM model_version m WHERE m.id = :model AND EXISTS (
                    SELECT 1 FROM scoring_run r WHERE r.client_id = :client AND r.model_id = m.id
                )
                """)
            .param("client", client).param("model", model)
            .query((row, index) -> new ModelView(row.getString("id"), row.getString("artifact_sha256"),
                row.getString("feature_schema_version"), row.getString("registry_uri"), row.getString("registry_version")))
            .optional().orElseThrow(() -> ApiException.missing("Model not found for this client."));
    }

    Overview overview(String client, String snapshot) {
        String current = currentRun(client);
        if (snapshot == null && current == null) return new Overview(null, null, 0, null, null);
        RunView reference = snapshot == null ? run(client, current) : jdbc.sql("""
                SELECT id FROM scoring_run WHERE client_id = :client AND snapshot_id = :snapshot
                ORDER BY published_at DESC, id DESC LIMIT 1
                """).param("client", client).param("snapshot", snapshot).query(String.class).optional()
            .map(id -> run(client, id)).orElseThrow(() -> ApiException.missing("Snapshot not found."));
        Long declining = jdbc.sql("""
                SELECT CASE WHEN count(declining) > 0 THEN count(*) FILTER (WHERE declining) END
                FROM observation WHERE client_id = :client AND snapshot_id = :snapshot
                """).param("client", client).param("snapshot", reference.snapshotId())
            .query((row, index) -> new Long[]{row.getObject(1, Long.class)}).single()[0];
        Double coverage = reference.inputRows() == 0 ? null : (double) reference.eligibleRows() / reference.inputRows();
        return new Overview(reference.snapshotId(), reference.observationCutoff(), reference.inputRows(), declining, coverage);
    }

    RankingPage rankings(String client, String requestedRun, String cursor, ReviewStatus status, String search, int limit) {
        String current = currentRun(client);
        String selectedRun = requestedRun;
        int after = 0;
        if (cursor != null) {
            String[] parts = Cursors.decode(cursor);
            if (selectedRun != null && !selectedRun.equals(parts[0])) {
                throw ApiException.invalid("Cursor belongs to a different scoring run.");
            }
            selectedRun = parts[0];
            try {
                after = Integer.parseInt(parts[1]);
                if (after < 1) throw new NumberFormatException();
            } catch (NumberFormatException ignored) {
                throw ApiException.invalid("Invalid ranking position in cursor.");
            }
        }
        String runId = selectedRun == null ? current : selectedRun;
        if (runId == null) return new RankingPage(null, List.of(), null, true);
        run(client, runId);
        String filters = " AND i.position > :after"
            + (status == null ? "" : " AND coalesce(c.status, 'OPEN') = :status")
            + (search == null || search.isBlank() ? "" : " AND strpos(lower(i.content_id), lower(:search)) > 0");
        JdbcClient.StatementSpec query = jdbc.sql(RANKS + filters + " ORDER BY i.position LIMIT :limit")
            .param("client", client).param("run", runId).param("after", after).param("limit", limit + 1);
        if (status != null) query.param("status", status.name());
        if (search != null && !search.isBlank()) query.param("search", search.strip());
        boolean active = runId.equals(current);
        List<RankItem> rows = query.query((row, index) -> rank(row, active ? runId : null)).list();
        String next = rows.size() > limit ? Cursors.encode(runId, rows.get(limit - 1).position()) : null;
        return new RankingPage(runId, rows.subList(0, Math.min(limit, rows.size())), next, false);
    }

    RankItem detail(String client, String run, String item) {
        String current = currentRun(client);
        return jdbc.sql(RANKS + " AND i.content_id = :item").param("client", client).param("run", run)
            .param("item", item).query((row, index) -> rank(row, run.equals(current) ? run : null))
            .optional().orElseThrow(() -> ApiException.missing("Ranked content not found."));
    }

    private RankItem rank(ResultSet row, String currentRun) throws SQLException {
        UUID caseId = row.getObject("case_id", UUID.class);
        return new RankItem(row.getString("content_id"), row.getInt("position"), row.getDouble("score"),
            json(row, "reason_codes"), row.getString("snapshot_id"), json(row, "metrics"),
            instant(row, "cutoff"), instant(row, "window_start"), instant(row, "window_end"),
            ISSUE_TYPE, ReviewStatus.valueOf(row.getString("review_status")), row.getLong("version"), caseId,
            caseId == null ? currentRun : null);
    }

    ObservationHistory observations(String client, String item, UUID caseId) {
        requireContent(client, item);
        List<Observation> items = jdbc.sql("""
            SELECT * FROM observation WHERE client_id = :client AND content_id = :item ORDER BY cutoff, snapshot_id
            """).param("client", client).param("item", item).query((row, index) -> new Observation(
                row.getString("snapshot_id"), instant(row, "cutoff"), row.getString("source_release"),
                row.getString("input_digest"), instant(row, "window_start"), instant(row, "window_end"),
                json(row, "metrics"), METRIC_DEFINITIONS)).list();
        return new ObservationHistory(items, caseId == null ? FollowUp.unavailable("NO_RECORDED_ACTION")
            : compare(client, item, caseId, items));
    }

    private FollowUp compare(String client, String item, UUID caseId, List<Observation> observations) {
        requireCase(client, item, caseId);
        ActionAnchor anchor = jdbc.sql("""
                SELECT snapshot_id, occurred_at FROM review_event WHERE client_id = :client
                    AND content_id = :item AND case_id = :case AND decision = 'act'
                ORDER BY occurred_at DESC, resulting_version DESC LIMIT 1
                """).param("client", client).param("item", item).param("case", caseId)
            .query((row, index) -> new ActionAnchor(row.getString("snapshot_id"), instant(row, "occurred_at")))
            .optional().orElse(null);
        if (anchor == null) return FollowUp.unavailable("NO_RECORDED_ACTION");
        Observation baseline = observations.stream().filter(o -> o.snapshotId().equals(anchor.snapshotId()))
            .findFirst().orElseThrow();
        boolean laterExists = false;
        for (Observation later : observations) {
            if (!later.cutoff().isAfter(baseline.cutoff())) continue;
            laterExists = true;
            if (baseline.cutoff().isAfter(anchor.occurredAt()) || baseline.windowEnd().isAfter(anchor.occurredAt())
                || !later.cutoff().isAfter(anchor.occurredAt()) || later.windowStart().isBefore(anchor.occurredAt())
                || !Duration.between(later.windowStart(), later.windowEnd())
                    .equals(Duration.between(baseline.windowStart(), baseline.windowEnd()))) continue;
            Map<String, Double> deltas = new TreeMap<>();
            for (String metric : METRIC_DEFINITIONS.keySet()) {
                JsonNode before = baseline.metrics().path(metric);
                JsonNode after = later.metrics().path(metric);
                if (before.isNumber() && after.isNumber()) deltas.put(metric, after.doubleValue() - before.doubleValue());
            }
            if (!deltas.isEmpty()) return new FollowUp("AVAILABLE", null, baseline, later, deltas);
        }
        return FollowUp.unavailable(laterExists ? "INCOMPARABLE_OBSERVATIONS" : "NO_LATER_OBSERVATION");
    }

    EventPage history(String client, String item, UUID caseId, String cursor, int limit) {
        requireContent(client, item);
        if (caseId != null) requireCase(client, item, caseId);
        String scope = client + "/" + item + "/" + Objects.toString(caseId, "");
        String cursorSql = "";
        List<Object> after = new ArrayList<>();
        if (cursor != null) {
            String[] parts = Cursors.decode(cursor);
            if (!scope.equals(parts[0])) throw ApiException.invalid("Cursor belongs to another history.");
            try {
                String[] position = parts[1].split("\\|", -1);
                if (position.length != 3) throw new IllegalArgumentException();
                after.add(OffsetDateTime.parse(position[0]));
                after.add(Long.parseLong(position[1]));
                after.add(UUID.fromString(position[2]));
                cursorSql = " AND (occurred_at, resulting_version, id) > (:time, :version, :event)";
            } catch (RuntimeException ignored) {
                throw ApiException.invalid("Invalid event cursor.");
            }
        }
        String caseSql = caseId == null ? "" : " AND case_id = :case";
        JdbcClient.StatementSpec query = jdbc.sql("""
                SELECT * FROM review_event WHERE client_id = :client AND content_id = :item
                """ + caseSql + cursorSql + " ORDER BY occurred_at, resulting_version, id LIMIT :limit")
            .param("client", client).param("item", item).param("limit", limit + 1);
        if (caseId != null) query.param("case", caseId);
        if (!after.isEmpty()) query.param("time", after.get(0)).param("version", after.get(1)).param("event", after.get(2));
        List<EventView> rows = query.query((row, index) -> new EventView(row.getObject("id", UUID.class),
            row.getObject("case_id", UUID.class), row.getLong("resulting_version"), row.getString("actor"),
            instant(row, "occurred_at"), row.getString("event_type"), row.getString("run_id"), row.getString("snapshot_id"),
            row.getString("prior_status"), row.getString("new_status"), row.getString("decision"), row.getString("note"))).list();
        EventView last = rows.size() > limit ? rows.get(limit - 1) : null;
        String next = last == null ? null
            : Cursors.encode(scope, last.occurredAt() + "|" + last.resultingVersion() + "|" + last.eventId());
        return new EventPage(rows.subList(0, Math.min(rows.size(), limit)), next);
    }

    private void requireCase(String client, String item, UUID caseId) {
        jdbc.sql("SELECT id FROM review_case WHERE client_id = :client AND content_id = :item AND id = :case")
            .param("client", client).param("item", item).param("case", caseId).query(UUID.class).optional()
            .orElseThrow(() -> ApiException.missing("Review case not found."));
    }

    static Instant instant(ResultSet row, String column) throws SQLException {
        OffsetDateTime stamp = row.getObject(column, OffsetDateTime.class);
        return stamp == null ? null : stamp.toInstant();
    }

    private JsonNode json(ResultSet row, String column) throws SQLException {
        try {
            return mapper.readTree(row.getString(column));
        } catch (JsonProcessingException failure) {
            throw new SQLException("Invalid observation JSON.", failure);
        }
    }
}
