# ADR-001 · Spring Boot REST with JPA

Status: proposed for architecture review.

## Context

React needs client-scoped ranking reads and persistent analyst reviews. Model training and scoring run in the Python pipeline and may outlast an interactive request. Spring and Flyway already define the API and database ownership boundaries.

## Alternatives

- Spring Boot with JPA for the application API and Python for the offline batch.
- Spring Boot backed by a separate Python ranking HTTP service.

## Decision and rationale

Use Spring Boot with JPA as the sole application REST API. Spring owns client authorization, review validation and review transactions. It serves published PostgreSQL rankings through the REST contract. The offline Python process prepares and publishes scores for later reads. A second HTTP service would duplicate authorization and contract tests without improving access to an already published queue.

## Consequences

The team maintains Java and Python tooling and versions the database publication contract they share. Backend integration tests must exercise the same publication schema that the offline scorer writes. The Phase 5 acceptance test follows model-generated rows through Spring and React and verifies the persisted review after a reload.

## Revisit conditions

Revisit the serving boundary if a product requirement introduces request-time scoring and tests show that the batch cadence cannot meet an agreed freshness target. Revisit the current identity setup before shared deployment requires authenticated client access.
