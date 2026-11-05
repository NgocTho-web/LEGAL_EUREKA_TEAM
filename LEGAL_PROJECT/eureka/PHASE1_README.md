# Legal AI Assistant — Phase 1 scaffold

This scaffold is additive: copy these files into the existing `eureka` project. It does not delete or overwrite `demo/`, `src/`, `semantic/`, or the existing Knowledge Graph.

## 1. Python environment (Windows PowerShell)

From the project root (`D:\Project-main\New project\eureka`):

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-phase1.txt
Copy-Item .env.example .env
```

Edit `.env`. Use credentials and endpoints for the EXISTING Neo4j/Qdrant instances. Do not put real `.env` secrets into Git or share them in chat.

## 2. Run API

From project root:

```powershell
python -m uvicorn apps.api.app.main:app --reload --host 127.0.0.1 --port 8000
```

Check:
- http://127.0.0.1:8000/health
- http://127.0.0.1:8000/health/connections
- http://127.0.0.1:8000/docs

The chat endpoint is a Phase 1 contract stub; it deliberately does not generate legal answers or fake citations.

## 3. Run React UI

Open another PowerShell window:

```powershell
cd "D:\Project-main\New project\eureka\apps\web"
npm install
npm run dev
```

Open http://localhost:5173.

## 4. Docker Compose (optional)

From project root, after creating `.env`:

```powershell
docker compose -f docker-compose.phase1.yml up --build
```

Compose only starts the API and React UI. It intentionally does NOT start a new Neo4j or Qdrant instance, to avoid accidentally creating a blank database instead of connecting to your existing data.

## Phase 1 acceptance checklist

- [ ] Python virtual environment and dependencies install successfully.
- [ ] `/health` returns `status: ok`.
- [ ] `/health/connections` accurately reports configured/reachable status.
- [ ] `/docs` shows request/response schemas.
- [ ] React page loads and can call `POST /api/v1/chat`.
- [ ] No API keys are committed or displayed.
- [ ] Existing graph/data is not rebuilt or modified.
