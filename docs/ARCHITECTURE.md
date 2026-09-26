# Documentation is incomplete for now. I will update it after the final code review.

# Initial architecture

# System Architecture

<!-- Documentation is incomplete for now. I will update it after the final code review. -->

## Overview

The system follows a layered architecture with a React frontend, FastAPI backend, PostgreSQL database, and separate ML/RAG components.

```text
React Frontend
      ↓
FastAPI API
      ↓
Service Layer
      ├── Claim Management
      ├── Claim Analysis
      ├── Human Review
      └── Similar Claim Detection
      ↓
AI / ML Layer
      ├── Fraud Risk Model
      ├── NLP Classifier
      ├── Policy Checks
      └── RAG + Gemini
      ↓
PostgreSQL / Vector Search
```

## Backend Structure

```text
app/
├── api/          # API routes
├── services/     # Business logic
├── db/           # Database models and connection
├── rag/          # RAG and vector-search logic
├── ml.py         # Model inference
└── main.py       # FastAPI application
```

## Claim Analysis Flow

```text
Claim
  ↓
Fraud Prediction
  ↓
NLP Classification
  ↓
Policy Checks + RAG
  ↓
Analysis Result
  ↓
Human Review
  ↓
Status / Audit History
```

Similar-claim detection is available as an additional analyst signal and does not itself determine fraud.

More detailed component and data-flow documentation will be added after the final code review.
