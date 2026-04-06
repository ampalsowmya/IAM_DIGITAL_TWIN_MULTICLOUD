# IAM Digital Twin — AI Risk Intelligence Platform  
### Research-oriented summary (IEEE-style framing)

This document mirrors the structure of a conference-style research contribution while describing the **IAM Digital Twin** system implemented in this repository. Use it alongside the main `README.md` for academic or proposal contexts.

---

## Title (suggested)

**IAM Digital Twin: A Multi-Layered Risk Intelligence Architecture for Cloud IAM with Graph Analytics and Ensemble Machine Learning**

---

## Authors (placeholder — replace with your team)

- Sowmya Karthikeyan — Department of Computer Science, Amrita School of Computing, Amrita Vishwa Vidyapeetham, Chennai, India  
- *(Add co-authors as required)*

---

## Abstract

The rapid adoption of multi-cloud infrastructure has expanded the attack surface for identity and access management (IAM). Static reviews and siloed cloud consoles rarely expose cross-account trust chains, risky permission combinations, or anomalous role behavior at scale. This work presents **IAM Digital Twin**, an end-to-end architecture that (1) ingests live IAM data from cloud providers (AWS implemented via boto3; additional clouds extensible), (2) materializes an identity and policy graph in **Neo4j**, (3) scores every identity using an ensemble of **Random Forest**, **XGBoost**, and **Isolation Forest** models with engineered features from permissions and trust metadata, and (4) exposes a **JWT-protected FastAPI** backend with a **React** dashboard for operational risk visibility. A continuous health subsystem verifies connectivity to AWS, Neo4j, and loaded ML models. Scheduled ingestion keeps the graph aligned with the live estate. The design follows defense-in-depth: cryptographic authentication, parameterized graph queries, auditable APIs, and graceful degradation when external dependencies are unavailable. This README does not claim peer-reviewed empirical results; experimental validation should be filled in from your own measurements.

**Index Terms** — Cloud IAM, identity graph, Neo4j, machine learning risk scoring, anomaly detection, FastAPI, multi-cloud security.

---

## I. Introduction

Enterprise IAM spans roles, policies, trust relationships, and escalation paths that are difficult to reason about in spreadsheets or per-console views. Misconfiguration remains a leading cause of breaches. IAM Digital Twin addresses this by combining **live ingestion**, a **queryable graph** of roles and policies, **ML-driven risk and anomaly scores**, and a **real-time dashboard** for security and platform teams.

---

## II. Related Work (brief)

Prior art includes CSP-native IAM analyzers, policy-as-code linters, and standalone CSPM tools. Few open designs integrate **live IAM APIs**, a **general-purpose property graph**, and **three complementary ML models** (classification, score calibration, unsupervised anomaly) behind a single API and UI. IAM Digital Twin is positioned as a reference implementation for teaching and further research.

---

## III. System Architecture and Methodology

### III-A. Logical layers

1. **Ingestion plane** — AWS IAM: `ListRoles`, attached and inline policies, permission counts, assume-role policy parsing, cross-account signals; periodic scheduler.  
2. **Graph plane** — Neo4j: `IAMRole` and `Policy` nodes; `HAS_POLICY`, `CAN_ASSUME` relationships; escalation path queries over bounded-length assume-role chains.  
3. **Analytics plane** — Feature extraction per role; RF (risk level), XGBoost (risk score), Isolation Forest (anomaly score vs. learned threshold).  
4. **Control plane** — FastAPI routers: auth, ingest, graph, risk, compliance (CIS-style heuristics), health.  
5. **Presentation plane** — React + Tailwind + Recharts: overview, ML metadata, anomalies, what-if preview, compliance table.

### III-B. Security of the platform itself

- **JWT** for all protected routes; OAuth2 password flow for token issuance.  
- **Parameterized Cypher** only.  
- **Environment-based secrets**; no credentials in source control.

---

## IV. Threat Model (operational)

**Assets:** IAM role metadata, policy text-derived features, graph topology, ML outputs.  
**Adversaries:** unauthorized API clients (mitigated by JWT), credential leakage from `.env` (operational hygiene), Neo4j exposure on the network (bind to trusted interfaces / TLS in production).  
**Out of scope for this codebase:** compromise of the cloud provider control plane itself.

---

## V. Formalisms (adaptable)

- **Layered security strength** (informative): \(S = 1 - \prod_{i=1}^{n}(1 - s_i)\) for independent layers \(s_i\).  
- **Risk scoring**: hybrid outputs from tree ensembles and isolation scores; exact formulas are implemented in `ml_engine.py` and `risk.py`.

---

## VI. Implementation Notes

- **Backend:** Python 3.11+, FastAPI, neo4j driver, scikit-learn, xgboost, APScheduler.  
- **Frontend:** Vite, React 18, axios, recharts.  
- **Infrastructure:** Docker Compose for Neo4j and optional full stack.

---

## VII. Experimental Results (to be completed by authors)

Populate this section with **your** runs: e.g., ingest latency, graph size, API p95 latency, detection vs. labeled test roles, false positive rate on a held-out set. The dashboard can export or screenshot metrics for the paper.

---

## VIII. Limitations and Future Work

- Azure/GCP ingestion stubs; expand with provider SDKs.  
- Richer policy semantics (condition keys, SCPs, organization-level context).  
- Online learning or periodic retraining on labeled incidents.  
- Stronger secrets management (Vault, KMS) for production.

---

## IX. Conclusion

IAM Digital Twin demonstrates a **practical pipeline** from live IAM APIs to **graph-backed risk intelligence** and **ensemble ML**, exposed through a **modern API and UI**, suitable as a capstone project, research prototype, or internal tool baseline.

---

## References (starter set — extend in BibTeX for LaTeX)

1. Neo4j Inc., *Neo4j Graph Database Documentation*.  
2. Amazon Web Services, *IAM API Reference*.  
3. Pedregosa et al., *Scikit-learn: Machine Learning in Python*, JMLR 2011.  
4. Chen & Guestrin, *XGBoost*, KDD 2016.  
5. Liu et al., *Isolation Forest*, ICDM 2008.

---

*Generated for the IAM Digital Twin repository. Adapt wording and metrics to your institution’s requirements.*
