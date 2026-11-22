package io.contentranking;

import com.fasterxml.jackson.annotation.JsonAlias;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.persistence.EntityManager;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.PositiveOrZero;
import jakarta.validation.constraints.Size;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Clock;
import java.time.OffsetDateTime;
import java.time.ZoneOffset;
import java.util.HexFormat;
import java.util.List;
import java.util.UUID;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.jdbc.core.simple.JdbcClient;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
class ReviewService {
    record StatusRequest(UUID caseId, @Size(max = 128) String runId, @Size(max = 128) String candidateRunId,
                         @JsonAlias("targetStatus") @NotNull ReviewStatus status,
                         @NotNull @PositiveOrZero Long expectedVersion) {}

    record DecisionRequest(@NotNull UUID caseId, @NotBlank @Size(max = 128) String runId,
                           @NotBlank @Pattern(regexp = "act|defer|no_action") String decision,
                           @Size(max = 1000) String note, @NotNull @PositiveOrZero Long expectedVersion) {}

    record MutationResult(UUID caseId, ReviewStatus status, long version, UUID eventId) {}
    record Mutation(MutationResult result, boolean replayed) {}
    record Replay(String fingerprint, MutationResult result) {}

    private final JdbcClient jdbc;
    private final RankingReadService reads;
    private final ReviewCaseRepository cases;
    private final EntityManager entityManager;
    private final ObjectMapper mapper;
    private final Clock clock;
    private final String actor;

    ReviewService(JdbcClient jdbc, RankingReadService reads, ReviewCaseRepository cases, EntityManager entityManager,
                  ObjectMapper mapper, Clock clock, @Value("${ranking.analyst}") String actor) {
        this.jdbc = jdbc;
        this.reads = reads;
        this.cases = cases;
        this.entityManager = entityManager;
        this.mapper = mapper;
        this.clock = clock;
        this.actor = actor;
    }

    @Transactional
    Mutation transition(String client, String item, String key, StatusRequest request) {
        String current = lockClient(client);
        String fingerprint = fingerprint("status", item, request);
        Mutation replay = replay(client, key, fingerprint);
        if (replay != null) return replay;

        String run = request.caseId() == null ? request.candidateRunId() : request.runId();
        if (run == null || run.isBlank() || (request.caseId() == null && request.runId() != null)
            || (request.caseId() != null && request.candidateRunId() != null)) {
            throw ApiException.invalid("Supply the candidate run or an existing case and evidence run.");
        }

        ReviewCase review;
        RankingReadService.RankItem evidence;
        if (request.caseId() == null) {
            if (!run.equals(current) || request.expectedVersion() != 0 || request.status() != ReviewStatus.IN_REVIEW) {
                throw ApiException.conflict("The open review candidate changed. Refresh the queue.");
            }
            evidence = reads.detail(client, run, item);
            if (evidence.caseId() != null) throw ApiException.conflict("This item already has a review case.");
            review = new ReviewCase(client, item, run, evidence.cutoff());
            entityManager.persist(review);
            entityManager.flush();
            append(review, run, evidence.snapshotId(), null, "CASE_OPENED", null, null);
        } else {
            review = caseAtVersion(client, item, request.caseId(), request.expectedVersion());
            evidence = reviewEvidence(review, run);
        }
        if (!review.status.canMoveTo(request.status())) {
            throw ApiException.conflict("This status transition is unavailable.");
        }
        return apply(client, key, fingerprint, current, review, run, evidence.snapshotId(),
            request.status(), null, null);
    }

    @Transactional
    Mutation decide(String client, String item, String key, DecisionRequest request) {
        String current = lockClient(client);
        String fingerprint = fingerprint("decision", item, request);
        Mutation replay = replay(client, key, fingerprint);
        if (replay != null) return replay;

        ReviewCase review = caseAtVersion(client, item, request.caseId(), request.expectedVersion());
        if (review.status != ReviewStatus.IN_REVIEW) {
            throw ApiException.conflict("Decisions require an active In Review case.");
        }
        RankingReadService.RankItem evidence = reviewEvidence(review, request.runId());
        ReviewStatus target = switch (request.decision()) {
            case "act" -> ReviewStatus.ACTION_TAKEN;
            case "defer" -> ReviewStatus.DEFERRED;
            case "no_action" -> ReviewStatus.NO_ACTION;
            default -> throw ApiException.invalid("Unsupported review decision.");
        };
        return apply(client, key, fingerprint, current, review, request.runId(), evidence.snapshotId(),
            target, request.decision(), request.note());
    }

    private ReviewCase caseAtVersion(String client, String item, UUID id, long version) {
        ReviewCase review = cases.findByIdAndClientIdAndContentId(id, client, item)
            .orElseThrow(() -> ApiException.missing("Review case not found."));
        if (review.version != version) throw ApiException.conflict("The review changed. Refresh and retry.");
        return review;
    }

    private RankingReadService.RankItem reviewEvidence(ReviewCase review, String run) {
        RankingReadService.RankItem evidence = reads.detail(review.clientId, run, review.contentId);
        if (evidence.cutoff().isBefore(review.openingCutoff)) {
            throw ApiException.conflict("Review evidence predates this case.");
        }
        return evidence;
    }

    private Mutation apply(String client, String key, String fingerprint, String current, ReviewCase review,
                           String run, String snapshot, ReviewStatus target, String decision, String note) {
        ReviewStatus prior = review.status;
        review.status = target;
        if (target.isTerminal()) {
            if (current == null) throw ApiException.conflict("The client has no published cutoff.");
            review.terminalCutoff = reads.run(client, current).observationCutoff();
        }
        cases.flush();
        UUID event = append(review, run, snapshot, prior, decision == null ? "STATUS_CHANGED" : "DECISION_RECORDED",
            decision, note);
        jdbc.sql("INSERT INTO review_request (client_id, request_key, fingerprint, event_id) VALUES (:client,:key,:hash,:event)")
            .param("client", client).param("key", key).param("hash", fingerprint).param("event", event).update();
        return new Mutation(new MutationResult(review.id, target, review.version, event), false);
    }

    private String lockClient(String client) {
        return jdbc.sql("SELECT published_run_id FROM lock_review_client(:client)")
            .param("client", client).query((row, index) -> new String[]{row.getString(1)})
            .optional().orElseThrow(() -> ApiException.missing("Client not found."))[0];
    }

    private Mutation replay(String client, String key, String fingerprint) {
        Replay replay = jdbc.sql("""
            SELECT q.fingerprint, e.id, e.case_id, e.new_status, e.resulting_version
            FROM review_request q JOIN review_event e ON e.id = q.event_id
            WHERE q.client_id = :client AND q.request_key = :key
            """).param("client", client).param("key", key).query((row, index) -> new Replay(
                row.getString("fingerprint"), new MutationResult(row.getObject("case_id", UUID.class),
                    ReviewStatus.valueOf(row.getString("new_status")), row.getLong("resulting_version"),
                    row.getObject("id", UUID.class)))).optional().orElse(null);
        if (replay == null) return null;
        if (!replay.fingerprint().equals(fingerprint)) {
            throw ApiException.conflict("This idempotency key belongs to a different request.");
        }
        return new Mutation(replay.result(), true);
    }

    private UUID append(ReviewCase review, String run, String snapshot, ReviewStatus prior, String type,
                        String decision, String note) {
        UUID id = UUID.randomUUID();
        jdbc.sql("""
            INSERT INTO review_event (id,case_id,client_id,content_id,resulting_version,actor,occurred_at,
                event_type,run_id,snapshot_id,prior_status,new_status,decision,note)
            VALUES (:id,:case,:client,:item,:version,:actor,:at,:type,:run,:snapshot,:prior,:status,:decision,:note)
            """).param("id", id).param("case", review.id).param("client", review.clientId)
            .param("item", review.contentId).param("version", review.version).param("actor", actor)
            .param("at", OffsetDateTime.ofInstant(clock.instant(), ZoneOffset.UTC)).param("type", type)
            .param("run", run).param("snapshot", snapshot).param("prior", prior == null ? null : prior.name())
            .param("status", review.status.name()).param("decision", decision).param("note", note).update();
        return id;
    }

    private String fingerprint(String action, String item, Object request) {
        try {
            byte[] payload = mapper.writeValueAsBytes(List.of(action, item, request));
            return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(payload));
        } catch (NoSuchAlgorithmException | JsonProcessingException failure) {
            throw new IllegalStateException("Could not fingerprint review request.", failure);
        }
    }
}
