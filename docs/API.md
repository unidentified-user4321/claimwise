# API

FastAPI OpenAPI at `/docs` is the authoritative request/response schema.
`GET /health` is public and returns `{"status":"ok"}`; it does not test dependencies.
All routes below have the `/api/v1` prefix.

Send `Authorization: Bearer <Clerk session token>`. Clerk verifies the session;
the local `users` mapping supplies the role and customer ownership. No local
login, registration, password, or token-issuing endpoint exists.

| Method | Route | Access / behavior |
|---|---|---|
| POST | `/auth/link` | Valid Clerk identity; body `{"customer_id":"C1001"}`; creates client mapping (201) |
| GET | `/auth/me` | Mapped client/employee; returns local identity and role |
| GET | `/customers/{customer_id}` | Employee or matching client; returns customer ID |
| POST | `/claims` | Client with own customer/policy, or employee; creates claim (201) |
| GET | `/claims` | Client's own claims or employee list; optional `status`, `customer_id`, `limit` (1-100, default 50) |
| GET | `/claims/{claim_id}` | Owner client or employee |
| PATCH | `/claims/{claim_id}` | Employee; updates supplied fields; status changes use workflow checks |
| DELETE | `/claims/{claim_id}` | Employee; deletes claim (204) |
| GET | `/claims/{claim_id}/context` | Employee; customer/policy/vehicle/previous-claim context |
| GET | `/claims/{claim_id}/similar` | Employee; similar claims; `limit` 1-20, default 5 |
| POST | `/claims/{claim_id}/analyze` | Employee; runs and stores ML/NLP, policy checks, and RAG analysis |
| GET | `/claims/{claim_id}/analysis` | Employee; most recent stored analysis, or 404 |
| PATCH | `/claims/{claim_id}/status` | Employee; body `status` and optional `note`; validated transition/history |
| GET | `/claims/{claim_id}/history` | Employee; status/review audit events |
| POST | `/claims/{claim_id}/review-action` | Employee; body `action` and optional `note`; review workflow |

Missing/invalid tokens receive 401; missing mappings or forbidden roles receive
403. Client requests for another customer's individual claim/identity return 404;
explicit cross-customer list/create requests receive 403. Linking a nonexistent
customer returns 400 and an already-linked identity returns 409. Invalid request
schemas return 422; workflow rules may reject otherwise well-formed requests.
Actor identity comes from the authenticated mapping, not client-supplied employee IDs.

Analysis includes `fraud_analysis`, `nlp_analysis`, `policy_checks`, and
`policy_analysis`. Retrieval evidence remains part of backend processing/contracts
even though the employee UI does not render a separate evidence section.
There are no standalone policy, vehicle, previous-claim, or document-upload routes.
Customer linking checks existence only; it is intended for a controlled demo.
