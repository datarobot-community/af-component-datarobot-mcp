# Build-time improvements (deploy E2E + user deployments)

Living document for BUZZOK-31992: every trick used to cut deployment time —
for users running `task deploy` and for the deploy E2E CI — plus the
constraints behind them. Update the change log at the bottom whenever one of
these mechanisms changes.

CI timings (deploy step, ubuntu runners; serverless-docker split measured on
run 33109580288 and its re-run):

| case                          | deploy step | dominated by                                   |
|-------------------------------|-------------|------------------------------------------------|
| serverless-ee                 | ~2:40       | pulumi up against a pinned platform EE         |
| workload-docker               | ~2:45       | remote image build from the slim root image    |
| workload-ee                   | ~4:00       | remote build FROM the multi-GB GenAI Agents EE |
| serverless-docker (hash miss) | ~8 min      | EE version build 239 s + Deployment create 116 s |
| serverless-docker (hash hit)  | ~2:42       | get-path — no EE build at all                  |

Why a hash miss always rebuilds even though the shared EE is imported: the
pulumi log shows `= 1 imported` followed by an update with
`[diff: +dockerContextPath]` — imported state never carries the docker
context, so any fresh stack on the build path triggers a new EE version
build. The hash check exists to decide *before* pulumi runs whether the run
needs the build path at all; the reuse lookup, description `mark`, and the
endpoint probe together add only seconds.

## 1. EE Docker image build (`template/{{mcp_app_name_file}}/Dockerfile` + `.dockerignore`)

- **Deps-only build context.** `.dockerignore` excludes `app/`, `tests/`,
  `dev_tools/`, docs, caches, and `start_server.sh` from the EE (app-root)
  context. The image only needs `pyproject.toml` + `uv.lock`; app code reaches
  serverless models via custom-model files, not the image.
- **Single-stage image.** DataRobot remote builds pay for each `FROM` pull and
  cross-stage copy; multi-stage bought nothing on ephemeral CI stacks.
- **No system packages.** The old `docker/Dockerfile` ran
  `apk add build-base curl bash`; all runtime deps have wheels, so the new
  image installs nothing.
- **Deps layer before app layer.** `COPY pyproject.toml uv.lock ./` +
  `uv sync --frozen --no-install-project` is its own layer, cached until the
  lockfile changes. `COPY . .` comes after, so app-only changes never
  invalidate the dependency install.
- **`COPY . .` is load-bearing — do not remove it.** For EE builds the
  `.dockerignore` reduces it to the manifests, but for workload
  DockerfileProvided builds the context is the Files catalog bundle (which has
  no `.dockerignore`), and this line is what puts `app/` into the image.
  Removing it made `CMD ["python", "-m", "app.main"]` crash-loop and the
  workload report status `ERRORED` (caught by the E2E endpoint probe).
- **uv pinned by digest** (`COPY --from=ghcr.io/astral-sh/uv@sha256:…`) — no
  `:latest` resolution; reproducible layer.
- **Dropped `UV_COMPILE_BYTECODE=1`.** Shorter build; cost is first-import
  bytecode compilation at container start (deliberate trade-off).
- **Deleted the `docker/` mirroring machinery.** No more copying
  `pyproject.toml`/`uv.lock` into a second directory on every install/deploy
  (`ensure_docker_dependency_files`, `copy-docker-dependency-files` task).

## 2. Skipping the EE build entirely

- **`DATAROBOT_DEFAULT_MCP_EXECUTION_ENVIRONMENT`** — selecting an existing EE
  (id or platform name) takes the `ExecutionEnvironment.get` path: no Docker
  build at all (serverless-ee / workload-ee cases).
- **Stable shared CI EE name** (`DATAROBOT_MCP_EXECUTION_ENVIRONMENT_NAME` +
  import/`retain_on_delete` in
  `template/infra/infra/{{mcp_app_name_file}}_infra/mcp_execution_environment.py.jinja`)
  — ephemeral CI stacks import/update one retained EE instead of leaving a new
  EE in the tenant per run. Note: this alone does **not** avoid the version
  rebuild — each fresh stack still built a new EE version. Hence:
- **Hash-based EE reuse** (`fixtures/e2e/resolve_ee_reuse.py`, wired in
  `fixtures/e2e/run_deploy_e2e.sh`). CI hashes
  `Dockerfile + pyproject.toml + uv.lock + .dockerignore`, stamps
  `context-hash=<sha>` on the shared EE description after a successful build,
  and flips to the `DEFAULT=<id>` get-path when the hash matches (and the
  latest EE version built successfully). serverless-docker drops from
  ~8–11 min to ~3 min when docker inputs are unchanged; any change to those
  files still exercises the full build path. API failures fall back to
  building — reuse can never fail a deploy.

## 3. CI pipeline structure (`.github/workflows/`)

- **Four parallel workflows** (one per use case) with per-case concurrency
  groups; `cancel-in-progress: false` protects real infra, queued duplicates
  collapse.
- **Path filters** — deploy E2Es only run when `fixtures/e2e/**`,
  `template/**`, `copier.yml`, or the workflow files change.
- **uv + apt caching** (`setup-caching` composite) in deploy and destroy jobs,
  keyed on the dependency manifests.
- **`uv sync` (not `--all-extras`)** in the deploy script — CI does not
  install dev tooling into the app env it deploys.
- **Deploy/destroy job split** with Pulumi state passed via a slim artifact
  (no `infra/.venv`, no `~/.pulumi/bin|plugins`, no `__pycache__`, secrets
  stripped) — cleanup never extends the deploy job and re-runs don't collide
  (`run_attempt` in the artifact name).
- **Destroy job renders nothing** — it restores `rendered/` from the artifact,
  skipping the copier render and its `apt update && apt install git g++`.
- **Step-level deploy timeouts** (`deploy-timeout-minutes` applies to the
  "Run deployment E2E" step; the job has a fixed 20-min cap). Prevents the
  failure mode where a successful deploy was cancelled during the post-run
  cache save and the whole run had to be repeated. Budgets: 8 default,
  10 workload-ee, 15 serverless-docker.
- **`ExecutionEnvironment.list(search_for=name)`** — server-side narrowing
  instead of listing every EE in the tenant.

## 4. Container start time

- **`start_server.sh` reuses the baked `/opt/venv`** when present
  (docker-built images): `uv sync --frozen --active` is a near no-op. Only
  pinned platform EEs (no custom Dockerfile) pay for a real sync into a
  project-local venv.
- **Docker-built paths never run `start_server.sh`** —
  `CMD ["python", "-m", "app.main"]` with deps baked at build time (matches
  the workload `DEFAULT_ENTRYPOINT`), so no bootstrap work at container start.

## 5. Failing fast (time not wasted is time saved)

- **Credential preflight** — `run_deploy_e2e.sh` validates
  `DATAROBOT_API_TOKEN`/`DATAROBOT_ENDPOINT` against `/account/info/` before
  any render/sync/pulumi work.
- **MCP endpoint probe** — after `pulumi up`, CI POSTs a JSON-RPC `initialize`
  to the deployed endpoint until it answers 2xx (~24 × 10 s). Catches images
  that build but crash at startup, which stack-outputs validation cannot see.
  Bails out early (after 3 sightings) when the workload reports status
  `ERRORED` — a crash loop, not a slow start.
- **Docker-context presence checks** (`ensure_docker_build_context_files`) —
  missing `Dockerfile`/`pyproject.toml`/`uv.lock`/`start_server.sh` fails in
  seconds instead of deep inside a remote build.

## Measured before/after (deploy jobs)

Baseline = first fully-green runs of the new workflows (commit 75446b4,
runs 33017785897–936; destroy still inline in the deploy step, no endpoint
probe). After = latest optimized runs (commit 7df668e, runs 33112697500–564;
destroy split out, endpoint probe **added**, serverless-docker on a hash hit).

| case              | baseline job | after job | Δ job  | baseline step | after step |
|-------------------|--------------|-----------|--------|---------------|------------|
| serverless-docker | 8:03         | 3:27      | −57 %  | 7:30          | 2:29 (−67 %) |
| serverless-ee     | 3:30         | 3:28      | ≈ 0 %  | 2:50          | 2:46       |
| workload-docker   | 4:47         | 4:02      | −16 %  | 4:16          | 3:17       |
| workload-ee       | 4:54         | 5:20      | +9 %   | 4:21          | 4:33       |

- **PR gate wall clock** (workflows run in parallel, slowest deploy job wins):
  8:03 → 5:20 ≈ **−34 %**.
- **Total deploy-job runner minutes** across the four cases: 21:14 → 16:17 ≈
  **−23 %** — while *adding* endpoint health verification the baseline never
  had (workload-ee's +9 % is exactly that probe waiting for the workload to
  come up, which is coverage, not overhead).
- serverless-docker on a **hash miss** (docker inputs changed): ~8–9:30
  including the probe — comparable to baseline, paid only when the EE build
  path actually needs re-testing.
- Destroy now runs in its own job; once real destroys execute it adds its own
  runner minutes after the deploy check is already green.

## Known immovable costs

- The remote builder's pull of the multi-GB GenAI Agents base image
  (workload-ee) — platform-side.
- The EE version build itself when docker inputs genuinely change
  (serverless-docker cache miss) — that build is exactly what the case tests.

## Change log

- **2026-08-27 (upload retry)** — A workload-ee deploy died in 3 s on a
  transient 502 from the Files catalog staged-upload endpoint. The shared HTTP
  session retries only idempotent methods (POST deliberately excluded —
  create-POSTs can duplicate on retry-after-phantom-success), so the upload got
  zero retries. Added `FilesApiClient._post_retrying_transient`: bounded
  backoff retries (4 attempts, 2→15 s) on 429/5xx for the repeat-safe POSTs
  only — catalog create, stage create, stage upload. `apply_stage` stays
  single-shot on purpose (re-applying an applied stage fails). Covered by unit
  tests, including one asserting apply does NOT retry.
- **2026-08-27 (pulumi home)** — Third and final destroy bug: pulumi expands
  `~` (for `PULUMI_HOME` **and** the `file://~` backend of
  `pulumi login --local`) via the **passwd entry** (`/root` in these
  containers), not the `$HOME` env var (`/github/home`) that GitHub sets — so
  the real state always lived in `/root/.pulumi` while staging copied
  `/github/home/.pulumi`, which only ever held the installer's `bin/`
  (verified by reproducing in the CI container image). Replaced
  `pulumi login --local` with an explicit workspace-anchored backend
  (`pulumi_login_e2e_backend` → `file://$GITHUB_WORKSPACE/pulumi-state`) used
  by both deploy and destroy; staging now ships `pulumi-state/` (its inner
  `.pulumi/` is hidden — `include-hidden-files: true` stays load-bearing).
  Round-trip verified in the real container image: deploy login → stack init →
  stage → restore → fresh login → `stack select` succeeds.
- **2026-08-27 (state hand-off)** — First run with the loud-fail guards caught
  a second silent-destroy bug: `PULUMI_STATE_DIR` was set from
  `${{ github.workspace }}`, which in **container jobs expands to the runner
  host path** (`/home/runner/work/...`) that does not exist inside the
  container — so the restored Pulumi state was never copied and `stack select`
  failed (previously this exited 0 as "nothing to destroy"). The workflow now
  passes the path relative and `destroy_deploy_e2e.sh` anchors it to
  `$GITHUB_WORKSPACE` (`resolve_workspace_path`, renamed from
  `resolve_rendered_dir`); a missing local state dir after a successful deploy
  is now its own explicit error. Rule of thumb: never use
  `${{ github.workspace }}` in these container jobs — use relative paths or
  `$GITHUB_WORKSPACE`.
- **2026-08-27 (check names)** — PR check names were mostly redundant prefix
  (`Deploy E2E (case) / deploy-e2e / Deploy E2E (case)`), truncating away the
  only part that differs. Final scheme: `E2E / <case> / Deploy|Destroy` — all
  four workflows share the name `E2E`, the caller job's display name is the
  case id, and the reusable jobs carry only the distinguishing word. Trade-off:
  the Actions sidebar shows four workflows all named "E2E" (disambiguate by
  filename/case in the run list). If branch protection ever lists these checks
  as required, the required names must be updated to match.
- **2026-08-27 (cleanup)** — Found that every destroy job had been silently
  no-oping: upload-artifact v4.4+ drops hidden files by default, so
  `rendered/.env` (a dotfile) never reached the cleanup artifact and
  `destroy_deploy_e2e.sh` exited via its "no .env" branch in ~1 s while
  reporting success — leaking every run's deployment/custom model/registered
  model/prediction environment/use case. Fixed with `include-hidden-files:
  true` (safe: the staged .env is secret-stripped), and destroy now **fails
  loudly** instead of no-oping when the deploy job succeeded but the state
  hand-off is missing (`DEPLOY_JOB_RESULT` guard in the script and lib). Added
  `fixtures/e2e/cleanup_orphan_stacks.py` (dry-run by default, `--delete` to
  act) to sweep the already-leaked resources by the `[ci-e2e-` naming
  convention, in dependency order.
- **2026-08-27 (later)** — Confirmed the EE hash reuse in CI: first
  serverless-docker run after the Dockerfile change missed the hash and did the
  full build (deploy job 7:58; EE version build 239 s; probe answered 200 on
  attempt 1), stamped `context-hash=ccfafb4977c9684e`; the re-run hit the hash
  and finished in 2:42. Added `UV_LINK_MODE=copy` to the e2e jobs to silence
  uv's cross-filesystem hardlink warning.
- **2026-08-27** — Initial version. Documented the PR #60 mechanisms plus the
  review-pass additions: hash-based EE reuse, step-level timeouts, destroy-job
  de-render, slim/secret-free cleanup artifact, endpoint probe. Restored
  `COPY . .` in the root Dockerfile after the probe exposed that
  workload-docker containers shipped without `app/` (workload `ERRORED`);
  probe now fails fast on `ERRORED`.
