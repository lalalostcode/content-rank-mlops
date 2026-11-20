# Phase 0 · REPOSITORY AUDIT

## Audit evidence · 20 November 2026

The requested workspace was absent on discovery. Created the main repository and cloned Paul separately. setup.ps1 and README_START_HERE.md were missing. The adjacent FlyRank Internship directory supplied GUIDE, DATA_USE, dictionary, capstone, scripts and notebooks. Its advanced ranking script groups folds by client but reports mean fold P@50. Its leakage notebook audits availability. Reuse validation ideas and rule definitions after checking terms. Recompute queue metrics within clients.

|Component|Status and evidence|
|---|---|
|Git repository and planning files|Created in this preparation pass|
|Paul reference|Clone verified via Git revision; services unverified|
|API, frontend, Python pipeline, migrations, tests, Compose, CI|Missing on discovery; planned in phases 2–7. No existing project tests to run|
|Runtime dependency manifests and locks|Missing; dependency compatibility unverified. Introduce pinned Python lock, Maven wrapper and npm lock with owning module|
|CLI probes|Git 2.48.1, JDK and javac 17.0.21, Node 22.14.0, npm 10.9.2, uv 0.9.8 and Compose 2.34.0. The Store python alias failed. The installed 3.13.9 interpreter ran by absolute path and the uv no-cache probe located it. Maven is absent from PATH and the project wrapper is planned for Phase 4|
|Container integration|Blocked in the audited shell. The desktop-linux context points to an unavailable Docker Engine pipe. The WSL status probe in that shell reported that WSL was missing|
|Warehouse|Gated; user authorization unverified|

The Windows bootstrap records the remedies and database setup for Phase 4–5. [Local bootstrap](../LOCAL_BOOTSTRAP.md)

## Iteration 0.1 · Inventory the workspace

- **Objective and scope** — Inventory the workspace.
- **Prerequisite** — Workspace path and brief.
- **Tasks** — List hidden files, Git roots, manifests and tests. Classify by evidence.
- **Expected files and deliverable** — docs/phases/PHASE_00_REPOSITORY_AUDIT.md.
- **Verification command** — `git status --short --branch` from project root in PowerShell.
- **Verification and review** — Every discovered component has a status and evidence.
- **Risk** — Assuming prior starter exists.
- **Definition of done and exit gate** — Record the command result and review evidence against the acceptance criterion before proceeding.

## Iteration 0.2 · Verify references and tools

- **Objective and scope** — Verify references and tools.
- **Prerequisite** — 0.1.
- **Tasks** — Inspect source terms, capstone, Paul checkout and available runtimes. Record blockers.
- **Expected files and deliverable** — docs/architecture/REFERENCE_ARCHITECTURE_AUDIT.md.
- **Verification command** — `git -C ../paul-reference rev-parse HEAD` from project root in PowerShell.
- **Verification and review** — Pinned source revision and tool probes recorded.
- **Risk** — Installed CLI may lack a daemon.
- **Definition of done and exit gate** — Record the command result and review evidence against the acceptance criterion before proceeding.
