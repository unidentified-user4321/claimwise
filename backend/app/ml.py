from pathlib import Path

import joblib
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

FRAUD_MODEL_PATH = (
    PROJECT_ROOT
    / "ml"
    / "artifacts"
    / "xgboost_fraud_pipeline.joblib"
)

NLP_MODEL_PATH = (
    PROJECT_ROOT
    / "ml"
    / "artifacts"
    / "claim_classifier.joblib"
)


if not FRAUD_MODEL_PATH.exists():
    raise FileNotFoundError(
        f"Fraud model not found at: {FRAUD_MODEL_PATH}"
    )

if not NLP_MODEL_PATH.exists():
    raise FileNotFoundError(
        f"NLP model not found at: {NLP_MODEL_PATH}"
    )


fraud_model = joblib.load(FRAUD_MODEL_PATH)
nlp_model = joblib.load(NLP_MODEL_PATH)


def predict_fraud(features: pd.DataFrame) -> dict:

    probability = float(
        fraud_model.predict_proba(features)[0][1]
    )

    prediction = int(probability >= 0.5)

    return {
        "fraud_probability": probability,
        "fraud_prediction": prediction,
    }


def classify_claim_description(description: str) -> dict:

    predicted_class = nlp_model.predict([description])[0]

    probabilities = nlp_model.predict_proba([description])[0]

    confidence = float(probabilities.max())

    return {
        "predicted_incident_type": predicted_class,
        "confidence": confidence,
    }