# PharmaGenie — Voice Pharmacy Assistant

A **multilingual voice-powered pharmacy AI agent** for your hackathon.  
Speech → Intent → Action → Speech.

## Features

- **Multilingual voice input** — Hindi, English, and more (Web Speech API)
- **LLM intent detection** — add_to_cart, search, check_order, etc.
- **Backend actions** — cart, orders, search, interactions
- **Text-to-speech response** — browser TTS (free)
- **Conversation UI** — mic button, chat-style interface

## Architecture

```
Speech Input (Web Speech API)
        ↓
Speech-to-Text
        ↓
LLM Intent Detection (Ollama/OpenAI)
        ↓
Action Router
        ↓
Backend API (Cart / Orders / Search)
        ↓
Text-to-Speech Response
```

## Quick Start

### 1. Backend (Python)

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. LLM (choose one)

**Option A — Ollama (recommended, free)**  
1. Install [Ollama](https://ollama.ai)  
2. Run: `ollama pull llama3.2`  
3. Backend will use Ollama by default  

**Option B — OpenAI**  
1. Set `LLM_PROVIDER=openai`  
2. Set `OPENAI_API_KEY=sk-...`  
3. Uses gpt-3.5-turbo  

**Fallback**  
If no LLM is available, a built-in rule-based intent detector runs (supports Hindi/English phrases).

### 3. Frontend

Open `frontend/index.html` in a browser, or serve it:

```bash
cd frontend
npx serve .
```

Then open http://localhost:3000 (or wherever serve runs).

**Note:** For Web Speech API to work, use **HTTPS** or **localhost**.

## Example Voice Inputs

- "Mujhe paracetamol chahiye" → adds Paracetamol to cart
- "Add 2 metformin" → adds Metformin x2
- "Search for insulin"
- "What's in my cart?"
- "Place order"

## Project Structure

```
voice assitance pharma/
├── backend/
│   ├── main.py           # FastAPI app
│   ├── intent_detector.py
│   ├── action_router.py
│   ├── config.py
│   ├── api/
│   │   ├── cart.py
│   │   ├── orders.py
│   │   └── search.py
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── .env.example
└── README.md
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/voice/process` | POST | `{"text": "..."}` → intent + action + response |
| `/docs` | GET | Swagger UI |

## Environment

Copy `.env.example` to `.env` and set:

- `LLM_PROVIDER` — `ollama` or `openai`
- `OPENAI_API_KEY` — if using OpenAI
- `OLLAMA_BASE_URL` — default `http://localhost:11434`
- `OLLAMA_MODEL` — default `llama3.2:latest`
