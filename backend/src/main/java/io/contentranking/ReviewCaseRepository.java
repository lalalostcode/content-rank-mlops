package io.contentranking;

import java.util.Optional;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

interface ReviewCaseRepository extends JpaRepository<ReviewCase, UUID> {
    Optional<ReviewCase> findByIdAndClientIdAndContentId(UUID id, String clientId, String contentId);
}
