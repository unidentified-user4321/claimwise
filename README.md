# AI Powered Insurance Claim Analysis

An end-to-end insurance claim analysis system that combines machine learning, NLP, RAG, and human review to assist with insurance claim assessment.

## Current Features

- Claim creation and management
- Fraud-risk prediction using XGBoost
- Claim description classification using TF-IDF + Logistic Regression
- Policy analysis using RAG + Gemini
- Deterministic policy checks
- Duplicate/similar claim detection
- Human review and approval workflow
- Claim status and investigation history
- MLflow experiment tracking and model comparison
- React-based claim analyst interface

## Tech Stack

**Backend:** FastAPI, SQLAlchemy, Alembic  
**Frontend:** React + Vite  
**Database:** PostgreSQL  
**ML:** Scikit-learn, XGBoost, MLflow  
**NLP:** TF-IDF + Logistic Regression  
**LLM:** Gemini  
**RAG / Vector Search:** Pinecone  
**Testing:** Pytest

## Project Structure

```text
insurance_project/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── db/
│   │   ├── rag/
│   │   └── services/
│   ├── alembic/
│   └── tests/
├── frontend/
├── ml/
│   ├── artifacts/
│   ├── data/
│   └── training/
└── README.md
```

## Local setup (PowerShell)

Use Python 3.12, Node.js 20.19+ or 22.12+, and PostgreSQL 16 with `psql`.
Commands below start at the repository root unless stated otherwise.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
Copy-Item .env.example .env
Copy-Item .env.example backend/.env
Copy-Item frontend/.env.example frontend/.env.local
```

Copy examples only on a new checkout; do not overwrite existing local configuration.
Replace placeholders in the ignored files:

- Root `.env`: Docker Compose PostgreSQL settings; the optional evaluation runner
  also loads this file.
- `backend/.env`: the backend config and Alembic read this file for `POSTGRES_*`
  (or `DATABASE_URL`), `CLERK_SECRET_KEY`, and `FRONTEND_ORIGIN`. RAG uses
  `GEMINI_API_KEY`, `PINECONE_API_KEY`, and `PINECONE_INDEX_NAME` here.
- `frontend/.env.local`: `VITE_CLERK_PUBLISHABLE_KEY` and
  `VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1`.

Keep database credentials consistent between root and backend files. `DATABASE_URL`
overrides the separate PostgreSQL fields; remove it to use those fields, or replace
its placeholders and URL-encode special characters in credentials. Exported environment
variables normally take precedence, but the embeddings module loads `backend/.env`
with override enabled. Keep overlapping values consistent. Never commit real keys.
`LLM_PROVIDER`, `LLM_MODEL`, and `PINECONE_INDEX` are not application settings.

### Fresh database only

Docker Compose currently provides **PostgreSQL only**, not the backend or frontend:

```powershell
docker compose up -d db
```

Alternatively, create an empty `insurance_claims` database owned by your configured
PostgreSQL role using pgAdmin or `createdb`. Do not initialize an existing database.
The following example assumes `insurance_app` and `insurance_claims`; substitute
only the role/database names if your configuration differs. `psql -W` prompts for
its password rather than embedding it in a command or SQL file.

```powershell
psql -h localhost -U insurance_app -d insurance_claims -W -v ON_ERROR_STOP=1 -f backend/sql/setup.sql
psql -h localhost -U insurance_app -d insurance_claims -W -v ON_ERROR_STOP=1 -f backend/sql/seed.sql
Push-Location backend
..\.venv\Scripts\python.exe -m alembic upgrade head
Pop-Location
```

`setup.sql` creates the six original tables from the current SQLAlchemy schema:
customers, policies, vehicles, previous_claims, claims, and claim_analyses, including
indexes. The original Alembic baseline is intentionally empty; later migrations
create **claim_history** and **users** only. Do not use `create_all`, manually create
these latter tables, or stamp past migrations. The scripts are transactional and
intentionally fail on existing tables/duplicate seeds instead of overwriting data.

`seed.sql` supplies fictional C1001/P1001 and C1002/P1002 customers/policies,
vehicles, previous claims, and two submitted claims. It is not an export of the
original local database. Policy periods are 2025-2030; demo incidents are in 2026.
P1002 has a synthetic coverage limit of 300000 and product MOTOR_STANDARD.
These sample amounts/dates are demo choices, not reconstructed insurance terms.
No Clerk identities, passwords, analyses, or review history are seeded. Provision
Clerk mappings as described below. For an existing correctly initialized database,
run only pending Alembic upgrades after your normal backup; never rerun setup SQL.

### Required local ML artifacts

Before starting FastAPI, obtain **trusted, compatible** trained artifacts or train
locally. The backend loads both files at import time:

- `ml/artifacts/xgboost_fraud_pipeline.joblib`
- `ml/artifacts/claim_classifier.joblib`

Artifacts and training datasets are intentionally ignored and are **not included**
in this public repository. A checkout alone cannot run inference. Joblib files must
come from a trusted source and use compatible training/runtime package versions.
To train, first supply appropriately licensed datasets at `ml/data/insurance_claims.csv`
and `ml/data/claim_text_training.csv` with the columns consumed by the corresponding
training scripts (NLP requires `claim_description` and `incident_type`):

```powershell
.\.venv\Scripts\python.exe -m pip install -r ml/requirements.txt
.\.venv\Scripts\python.exe ml/training/train_fraud.py
.\.venv\Scripts\python.exe ml/training/train_nlp.py
```

Dataset acquisition is not automated. Fraud training compares XGBoost and Random
Forest and records local MLflow experiments. The current backend Dockerfile does
not package the model artifacts or migrations; it is not a complete deployment
recipe. Use the local startup below.

### RAG prerequisites and startup

Configure a Pinecone index compatible with the embeddings used in
`backend/app/rag/embeddings.py`, then ingest the bundled policy documents once.
This command makes real Gemini/Pinecone calls and writes vectors:

```powershell
Push-Location backend
..\.venv\Scripts\python.exe -m scripts.ingest_policies
Pop-Location
```

After database setup, model preparation, and Clerk configuration:

```powershell
Push-Location backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
Pop-Location
```

In another terminal:

```powershell
cd frontend
npm ci
npm run dev
```

Frontend: http://localhost:5173. API documentation: http://127.0.0.1:8000/docs.
Normal startup does not require LangSmith or a live evaluation run.

## Main Workflow

```text
Claim
  ↓
Fraud Risk Model
  ↓
NLP Classification
  ↓
Policy Checks
  ↓
RAG + LLM Analysis
  ↓
Similar Claim Detection
  ↓
Human Review
  ↓
Claim Status + Audit History
```

## Documentation

- [API](docs/API.md): current routes and authorization.
- [Architecture](docs/ARCHITECTURE.md): application components.

## Clerk authentication setup

Clerk owns sign-up, email verification, sign-in, sessions, and sign-out. The local
`users` table stores only `user_id`, unique `clerk_user_id`, `role`, and nullable
`customer_id`. The existing backend ownership/employee checks remain authoritative.
No passwords, email addresses, verification codes, or tokens are stored locally.

### Clerk Dashboard

1. Create/select a Clerk application and use its Development instance for this demo.
2. Under **User & authentication**, enable **Email** as a required identifier,
   require email verification during sign-up, and enable **Email verification code**
   for sign-in. Disable unnecessary identifiers/requirements for the minimal demo.
   Clerk's built-in components perform the configured verification flow.
3. Optionally enable **Google** under **SSO connections / Social connections**.
   Development uses Clerk's development configuration; production requires your
   own Google OAuth credentials and the redirect URI shown by Clerk.
4. Copy the Publishable Key and Secret Key from **API keys**, from the SAME instance.
5. Configure the application's development/Home URL as `http://localhost:5173/login`.
   Use this origin consistently; backend `FRONTEND_ORIGIN` must match the browser's
   origin (including port). No JWT template or custom claims are needed.
6. For an employee, create a Clerk user through Dashboard **Users** (or have the
   employee complete Clerk sign-up first without linking a customer). Copy its
   `user_...` ID and provision its local mapping with the script below. Do not
   assign application roles through Clerk metadata.

Official references:
[React setup](https://clerk.com/docs/react/getting-started/quickstart),
[sign-in component](https://clerk.com/docs/react/reference/components/authentication/sign-in),
[authentication settings](https://clerk.com/docs/guides/configure/auth-strategies/sign-up-sign-in-options),
[Google](https://clerk.com/docs/guides/configure/auth-strategies/social-connections/google),
[Python SDK](https://github.com/clerk/clerk-sdk-python#request-authentication).

### Local configuration

Set these in `backend/.env` (the path resolved by the backend config):

```dotenv
CLERK_SECRET_KEY=<your Clerk secret key>
FRONTEND_ORIGIN=http://localhost:5173
```

Set these in `frontend/.env.local`:

```dotenv
VITE_CLERK_PUBLISHABLE_KEY=<your Clerk publishable key>
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

Remove the obsolete `JWT_SECRET` and `JWT_ACCESS_TOKEN_MINUTES` settings from your
local environment files. Never place `CLERK_SECRET_KEY` in a `VITE_` variable or
commit real keys. No new Clerk keys are supplied by the repository.

### Legacy custom-auth databases only

Fresh installations must follow the setup above and need no reset. Some early
local databases applied revision `8f2a6c9d104b` when it still described a custom
username/password table. A revision number alone cannot identify that old schema.
If an existing installation has `username`/`password_hash` instead of
`clerk_user_id`, back it up and plan a deliberate one-time migration before use.
Do not downgrade or drop `users` on a current Clerk installation: that destroys
valid account mappings. Automatic/reset commands are intentionally omitted here.

### Provision an employee

After creating the Clerk employee account, run from `backend/`:

```powershell
..\.venv\Scripts\python.exe scripts/create_user.py
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Use the activated project virtual environment for these commands (or invoke
`..\.venv\Scripts\python.exe scripts/create_user.py` and
`..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload`). The provisioning
script verifies the Clerk user exists in the configured instance and refuses to
overwrite any existing mapping. It never asks for a password.

In another terminal, from `frontend/`:

```powershell
npm.cmd run dev
```

### Demo flows and authorization

- **Client:** choose Client, use Clerk sign-up/sign-in, complete Clerk verification,
  and enter an existing Customer ID once. `POST /api/v1/auth/link` verifies the Clerk
  session and customer existence, refuses an already mapped identity, and always
  creates a client. The request accepts only `customer_id`.
- **Employee:** choose Employee and sign in with Clerk. Sign-up links and automatic
  OAuth sign-up transfer are disabled in this workspace. Only a database mapping
  provisioned as employee grants employee access. An unmapped employee must run
  provisioning before proceeding; use Retry or reload after provisioning.
- `GET /api/v1/auth/me` resolves the local mapping. An authenticated but unmapped
  identity receives `403 Account linking required`. Invalid/missing tokens receive
  `401`. The old `/auth/login` and `/auth/register` endpoints no longer exist.
- The API service requests a current Clerk token using `getToken()` for every call.
  Clerk restores sessions and handles sign-out. Workspace selection is UI only;
  backend database roles/customer links enforce access. Audit events keep using
  the local employee `user_id`.

Customer linking checks existence, not real-world customer ownership. This is a
controlled demo: anyone with a Clerk account and a known customer ID can request
that link, and multiple Clerk users can link to one customer. There are no webhooks:
Clerk account deletion does not automatically remove the local mapping. Token
validity follows Clerk session verification; no custom revocation system is added.
Email/Google flows require configured Clerk keys, internet access, and manual
browser verification; automated tests mock Clerk and do not contact it.

## Backend tests

From the repository root (PowerShell):

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
```

Pytest collects `backend/tests` only. Each API test gets a fresh in-memory SQLite
database; local `.env` files and PostgreSQL are not used. Clerk verification,
ML inference, and external policy/embedding providers are mocked at their boundaries.
No trained model artifacts, Clerk account, Gemini key, or network services are required.
Tests cover health, client linking and authorization, claim CRUD, analysis response
and persistence, validation/errors, and the existing review/status/similarity regressions.
SQLite checks application persistence, not PostgreSQL-specific JSONB operators or migrations.


## Optional RAG evaluation (LangSmith)

Pytest checks software behavior; this separate experiment measures RAG quality.
It uses ten curated fictional cases (five per policy), the existing chunker/index,
real Gemini embeddings, Pinecone product filtering, and the unchanged production
policy-analysis prompt. It does not access PostgreSQL, invoke ML models, or change
production files. Fixed synthetic policy/vehicle records are evaluation context,
not claimed policy facts. Fraud/NLP signals are marked as not evaluated.

From the repository root in PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-eval.txt
.\.venv\Scripts\python.exe backend/evals/evaluate_rag.py --check
.\.venv\Scripts\python.exe backend/evals/evaluate_rag.py
```

`--check` validates reference phrases against chunks produced from the local policy
documents without any external calls. The full run requires `LANGSMITH_API_KEY`,
`GEMINI_API_KEY`, `PINECONE_API_KEY`, and the intended `PINECONE_INDEX_NAME`.
Add secrets only to ignored environment files. The runner loads root `.env`;
the existing embeddings module also loads `backend/.env` with override enabled,
so keep overlapping values consistent. Set `LANGSMITH_ENDPOINT` only for a different
LangSmith region/deployment, and `LANGSMITH_WORKSPACE_ID` if required by your key.
No global tracing flag or LangSmith configuration is required for normal app startup.

The configured Pinecone index must already contain the current policy documents,
loaded with the existing `backend/scripts/ingest_policies.py` workflow. The evaluation
does not upload or rewrite vectors. Re-ingest updated policy documents separately
when appropriate; local reference validation cannot establish what is in Pinecone.

- **Retrieval Hit@5:** 1 when at least one of the five actual retrieved chunks has
  the expected product code and contains all curated evidence phrases (case and
  whitespace normalized); otherwise 0. The aggregate is successful cases / cases.
- **Groundedness:** the existing Gemini model acts as a structured-output judge,
  scoring 0/1 for support by retrieved text and synthetic case facts/checks.
- **Correctness:** that judge separately scores 0/1 against the concise reference
  interpretation, allowing justified conditional coverage/human review wording.

One judge call returns both quality scores with short reasons. A temporary wrapper
inside this standalone process records the real retrieval results without changing
what generation receives or running retrieval twice. Runs are serial for that reason.
Do not import this instrumentation into the API server. Expected answers are supplied
only to evaluators, never to the production generation prompt.

The script uses the supported `Client.evaluate` API in LangSmith 0.14 and creates
or reuses a dataset named `insurance-rag-evaluation-<case-file-hash>`. Find its experiment
under **Datasets & Experiments** in your LangSmith workspace; experiment names begin
with `insurance-rag-evaluation`. Inputs, generated analyses, retrieved text/metadata,
and scores are uploaded. Only the curated fictional records are used.

A normal run performs ten retrieval/generation operations and ten judge calls
(provider retries may add requests). It incurs external-service usage; do not run
it repeatedly without a reason. Missing credentials stop the run before evaluation.
Unavailable generation/judging is reported as incomplete/unscored, not a fabricated
zero or success. Complete-run percentages use all ten cases; partial-run percentages
use only scored cases and explicitly report the missing count.

Limitations: ten cases are a small demonstration, phrase matching may miss equivalent
evidence, stale index contents affect results, and an LLM judge (especially the same
model as the generator) can be biased or variable. These scores are not calibrated
insurance decisions. No extra evaluation framework is used.

Recorded live evaluation: Retrieval Hit@5 **7/10 (70%)**, groundedness **10/10
(100%)**, correctness **10/10 (100%)**. These are results on the curated ten-case
demo set, not general system accuracy or evidence of production readiness.
