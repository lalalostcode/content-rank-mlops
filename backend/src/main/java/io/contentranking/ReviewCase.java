package io.contentranking;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import jakarta.persistence.Version;
import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "review_case")
class ReviewCase {
    @Id UUID id;
    @Column(nullable = false, updatable = false) String clientId;
    @Column(nullable = false, updatable = false) String contentId;
    @Column(nullable = false, updatable = false) String issueType;
    @Column(nullable = false, updatable = false) String openingRunId;
    @Column(nullable = false, updatable = false) Instant openingCutoff;
    Instant terminalCutoff;
    @Enumerated(EnumType.STRING) @Column(nullable = false) ReviewStatus status;
    @Version long version;

    protected ReviewCase() {}

    ReviewCase(String client, String item, String run, Instant cutoff) {
        id = UUID.randomUUID();
        clientId = client;
        contentId = item;
        issueType = RankingReadService.ISSUE_TYPE;
        openingRunId = run;
        openingCutoff = cutoff;
        status = ReviewStatus.OPEN;
    }
}
