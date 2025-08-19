# Tech Stack

## Context
Global tech stack defaults for the Home Assistant → Time‑Series Ingestion platform. These are organization-wide defaults; projects may override via `.agent-os/product/tech-stack.md` when justified.

> This document supersedes the older Rails/Ruby defaults and standardizes on **Python, Mosquitto (MQTT), InfluxDB, PostgreSQL, and Node.js** across services.

---

## High-Level Architecture
- **Edge / Sources:** Home Assistant devices/topics via **MQTT (Mosquitto)** and Home Assistant **WebSocket/Event API** for non‑MQTT domains.
- **Ingress:** Python async ingestors consume MQTT and WS events, validate, enrich, and fan-out to stream or direct writes depending on throughput.
- **Time-Series Storage:** **InfluxDB** for raw/high‑cardinality metrics with retention + downsampling.
- **Relational Storage:** **PostgreSQL** for configuration, metadata, auth, billing, and aggregated/read-optimized views when needed.
- **API / Control Plane:** Python FastAPI services for admin APIs, device onboarding, and aggregation/analytics endpoints.
- **UI:** React + Vite dashboard for operations, observability, and customer views.
- **Observability:** OpenTelemetry → Prometheus / Loki / Tempo, with Grafana dashboards and SLO alerts.

---

## Core Technologies & Versions

### Languages & Runtimes
- **Python:** 3.12+ (async-first)
- **Node.js:** 22 LTS (ESM by default)

### Messaging & Protocols
- **MQTT Broker:** **Eclipse Mosquitto 2.x** (TLS, auth via JWT/OIDC-backed plugin or username/password with DO Secrets)
- **Home Assistant Integration:** MQTT discovery; Home Assistant WebSocket/Event API as supplemental source

### Datastores
- **Time-Series DB:** **InfluxDB 2.7+ (OSS or Cloud)**
  - Buckets by tenant/environment.
  - **Retention:** Raw 30–90 days.
  - **Downsampling:** Flux or Tasks to 1m/5m/1h rollups (kept 12–24 months).
  - **Cardinality control:** device_id + measurement + field normalization; avoid unbounded tag values.
- **Relational DB:** **PostgreSQL 17+ (Managed)**
  - Schemas: `core` (users, orgs, devices), `billing`, `iam`, `ops`.
  - Use **pg_partman** or native partitioning for heavy event tables if needed.
  - **Extensions:** `uuid-ossp`, `pgcrypto`, `citext`.
  - **Backups:** daily + PITR; quarterly restore tests.

### Application / API Services
- **Framework:** **FastAPI 0.115+**
- **Server:** **uvicorn** with **gunicorn** (async workers) behind an ingress
- **ORM:** **SQLAlchemy 2.x** + **Alembic** (migrations)
- **Task Queue / Schedulers:** **Celery** (Redis broker) or **Arq** for lightweight async jobs; CronJobs for periodic compaction/downsampling triggers
- **Schema/Contracts:** **Protobuf** for internal event contracts (optional: JSON for simplicity, include `schema_version`)

### Front-End
- **Framework:** **React (latest stable)** + **TypeScript**
- **Build Tool:** **Vite**
- **Styling:** **Tailwind CSS 4.x**
- **UI Components:** **shadcn/ui** (or “Instrumental Components” if required)
- **Icons:** **lucide-react**
- **Fonts:** Google Fonts, **self-hosted** at build time for performance
- **Package Manager:** **pnpm** (workspaces, faster CI)

### Packaging & Dependencies
- **Python:** `uv` or **Poetry** for dependency management and locking; `ruff` + `mypy` for lint/type
- **Node:** **pnpm** with `eslint` + `prettier` + `tsc`

---

## Infrastructure

### Hosting & Network
- **Platform:** **DigitalOcean Kubernetes (DOKS)** for services; optional Droplets for stateful workloads
- **Ingress:** Cloudflare → DO Load Balancer → NGINX Ingress
- **TLS:** cert-manager + Let’s Encrypt (or Cloudflare certs)
- **Secrets:** DO Secrets + SOPS (git-ops) or external **Doppler/1Password** with GitHub OIDC
- **Regions:** Choose primary close to user/device base; HA with multi-AZ where applicable

### Data Services (Managed Preferred)
- **PostgreSQL:** DO Managed Postgres (v17+) with PITR
- **InfluxDB:** Self-hosted on DOKS or InfluxDB Cloud; attach DO Volumes/S3-compatible backend for durability if self-hosting
- **Redis:** DO Managed Redis for Celery/Arq and rate-limiting
- **Object Storage:** **Amazon S3** (private) with **CloudFront** CDN; signed URLs

### Containerization & IaC
- **Images:** Docker; build multi-arch where relevant
- **IaC:** **Terraform** + **Helm**; one workspace per environment (dev/staging/prod)
- **Policies:** PodSecurity, NetworkPolicies, resource requests/limits, HPA enabled

---

## CI/CD & Branching

- **Platform:** GitHub Actions
- **Triggers:** PRs; push to `staging` and `main`
- **Pipelines (per service):**
  1. **Static checks:** ruff, mypy, eslint, tsc
  2. **Tests:** `pytest` (coverage), `vitest`/`playwright`
  3. **Security:** Dependabot, CodeQL, Trivy image scan, license checks
  4. **Build:** container images; generate SBOM (Syft); sign with Cosign
  5. **Deploy:** Auto to **staging** on push; manual approval to **production** on `main`
- **Environments:**
  - **Production:** `main`
  - **Staging:** `staging`
  - **Preview:** ephemeral per PR (optional)

---

## Observability & SRE

- **Telemetry:** OpenTelemetry SDKs (Python/Node)
- **Metrics:** Prometheus; **RED**/**USE** dashboards for APIs and brokers
- **Traces:** Tempo/Jaeger
- **Logs:** Loki with structured JSON logging
- **Dashboards:** Grafana
- **Alerts:** SLOs with burn-rate policies; on-call via PagerDuty or Opsgenie
- **Health & HA:** readiness/liveness probes; broker clustering; DB replicas; consumer backpressure & DLQs

---

## Security & Compliance

- **Authn/Authz:** OIDC (Auth0/Zitadel/Cloudflare); JWT for services; least-privilege RBAC
- **Secrets:** never in git; rotate quarterly
- **Transport Security:** TLS everywhere; optional mTLS inside cluster
- **Supply Chain:** Signed images (Cosign), SBOMs (Syft), provenance (SLSA)
- **Data:** PII minimization; encryption at rest (Postgres & object storage) and in transit
- **Retention:** Influx raw 30–90d; rollups 12–24m; Postgres audit logs 12m (configurable)

---

## Operational Playbooks

- **Capacity:** scale MQTT consumers horizontally; shard by tenant/topic
- **Migrations:** backward‑compatible changes; Alembic gated deploys
- **Rollouts:** canary to 10%, auto‑promote on SLO pass
- **Backups/DR:** verify nightly PITR snapshots weekly; quarterly game‑days
- **Runbooks:** incident templates for broker outage, DB failover, and backpressure

---

## Default Versions (pin at project bootstrap)
- Python **3.12.x**
- Node.js **22.x LTS**
- Mosquitto **2.x**
- InfluxDB **2.7.x**
- PostgreSQL **17.x**
- Redis **7.x**
- FastAPI **0.115+**, SQLAlchemy **2.0+**, Alembic **1.13+**
- React **latest**, Vite **latest**, Tailwind **4.x**, lucide-react **latest**

---

## Alternatives & Notes
- If future needs require SQL-style analytics on time series within Postgres, consider adding **TimescaleDB** alongside or instead of InfluxDB; keep event contracts stable to allow parallel writes during migrations.
- For ultra‑low latency fan‑out at scale, you may introduce **NATS JetStream** between ingestion and writers; keep it optional until throughput justifies it.
