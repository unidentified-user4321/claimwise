"""Small-dataset claim comparison: an analyst signal, never a fraud decision."""

from math import isfinite, sqrt

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Claim, Vehicle
from app.rag.embeddings import get_embeddings


SIMILARITY_THRESHOLD = 0.60
SEMANTIC_WEIGHT = 0.60
STRUCTURED_WEIGHTS = {
    "customer_id": 0.25, "policy_id": 0.25, "vehicle": 0.20,
    "incident_type": 0.08, "incident_location": 0.07,
    "amount": 0.06, "date": 0.06, "collision_type": 0.03,
}
DATE_WINDOW_DAYS = 30


def _description_vectors(texts: list[str]) -> list[list[float]]:
    """Provider boundary; no policy vector store or claim persistence involved."""
    return get_embeddings().embed_documents(texts)


def _cosine(left, right):
    if not left or len(left) != len(right) or not all(isfinite(x) for x in (*left, *right)):
        raise ValueError("Invalid embedding vectors")
    denominator = sqrt(sum(x * x for x in left)) * sqrt(sum(x * x for x in right))
    return max(0.0, min(1.0, sum(a * b for a, b in zip(left, right)) / denominator)) if denominator else 0.0


def _normalized(value):
    return " ".join(str(value).casefold().split()) if value is not None else ""


def _structured_similarity(target, candidate, vehicles):
    score, reasons = 0.0, []
    for field, reason in (
        ("customer_id", "Same customer"), ("policy_id", "Same policy"),
        ("incident_type", "Same incident type"),
        ("incident_location", "Same incident location"),
        ("collision_type", "Same collision type"),
    ):
        a, b = getattr(target, field), getattr(candidate, field)
        # Identifiers are exact; descriptive fields ignore case/extra whitespace.
        if field not in ("customer_id", "policy_id"):
            a, b = _normalized(a), _normalized(b)
        if a and a == b:
            score += STRUCTURED_WEIGHTS[field]
            reasons.append(reason)

    a = vehicles.get((target.customer_id, target.policy_id), [])
    b = vehicles.get((candidate.customer_id, candidate.policy_id), [])
    if len(a) == len(b) == 1 and a[0] == b[0]:
        score += STRUCTURED_WEIGHTS["vehicle"]
        reasons.append("Same insured vehicle (unique customer/policy vehicle)")

    a, b = float(target.total_claim_amount), float(candidate.total_claim_amount)
    if max(a, b) > 0 and min(a, b) >= 0:
        difference = abs(a - b) / max(a, b)
        score += STRUCTURED_WEIGHTS["amount"] * (1 - difference)
        if difference <= 0.10:
            reasons.append(f"Claim amounts differ by {difference:.0%}")
    days = abs((target.incident_date - candidate.incident_date).days)
    date_score = max(0.0, 1 - days / DATE_WINDOW_DAYS)
    score += STRUCTURED_WEIGHTS["date"] * date_score
    if date_score > 0:
        reasons.append(f"Incident dates are {days} days apart")
    return score, reasons


def find_similar_claims(db: Session, claim_id: str, limit: int = 5):
    target = db.get(Claim, claim_id)
    if target is None:
        raise HTTPException(404, "Claim not found")
    if not 1 <= limit <= 20:
        raise HTTPException(400, "Limit must be between 1 and 20")
    candidates = db.scalars(select(Claim).where(Claim.claim_id != claim_id)).all()
    if not candidates:
        return {"claim_id": claim_id, "similar_claims": []}

    vehicles = {}
    for vehicle in db.scalars(select(Vehicle)).all():
        vehicles.setdefault((vehicle.customer_id, vehicle.policy_id), []).append(vehicle.vehicle_id)

    # Embed each distinct nonblank description once per request in one batch.
    texts = list(dict.fromkeys(c.claim_description.strip() for c in [target, *candidates] if c.claim_description.strip()))
    try:
        vectors = _description_vectors(texts) if texts else []
        if len(vectors) != len(texts):
            raise ValueError("Incomplete embedding response")
        embeddings = dict(zip(texts, vectors))
        target_vector = embeddings.get(target.claim_description.strip())
        matches = []
        for candidate in candidates:
            vector = embeddings.get(candidate.claim_description.strip())
            semantic = _cosine(target_vector, vector) if target_vector is not None and vector is not None else 0.0
            structured, reasons = _structured_similarity(target, candidate, vehicles)
            score = SEMANTIC_WEIGHT * semantic + (1 - SEMANTIC_WEIGHT) * structured
            if score < SIMILARITY_THRESHOLD:
                continue
            if semantic >= 0.80:
                reasons.append("Descriptions are highly semantically similar")
            elif semantic >= 0.60:
                reasons.append("Descriptions are semantically similar")
            matches.append({"claim_id": candidate.claim_id, "similarity_score": round(score, 6),
                            "description_similarity": round(semantic, 6), "reasons": reasons})
    except Exception as exc:
        raise HTTPException(503, "Claim similarity is temporarily unavailable. Please try again later.") from exc

    matches.sort(key=lambda match: (-match["similarity_score"], match["claim_id"]))
    return {"claim_id": claim_id, "similar_claims": matches[:limit]}
