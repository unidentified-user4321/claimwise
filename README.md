# Documentation is incomplete for now. I will update it after the final code review.

# AI Powered Insurance Claim Analysis

An end-to-end insurance claim analysis system that combines machine learning, NLP, RAG, and human review to assist with insurance claim assessment.

<!-- Documentation is incomplete for now. I will update it after the final code review. -->

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

## Configuration

Create a `.env` file inside the backend directory and configure the required services.

Example:

```env
DATABASE_URL=postgresql+psycopg://postgres:password@localhost:5432/insurance_claims

GEMINI_API_KEY=your_gemini_api_key
LLM_PROVIDER=gemini
LLM_MODEL=your_gemini_model

PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX=your_index_name
```

Do not commit real API keys or database passwords to GitHub.

## Database Setup

The project currently uses PostgreSQL with Alembic for database migrations.

Some of the initial database tables and demo data were created manually during early development, while later schema changes are managed through Alembic migrations.

The database setup will be updated with a complete PostgreSQL initialization/seed script so the full database can be reproduced directly from the repository.

For now, the repository represents the current demo version of the application.

## PostgreSQL Database

The application uses PostgreSQL for storing:

- Customers
- Policies
- Vehicles
- Claims
- Previous claims
- Claim analyses
- Claim status/history

Create the database before starting the backend:

```sql
CREATE DATABASE insurance_claims;
```

Database schema changes are managed using Alembic.

From the `backend` directory:

```bash
alembic upgrade head
```

## Running the Backend

```bash
cd backend

python -m venv .venv
```

Activate the environment and install dependencies:

```bash
pip install -r requirements.txt
```

Start FastAPI:

```bash
uvicorn app.main:app --reload
```

Swagger API documentation will be available at:

```text
http://127.0.0.1:8000/docs
```

## Running the Frontend

```bash
cd frontend
npm install
npm run dev
```

The Vite development server normally runs at:

```text
http://localhost:5173
```

## ML Models

Training scripts are available under:

```text
ml/training/
```

The project currently uses:

- XGBoost for fraud-risk prediction
- Random Forest as a fraud-model baseline/comparison
- TF-IDF + Logistic Regression for claim-description classification

Trained model artifacts are stored under:

```text
ml/artifacts/
```

MLflow is used to track fraud-model experiments and compare model performance.

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

More detailed documentation is available/will be completed in:

- `API.md` — main API endpoints and request/response flow
- `ARCHITECTURE.md` — system components and architecture

Detailed setup, configuration, API, and architecture documentation will be finalized after the code review.
