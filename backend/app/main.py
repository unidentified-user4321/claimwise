"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.analysis import router as analysis_router
from app.api.claims import router as claims_router
from app.api.customers import router as customers_router
from app.config import FRONTEND_ORIGIN

app = FastAPI(title="Insurance Claim Analysis API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router, prefix="/api/v1")
app.include_router(claims_router, prefix="/api/v1")
app.include_router(analysis_router, prefix="/api/v1")
app.include_router(customers_router, prefix="/api/v1")


@app.get("/health")
def health_check():
    return {"status": "ok"}
