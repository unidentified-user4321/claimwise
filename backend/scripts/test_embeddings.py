from app.rag.embeddings import get_embeddings


embeddings = get_embeddings()

vector = embeddings.embed_query(
    "My friend borrowed my car and crashed it into a wall."
)

print("Embedding generated successfully")
print("Dimension:", len(vector))
print("First 10 values:")
print(vector[:10])