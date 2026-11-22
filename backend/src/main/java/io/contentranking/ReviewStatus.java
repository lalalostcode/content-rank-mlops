package io.contentranking;

enum ReviewStatus {
    OPEN, IN_REVIEW, ACTION_TAKEN, DEFERRED, RESOLVED, NO_ACTION;

    boolean canMoveTo(ReviewStatus next) {
        return switch (this) {
            case OPEN, DEFERRED -> next == IN_REVIEW;
            case ACTION_TAKEN -> next == RESOLVED;
            default -> false;
        };
    }

    boolean isTerminal() {
        return this == RESOLVED || this == NO_ACTION;
    }
}
