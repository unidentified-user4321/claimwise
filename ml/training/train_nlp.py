from pathlib import Path

import joblib
import pandas as pd

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline


# --------------------------------------------------
# Paths
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_PATH = PROJECT_ROOT / "ml" / "data" / "claim_text_training.csv"
MODEL_PATH = PROJECT_ROOT / "ml" / "artifacts" / "claim_classifier.joblib"

MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------
# Load and clean dataset
# --------------------------------------------------

df = pd.read_csv(DATA_PATH)

df = df.dropna(subset=["claim_description", "incident_type"])
df = df.drop_duplicates(subset=["claim_description", "incident_type"])

df["claim_description"] = df["claim_description"].str.strip()
df["incident_type"] = df["incident_type"].str.strip().str.lower()

print("Dataset shape:", df.shape)
print("\nClass distribution:")
print(df["incident_type"].value_counts())


# --------------------------------------------------
# Features / target
# --------------------------------------------------

X = df["claim_description"]
y = df["incident_type"]


# --------------------------------------------------
# Train / test split
# --------------------------------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y,
)

print("\nTraining samples:", len(X_train))
print("Testing samples:", len(X_test))


# --------------------------------------------------
# NLP Pipeline
# --------------------------------------------------





# After testing the baseline, I increased the TF-IDF vocabulary and used
# both single words and two-word phrases to capture more information from
# the claim descriptions. Logistic Regression worked well for this small dataset.
nlp_pipeline = Pipeline([
    (
        "tfidf",
        TfidfVectorizer(
            lowercase=True,
            ngram_range=(1, 2),
            min_df=1,
            max_df=0.95,
            max_features=10000,
            sublinear_tf=True,
            strip_accents="unicode",
        ),
    ),
    (
        "classifier",
        LogisticRegression(
            max_iter=1500,
            class_weight="balanced",
            random_state=42,
        ),
    ),
])


# --------------------------------------------------
# Train
# --------------------------------------------------

print("\nTraining NLP classifier...")

nlp_pipeline.fit(X_train, y_train)


# --------------------------------------------------
# Evaluate
# --------------------------------------------------

predictions = nlp_pipeline.predict(X_test)

print("\n--- NLP Classification Results ---")
print("\nAccuracy:", round(accuracy_score(y_test, predictions), 4))

print("\nClassification Report:")
print(classification_report(y_test, predictions, digits=3))

print("Confusion Matrix:")
print(confusion_matrix(y_test, predictions))


# --------------------------------------------------
# Save model
# --------------------------------------------------

joblib.dump(nlp_pipeline, MODEL_PATH)

print("\nModel saved to:")
print(MODEL_PATH)


# --------------------------------------------------
# Sanity tests
# --------------------------------------------------




# The test accuracy is very high, so I also check the model on differently
# written claim examples to make sure it is not only learning the dataset patterns.
examples = [
    "I returned to the parking area and my vehicle was missing.",
    "I lost control while turning and the front of my car struck a divider.",
    "Heavy rainfall caused water to enter the vehicle and damage the engine.",
    "I found the windows broken and scratches across the doors after returning.",
    "Smoke started coming from the engine before the vehicle caught fire.",
]

print("\n--- Example Predictions ---")

for text in examples:
    predicted = nlp_pipeline.predict([text])[0]
    probabilities = nlp_pipeline.predict_proba([text])[0]
    confidence = probabilities.max()

    print("\nDescription:", text)
    print("Prediction:", predicted)
    print("Confidence:", f"{confidence:.2%}")