# ADR-005 · Static React with independent synthetic fixtures

Status: proposed for architecture review.

## Context

The portfolio demo needs to run in a visitor's browser without access to the private dataset and model. The local Product MVP needs to prove the full path from authorized observations to a persisted review.

## Alternatives

- Publish static React assets with an independent synthetic adapter.
- Host a separate public app stack and a database seeded exclusively with synthetic data.

## Decision and rationale

Build the public demo as a static React site using independently generated fixtures behind the shared adapter contract. Label the data and review interactions as simulated. Static hosting gives visitors a walkthrough without backend credentials or public write endpoints. The local Product MVP uses the Spring API and PostgreSQL with a queue produced by scoring authorized data with a trained model.

## Consequences

Simulated review changes live in browser memory and reset on reload. Verify that the built demo bundles only synthetic data and makes no backend requests during the analyst journey. Test the two adapters against the same response shapes and run the Product MVP acceptance test in the API-backed local environment.

## Revisit conditions

Revisit hosting if the public demo must support persistent or shared reviews. A hosted alternative would require a dedicated synthetic datastore and an operating plan for public writes.
