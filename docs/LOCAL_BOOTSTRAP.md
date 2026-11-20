# Local bootstrap for Phase 4–5

Use PowerShell 7 from a local clone. The tool probes below can run now. Database setup is for a dedicated local integration instance. Build, launch and test commands depend on the modules and locks delivered in their respective phases.

## 1. Verify the toolchain

```powershell
git --version
java -version
javac -version
node --version
npm.cmd --version
uv --version
wsl.exe --status
docker context show
docker info --format '{{.OSType}} {{.ServerVersion}}'
```

- **Docker Engine** — Launch Docker Desktop and use its WSL 2 Linux engine. If WSL is absent on the host, run `wsl.exe --install --no-distribution` in an elevated shell, restart Windows if prompted, then run `wsl.exe --update`. If another context is active, verify `desktop-linux` appears in `docker context ls` and select it with `docker context use desktop-linux`. Wait for `docker info` to report a Linux server and version before starting database-backed tests. Use Docker Desktop's Troubleshoot > Restart if its Linux pipe is still missing. [Docker Desktop for Windows](https://docs.docker.com/desktop/setup/install/windows-install/) · [WSL commands](https://learn.microsoft.com/en-us/windows/wsl/basic-commands)
- **Java and Maven** — Start with JDK 17 and confirm it matches the Phase 4 POM. If the wrapper selects a different JDK, point `JAVA_HOME` to the intended JDK root and check `javac -version`. Phase 4 should commit `mvnw`, `mvnw.cmd` and `.mvn/wrapper/maven-wrapper.properties` with a pinned Maven distribution. Generate them through the Spring project starter, or run `mvn.cmd wrapper:wrapper "-Dmaven=$mavenVersion"` from the directory containing `pom.xml` after setting `$mavenVersion` and placing a verified Maven distribution on PATH. Verify with `.\mvnw.cmd --version` inside `backend`. Allow the first wrapper run to download Maven and dependencies. Subsequent checkouts use the wrapper. [Apache Maven Wrapper](https://maven.apache.org/tools/wrapper/index.html)
- **Python** — Use the pipeline's pinned version once the lock exists. For a preflight on the audit machine, `$pipelinePython = uv --no-cache python find --managed-python 3.13` locates the installed interpreter. Run `& $pipelinePython --version` to bypass the Windows Store alias. If the pinned version is absent, install it with `uv python install <version>` with the project's version in place of `<version>`, then locate it with `uv python find --managed-python <version>`. If the default cache is unwritable, use `--no-cache` for the probe or set `UV_CACHE_DIR` to a writable directory. From the Python project root, use `uv sync --locked --python $pipelinePython` and `uv run --locked python --version` after the lock is available and `$pipelinePython` points to its interpreter. [uv Python versions](https://docs.astral.sh/uv/concepts/python-versions/)
- **Node** — Confirm the version specified by the frontend and install dependencies with `npm.cmd ci` from `frontend` once its lockfile is available.

## 2. Start local PostgreSQL

Use a dedicated instance and volume for integration. The example assumes port 5432 is free. If using another port, update the published port, JDBC URL and `PGPORT` together. The named volume persists through a container restart. [PostgreSQL Docker image](https://hub.docker.com/_/postgres)

```powershell
$env:POSTGRES_PASSWORD = Read-Host -MaskInput 'Choose a local PostgreSQL bootstrap password'
docker run --detach --name content-ranking-db --publish 127.0.0.1:5432:5432 --env POSTGRES_PASSWORD --env POSTGRES_DB=content_ranking --volume content-ranking-db:/var/lib/postgresql/data postgres:16
Remove-Item Env:POSTGRES_PASSWORD
docker exec content-ranking-db pg_isready -h 127.0.0.1 -U postgres -d content_ranking
```

Repeat the readiness check until it reports accepting connections. For an existing stopped container, run `docker start content-ranking-db` and check readiness again. For an existing native PostgreSQL 16 instance, create a dedicated `content_ranking` database and perform the same role setup. Tests that provision PostgreSQL through Docker still require the engine.

On a fresh database, connect as the initialization user with `docker exec -it content-ranking-db psql -U postgres -d content_ranking`. In the session, create the roles and choose separate local passwords at the prompts.

```sql
CREATE ROLE content_migrate LOGIN;
CREATE ROLE content_app LOGIN;
CREATE ROLE content_scoring LOGIN;
ALTER DATABASE content_ranking OWNER TO content_migrate;
\password content_migrate
\password content_app
\password content_scoring
\q
```

Phase 4 Flyway migrations own the schema and grant the app and scoring roles only their required access. The migration role owns DDL. The app role reads ranking data and writes analyst review data. The scoring role publishes rankings and writes ingestion and run metadata through the Phase 4 persistence contract. Keep credentials in local environment variables.

## 3. Run Phase 4–5 integration checks

1. From `backend`, run `.\mvnw.cmd verify` using the Phase 4 project's isolated integration test database settings. To launch against the local instance above and apply Flyway migrations, set the following in the backend shell.

   ```powershell
   $env:SPRING_DATASOURCE_URL = 'jdbc:postgresql://127.0.0.1:5432/content_ranking'
   $env:SPRING_DATASOURCE_USERNAME = 'content_app'
   $env:SPRING_DATASOURCE_PASSWORD = Read-Host -MaskInput 'Application role password'
   $env:SPRING_FLYWAY_USER = 'content_migrate'
   $env:SPRING_FLYWAY_PASSWORD = Read-Host -MaskInput 'Migration role password'
   $env:SERVER_ADDRESS = '127.0.0.1'
   .\mvnw.cmd spring-boot:run
   ```

2. In a separate shell, check readiness and configure the scoring CLI database connection. Use the authorized manifest and model bundle to publish the acceptance run. [Phase 5 acceptance procedure](phases/PHASE_05_DASHBOARD.md)

   ```powershell
   Invoke-RestMethod http://127.0.0.1:8080/api/v1/health
   $env:PGHOST = '127.0.0.1'
   $env:PGPORT = '5432'
   $env:PGDATABASE = 'content_ranking'
   $env:PGUSER = 'content_scoring'
   $env:PGPASSWORD = Read-Host -MaskInput 'Scoring role password'
   ```

3. From `frontend` in a new shell, run `npm.cmd ci` and `npm.cmd run dev -- --host 127.0.0.1 --port 5173 --strictPort`. Phase 5 should default the local adapter to the live Spring API through a Vite proxy for `/api/v1` at `http://127.0.0.1:8080`. Run `npm.cmd run test:e2e:mvp` from a separate shell using the published run ID. The suite uses the local dashboard on port 5173 and Spring on port 8080. Record the run metadata and test results in the approved local workspace. [Phase 5 acceptance commands](phases/PHASE_05_DASHBOARD.md#product-mvp-end-to-end-acceptance-test)
