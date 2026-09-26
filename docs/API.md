# Documentation is incomplete for now. I will update it after the final code review.

# Claim API contract

All routes use the `/api/v1` prefix. The Claim CRUD routes use the existing PostgreSQL `claims` table. Analysis and history routes remain placeholders; the separate `/status` route remains a placeholder, while the Claim PATCH endpoint can update the `status` column.

| Method | Path                          | Purpose                                                                         |
| ------ | ----------------------------- | ------------------------------------------------------------------------------- |
| POST   | `/claims`                     | Submit a motor insurance claim; returns `201` and the created claim             |
| GET    | `/claims`                     | List claims                                                                     |
| GET    | `/claims/{claim_id}`          | Retrieve a claim; returns `404` if missing                                      |
| GET    | `/claims/{claim_id}/context`  | Retrieve claim, customer, policy, vehicle, previous claims, and derived context |
| PATCH  | `/claims/{claim_id}`          | Update supplied claim fields; returns `404` if missing                          |
| DELETE | `/claims/{claim_id}`          | Delete a claim; returns `204` or `404` if missing                               |
| POST   | `/claims/{claim_id}/analyze`  | Request analysis (placeholder)                                                  |
| GET    | `/claims/{claim_id}/analysis` | Retrieve latest analysis                                                        |
| PATCH  | `/claims/{claim_id}/status`   | Change claim status                                                             |
| GET    | `/claims/{claim_id}/history`  | Retrieve investigation history                                                  |

# API Documentation

<!-- Documentation is incomplete for now. I will update it after the final code review. -->

Base path:

```text
/api/v1
```

Interactive Swagger documentation is available at:

```text
http://127.0.0.1:8000/docs
```

## Main APIs

### Claims

```http
POST   /api/v1/claims
GET    /api/v1/claims
GET    /api/v1/claims/{claim_id}
PATCH  /api/v1/claims/{claim_id}
DELETE /api/v1/claims/{claim_id}
```

Used for creating and managing insurance claims.

### Claim Analysis

```http
POST /api/v1/claims/{claim_id}/analyze
GET  /api/v1/claims/{claim_id}/analysis
```

Runs and retrieves claim analysis including fraud risk, NLP classification, policy checks, and RAG-based policy analysis.

### Human Review

```http
POST /api/v1/claims/{claim_id}/review-action
PATCH /api/v1/claims/{claim_id}/status
GET   /api/v1/claims/{claim_id}/history
```

Supports reviewer actions, claim status transitions, and audit history.

### Similar Claims

```http
GET /api/v1/claims/{claim_id}/similar?limit=5
```

Finds potentially similar previous claims using semantic and structured similarity signals.

## Other APIs

The backend also contains APIs for supporting resources such as customers, policies, vehicles, previous claims, health checks, and RAG documents.

Exact request/response schemas, examples, validation rules, and error responses will be documented after the final code review.
