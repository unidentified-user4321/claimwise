from app.rag.retriever import retrieve_policy_chunks


def test_query(query: str, product_code: str):

    print("\n" + "=" * 80)
    print("QUERY:")
    print(query)

    print("\nPRODUCT:")
    print(product_code)

    results = retrieve_policy_chunks(
        query=query,
        product_code=product_code,
        k=5,
    )

    print(f"\nRetrieved {len(results)} chunks")

    for rank, doc in enumerate(results, start=1):

        print("\n" + "-" * 80)
        print(f"RANK: {rank}")
        print(f"PRODUCT: {doc.metadata.get('product_code')}")
        print(f"CHUNK: {doc.metadata.get('chunk_index')}")
        print(f"SOURCE: {doc.metadata.get('source')}")
        print("-" * 80)

        print(doc.page_content[:1000])


if __name__ == "__main__":

    test_query(
        query=(
            "The customer drove the vehicle through deep standing "
            "flood water. Water entered the engine and damaged it. "
            "The customer is requesting payment for the repairs."
        ),
        product_code="MOTOR_COMPREHENSIVE",
    )