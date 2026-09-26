from pathlib import Path

from langchain_core.documents import Document

from app.rag.chunker import split_text_into_chunks
from app.rag.pinecone_store import get_vector_store



# Paths


PROJECT_ROOT = Path(__file__).resolve().parents[2]

POLICY_DIR = PROJECT_ROOT / "knowledge_base" / "policies"



# Policy documents we want to ingest


POLICIES = [
    {
        "filename": "motor_comprehensive.md",
        "product_code": "MOTOR_COMPREHENSIVE",
    },
    {
        "filename": "motor_standard.md",
        "product_code": "MOTOR_STANDARD",
    },
]



# Load + chunk policies


def load_policy_chunks() -> list[Document]:

    all_chunks = []

    for policy in POLICIES:

        file_path = POLICY_DIR / policy["filename"]

        if not file_path.exists():
            raise FileNotFoundError(
                f"Policy document not found: {file_path}"
            )

        text = file_path.read_text(encoding="utf-8")

        chunks = split_text_into_chunks(
            text=text,
            product_code=policy["product_code"],
            source=policy["filename"],
        )

        all_chunks.extend(chunks)

    return all_chunks



# Ingest into Pinecone


def ingest_policies():

    chunks = load_policy_chunks()

    print(f"Policies loaded: {len(POLICIES)}")
    print(f"Chunks created: {len(chunks)}")

    # Connect LangChain to Pinecone
    vector_store = get_vector_store()

    # Create deterministic IDs
    #
    # Example:
    # MOTOR_COMPREHENSIVE-0
    # MOTOR_COMPREHENSIVE-1
    # MOTOR_STANDARD-0
    #
    # This prevents duplicate vectors when ingestion
    # is run again.
    ids = [
        f"{doc.metadata['product_code']}-{doc.metadata['chunk_index']}"
        for doc in chunks
    ]

    print("\nUploading chunks to Pinecone...")

    vector_store.add_documents(
        documents=chunks,
        ids=ids,
    )

    print(f"\nSuccessfully uploaded {len(chunks)} chunks to Pinecone.")

    print("\nExample vector IDs:")

    for vector_id in ids[:5]:
        print(f"  {vector_id}")



# Entry point


if __name__ == "__main__":
    ingest_policies()