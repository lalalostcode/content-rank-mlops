# Phase 1 · ARCHITECTURE

## Iteration 1.1 · Specify the analyst workflow

- **Objective and scope** — Specify the analyst workflow.
- **Prerequisite** — Phase 0 exit gate.
- **Tasks** — Map users and exception paths to FR IDs, inputs and test oracles.
- **Expected files and deliverable** — docs/prd/.
- **Verification command** — `git diff --check` from project root in PowerShell.
- **Verification and review** — Every Must has an acceptance test.
- **Risk** — Ambiguous review ownership.
- **Definition of done and exit gate** — Record the command result and review evidence against the acceptance criterion before proceeding.

## Iteration 1.2 · Review boundaries and contracts

- **Objective and scope** — Review boundaries and contracts.
- **Prerequisite** — 1.1.
- **Tasks** — Trace tenant, run and version across diagrams, endpoints and schema. Review ADRs and approve Phase 2 scope.
- **Expected files and deliverable** — docs/architecture/, docs/adr/.
- **Verification command** — `git ls-files docs/architecture` from project root in PowerShell.
- **Verification and review** — Reviewer accepts ownership, data access and evaluation protocol.
- **Risk** — Unapproved dataset scope.
- **Definition of done and exit gate** — Record the command result and review evidence against the acceptance criterion before proceeding.
