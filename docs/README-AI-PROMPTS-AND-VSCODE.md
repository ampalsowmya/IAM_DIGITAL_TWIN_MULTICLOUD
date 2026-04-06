# Prompts for another AI + how to run in VS Code

Use this file when you want **another AI** to draft your **project report**, **IEEE-style paper**, or **slides**. Copy the prompt blocks below and paste them into ChatGPT, Claude, Gemini, etc. Fill in the bracketed parts first.

Also read **How to run this project in VS Code** at the bottom.

---

## 1. Master context (paste this first in a new chat)

Use this so the AI knows what your project actually is:

```
You are helping me write academic documents for my software project called "IAM Digital Twin — AI Risk Intelligence Platform."

Stack summary:
- Backend: Python 3.11+, FastAPI, boto3 (AWS IAM ingestion), Neo4j official driver, scikit-learn (RandomForest, IsolationForest), XGBoost, JWT auth (python-jose, passlib), APScheduler for periodic ingest.
- Data: IAM roles and policies ingested into Neo4j as IAMRole and Policy nodes; relationships HAS_POLICY and CAN_ASSUME for trust/escalation paths.
- ML: engineered features (permissions count, admin/wildcard flags, trust counts, cross-account, age, policy counts); RF for risk level, XGBoost for risk score 0–100, Isolation Forest for anomaly score.
- Frontend: React 18, Vite, Tailwind, Recharts, axios; dark cyber dashboard with login, risk tables, charts, compliance tab, what-if preview.
- Ops: Docker Compose for Neo4j + backend + frontend; health endpoint checks AWS, Neo4j, ML models.

Repository layout: backend/ (main.py, config.py, auth.py, ingestion.py, graph_store.py, ml_engine.py, risk.py, health.py), frontend/, docker-compose.yml, README.md.

Constraints: I need original academic tone, no fabricated lab numbers unless I provide them. Use placeholders like [INSERT N ROLES] where I will add real measurements later.
```

---

## 2. Prompt: full B.Tech / capstone project report

```
Using the project context I gave you, write a complete B.Tech project report in English for "IAM Digital Twin — AI Risk Intelligence Platform."

Include these sections in order:
1. Certificate / bonafide / declaration (template wording only)
2. Abstract (200–250 words) + Keywords
3. Acknowledgement (generic, respectful)
4. Table of contents (headings only)
5. Chapter 1 Introduction (motivation, problem, objectives, scope)
6. Chapter 2 Literature Survey (IAM risk, graph DBs for security, ML for risk — cite real survey papers generically as [Author, Year] placeholders)
7. Chapter 3 System Analysis (requirements: functional/non-functional, use cases in bullet form)
8. Chapter 4 Design (architecture diagram description, database schema, API list, ML pipeline diagram in words)
9. Chapter 5 Implementation (map modules to filenames: backend/main.py, ingestion.py, graph_store.py, etc.)
10. Chapter 6 Testing and Results (use placeholders [TBD] for metrics; describe what to measure)
11. Chapter 7 Conclusion and Future Work
12. References (10–15 entries, mix of AWS docs, Neo4j, scikit-learn, security standards)

Tone: formal, third person where appropriate. Institution: Amrita Vishwa Vidyapeetham, Amrita School of Computing, Chennai — adjust if I say otherwise.

My details to insert:
- Student name(s): [YOUR NAME]
- Register number(s): [YOUR ID]
- Supervisor: [SUPERVISOR NAME]
- Month/Year: [MONTH YEAR]
```

---

## 3. Prompt: IEEE-style conference paper (6–8 pages equivalent)

```
Using the project context, draft an IEEE-style research paper (IMRaD structure) titled "IAM Digital Twin: Graph-Based Risk Intelligence for Multi-Cloud IAM with Ensemble Machine Learning."

Sections:
- Abstract (150 words max style)
- Index Terms
- I. Introduction
- II. Related Work (IAM analytics, property graphs, anomaly detection — high level)
- III. System Architecture (layers: ingest, graph, ML, API, UI)
- IV. Methodology (features, models, training on synthetic data if labels absent — be honest)
- V. Security Considerations (JWT, parameterized queries, secrets in env)
- VI. Evaluation (placeholder subsection for experiments — list what we should benchmark)
- VII. Conclusion and Future Work
- References in IEEE style [1], [2], …

Do not invent specific accuracy percentages; use "to be evaluated" or placeholders. Keep length suitable for 6–8 pages when converted to PDF.
```

---

## 4. Prompt: short abstract only (conference / poster)

```
Write a 120-word single-paragraph abstract and 5 IEEE keywords for "IAM Digital Twin," combining Neo4j identity graphs, AWS IAM ingestion, and ensemble ML (RF, XGBoost, Isolation Forest) with a FastAPI + React stack. Mention JWT and health checks in one sentence.
```

---

## 5. Prompt: chapter rewrite / plagiarism-safe pass

```
Here is my draft chapter text:
[PASTE YOUR TEXT]

Rewrite it in formal academic English, preserve technical meaning, improve flow, and vary sentence structure. Do not add new factual claims about performance unless they appear in my text. Highlight anything that still needs a citation.
```

---

## 6. Prompt: figure captions for screenshots

```
I will paste captions for figures from my IAM Digital Twin dashboard and API docs. For each, write a one-sentence IEEE-style caption and a label (Fig. 1, Fig. 2, …).

My figure list:
1. [describe screenshot 1]
2. [describe screenshot 2]
...
```

---

## How to run this project in VS Code

### Prerequisites

- **Python 3.11+** installed and on PATH (`python --version`).
- **Node.js 20+** and npm (`node --version`, `npm --version`).
- **Docker Desktop** (optional but recommended for Neo4j).

### Open the project

1. In VS Code: **File → Open Folder…**
2. Select: `multi-cloud-iam-digital-twin` (the folder that contains `backend/`, `frontend/`, `docker-compose.yml`).

### Python environment (backend)

1. Open a terminal in VS Code: **Terminal → New Terminal** (`` Ctrl+` ``).
2. Create a venv (once):

   ```text
   cd backend
   python -m venv .venv
   ```

3. Activate:

   - **Windows (PowerShell):** `.\.venv\Scripts\Activate.ps1`
   - **Windows (cmd):** `.\.venv\Scripts\activate.bat`

4. Install dependencies:

   ```text
   pip install -r requirements.txt
   ```

5. Copy env file and edit:

   ```text
   copy .env.example .env
   ```

   Set at least: `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`, AWS keys if testing ingest, `JWT_SECRET_KEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`.

### Start Neo4j

From the **repository root** (parent of `backend`):

```text
docker compose up -d neo4j
```

For local dev, use in `backend/.env`:

`NEO4J_URI=bolt://localhost:7687`

Wait ~30 seconds, then open **http://localhost:7474** (Neo4j Browser) if you want to verify.

### Run the backend

With venv activated and `cd backend`:

```text
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

- API: **http://127.0.0.1:8000**
- Swagger: **http://127.0.0.1:8000/docs**

### Run the frontend

**Second terminal** in VS Code:

```text
cd frontend
npm install
npm run dev
```

- UI: **http://localhost:5173**

### VS Code tips

- **Python extension:** Install Microsoft’s “Python” extension; select the interpreter `backend\.venv\Scripts\python.exe`.
- **Two terminals:** Keep one for backend, one for frontend.
- **Debugging backend:** Run and Debug → create `launch.json` → Python → module `uvicorn` with args `main:app --reload` and `cwd` set to `backend` (optional).
- **Env file safety:** Do not commit `.env`; keep secrets only locally.

### Full stack with Docker (alternative)

From repo root:

```text
docker compose up -d --build
```

Set `NEO4J_URI=bolt://neo4j:7687` in `backend/.env` for this mode. Then open **http://localhost:5173** and **http://localhost:8000/docs**.

---

## Quick checklist

| Step | Command / action |
|------|-------------------|
| Open folder | VS Code → Open `multi-cloud-iam-digital-twin` |
| Neo4j | `docker compose up -d neo4j` |
| Backend venv + deps | `cd backend` → venv → `pip install -r requirements.txt` |
| Backend run | `uvicorn main:app --reload --port 8000` |
| Frontend | `cd frontend` → `npm install` → `npm run dev` |
| Login | Use credentials from `backend/.env` (default admin / admin123 if unchanged) |

---

*Keep this file in `docs/` and share the prompt sections with any AI you use for report or paper drafting.*
