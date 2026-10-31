# Text Detective: Authentication & Case-Level Authorization Architecture Specification

> **Deployment Notice:**  
> In its current version, **Text Detective** is architected for local, single-analyst, offline, and laboratory demo usage. It **MUST NOT** be exposed directly to the public Internet without implementing the authentication and multi-tenant authorization controls detailed in this specification.

---

## 1. Threat Model & Security Posture

### Single-Tenant Local/Demo Baseline (Current)
- The server binds to `127.0.0.1` (loopback interface).
- Requests from the local frontend or CLI are assumed to be issued by the designated local forensic investigator.
- Sensitive API keys (OpenAI / Anthropic) are read exclusively from environment variables (`.env`) and are never returned over API endpoints.
- Path traversal and malicious filenames are sanitized at ingestion.

### Target Multi-Tenant Enterprise Investigation Architecture (Future)
When deploying Text Detective in collaborative intelligence environments, law enforcement agencies, or enterprise forensic units, the following authentication and authorization layers must be implemented.

```
   ┌────────────────────────────────────────────────────────┐
   │             Identity Provider (OIDC / OAuth2)          │
   │           (Azure AD, Okta, Keycloak, Auth0)            │
   └───────────────────────────┬────────────────────────────┘
                               │ JWT / Bearer Token
                               ▼
   ┌────────────────────────────────────────────────────────┐
   │                  API Gateway & Reverse Proxy           │
   │         (TLS Termination, Rate Limiting, WAF)          │
   └───────────────────────────┬────────────────────────────┘
                               │
                               ▼
   ┌────────────────────────────────────────────────────────┐
   │            FastAPI Authentication Middleware           │
   │    - Signature Verification (RS256 / EdDSA)            │
   │    - Claims extraction: sub (user_id), roles, org      │
   └───────────────────────────┬────────────────────────────┘
                               │
                               ▼
   ┌────────────────────────────────────────────────────────┐
   │        Case-Level Access Control (RBAC & ABAC)         │
   │   - Case Permission Matrix (Lead, Contributor, Reader) │
   │   - Evidence redaction & audit logging                 │
   └────────────────────────────────────────────────────────┘
```

---

## 2. Role-Based Access Control (RBAC) Definitions

| Role | Permissions | Use Case |
|---|---|---|
| **Forensic Administrator** (`admin`) | Full system access, case creation/deletion, audit log export, LLM configuration, user role assignments. | Lead Architect / IT Security Officer |
| **Lead Investigator** (`lead_investigator`) | Create, update, archive assigned cases; run full analyses; accept/reject hypotheses; assign review tasks. | Case Detective / Lead Compliance Officer |
| **Case Analyst / Contributor** (`analyst`) | Upload evidence documents; review and annotate contradictions; search evidence; query Q&A. | Junior Forensic Analyst / Paralegal |
| **External Auditor / Observer** (`auditor`) | Read-only access to case reports, chronological timelines, case graphs, and provenance verification audits. | Legal Counsel / Court Auditor / Regulators |

---

## 3. Case-Level Authorization Matrix (ABAC)

Every case object will include an Access Control List (ACL):
```json
{
  "case_id": "case_01_meridian",
  "owner_id": "usr_991823",
  "organization_id": "dept_cyber_forensics",
  "clearance_level": "SECRET",
  "acl": {
    "usr_991823": "owner",
    "usr_441209": "contributor",
    "usr_881920": "viewer"
  }
}
```

### Authorization Enforcement Checks:
1. **Case Access Check:**
   Before any endpoint in `/api/cases/{case_id}/*` executes, the dependency `verify_case_access(required_role)` inspects the requester's JWT.
2. **Document Segregation:**
   Physical files and vector collections are namespaced by `organization_id/case_id/`. No cross-case embedding queries are permitted.
3. **Audit Trail Immutability:**
   Every read, download, review decision, and question asked is appended to a cryptographically hashed, append-only audit log signed with HMAC-SHA256.

---

## 4. Document Retention & Purge Protocol

1. **Document Deletion (`DELETE /api/cases/{case_id}/documents/{doc_id}`):**
   - Immediate unlinking of raw uploaded binary from local filesystem or S3 bucket.
   - Deletion of extracted text chunks from `documents.json`.
   - Purge of vector embeddings from ChromaDB.
   - Invalidation of downstream analysis records (`case.status = OUTDATED`).
2. **Case Destruction (`DELETE /api/cases/{case_id}`):**
   - Recursive wipe of `storage/cases/{case_id}/`, `storage/uploads/{case_id}/`, and ChromaDB collection.
   - Cryptographic record of destruction recorded in the system audit log.
