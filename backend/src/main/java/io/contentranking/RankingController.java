package io.contentranking;

import jakarta.validation.Valid;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.jdbc.core.simple.JdbcClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1")
class RankingController {
    private static final String CLIENT = "/clients/{client}";
    private static final String ITEM = CLIENT + "/items/{item}";

    private final JdbcClient jdbc;
    private final RankingReadService reads;
    private final ReviewService reviews;

    RankingController(JdbcClient jdbc, RankingReadService reads, ReviewService reviews) {
        this.jdbc = jdbc;
        this.reads = reads;
        this.reviews = reviews;
    }

    @GetMapping("/health")
    Map<String, String> health() {
        jdbc.sql("SELECT 1").query(Integer.class).single();
        return Map.of("status", "UP");
    }

    @GetMapping("/clients")
    List<RankingReadService.ClientView> clients() {
        return reads.clients();
    }

    @GetMapping(CLIENT + "/overview")
    RankingReadService.Overview overview(@PathVariable String client, @RequestParam(required = false) String snapshotId) {
        return reads.overview(client, snapshotId);
    }

    @GetMapping(CLIENT + "/rankings")
    RankingReadService.RankingPage rankings(@PathVariable String client, @RequestParam(required = false) String runId,
                                            @RequestParam(required = false) ReviewStatus status,
                                            @RequestParam(required = false) String cursor,
                                            @RequestParam(required = false) @Size(max = 128) String q,
                                            @RequestParam(defaultValue = "50") @Min(1) @Max(100) int limit) {
        return reads.rankings(client, runId, cursor, status, q, limit);
    }

    @GetMapping(CLIENT + "/rankings/{run}/items/{item}")
    RankingReadService.RankItem detail(@PathVariable String client, @PathVariable String run, @PathVariable String item) {
        return reads.detail(client, run, item);
    }

    @GetMapping(ITEM + "/observations")
    RankingReadService.ObservationHistory observations(@PathVariable String client, @PathVariable String item,
                                                       @RequestParam(required = false) UUID caseId) {
        return reads.observations(client, item, caseId);
    }

    @GetMapping(ITEM + "/actions")
    RankingReadService.EventPage history(@PathVariable String client, @PathVariable String item,
                                        @RequestParam(required = false) UUID caseId,
                                        @RequestParam(required = false) String cursor,
                                        @RequestParam(defaultValue = "50") @Min(1) @Max(100) int limit) {
        return reads.history(client, item, caseId, cursor, limit);
    }

    @PostMapping(ITEM + "/actions")
    ResponseEntity<ReviewService.MutationResult> decision(@PathVariable String client, @PathVariable String item,
             @RequestHeader("Idempotency-Key") @NotBlank @Size(max = 200) String key,
             @Valid @RequestBody ReviewService.DecisionRequest decision) {
        ReviewService.Mutation mutation = reviews.decide(client, item, key, decision);
        return ResponseEntity.status(mutation.replayed() ? HttpStatus.OK : HttpStatus.CREATED).body(mutation.result());
    }

    @PatchMapping(ITEM + "/status")
    ReviewService.MutationResult status(@PathVariable String client, @PathVariable String item,
             @RequestHeader("Idempotency-Key") @NotBlank @Size(max = 200) String key,
             @Valid @RequestBody ReviewService.StatusRequest status) {
        return reviews.transition(client, item, key, status).result();
    }

    @GetMapping(CLIENT + "/runs/{run}")
    RankingReadService.RunView run(@PathVariable String client, @PathVariable String run) {
        return reads.run(client, run);
    }

    @GetMapping(CLIENT + "/models/{model}")
    RankingReadService.ModelView model(@PathVariable String client, @PathVariable String model) {
        return reads.model(client, model);
    }
}
