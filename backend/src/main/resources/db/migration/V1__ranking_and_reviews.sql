CREATE TABLE client (
    id text PRIMARY KEY,
    label text NOT NULL,
    published_run_id text
);

CREATE TABLE content (
    client_id text NOT NULL REFERENCES client(id),
    id text NOT NULL,
    PRIMARY KEY (client_id, id)
);

CREATE TABLE model_version (
    id text PRIMARY KEY,
    artifact_sha256 text NOT NULL CHECK (artifact_sha256 ~ '^[a-f0-9]{64}$'),
    feature_schema_version text NOT NULL,
    registry_uri text,
    registry_version text
);

CREATE TABLE scoring_run (
    client_id text NOT NULL REFERENCES client(id),
    id text NOT NULL,
    snapshot_id text NOT NULL,
    input_digest text NOT NULL CHECK (input_digest ~ '^[a-f0-9]{64}$'),
    observation_cutoff timestamptz NOT NULL,
    transform_revision text NOT NULL,
    model_id text NOT NULL REFERENCES model_version(id),
    status text NOT NULL,
    input_rows integer NOT NULL CHECK (input_rows >= 0),
    eligible_rows integer NOT NULL CHECK (eligible_rows BETWEEN 0 AND input_rows),
    started_at timestamptz NOT NULL,
    finished_at timestamptz NOT NULL CHECK (finished_at >= started_at),
    published_at timestamptz NOT NULL,
    PRIMARY KEY (client_id, id),
    UNIQUE (client_id, input_digest, transform_revision, model_id),
    UNIQUE (client_id, id, snapshot_id)
);

ALTER TABLE client ADD CONSTRAINT client_published_run_fk
    FOREIGN KEY (id, published_run_id) REFERENCES scoring_run(client_id, id);

CREATE TABLE observation (
    client_id text NOT NULL,
    content_id text NOT NULL,
    snapshot_id text NOT NULL,
    cutoff timestamptz NOT NULL,
    source_release text NOT NULL,
    input_digest text NOT NULL CHECK (input_digest ~ '^[a-f0-9]{64}$'),
    window_start timestamptz NOT NULL,
    window_end timestamptz NOT NULL CHECK (window_end > window_start AND window_end <= cutoff),
    metrics jsonb NOT NULL CHECK (jsonb_typeof(metrics) = 'object'),
    declining boolean,
    PRIMARY KEY (client_id, content_id, snapshot_id),
    FOREIGN KEY (client_id, content_id) REFERENCES content(client_id, id)
);
CREATE INDEX observation_client_snapshot_idx ON observation (client_id, snapshot_id);

CREATE TABLE rank_item (
    client_id text NOT NULL,
    run_id text NOT NULL,
    content_id text NOT NULL,
    snapshot_id text NOT NULL,
    position integer NOT NULL CHECK (position > 0),
    score double precision NOT NULL CHECK (score > '-Infinity'::double precision AND score < 'Infinity'::double precision),
    reason_codes jsonb NOT NULL CHECK (jsonb_typeof(reason_codes) = 'array'),
    PRIMARY KEY (client_id, run_id, content_id),
    UNIQUE (client_id, run_id, position),
    FOREIGN KEY (client_id, run_id, snapshot_id) REFERENCES scoring_run(client_id, id, snapshot_id),
    FOREIGN KEY (client_id, content_id, snapshot_id) REFERENCES observation(client_id, content_id, snapshot_id)
);

CREATE TABLE review_case (
    id uuid PRIMARY KEY,
    client_id text NOT NULL,
    content_id text NOT NULL,
    issue_type text NOT NULL CHECK (issue_type = 'DECLINE_PRIORITY'),
    opening_run_id text NOT NULL,
    opening_cutoff timestamptz NOT NULL,
    terminal_cutoff timestamptz,
    status text NOT NULL CHECK (status IN ('OPEN', 'IN_REVIEW', 'ACTION_TAKEN', 'DEFERRED', 'RESOLVED', 'NO_ACTION')),
    version bigint NOT NULL CHECK (version >= 0),
    UNIQUE (client_id, content_id, id),
    UNIQUE (client_id, content_id, issue_type, opening_cutoff),
    FOREIGN KEY (client_id, opening_run_id, content_id) REFERENCES rank_item(client_id, run_id, content_id),
    CHECK ((status IN ('RESOLVED', 'NO_ACTION')) = (terminal_cutoff IS NOT NULL)),
    CHECK (terminal_cutoff IS NULL OR terminal_cutoff >= opening_cutoff)
);
CREATE UNIQUE INDEX active_review_case_idx ON review_case(client_id, content_id, issue_type)
    WHERE terminal_cutoff IS NULL;

CREATE TABLE review_event (
    id uuid PRIMARY KEY,
    case_id uuid NOT NULL,
    client_id text NOT NULL,
    content_id text NOT NULL,
    resulting_version bigint NOT NULL CHECK (resulting_version >= 0),
    actor text NOT NULL,
    occurred_at timestamptz NOT NULL,
    event_type text NOT NULL CHECK (event_type IN ('CASE_OPENED', 'STATUS_CHANGED', 'DECISION_RECORDED')),
    run_id text NOT NULL,
    snapshot_id text NOT NULL,
    prior_status text,
    new_status text NOT NULL,
    decision text CHECK (decision IN ('act', 'defer', 'no_action')),
    note varchar(1000),
    FOREIGN KEY (client_id, content_id, case_id) REFERENCES review_case(client_id, content_id, id),
    FOREIGN KEY (client_id, run_id, content_id) REFERENCES rank_item(client_id, run_id, content_id),
    FOREIGN KEY (client_id, content_id, snapshot_id) REFERENCES observation(client_id, content_id, snapshot_id),
    UNIQUE (case_id, resulting_version)
);
CREATE INDEX review_event_history_idx ON review_event(client_id, content_id, occurred_at, resulting_version, id);

CREATE TABLE review_request (
    client_id text NOT NULL REFERENCES client(id),
    request_key text NOT NULL CHECK (length(request_key) BETWEEN 1 AND 200),
    fingerprint text NOT NULL CHECK (fingerprint ~ '^[a-f0-9]{64}$'),
    event_id uuid NOT NULL UNIQUE REFERENCES review_event(id),
    PRIMARY KEY (client_id, request_key)
);

CREATE FUNCTION prevent_review_event_mutation() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'Review events are immutable';
END;
$$;
CREATE TRIGGER immutable_review_event BEFORE UPDATE OR DELETE ON review_event
    FOR EACH ROW EXECUTE FUNCTION prevent_review_event_mutation();

CREATE FUNCTION lock_review_client(requested_client text) RETURNS TABLE (published_run_id text)
LANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog, public AS $$
    SELECT c.published_run_id FROM public.client c WHERE c.id = requested_client FOR UPDATE;
$$;
REVOKE ALL ON FUNCTION lock_review_client(text) FROM PUBLIC;

DO $$
BEGIN
    IF EXISTS (SELECT FROM pg_roles WHERE rolname = 'content_app') THEN
        GRANT USAGE ON SCHEMA public TO content_app;
        GRANT SELECT ON client, content, model_version, scoring_run, observation, rank_item TO content_app;
        GRANT EXECUTE ON FUNCTION lock_review_client(text) TO content_app;
        GRANT SELECT, INSERT, UPDATE ON review_case TO content_app;
        GRANT SELECT, INSERT ON review_event, review_request TO content_app;
    END IF;
    IF EXISTS (SELECT FROM pg_roles WHERE rolname = 'content_scoring') THEN
        GRANT USAGE ON SCHEMA public TO content_scoring;
        GRANT SELECT, INSERT ON client, content, model_version, scoring_run, observation, rank_item TO content_scoring;
        GRANT UPDATE (published_run_id) ON client TO content_scoring;
    END IF;
END;
$$;
