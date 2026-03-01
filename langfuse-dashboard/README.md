# PharmaGenie — LangChain + Langfuse Observability Stack

A **self-contained, production-grade** observability setup that runs entirely
in Docker alongside the main PharmaGenie backend.

```
langfuse-dashboard/
├── docker-compose.yml          ← spins up everything
├── .env.example                ← copy to .env and fill in secrets
└── server/                     ← PharmaGenie Observability API (port 8001)
    ├── Dockerfile
    ├── requirements.txt
    ├── main.py                 ← FastAPI app entry point
    ├── config.py               ← all settings from env vars
    ├── middleware/
    │   └── tracing.py          ← request-id / structlog middleware
    ├── callbacks/
    │   └── langfuse_handler.py ← builds LangChain → Langfuse callback handlers
    ├── integrations/
    │   └── pharmagenie.py      ← 5 pre-built traced chains for all agents
    └── routers/
        ├── health.py           ← GET  /health
        ├── agents.py           ← POST /run/*
        ├── traces.py           ← GET  /traces/*
        ├── metrics.py          ← GET  /metrics/summary
        └── feedback.py         ← POST /feedback
```

---

## Services

| Container              | Purpose                        | Local port |
|------------------------|--------------------------------|------------|
| `langfuse-postgres`    | Langfuse internal database     | 5433       |
| `langfuse-redis`       | Queue + caching                | 6380       |
| `langfuse-server`      | Langfuse UI + REST API         | **3100**   |
| `pharmagenie-obs-server` | PharmaGenie Observability API | **8001**   |

---

## Quick Start

### 1 — Prerequisites

- Docker + Docker Compose installed
- Git (already have the project)

### 2 — Create your `.env`

```bash
cd langfuse-dashboard
cp .env.example .env
```

Edit `.env` — the only values you **must** change before production:

| Key | What to change |
|-----|---------------|
| `POSTGRES_PASSWORD` | Strong random password |
| `REDIS_PASSWORD` | Strong random password |
| `NEXTAUTH_SECRET` | 32+ random chars |
| `LANGFUSE_SALT` | Any unique string |
| `LANGFUSE_PUBLIC_KEY` | Replace with Langfuse-generated key |
| `LANGFUSE_SECRET_KEY` | Replace with Langfuse-generated key |
| `LANGFUSE_INIT_USER_PASSWORD` | Your admin password |
| `OPENAI_API_KEY` | Your OpenAI key |

### 3 — Start everything

```bash
cd langfuse-dashboard
docker compose up -d
```

Wait ~30 seconds for Langfuse to run migrations, then:

| URL | What |
|-----|------|
| http://localhost:3100 | **Langfuse Dashboard** (login with admin email/password from .env) |
| http://localhost:8001 | **PharmaGenie Observability API** |
| http://localhost:8001/docs | Swagger UI |
| http://localhost:8001/health | Health check |

### 4 — Verify it works

```bash
# Health check
curl http://localhost:8001/health

# Run a traced safety check (needs OPENAI_API_KEY set)
curl -X POST http://localhost:8001/run/safety-check \
  -H "Content-Type: application/json" \
  -d '{"medicine_name":"Paracetamol","dosage":"500mg","user_id":"test-user"}'
```

Then open http://localhost:3100 → **Traces** — you should see the run appear.

---

## API Reference

### Agent Runs (all traced to Langfuse automatically)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/run/safety-check` | Medicine safety + prescription check |
| POST | `/run/prescription-analysis` | Analyse prescription text / OCR output |
| POST | `/run/drug-interaction` | Check interactions between ≥2 medicines |
| POST | `/run/planner` | Monthly refill planner with cost optimisation |
| POST | `/run/custom` | Run any custom system+user prompt pair |

All run endpoints accept optional `session_id` and `user_id` fields — these
appear in the Langfuse dashboard to group traces by user or session.

### Traces

| Method | Path | Description |
|--------|------|-------------|
| GET | `/traces?page=1&limit=20` | List recent traces |
| GET | `/traces/{trace_id}` | Get single trace |
| GET | `/traces/{trace_id}/observations` | Get all spans in a trace |

### Metrics

| Method | Path | Description |
|--------|------|-------------|
| GET | `/metrics/summary?days=7` | Aggregated cost / latency / error stats |

### Feedback

| Method | Path | Description |
|--------|------|-------------|
| POST | `/feedback` | Submit a 0–1 score for a trace |

```json
{
  "trace_id": "abc123",
  "score": 0.9,
  "name": "user-feedback",
  "comment": "Very accurate result"
}
```

---

## How Tracing Works

```
PharmaGenie Frontend
      │
      ▼
PharmaGenie Backend (port 8000)  ──or──  Observability Server (port 8001)
      │                                           │
      └──────────────┬────────────────────────────┘
                     │
                     ▼
            LangChain Chain runs
                     │
                     ▼  (via CallbackHandler)
            Langfuse Server (port 3100)
                     │
                     ▼
            PostgreSQL  ←→  Langfuse Dashboard
```

1. Every `POST /run/*` call builds a `LangfuseCallbackHandler` via `callbacks/langfuse_handler.py`.
2. The handler is injected into the LangChain `config={"callbacks": [handler]}`.
3. LangChain automatically fires events (LLM start, LLM end, tool call, etc.) to Langfuse.
4. Langfuse stores everything in PostgreSQL and shows it in the dashboard.

---

## Integrating with Your Existing PharmaGenie Agents

If you want to trace your **existing** backend agents without routing through
the observability server, just import the callback handler directly:

```python
# In any agent file inside backend/app/agents/
from langfuse.callback import CallbackHandler

handler = CallbackHandler(
    public_key="pk-lf-pharmagenie-public",
    secret_key="sk-lf-pharmagenie-secret",
    host="http://localhost:3100",
    session_id=customer_id,
    user_id=customer_id,
    trace_name="safety-check-agent",
)

result = await your_chain.ainvoke(inputs, config={"callbacks": [handler]})
```

---

## Dashboard Features

Once traces are flowing, the Langfuse dashboard shows:

- **Traces** — every agent run with full input/output, latency, cost
- **Sessions** — group traces by user session
- **Users** — all traces grouped by user ID
- **Prompts** — versioned prompt management (edit prompts in UI, deploy without redeploy)
- **Evaluations** — scores submitted via `/feedback` endpoint
- **Metrics** — cost over time, latency percentiles, model usage
- **Datasets** — build eval datasets from real traces

---

## Stopping / Resetting

```bash
# Stop all containers (keep data)
docker compose down

# Stop and wipe all data (full reset)
docker compose down -v
```

---

## Production Hardening Checklist

- [ ] Change all default passwords in `.env`
- [ ] Replace bootstrap Langfuse keys with proper generated keys from the UI
- [ ] Set `NEXTAUTH_URL` to your real domain
- [ ] Put Langfuse behind nginx/Caddy with HTTPS
- [ ] Set `TELEMETRY_ENABLED=false` (already done)
- [ ] Restrict CORS in `main.py` to your actual frontend domain
- [ ] Add rate limiting (e.g., `slowapi`) to observability server endpoints
- [ ] Set up log rotation for Docker containers
- [ ] Configure PostgreSQL backups
