# InboxPilot

**AI Workflow Automation Platform for Email Productivity**

InboxPilot connects to Gmail, classifies emails using Claude (Anthropic), extracts actionable tasks, and delivers a daily briefing — turning inbox chaos into a structured workflow.

---

## Features

- **Gmail OAuth integration** — read-only access, no passwords stored, syncs both received *and* sent mail (job applications are usually something you sent, not received)
- **AI email classification** — category, priority, and confidence score
- **Automated task extraction** — converts email content into structured tasks
- **Daily briefing** — AI-generated summary of your inbox and pending tasks
- **Dashboard** — real-time stats and briefing overview
- **Task management** — create, complete, and filter tasks
- **Job application tracker** — auto-detects job-application emails (sent *or* received), groups them by company, tracks stage (applied → interviewing → offer/rejected), and flags companies that haven't responded in 14+ days; manual add/edit supported too. "Scan inbox" classifies any not-yet-processed mail in batches rather than requiring each email to be opened individually.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, Python 3.12 |
| Database | PostgreSQL 16, SQLAlchemy 2.0, Alembic |
| AI | Anthropic Claude (claude-opus-4-8) |
| Frontend | Next.js 15, TypeScript, TailwindCSS, ShadCN UI |
| Auth | Google OAuth 2.0 + JWT |
| Deploy | Docker, Docker Compose |

---

## Quick Start

### 1. Clone and configure

```bash
git clone <repo-url>
cd InboxPilot
cp .env.example .env
# Fill in: GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, ANTHROPIC_API_KEY, SECRET_KEY
```

### 2. Set up Google OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create an OAuth 2.0 Client ID (Web application)
3. Add authorized redirect URI: `http://localhost:8000/api/auth/google/callback`
4. Enable: **Gmail API**, **Google People API**
5. Copy Client ID and Secret into `.env`

### 3. Run with Docker

```bash
# Start all services
docker compose up -d

# Run database migrations (first time only)
docker compose --profile migrate run migrate

# View logs
docker compose logs -f backend
```

### 4. Open the app

- Frontend: http://localhost:3000
- API docs: http://localhost:8000/docs

---

## Development (without Docker)

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Run migrations (requires running PostgreSQL)
alembic upgrade head

# Start server
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## API Overview

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/google/login` | Get OAuth URL |
| GET | `/api/auth/google/callback` | OAuth callback |
| GET | `/api/emails` | List emails (paginated, filterable) |
| POST | `/api/emails/sync` | Sync latest Gmail messages |
| POST | `/api/emails/process/{id}` | Run AI classification + task extraction |
| GET | `/api/tasks` | List tasks |
| POST | `/api/tasks` | Create task manually |
| PATCH | `/api/tasks/{id}` | Update / complete task |
| POST | `/api/briefings/generate` | Generate AI daily briefing |
| GET | `/api/briefings/latest` | Get latest briefing |
| GET | `/api/job-applications` | List tracked applications (filter by status, waiting-only, search) |
| POST | `/api/job-applications` | Add a company manually |
| PATCH | `/api/job-applications/{id}` | Update status / role / notes |
| DELETE | `/api/job-applications/{id}` | Remove an application |
| POST | `/api/job-applications/scan` | Re-scan already-classified emails and (re)link applications |

Full interactive docs at `/docs` (Swagger UI).

---

## Architecture

```
Gmail API
    ↓
Email Ingestion Service (sync_emails)
    ↓
PostgreSQL (emails, tasks, ai_extractions)
    ↓
AI Service (Claude claude-opus-4-8)
  ├─ classify_email()        → category, priority, confidence
  ├─ extract_tasks()         → structured task list
  ├─ extract_job_details()   → company, role, application stage
  └─ generate_briefing()     → plain-text daily summary
    ↓
PostgreSQL (+ job_applications, grouped by company)
    ↓
FastAPI REST API
    ↓
Next.js 15 Dashboard
```

---

## Project Structure

```
InboxPilot/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI app + CORS
│   │   ├── config.py         # Settings (pydantic-settings)
│   │   ├── database.py       # Async SQLAlchemy engine
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── schemas/          # Pydantic request/response schemas
│   │   ├── routers/          # API route handlers
│   │   ├── services/
│   │   │   ├── gmail_service.py           # OAuth + email sync
│   │   │   ├── ai_service.py              # Claude prompts (Anthropic)
│   │   │   ├── task_service.py            # Task CRUD helpers
│   │   │   └── job_application_service.py # Application tracker upsert/CRUD/scan
│   │   └── middleware/
│   │       └── auth.py       # JWT bearer authentication
│   ├── alembic/              # Database migrations
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── app/              # Next.js App Router pages
│       ├── components/       # UI components (ShadCN-based)
│       └── lib/
│           ├── api.ts        # Typed API client
│           └── utils.ts      # Tailwind cn() helper
├── docker-compose.yml
└── .env.example
```
