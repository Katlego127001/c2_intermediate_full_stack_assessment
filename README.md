# JobTracker — Internal Job Tracking System

A production-grade, full-stack internal tooling platform for managing employees, creating and assigning jobs, tracking progress, and visualizing team workload — built with FastAPI + Next.js, hardened with JWT/RBAC, dockerized end-to-end, and shipped with CI.

> **Stack:** FastAPI · SQLAlchemy 2 (async) · PostgreSQL · Redis · Celery · Next.js 14 (App Router) · TypeScript · TailwindCSS · TanStack Query · Zustand · React Hook Form + Zod · Recharts · Nginx · Docker Compose · GitHub Actions

---

## Table of Contents

1. [Architecture](#architecture)
2. [Features](#features)
3. [Quick start (Docker)](#quick-start-docker)
4. [Local development](#local-development)
5. [Environment variables](#environment-variables)
6. [API documentation](#api-documentation)
7. [Database & migrations](#database--migrations)
8. [Testing](#testing)
9. [CI/CD](#cicd)
10. [Deployment notes](#deployment-notes)
11. [Project layout](#project-layout)

---

## Architecture

```
                ┌─────────────────────────┐
                │       Nginx :80         │  reverse proxy, gzip, SPA routing
                └────┬──────────┬─────────┘
                     │          │
        ┌────────────▼─┐    ┌───▼─────────────┐
        │  Next.js     │    │  FastAPI        │  /api/v1/*   + /ws/notifications
        │  (standalone)│    │  (uvicorn)      │
        └──────────────┘    └──┬─────┬─────┬──┘
                               │     │     │
                       ┌───────▼┐  ┌─▼──┐ ┌▼─────────┐
                       │Postgres│  │Redis│ │ Celery   │  worker + beat
                       └────────┘  └─────┘ └──────────┘
```

**Backend** follows clean / layered architecture:

```
routes (HTTP)  →  services (business logic)  →  repositories (data access)  →  models (ORM)
                                  │
                                  └─ activity_service (audit), ws_manager (real-time)
```

* **Auth:** stateless JWT (access + refresh) with bcrypt-hashed passwords.
* **RBAC:** `admin` vs `employee` enforced via FastAPI dependencies (`require_admin`, `require_role`).
* **Audit:** every sensitive mutation is logged to `activity_logs` with actor + JSONB metadata.
* **Soft delete:** `users`, `jobs` carry `is_deleted` + `deleted_at`.
* **Rate limiting:** SlowAPI backed by Redis.
* **Structured logging:** structlog (JSON in prod, pretty in dev) + request-id middleware.
* **Real-time:** `/api/v1/ws/notifications` pushes events like `job.assigned` to the right assignee (admins broadcast).
* **Background work:** Celery worker + beat with example tasks (`send_overdue_reminders`, `audit_cleanup`).

**Frontend** is App Router + RSC-friendly with:
* Auth store (Zustand, persisted) + Axios interceptor (auto-logout on 401)
* TanStack Query for server state, with optimistic-friendly invalidation
* Tailwind + light/dark theme (zero FOUC via head script)
* Role-gated layouts (`/admin/*` for admins, `/employee/*` for employees)

---

## Features

### Functional
- Open self-service Register (first user becomes admin, rest are employees) / Login / Logout / Change password
- Admin: create / edit / activate-deactivate employees; search & filter
- Admin: create / edit / delete / assign / reassign jobs; search & filter; pagination
- Employee: see only their jobs; update **status only**; update own phone & password
- Admin dashboard: job & employee counts, workload bar chart, status pie chart, recent activity
- Employee dashboard: counts, upcoming due dates, profile summary
- Real-time toast notification when a new job is assigned

### Non-functional
- Multi-stage Docker builds (small, non-root, healthchecks)
- Internal Docker network, named volumes for Postgres & Redis
- Idempotent seed script bootstraps admin + sample employees + sample jobs
- pytest backend suite (auth + RBAC + jobs + dashboards)
- Jest/RTL frontend smoke tests
- GitHub Actions: lint, test, build for both apps + Docker image build verification

---

## Quick start (Docker)

Requirements: Docker 24+, Docker Compose v2.

```bash
git clone <this-repo> && cd c2_intermediate_full_stack_assessment

cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
cp .env.example .env      # for compose-level vars (optional)

docker compose up -d --build
```

Troubleshooting
If you encounter an error like:

sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) 
connection to server at "db" (192.168.208.2), port 5432 failed: 
FATAL:  password authentication failed for user "postgres_tracking_user"
This usually means the database container has stale volumes with old credentials.
To fix it, remove the containers and volumes, then rebuild:

```bash
docker compose down -v
docker compose up -d --build
docker compose down -v → stops all containers and deletes associated volumes (removes old DB state).

docker compose up -d --build → rebuilds images and starts fresh containers with the correct environment variables.
```

Wait ~30 seconds for healthchecks, then open:

| URL | Purpose |
|---|---|
| http://localhost          | Web app (Next.js via Nginx) |
| http://localhost/docs     | Swagger UI |
| http://localhost/health   | Backend health probe |

**Default seeded credentials** (created by `python -m app.utils.seed` on first boot):

| Role | Email | Password |
|---|---|---|
| Admin    | `admin@jobtracker.com` | `Admin123!` |
| Employee | `alice@jobtracker.com` | `Password123!` |
| Employee | `bob@jobtracker.com`   | `Password123!` |
| Employee | `carol@jobtracker.com` | `Password123!` |
| Employee | `dan@jobtracker.com`   | `Password123!` |

> Change `FIRST_ADMIN_PASSWORD` in `backend/.env` before first boot for any non-throwaway deployment.

Useful commands:
```bash
docker compose logs -f backend
docker compose exec backend alembic upgrade head      # explicit migration
docker compose exec backend python -m app.utils.seed  # re-run seed (idempotent)
docker compose exec db psql -U postgres_tracking_user -d job_tracking_db
docker compose down -v                                 # tear down + wipe volumes
```

---

## Local development

### 1. One‑time Postgres Database Setup
Before running migrations, you need to create the database and user once:

```bash
# Connect to PostgreSQL as the default superuser
psql -U postgres

# In the psql prompt, run:
->> CREATE DATABASE job_tracking_db;
->> CREATE USER postgres_tracking_user WITH PASSWORD 'JobTracking3213';
->> ALTER ROLE postgres_tracking_user CREATEDB;
->> GRANT ALL PRIVILEGES ON DATABASE job_tracking_db TO postgres_tracking_user;
->> \connect job_tracking_db
->> GRANT ALL ON SCHEMA public TO postgres_tracking_user;
->> \q

```

### 2. Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.local.example .env
alembic upgrade head
python -m app.utils.seed

# --- Important ---
# Start Redis in a separate terminal window before running uvicorn.
# This keeps rate limiting and Celery working in local dev.
docker run -p 6379:6379 redis:7-alpine

# Back in your backend terminal, start the app:
uvicorn app.main:app --reload

```

### 3. Frontend
```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

App is at http://localhost:3000; ensure `NEXT_PUBLIC_API_URL` points to your backend (e.g. `http://localhost:8000/api/v1`).

---

## Environment variables

### Backend (`backend/.env`)
| Var | Description |
|---|---|
| `SECRET_KEY` | JWT signing key (generate via `openssl rand -hex 32`) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token TTL (default 60) |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token TTL (default 7) |
| `DATABASE_URL` | Async URL (`postgresql+asyncpg://…`) |
| `SYNC_DATABASE_URL` | Sync URL for Alembic (`postgresql+psycopg2://…`) |
| `REDIS_URL` | Redis URL (used for rate-limit + cache) |
| `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` | Redis URLs for Celery |
| `BACKEND_CORS_ORIGINS` | JSON or comma-separated origins |
| `RATE_LIMIT_PER_MINUTE` | Default per-IP limit |
| `FIRST_ADMIN_*` | Used by seed script (idempotent) |

### Frontend (`frontend/.env.local`)
| Var | Description |
|---|---|
| `NEXT_PUBLIC_API_URL` | e.g. `http://localhost/api/v1` (proxied via Nginx) or `http://localhost:8000/api/v1` (direct) |
| `NEXT_PUBLIC_WS_URL` | e.g. `ws://localhost/api/v1/ws/notifications` |

---

## API documentation

Auto-generated OpenAPI + Swagger UI:
- Swagger UI: `/docs`
- JSON spec: `/openapi.json`

### Quick reference

| Method | Path | Auth | Notes |
|---|---|---|---|
| POST | `/api/v1/auth/register` | – | Open self-service. First-ever user becomes admin; later users default to employee |
| POST | `/api/v1/auth/login` | – | Returns `{access_token, refresh_token}` |
| POST | `/api/v1/auth/logout` | Bearer | Stateless ack |
| POST | `/api/v1/auth/change-password` | Bearer | |
| GET  | `/api/v1/auth/me` | Bearer | |
| GET  | `/api/v1/employees` | Admin | Pagination + `q`, `department`, `status`, `role` |
| POST | `/api/v1/employees` | Admin | |
| GET  | `/api/v1/employees/me` | Bearer | |
| PATCH| `/api/v1/employees/me` | Bearer | Employee may only update `phone_number` |
| GET  | `/api/v1/employees/{id}` | Admin | |
| PUT  | `/api/v1/employees/{id}` | Admin | |
| PATCH| `/api/v1/employees/{id}/status` | Admin | Activate/deactivate |
| GET  | `/api/v1/jobs` | Bearer | Employees auto-scoped to their jobs |
| POST | `/api/v1/jobs` | Admin | |
| GET  | `/api/v1/jobs/{id}` | Bearer | |
| PUT  | `/api/v1/jobs/{id}` | Admin | |
| PATCH| `/api/v1/jobs/{id}/status` | Bearer | Admin: any; Employee: only their jobs |
| DELETE| `/api/v1/jobs/{id}` | Admin | Soft delete |
| GET  | `/api/v1/dashboard/admin` | Admin | |
| GET  | `/api/v1/dashboard/employee` | Employee | |
| WS   | `/api/v1/ws/notifications?token=…` | – | JWT in query string |

---

## Database & migrations

- ORM: SQLAlchemy 2 (async via asyncpg)
- Migrations: Alembic, with a single bootstrap migration (`0001_initial`) that creates all tables, enums, and indexes (including composite `(status, priority)` and `due_date`).
- Generate a new migration:
  ```bash
  docker compose exec backend alembic revision --autogenerate -m "add foo"
  docker compose exec backend alembic upgrade head
  ```

---

## Testing

### Backend
```bash
cd backend
pytest -q                # uses ephemeral SQLite (no Postgres needed)
pytest -q --cov=app      # with coverage
```

Covers: registration bootstrap rule, login/logout, change-password, RBAC enforcement, employee self-update restriction, full job lifecycle (admin), employee-only-status restriction, dashboard access control, and employee-job scoping.

### Frontend
```bash
cd frontend
npm test                 # Jest + RTL
```

---

## CI/CD

GitHub Actions in `.github/workflows`:

- `backend.yml` — lint (flake8/black/isort), pytest with coverage, Docker image build using buildx + GHA cache.
- `frontend.yml` — ESLint, Jest, `next build`, Docker image build.

Add a deploy job by pushing images to GHCR/ECR and triggering your orchestrator (Kubernetes, ECS, Nomad, etc.).

---

## Deployment notes

- **Secrets:** rotate `SECRET_KEY`, set strong `POSTGRES_PASSWORD`, and never commit `.env`.
- **TLS:** put a real cert in front of Nginx (Let's Encrypt via Caddy, Traefik, or an ALB).
- **Scaling:** Backend is stateless — scale horizontally. The in-process WebSocket manager is single-process; for >1 replica swap it for a Redis pub/sub fanout (the manager interface is stable so callers are unaffected).
- **Observability:** structured JSON logs ship `request_id`, `path`, `method`, `status`, `duration_ms`. Ingest into any log aggregator (Loki, ELK, Datadog).
- **DB sizing:** all hot columns are indexed; `jobs` carries a composite index `(status, priority)` and `due_date` for dashboard queries.

---

## Project layout

```
job-tracker/
├── backend/
│   ├── app/
│   │   ├── api/v1/{routes,dependencies,router.py}
│   │   ├── core/{config,security,database,logging}.py
│   │   ├── middleware/request_context.py
│   │   ├── models/{user,employee,job,activity,mixins}.py
│   │   ├── repositories/{base,user,employee,job,activity}.py
│   │   ├── schemas/{auth,employee,job,dashboard,common}.py
│   │   ├── services/{auth,employee,job,dashboard,activity}_service.py
│   │   ├── websockets/manager.py
│   │   ├── tasks/celery_app.py
│   │   ├── utils/seed.py
│   │   ├── tests/{conftest,test_auth,test_rbac_and_jobs}.py
│   │   └── main.py
│   ├── alembic/{env.py,versions/0001_initial.py}
│   ├── Dockerfile · requirements.txt · pyproject.toml · pytest.ini · .env.example
├── frontend/
│   ├── app/{(auth)/{login,register},admin,employee,profile,api/health}/...
│   ├── components/{ui,app-shell,providers,stat-card,empty,theme-toggle}.tsx
│   ├── features/{jobs,employees}/...
│   ├── hooks/{useAuth,useNotificationsSocket}.ts
│   ├── services/{auth,employees,jobs,dashboard}.service.ts
│   ├── store/auth.ts
│   ├── lib/{api,utils}.ts
│   ├── types/api.ts
│   ├── middleware.ts
│   ├── Dockerfile · package.json · tsconfig.json · tailwind.config.ts
├── nginx/nginx.conf
├── docker-compose.yml
├── .github/workflows/{backend,frontend}.yml
└── README.md
```

---

© JobTracker — built as a reference implementation for enterprise-grade internal tooling.
