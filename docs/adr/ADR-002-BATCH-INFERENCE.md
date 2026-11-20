# ADR-002 · Score complete client inventories offline

Status: proposed for architecture review.

## Context

Ranking depends on relative features and within-client scores computed across the eligible inventory at an observation cutoff. The dashboard consumes a stable queue while the next batch is processed.

## Alternatives

- Batch score a complete eligible client inventory and publish a snapshot.
- Evaluate individual items on demand with precomputed client context.

## Decision and rationale

Run Python scoring locally against authorized inputs and publish the results to PostgreSQL. A complete client batch provides consistent feature context and stable positions for a cutoff. Before Phase 6, a reproducible CLI loads an immutable trained artifact using an expected SHA-256 digest from its model manifest. It verifies the artifact bytes and feature schema version before scoring. The Product MVP requires this path to reach the React dashboard and a persistent analyst review.

## Consequences

Record the model identifier, artifact digest, feature schema version, input digest, observation cutoff and scoring run metadata with publication. Expose the cutoff to the analyst. Keep serving the last valid published run if a later batch fails verification or publication. Synthetic queues support development, tests and the public demo. Phase 6 wraps the established scoring path with managed model versioning and orchestration.

## Revisit conditions

Revisit the full-inventory batch size or cadence if measured runtime breaches the agreed batch budget or analysts need fresher results than the available authorized observations and cadence can supply.
