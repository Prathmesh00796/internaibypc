# InternAI — AI-Powered Internship Finder & Application Assistant

InternAI helps students find internships and prepare applications faster: upload a resume, get it parsed automatically, see every new listing scored against your profile, and review AI-prepared applications before anything is sent.

**Compliance-first by design.** InternAI never submits an application without an explicit, per-application confirmation from the user, and it only integrates with job platforms through official, permitted APIs (see [Compliance](#compliance--job-source-policy) below). It does not scrape or auto-apply on platforms like LinkedIn, Internshala, Naukri, or Indeed, since their terms of service do not permit that.

---

## Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14 (App Router), React, TypeScript, Tailwind CSS, Radix-based UI components |
| Backend | FastAPI, SQLAlchemy 2.0 (async), Pydantic v2 |
| Background jobs | Celery + Redis (broker/result backend + rate limiting) |
| Database | PostgreSQL 16 |
| Storage | Local disk by default; pluggable S3 / Supabase backend |
| Auth | JWT (access + refresh), OAuth extension point for Google/GitHub |
| Resume parsing | PyMuPDF, pdfplumber, spaCy |
| Matching engine | scikit-learn (TF-IDF + cosine similarity) + weighted rule-based scoring |
| Document generation | ReportLab (ATS-friendly PDF resumes) |
| Deployment | Docker Compose, Nginx reverse proxy, GitHub Actions CI |

---

## Project layout

```
internai/
├── backend/
│   ├── app/
│   │   ├── api/routes/        # FastAPI route modules (auth, profile, resumes, jobs, applications, dashboard, admin)
│   │   ├── core/               # config, database, security, logging, rate limiting
│   │   ├── models/              # SQLAlchemy ORM models
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   ├── services/            # business logic: resume parser, matching engine, job connectors, generators
│   │   │   └── job_sources/     # per-platform connectors (Greenhouse, Lever, ...)
│   │   ├── workers/             # Celery app + scheduled/background tasks
│   │   └── main.py              # FastAPI entrypoint
│   ├── alembic/                 # DB migrations
│   ├── tests/                   # unit + integration tests
│   └── requirements.txt
├── frontend/
│   ├── app/                     # Next.js App Router pages
│   ├── components/              # shared UI (shadcn-style primitives + custom widgets)
│   └── lib/                     # API client, types, utils
├── docker/
│   └── nginx.conf
├── docker-compose.yml
└── .github/workflows/ci.yml
```

---

## Quick start (Docker Compose)

```bash
git clone <your-repo-url>
cd internai

cp backend/.env.example backend/.env
# Edit backend/.env: at minimum set SECRET_KEY and ENCRYPTION_KEY (see comments in the file)

docker compose up --build
```

- App: http://localhost (via Nginx) or http://localhost:3000 (frontend directly)
- API docs: http://localhost:8000/api/docs
- Backend health check: http://localhost:8000/health

The first `backend` container run applies Alembic migrations automatically (`alembic upgrade head`) before starting Uvicorn.

### Generate required secrets

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"                       # SECRET_KEY
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"  # ENCRYPTION_KEY
```

---

## Running locally without Docker

**Backend**

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm

cp .env.example .env   # point DATABASE_URL/REDIS_URL at local services

alembic upgrade head
uvicorn app.main:app --reload
```

**Celery worker + beat** (separate terminals)

```bash
celery -A app.workers.celery_app worker --loglevel=info
celery -A app.workers.celery_app beat --loglevel=info
```

**Frontend**

```bash
cd frontend
npm install --legacy-peer-deps
cp .env.example .env.local
npm run dev
```

---

## Core flows

1. **Register → Profile → Resume upload.** Uploading a PDF resume triggers an async Celery task (`parse_resume_task`) that extracts name, skills, education, experience, CGPA, languages, and certificates via PyMuPDF/pdfplumber/spaCy, then auto-fills empty profile fields and adds parsed skills.
2. **Scheduled search.** `celery beat` triggers `run_scheduled_search` three times daily (morning/afternoon/night, configurable in `app/workers/celery_app.py`). It calls every registered job source connector, deduplicates by `(source, external_id)`, and saves new listings.
3. **Matching.** After new jobs are saved, `match_new_jobs_for_all_users` scores each new job against every user's profile (skills, experience, CGPA, grad year, location, resume-text similarity) and creates `Application` rows with a 0–100 `match_score`. Strong matches (≥70) trigger a notification.
4. **Review & apply.** From the Jobs page, the user can Apply / Save / Skip. "Apply" prepares a cover letter and an autofill payload and places the application in the **review queue** — nothing is submitted yet.
5. **Confirm & submit.** The user reviews the prepared application on the Queue page and clicks **Confirm & submit**. This is the only action that can move an application to `SUBMITTED`, and it's logged in the audit trail.
6. **Track.** The Applications and Analytics pages show status over time, response/interview/offer rates, and top companies/skills.

---

## Compliance & job source policy

This is a hard architectural rule, not just a UI convention:

- `app/services/job_sources/base.py` defines the connector interface. `supports_auto_submit` defaults to `False`.
- Only connectors backed by an **official, documented, read/write-permitted API** may set it `True` — and even then, `app/services/application_service.py` requires an explicit per-application user confirmation (`confirm_and_submit`) before anything is marked `SUBMITTED`.
- The included connectors (`greenhouse.py`, `lever.py`) use Greenhouse's and Lever's public Job Board / Postings APIs, which are read-only and explicitly intended for third-party consumption. Even for these, application submission still happens on the company's own hosted apply page, so `allows_auto_submit` stays `False` for all seeded listings.
- Platforms without a public application-submission API for third parties (LinkedIn, Internshala, Naukri, Indeed, etc.) are **intentionally not scraped**. See the comment block in `app/services/job_sources/registry.py`. If a platform later offers an official OAuth-based application API, add a new connector gated behind a user's own `PlatformConnection` — never a shared scraper or stored password.

---

## Testing

```bash
cd backend
pytest tests/ -v
```

- `tests/test_matching_engine.py` — unit tests for each scoring sub-function
- `tests/test_resume_parser.py` — unit tests for regex/section-extraction helpers
- `tests/test_auth_api.py` — integration tests against a real (test) Postgres database via httpx's ASGI transport

CI (`.github/workflows/ci.yml`) runs backend tests against a Postgres+Redis service, builds the frontend, and builds both Docker images on every push/PR to `main`.

---

## API documentation

Interactive OpenAPI docs are auto-generated by FastAPI:
- Swagger UI: `/api/docs`
- ReDoc: `/api/redoc`
- Raw schema: `/api/openapi.json`

All endpoints are prefixed with `/api/v1`. See `app/api/router.py` for the full route list.

---

## Security notes

- Passwords hashed with bcrypt (`passlib`).
- JWT access (24h) + refresh (30d) tokens; see `app/core/security.py`.
- Sensitive profile fields (phone number) are encrypted at rest with Fernet symmetric encryption before being written to Postgres.
- Redis-backed sliding-window rate limiting on all routes (`app/core/rate_limit.py`), configurable via `RATE_LIMIT_PER_MINUTE`.
- All state-changing actions relevant to security/compliance (login, registration, application submission) are written to an immutable `audit_logs` table.
- Run behind HTTPS in production — see [DEPLOYMENT.md](./DEPLOYMENT.md).

---

## Extending

- **New job source**: implement `JobSourceConnector` in `app/services/job_sources/`, register it in `registry.py`.
- **New notification channel**: add a sender function in `app/services/notification_service.py` and a case in the Celery tasks that call it.
- **Tune matching weights**: adjust `WEIGHT_*` settings in `.env` (backend) — no code change needed.
- **LLM-based cover letters**: swap the template logic in `app/services/cover_letter_generator.py` for an API call; the function signature is the extension point.

See [DEPLOYMENT.md](./DEPLOYMENT.md) for production deployment guidance.
"# internaibypc" 
