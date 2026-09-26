"""Minimal application settings loaded from environment variables."""

import os
from pathlib import Path
from urllib.parse import quote

from dotenv import load_dotenv


# .env is in the project root
load_dotenv(Path(__file__).resolve().parents[2] / ".env")


# print("===== DATABASE CONFIG =====")
# print("ENV FILE:", Path(__file__).resolve().parents[2] / ".env")
# print("HOST:", os.getenv("POSTGRES_HOST"))
# print("PORT:", os.getenv("POSTGRES_PORT"))
# print("DATABASE:", os.getenv("POSTGRES_DB"))
# print("USER:", os.getenv("POSTGRES_USER"))
# print("PASSWORD SET:", bool(os.getenv("POSTGRES_PASSWORD")))
# print("DATABASE_URL SET:", bool(os.getenv("DATABASE_URL")))
# print("===========================")


database_user = quote(
    os.getenv("POSTGRES_USER", "insurance_app"),
    safe=""
)

database_password = quote(
    os.getenv("POSTGRES_PASSWORD", ""),
    safe=""
)

database_host = os.getenv("POSTGRES_HOST", "localhost")
database_port = os.getenv("POSTGRES_PORT", "5432")

database_name = quote(
    os.getenv("POSTGRES_DB", "insurance_claims"),
    safe=""
)


DATABASE_URL = os.getenv("DATABASE_URL") or (
    f"postgresql+psycopg://{database_user}:{database_password}"
    f"@{database_host}:{database_port}/{database_name}"
)


FRONTEND_ORIGIN = os.getenv(
    "FRONTEND_ORIGIN",
    "http://localhost:5173"
)