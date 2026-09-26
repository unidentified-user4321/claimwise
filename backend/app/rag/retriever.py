from langchain_core.documents import Document

from app.rag.pinecone_store import get_vector_store


def build_claim_retrieval_query(context: dict) -> str:

    claim = context["claim"]
    policy = context["policy"]
    vehicle = context["vehicle"]

    parts = [
        f"Claim description: {claim.claim_description}",
        f"Incident type: {claim.incident_type}",
    ]

    if claim.collision_type:
        parts.append(f"Collision type: {claim.collision_type}")

    if claim.incident_severity:
        parts.append(f"Incident severity: {claim.incident_severity}")

    parts.extend(
        [
            f"Incident date: {claim.incident_date}",
            f"Number of vehicles involved: {claim.number_of_vehicles_involved}",
            f"Property damage: {claim.property_damage}",
            f"Bodily injuries: {claim.bodily_injuries}",
            f"Witnesses: {claim.witnesses}",
            f"Police report available: {claim.police_report_available}",
            f"Claim amount: {claim.total_claim_amount}",
            f"Vehicle: {vehicle.make} {vehicle.model} {vehicle.year}",
            f"Policy deductible: {policy.deductible}",
            f"Policy coverage limit: {policy.coverage_limit}",
        ]
    )

    return "\n".join(parts)


def retrieve_policy_chunks(
    query: str,
    product_code: str,
    k: int = 5,
) -> list[Document]:

    vector_store = get_vector_store()

    return vector_store.similarity_search(
        query=query,
        k=k,
        filter={
            "product_code": product_code,
        },
    )


def retrieve_for_claim(
    context: dict,
    k: int = 5,
) -> list[Document]:

    policy = context["policy"]

    query = build_claim_retrieval_query(context)

    return retrieve_policy_chunks(
        query=query,
        product_code=policy.product_code,
        k=k,
    )