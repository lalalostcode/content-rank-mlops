package io.contentranking;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

import java.util.List;
import org.junit.jupiter.api.Test;
import org.springframework.jdbc.core.simple.JdbcClient;

class ReviewStatusTest {
    @Test
    void onlyExplicitStatusTransitionsAreAvailable() {
        assertThat(ReviewStatus.OPEN.canMoveTo(ReviewStatus.IN_REVIEW)).isTrue();
        assertThat(ReviewStatus.DEFERRED.canMoveTo(ReviewStatus.IN_REVIEW)).isTrue();
        assertThat(ReviewStatus.ACTION_TAKEN.canMoveTo(ReviewStatus.RESOLVED)).isTrue();
        assertThat(ReviewStatus.OPEN.canMoveTo(ReviewStatus.RESOLVED)).isFalse();
        assertThat(ReviewStatus.IN_REVIEW.canMoveTo(ReviewStatus.NO_ACTION)).isFalse();
        assertThat(ReviewStatus.RESOLVED.canMoveTo(ReviewStatus.OPEN)).isFalse();
        assertThat(ReviewStatus.NO_ACTION.isTerminal()).isTrue();
    }

    @Test
    void cursorsPreserveRunAndRejectInvalidInput() {
        assertThat(Cursors.decode(Cursors.encode("run-1", 4))).containsExactly("run-1", "4");
        assertThatThrownBy(() -> Cursors.decode("invalid %%")).isInstanceOf(ApiException.class);
    }

    @Test
    void controllerReturnsScopedLookupResults() {
        RankingReadService reader = mock(RankingReadService.class);
        List<RankingReadService.ClientView> expected = List.of(new RankingReadService.ClientView("example", "Example"));
        when(reader.clients()).thenReturn(expected);
        var controller = new RankingController(mock(JdbcClient.class), reader, mock(ReviewService.class));
        assertThat(controller.clients()).isEqualTo(expected);
    }
}
