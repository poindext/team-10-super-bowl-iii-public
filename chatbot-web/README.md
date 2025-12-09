# Chatbot Web (Clinical Trials)

Minimal web UI + backend proxy for a ChatGPT-powered clinical trials chatbot.

## Structure
```
public/chatbot-web/
  backend/    # FastAPI backend (calls OpenAI + IRIS)
  frontend/   # Static HTML/JS/CSS chat UI
```

## Backend (FastAPI)

### Prereqs
- Python 3.10+ (your Homebrew Python is fine)
- Create a virtual env (recommended):
  ```bash
  cd public/chatbot-web/backend
  python3 -m venv venv
  source venv/bin/activate
  ```

### Install deps
```bash
cd public/chatbot-web/backend
source venv/bin/activate
python3 -m pip install -r requirements.txt
```

### Configure env
Copy `env.example` to `.env` or export variables:
```bash
export OPENAI_API_KEY=sk-...
# Choose one auth method:
export IRIS_USERNAME=...
export IRIS_PASSWORD=...
# OR
export IRIS_BEARER_TOKEN=...
# OR
export IRIS_API_KEY=...
```

### Run backend
```bash
cd public/chatbot-web/backend
source venv/bin/activate
uvicorn app:app --reload --port 8000
```

The backend exposes:
- `POST /chat` for chat/tool calls
- `GET /health`

## Frontend (static)
- Files in `frontend/` are static HTML/JS/CSS.
- By default, the JS calls `/chat` on the same origin.

### Quick serve frontend (with backend)
For local testing, you can serve frontend via a simple file server while backend runs on 8000, then open `http://localhost:8000` if you mount `frontend` there, or use any static server (e.g., `python3 -m http.server 8080` in `frontend` and set backend CORS to allow it).

Simplest: run both from the same origin using FastAPI’s `--app-dir` mount if desired, or use a reverse proxy; otherwise, enable CORS (already enabled) and point the frontend fetch to `http://localhost:8000/chat`.

To point the frontend at a different backend origin, edit `frontend/app.js` fetch URL.

## Notes
- Backend uses OpenAI function calling to invoke the IRIS vector search tool.
- IRIS endpoint is called server-side only; credentials stay off the client.
- CORS is open (`*`) for quick testing; tighten for production.

