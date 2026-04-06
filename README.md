# IAM Digital Twin

Real-time IAM risk intelligence: AWS IAM ingestion (boto3), Neo4j identity graph, ML scoring (RandomForest + XGBoost + Isolation Forest), and a React dashboard.

## Quick Start

1. Copy environment file and add AWS credentials:

   `cp backend/.env.example backend/.env`

2. For **Docker Compose**, set in `backend/.env`:

   `NEO4J_URI=bolt://neo4j:7687` (container-to-container; internal port **7687**)

   On the **Windows host**, Neo4j Bolt is mapped to **7688** and HTTP UI to **7475** (see `docker-compose.yml`) so it does not clash with another Neo4j on 7687/7474.

3. Start the stack:

   `docker-compose up -d --build`

4. Open the UI: [http://localhost:5173](http://localhost:5173)

5. Log in with `ADMIN_USERNAME` / `ADMIN_PASSWORD` from `backend/.env` (defaults: `admin` / `admin123`).

6. In the sidebar, choose **AWS** (or Azure/GCP stub) and click **Run ingest** to pull live IAM data.

7. The dashboard refreshes risk data about every 10 seconds.

API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

## Local development (without Docker for app code)

- Start Neo4j only: `docker-compose up -d neo4j`
- Use `NEO4J_URI=bolt://localhost:7687` in `backend/.env`
- Backend: `cd backend && pip install -r requirements.txt && uvicorn main:app --reload --port 8000`
- Frontend: `cd frontend && npm install && npm run dev`

## Architecture

AWS IAM → boto3 ingestion → FastAPI → Neo4j graph + ML scoring → React dashboard (JWT-protected API).

Backend modules: `main.py` (lifespan + scheduler), `graph_store.py` (Neo4j + wait/retry), `ml_engine.py` (RF / XGBoost / Isolation Forest). Optional `nginx` service on port **8080** proxies `/api` to the backend; UI dev server remains on **5173**.

## Academic / report write-ups

- [IEEE-style research summary](docs/README-RESEARCH-PAPER-IEEE-STYLE.md) — conference-style framing for this IAM Digital Twin project.  
- [B.Tech project report–style outline](docs/README-PROJECT-REPORT-BTECH-STYLE.md) — sections aligned to a typical capstone report (abstract, chapters, annexures).  
- [AI prompts + VS Code run guide](docs/README-AI-PROMPTS-AND-VSCODE.md) — copy-paste prompts for another AI to help with report/paper; how to run the app in VS Code.

## Security

- Never commit `backend/.env` with real secrets.
- Change `JWT_SECRET_KEY` and admin password for any shared or production deployment.
