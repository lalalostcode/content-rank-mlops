WITH eligible AS (
    SELECT
        client_id, content_id,
        search_volume, competition, cpc, word_count, char_count,
        ln(1 + impressions_90d) AS log_impressions_90d,
        ln(1 + clicks_90d) AS log_clicks_90d,
        ln(1 + sessions_90d) AS log_sessions_90d,
        ln(1 + ai_sessions_90d) AS log_ai_sessions_90d,
        days_with_impressions, days_with_sessions, content_age_days, days_since_last_update,
        ctr, nullif(avg_position, 0) AS avg_position, engagement_rate, scroll_rate, ai_traffic_pct,
        competition_level, content_type, main_intent, age_tier, freshness_tier, word_count_tier,
        impression_tier, position_tier,
        impressions_90d, clicks_90d, sessions_90d
    FROM snapshot_signals
    WHERE impressions_90d > 0 AND content_age_days >= 90
)
SELECT
    * EXCLUDE (impressions_90d, clicks_90d, sessions_90d),
    cast(avg_position IS NULL AS DOUBLE) AS missing_position_flag,
    cast(search_volume IS NOT NULL AS DOUBLE) AS has_keyword_data,
    cast(word_count IS NOT NULL AS DOUBLE) AS has_word_count,
    cast(main_intent IS NOT NULL AS DOUBLE) AS has_intent,
    cast(scroll_rate IS NOT NULL AS DOUBLE) AS has_scroll_rate,
    ln(1 + impressions_90d / nullif(days_with_impressions, 0)) AS log_impressions_per_active_day,
    ln(1 + clicks_90d / nullif(days_with_impressions, 0)) AS log_clicks_per_active_day,
    ln(1 + sessions_90d / nullif(days_with_sessions, 0)) AS log_sessions_per_active_day,
    days_with_impressions / 90.0 AS impression_day_coverage,
    days_with_sessions / 90.0 AS session_day_coverage,
    log_impressions_90d * ln(1 + days_since_last_update) AS visibility_x_staleness,
    ln(1 + avg_position) * log_impressions_90d AS position_x_visibility,
    engagement_rate / 100.0 * log_sessions_90d AS engagement_x_sessions,
    word_count / nullif(log_impressions_90d, 0) AS content_depth_per_visibility,
    log_impressions_90d - median(log_impressions_90d) OVER client AS client_log_impressions_delta,
    days_since_last_update - median(days_since_last_update) OVER client AS client_staleness_delta,
    engagement_rate - median(engagement_rate) OVER client AS client_engagement_delta
FROM eligible
WINDOW client AS (PARTITION BY client_id)
ORDER BY client_id, content_id
