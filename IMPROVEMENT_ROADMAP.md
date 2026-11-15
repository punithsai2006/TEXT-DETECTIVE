# Text Detective: Engineering Improvement & Production Roadmap

> **Target Version:** Text Detective v2.0 / Production Release  
> **Horizon:** Q1 – Q3 2027  
> **Audience:** Core Engineering Team, Security Architects, Product Leadership

---

## 1. Overview & Strategic Goals

While Text Detective now operates with 100% test pass rate, robust date parsing, and verified deterministic hypothesis ranking, transitioning the prototype into a high-concurrency, enterprise-grade investigative platform requires targeted architectural upgrades across storage, NLP modeling, distributed queuing, and security governance.

---

## 2. Phase 1: Storage Layer & Concurrency Overhaul (Q1 2027)

### 2.1 Transition from File-Based JSON to Relational ACID Engine
- **Current State:** Investigation dossiers, documents, entities, and contradictions are stored as discrete `.json` files in `storage/cases/{case_id}/`. While atomic writes (`atomic_write_json`) prevent partial writes, file-based storage lacks row-level locking, indexing, and multi-user concurrency.
- **Target Architecture:** Migrate to **PostgreSQL 16+** with **pgvector** (or embedded SQLite with WAL mode for standalone edge deployments).
  - Relational tables: `cases`, `documents`, `chunks`, `entities`, `events`, `contradictions`, `hypotheses`, `audit_runs`, `reviews`.
  - Foreign key constraints with cascading deletes for complete case purge.
  - Full transactional rollbacks on batch ingestion failures.

### 2.2 Vector Storage Migration
- **Current State:** Custom offline TF-IDF/lexical index and local Chroma directory partitioned by `case_id`.
- **Target Architecture:** Integrate `pgvector` with HNSW indexing or dedicated Qdrant/Milvus instance.
  - Sub-millisecond vector similarity filtering strictly scoped by tenant and `case_id`.
  - Zero filesystem directory synchronization overhead.

---

## 3. Phase 2: Advanced NLP & Transformer Extraction (Q2 2027)

### 3.1 Zero-Shot & Fine-Tuned Entity Extraction (GLiNER)
- **Current State:** SpaCy `en_core_web_sm` with regex filters. Average Entity F1 is ~0.30 due to false positive extraction of generic noun phrases and fragments ("local terminal", "critical alert").
- **Target Architecture:** Replace standard heuristic SpaCy models with **GLiNER (Generalist and Lightweight Model for Named Entity Recognition)**:
  - Zero-shot / few-shot bidirectional transformer architecture for arbitrary investigative schemas (Suspect, Weapon, Vehicle, Alibi, Keycard, IP Address, Account).
  - Drastic reduction of false positives, targeting **Entity F1 > 0.85**.
  - Contextual entity linking and co-reference resolution ("he" / "the security guard" -> "Julian Vance").

### 3.2 Cross-Encoder NLI for Subtle Contradictions
- **Current State:** Rule-based syntactic contradiction engine (negation, numerical bounds, location disjointness, departure time alibi checks).
- **Target Architecture:** Deploy a lightweight **DeBERTa-v3-base-mnli** or **BART-large-MNLI** cross-encoder:
  - Direct natural language inference scoring ($P(\text{entailment}), P(\text{neutral}), P(\text{contradiction})$) across claim-evidence sentence pairs.
  - Ability to detect implicit, semantic, and pragmatic contradictions (e.g. "I was in Paris on Friday" vs "My bank card was used in Tokyo on Friday") that evade rigid regex matching.

---

## 4. Phase 3: Distributed Execution & Job Queues (Q2 2027)

### 4.1 Asynchronous Background Processing
- **Current State:** Investigation analysis (`controller.run_investigation`) executes synchronously in-process on the FastAPI worker. Large document batches (e.g. 50+ PDFs) block API worker threads.
- **Target Architecture:** Introduce **Celery / Redis** (or ARQ / Temporal):
  - Ingestion, OCR parsing, embedding generation, and contradiction detection offloaded to distributed background workers.
  - Server-Sent Events (SSE) or WebSockets to stream granular pipeline progress (`Processing Document 4/12...`, `Extracting Entities...`, `Detecting Contradictions...`) directly to the frontend in real time.

---

## 5. Phase 4: Enterprise Security & Governance (Q3 2027)

### 5.1 Role-Based Access Control (RBAC) & OAuth2
- **Target Roles:**
  - `Viewer / Auditor`: Read-only access to dossiers, timelines, reports, and provenance checks.
  - `Analyst / Investigator`: Can upload documents, create hypotheses, run Q&A, and confirm/reject contradictions.
  - `Lead Investigator / Admin`: Case deletion, model reconfiguration, evidence tampering audits, and user management.
- **Authentication:** OAuth2 with PKCE / JWT bearer tokens, integrating with enterprise IdPs (Okta, Azure AD, Keycloak).

### 5.2 Immutable Cryptographic Audit Log
- **Target Architecture:** Anchor case SHA-256 state hashes in an append-only cryptographic ledger (or RFC 3161 trusted timestamping authority).
  - Guarantees chain of custody for digital evidence presented in legal or disciplinary proceedings.
  - Any post-hoc file modification immediately invalidates the cryptographic verification signature.

---

## 6. Milestone & Delivery Roadmap

```
2027 Q1 ──┬── PostgreSQL + pgvector Migration
          └── Row-Level Security & Transactional Rollbacks
2027 Q2 ──┬── GLiNER Integration (Entity F1 > 0.85)
          ├── DeBERTa-v3 Cross-Encoder for Semantic NLI
          └── Celery/Redis Distributed Ingestion Pipeline
2027 Q3 ──┬── OAuth2 / RBAC Role Governance
          ├── Real-Time WebSocket Pipeline Streaming
          └── Cryptographic RFC 3161 Chain-of-Custody Attestation
```
