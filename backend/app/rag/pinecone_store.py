import os
from functools import lru_cache

from dotenv import load_dotenv
from langchain_pinecone import PineconeVectorStore

from app.rag.embeddings import get_embeddings


load_dotenv()

PINECONE_INDEX_NAME = os.getenv(
    "PINECONE_INDEX_NAME",
    "insurance-policy-rag",
)


@lru_cache(maxsize=1)
def get_vector_store() -> PineconeVectorStore:
    return PineconeVectorStore(
        index_name=PINECONE_INDEX_NAME,
        embedding=get_embeddings(),
    )