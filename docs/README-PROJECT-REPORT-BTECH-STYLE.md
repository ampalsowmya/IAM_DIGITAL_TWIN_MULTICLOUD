# IAM Digital Twin — AI Risk Intelligence Platform  
### Project report–style documentation (B.Tech / capstone format)

This document follows the **tone and section flow** of a typical undergraduate project report (title block, abstract, chapters) while describing the **software project in this repository**. Replace bracketed placeholders with your official names, IDs, and supervisor details before submission.

---

## Cover page (fill in LaTeX or Word separately)

| Field | Suggested text |
|--------|----------------|
| **Title** | IAM Digital Twin: AI Risk Intelligence Platform for Multi-Cloud IAM |
| **Type** | A PROJECT REPORT / B.Tech Project Report |
| **Submitted by** | *[Your name(s), registration number(s)]* |
| **Degree** | Bachelor of Technology in Computer Science and Engineering (Cyber Security) — *adjust if different* |
| **Supervisor** | *[Dr. …]* |
| **Institution** | Amrita Vishwa Vidyapeetham, Amrita School of Computing, Chennai |
| **Month / Year** | *[e.g., April 2026]* |

---

## Bonafide certificate (template text)

This is to certify that the project report entitled **“IAM Digital Twin: AI Risk Intelligence Platform for Multi-Cloud IAM”** is the bonafide work of **[student names and register numbers]** carried out under the supervision of **[supervisor name]**.

*[Signatures: Chairperson, Supervisor, Examiners — as per department format.]*

---

## Declaration

We declare that the report entitled **“IAM Digital Twin: AI Risk Intelligence Platform for Multi-Cloud IAM”** submitted for the award of the degree of **[B.Tech CSE (Cyber Security)]** is the record of the project work carried out by us under the guidance of **[supervisor]**, and this work has not been submitted elsewhere for any other degree or diploma.

*[Student signatures and dates.]*

---

## Abstract

Cloud environments distribute identity across many accounts and services; misconfigured IAM roles and dangerous trust relationships remain a major source of security incidents. This project implements **IAM Digital Twin**, a full-stack **AI risk intelligence platform** that ingests IAM data (AWS via boto3), stores roles and policies in a **Neo4j** graph database, computes **risk levels**, **numeric risk scores**, and **anomaly indicators** using **Random Forest**, **XGBoost**, and **Isolation Forest** models, and presents results through a **dark-themed React dashboard**. The backend is built with **FastAPI** and protects APIs with **JWT authentication**. A **health service** reports the status of AWS connectivity, Neo4j, and ML model readiness. Optional **CIS-style compliance checks** flag high-risk patterns such as administrative wildcards and cross-account trust. The system is container-ready via **Docker Compose**. The outcome is a reproducible prototype suitable for security operations, auditing coursework, and further research on IAM analytics.

**Keywords:** IAM, Neo4j, eBPF-free (user/kernel API only), machine learning, anomaly detection, FastAPI, React, multi-cloud.

---

## Acknowledgement

*[Standard acknowledgement to institution, faculty, supervisor, family — reuse your department’s approved template.]*

---

## Table of contents (outline)

1. Introduction  
2. Literature Survey  
3. Problem Statement and Objectives  
4. Requirements and Feasibility  
5. System Design  
6. Implementation  
7. Testing and Results  
8. Conclusion and Future Work  
9. References  
10. Appendices (screenshots, API list, user manual)

---

## Chapter 1 — Introduction

Identity is the new perimeter. Organizations use IAM roles, policies, and trust policies that are hard to audit at scale. This project builds a **digital twin** of IAM state in a graph database and layers **ML-based risk scoring** and **anomaly detection** on top, with a web dashboard for analysts.

---

## Chapter 2 — Literature Survey

Survey topics you can expand in your own words:

- Cloud IAM best practices and common misconfigurations.  
- Graph databases for security relationship modeling.  
- Supervised and unsupervised learning for risk scoring.  
- Related tools: CSPM, CIEM, policy linters (compare with your integrated graph + ML approach).

---

## Chapter 3 — Problem Statement and Objectives

**Problem:** Manual review of IAM across accounts does not scale; escalation paths and toxic combinations are easy to miss.

**Objectives:**

1. Ingest IAM roles and policies from at least one cloud (AWS) into Neo4j.  
2. Train and serve ML models for risk level, risk score, and anomalies.  
3. Expose REST APIs with authentication and health checks.  
4. Provide a dashboard for visualization, what-if analysis, and compliance hints.

---

## Chapter 4 — Requirements

**Functional:** login, ingest trigger, risk list, graph/escalation endpoints, compliance list, what-if preview.  
**Non-functional:** sub-minute ingest for typical accounts (network dependent), responsive UI, documented API (`/docs`).

**Hardware/software:** PC with Docker; AWS credentials for live tests; Neo4j 5.x.

---

## Chapter 5 — System Design

### 5.1 Architecture diagram

Describe: Browser → React → FastAPI → Neo4j / boto3 / ML in memory. Reference `docker-compose.yml` for deployment.

### 5.2 Database design

Nodes: `IAMRole`, `Policy`. Relationships: `HAS_POLICY`, `CAN_ASSUME`.

### 5.3 ML pipeline

Features: permission counts, admin flags, wildcards, trust counts, cross-account, age, policy counts. Models: RF, XGBoost, Isolation Forest.

### 5.4 API design

Prefix `/api/v1`; JWT except `/auth/token` and `/health`.

---

## Chapter 6 — Implementation

Map report sections to repository paths:

| Component | Location |
|-----------|----------|
| Configuration | `backend/config.py` |
| Auth | `backend/auth.py` |
| Ingestion | `backend/ingestion.py` |
| Graph | `backend/graph_store.py` |
| ML | `backend/ml_engine.py` |
| Risk & compliance | `backend/risk.py` |
| Health | `backend/health.py` |
| App entry | `backend/main.py` |
| UI | `frontend/src/` |

---

## Chapter 7 — Testing and Results

Document:

- **Unit/manual tests:** login, health, ingest (with test AWS account), risk scores populated.  
- **Screenshots:** dashboard overview, ML tab, compliance table.  
- **Metrics:** number of roles ingested, time to ingest, sample risk distribution.

*[Insert your actual tables and figures here.]*

---

## Chapter 8 — Conclusion and Future Work

The project delivers a working IAM risk intelligence stack. Future work: full Azure/GCP ingestion, richer policy semantics, persistent model versioning, RBAC for multiple dashboard users, and production hardening (TLS, secrets manager).

---

## References

1. Amazon Web Services. *AWS Identity and Access Management Documentation.*  
2. Neo4j. *Cypher Manual.*  
3. FastAPI Documentation.  
4. Scikit-learn, XGBoost documentation.  
5. OWASP / CIS AWS Foundations Benchmark (for compliance mapping).

---

## Annexure A — API summary

- `POST /api/v1/auth/token` — obtain JWT  
- `GET /api/v1/health` — AWS, Neo4j, ML status  
- `POST /api/v1/ingest/{cloud}` — trigger ingestion  
- `GET /api/v1/risk/scores` — all role scores  
- `GET /api/v1/graph/escalation-paths` — escalation paths  
- *(See Swagger UI at `/docs` for the full list.)*

---

## Annexure B — User manual (short)

1. Copy `backend/.env.example` to `backend/.env` and set variables.  
2. Start Neo4j (e.g. `docker-compose up -d neo4j`).  
3. Run backend and frontend per main `README.md`.  
4. Log in, run ingest for AWS, observe dashboard refresh.

---

*This file is a report-style companion to the repository. It is not a substitute for your department’s official Word/LaTeX template.*
