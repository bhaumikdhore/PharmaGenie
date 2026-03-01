🚀 PharmaGenie
Agentic AI-Powered Autonomous Pharmacy Platform

PharmaGenie transforms a traditional pharmacy system into an AI-driven, multi-agent autonomous ecosystem capable of:

Conversational medicine ordering

Safety & prescription enforcement

Predictive refill intelligence

Inventory automation

Real-time observability

Multi-role operational dashboards

🧠 Project Vision

Traditional pharmacy systems are:

Reactive

Manual

Fragmented

Operationally heavy

PharmaGenie introduces an Agentic AI architecture where intelligent agents collaborate to automate pharmacy workflows safely and intelligently.

🏗️ System Architecture
User → FastAPI → Orchestrator
                   ↓
             AI Agents Layer
                   ↓
             Services Layer
                   ↓
     Supabase (Postgres) + MongoDB
                   ↓
                n8n Webhooks
                   ↓
          Email / WhatsApp Alerts
                   ↓
              Langfuse Observability
🤖 Multi-Agent Architecture

PharmaGenie uses a modular AI system:

1️⃣ Conversation Agent

Extracts structured JSON from natural language

Validates schema via Pydantic

Handles fallback safely

2️⃣ Safety Agent

Enforces prescription rules

Validates stock

Flags pharmacist approval cases

3️⃣ Predictive Agent

Analyzes historical orders

Estimates medication exhaustion

Generates proactive refill alerts

4️⃣ Action Agent

Updates inventory

Creates orders

Triggers n8n automation

Handles webhook failures gracefully

5️⃣ Orchestrator

Coordinates full workflow

Tracks structured execution steps

Logs everything to MongoDB

Traces AI decisions via Langfuse

🗄️ Database Design
🔹 Supabase (Postgres)

Handles structured transactional data:

Medicines

Customers

Orders

Inventory

🔹 MongoDB

Stores:

Chat history

Agent decision logs

Orchestration traces

This hybrid architecture ensures:

ACID compliance for orders

Flexible schema for AI logging

🌐 Role-Based Dashboards

The system includes four operational dashboards:

👤 Primary User

AI chat interface (text + voice)

Order history

Refill alerts

Order tracking

💊 Pharmacist

Prescription approval queue

Risk alerts

Order validation controls

📦 Warehouse

Inventory monitoring

Low stock alerts

Dispatch management

Restock controls

📊 Admin

System health monitoring

Order analytics

Refill intelligence metrics

Langfuse observability link

Database connectivity status

🔍 Observability

PharmaGenie integrates Langfuse for:

LLM trace visualization

Cost tracking

Latency monitoring

Agent decision transparency

Structured event tracking

Every conversation creates a trace tree visible in the observability dashboard.

🔐 Security & Stability

Strict Pydantic request/response validation

No raw DB responses exposed

Structured error handling

Global exception middleware

Safe webhook execution with retry

Environment-variable based configuration

CORS secured for frontend integration

🛠️ Tech Stack
Backend

FastAPI

Supabase (PostgreSQL)

MongoDB

LangChain

OpenAI GPT

Langfuse

n8n automation

Frontend

Next.js (App Router)

TypeScript

TailwindCSS

shadcn/ui

Axios

DevOps

Vercel (Frontend)

Render/Railway (Backend)

GitHub CI/CD

📦 Project Structure
├── data/
├── backend/
├── agents/
├── services/
├── tools/
├── observability/
├── workflows/
├── frontend/
├── tests/
├── requirements.txt
└── .env
🚀 Installation & Setup
1️⃣ Backend Setup
pip install -r requirements.txt
uvicorn backend.main:app --reload

Access:

http://localhost:8000/docs
2️⃣ Frontend Setup
cd frontend
npm install
npm run dev

Ensure .env.local contains:

NEXT_PUBLIC_API_URL=http://localhost:8000
🧪 Testing

Run:

pytest -q

Includes:

API tests

Orchestrator tests

Service layer tests

Langfuse integration tests

🎯 Demo Scenarios
✔️ Conversational Ordering

User places medicine order via chat.

✔️ Prescription Enforcement

Prescription-required medicines are routed to pharmacist dashboard.

✔️ Predictive Refill Intelligence

System proactively alerts users about upcoming refill needs.

✔️ Inventory Automation

Low stock triggers operational alerts.

✔️ Observability

Full agent trace visible in Langfuse dashboard.

📈 Innovation Highlights

Multi-agent LLM orchestration

Hybrid structured + flexible DB architecture

Real-time operational dashboards

Proactive healthcare intelligence

Enterprise-grade observability

Autonomous workflow execution

🏆 Hackathon Impact

PharmaGenie demonstrates:

Agentic AI collaboration

Safe AI in healthcare workflows

Operational automation

Production-grade architecture

Real-world execution capability

📄 License

MIT License

👨‍💻 Developed For

HackFusion 3 — Agentic AI System Challenge
