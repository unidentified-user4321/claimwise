import os
from pathlib import Path
from functools import lru_cache

from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings



BACKEND_DIR = Path(__file__).resolve().parents[2]


ENV_FILE = BACKEND_DIR / ".env"


load_dotenv(
    dotenv_path=ENV_FILE,
    override=True,
)

EMBEDDING_MODEL = "models/gemini-embedding-2"


@lru_cache(maxsize=1)
def get_embeddings() -> GoogleGenerativeAIEmbeddings:

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            f"GEMINI_API_KEY is not configured. "
            f"Expected .env at {ENV_FILE}. "
            f"File exists: {ENV_FILE.exists()}"
        )

    return GoogleGenerativeAIEmbeddings(
        model=EMBEDDING_MODEL,
        google_api_key=api_key,
    )