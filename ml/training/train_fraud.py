"""Train fraud-detection models and track experiments with MLflow."""

from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import mlflow
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    classification_report,
    confusion_matrix,
    ConfusionMatrixDisplay,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from xgboost import XGBClassifier



# Paths


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_PATH = PROJECT_ROOT / "ml" / "data" / "insurance_claims.csv"
ARTIFACT_DIR = PROJECT_ROOT / "ml" / "artifacts"
MLRUNS_DIR = PROJECT_ROOT / "ml" / "mlruns"
MLFLOW_ARTIFACT_DIR = ARTIFACT_DIR / "mlflow"

ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
MLRUNS_DIR.mkdir(parents=True, exist_ok=True)
MLFLOW_ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)



# MLflow configuration


MLFLOW_DB = PROJECT_ROOT / "ml" / "mlflow.db"

mlflow.set_tracking_uri(
    f"sqlite:///{MLFLOW_DB.as_posix()}"
)

EXPERIMENT_NAME = "insurance-fraud-detection"

mlflow.set_experiment(EXPERIMENT_NAME)



# Configuration








TEST_SIZE = 0.20
RANDOM_STATE = 42

# Optimized XGBoost classification threshold
# XGB_THRESHOLD = 0.25
XGB_THRESHOLD = 0.45



# Features available to our application


MODEL_FEATURES = [
    "months_as_customer",
    "age",
    "policy_state",
    "policy_csl",
    "policy_deductable",
    "policy_annual_premium",
    "umbrella_limit",
    "insured_sex",
    "insured_education_level",
    "insured_occupation",
    "insured_hobbies",
    "insured_relationship",

    "incident_type",
    "collision_type",
    "incident_severity",
    "authorities_contacted",
    "incident_state",
    "incident_city",
    "incident_hour_of_the_day",
    "number_of_vehicles_involved",
    "property_damage",
    "bodily_injuries",
    "witnesses",
    "police_report_available",
    "total_claim_amount",

    "auto_make",
    "auto_model",
    "auto_year",

    "incident_month",
    "incident_day_of_week",
]

TARGET = "fraud_reported"



# Helper: preprocessing



# this is for  Create a fresh preprocessor for each model.This keeps the Random Forest and XGBoost pipelines independent.
def create_preprocessor(categorical_features, numeric_features):
    return ColumnTransformer(
        transformers=[
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore"),
                categorical_features,
            ),
            (
                "numeric",
                "passthrough",
                numeric_features,
            ),
        ]
    )



# Helper: evaluation


def evaluate_model(
    model_name,
    pipeline,
    X_test,
    y_test,
    artifact_filename,
    threshold=0.5,
):
    # Always obtain probability first
    probabilities = pipeline.predict_proba(X_test)[:, 1]

    # Apply model-specific classification threshold
    predictions = (
        probabilities >= threshold
    ).astype(int)

   
    # Metrics
    

    accuracy = accuracy_score(
        y_test,
        predictions,
    )

    fraud_precision = precision_score(
        y_test,
        predictions,
        pos_label=1,
        zero_division=0,
    )

    fraud_recall = recall_score(
        y_test,
        predictions,
        pos_label=1,
        zero_division=0,
    )

    fraud_f1 = f1_score(
        y_test,
        predictions,
        pos_label=1,
        zero_division=0,
    )

    roc_auc = roc_auc_score(
        y_test,
        probabilities,
    )

    pr_auc = average_precision_score(
        y_test,
        probabilities,
    )

    cm = confusion_matrix(
        y_test,
        predictions,
        labels=[0, 1],
    )

    tn, fp, fn, tp = cm.ravel()

   
    # Terminal output
    

    print(f"\n--- {model_name} ---")

    print(
        classification_report(
            y_test,
            predictions,
            zero_division=0,
        )
    )

    print("Confusion Matrix:")
    print(cm)

    print("Classification threshold:", threshold)
    print("Accuracy:", accuracy)
    print("Fraud Precision:", fraud_precision)
    print("Fraud Recall:", fraud_recall)
    print("Fraud F1:", fraud_f1)
    print("ROC-AUC:", roc_auc)
    print("PR-AUC:", pr_auc)

    
    # MLflow metrics
    

    mlflow.log_metrics(
        {
            "accuracy": float(accuracy),
            "fraud_precision": float(fraud_precision),
            "fraud_recall": float(fraud_recall),
            "fraud_f1": float(fraud_f1),
            "roc_auc": float(roc_auc),
            "pr_auc": float(pr_auc),

            "true_negatives": int(tn),
            "false_positives": int(fp),
            "false_negatives": int(fn),
            "true_positives": int(tp),
        }
    )

    
    # Classification report artifact
    

    report = classification_report(
        y_test,
        predictions,
        zero_division=0,
    )

    report_path = (
        MLFLOW_ARTIFACT_DIR
        / f"{model_name}_classification_report.txt"
    )

    report_path.write_text(
        report,
        encoding="utf-8",
    )

    mlflow.log_artifact(
        str(report_path),
        artifact_path="evaluation",
    )

    
    # Confusion matrix artifact
    

    display = ConfusionMatrixDisplay(
        confusion_matrix=cm,
        display_labels=["Not Fraud", "Fraud"],
    )

    display.plot()

    plt.title(
        f"{model_name.replace('_', ' ').title()} Confusion Matrix"
    )

    confusion_matrix_path = (
        MLFLOW_ARTIFACT_DIR
        / f"{model_name}_confusion_matrix.png"
    )

    plt.savefig(
        confusion_matrix_path,
        bbox_inches="tight",
    )

    plt.close()

    mlflow.log_artifact(
        str(confusion_matrix_path),
        artifact_path="evaluation",
    )

    
    # Save pipeline
    

    model_path = ARTIFACT_DIR / artifact_filename

    joblib.dump(
        pipeline,
        model_path,
    )

    mlflow.log_artifact(
        str(model_path),
        artifact_path="model",
    )

    print(f"Saved model: {model_path}")



# Load data


print(f"Loading dataset: {DATA_PATH}")

df = pd.read_csv(DATA_PATH)

df = df.drop(
    columns=["_c39"],
    errors="ignore",
)

df = df.replace(
    "?",
    pd.NA,
)



# Missing categorical values


missing_categorical = [
    "collision_type",
    "authorities_contacted",
    "property_damage",
    "police_report_available",
]

df[missing_categorical] = (
    df[missing_categorical]
    .fillna("Unknown")
)



# Date feature engineering


df["incident_date"] = pd.to_datetime(
    df["incident_date"]
)

df["incident_month"] = (
    df["incident_date"].dt.month
)

df["incident_day_of_week"] = (
    df["incident_date"].dt.dayofweek
)



# X and y


X = df[MODEL_FEATURES].copy()

y = df[TARGET].map(
    {
        "N": 0,
        "Y": 1,
    }
)



# Dataset information


print("\nDataset size:", len(df))

print("Fraud distribution:")
print(y.value_counts())

print("\nFraud percentage:")
print(y.value_counts(normalize=True))



# Train/test split


X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=TEST_SIZE,
    random_state=RANDOM_STATE,
    stratify=y,
)



# Identify feature types


categorical_features = (
    X_train
    .select_dtypes(
        include=["object", "category"]
    )
    .columns
    .tolist()
)

numeric_features = (
    X_train
    .select_dtypes(
        include=["number"]
    )
    .columns
    .tolist()
)


print(
    "\nCategorical features:",
    categorical_features,
)

print(
    "\nNumeric features:",
    numeric_features,
)


# RANDOM FOREST


rf_preprocessor = create_preprocessor(
    categorical_features,
    numeric_features,
)

rf_pipeline = Pipeline(
    steps=[
        (
            "preprocessor",
            rf_preprocessor,
        ),
        (
            "classifier",
            RandomForestClassifier(
    n_estimators=300,
    max_depth=10,
    min_samples_split=4,
    min_samples_leaf=2,
    max_features="sqrt",
    class_weight="balanced",
    random_state=RANDOM_STATE,
    n_jobs=-1,
),
        ),
    ]
)








print("\n========================================")
print("Training Random Forest...")
print("========================================")


with mlflow.start_run(
    run_name="random_forest_baseline"
):

    mlflow.set_tag(
        "model_family",
        "RandomForest",
    )

    mlflow.set_tag(
        "task",
        "insurance_fraud_detection",
    )

    mlflow.log_params(
        {
            "model": "RandomForestClassifier",
            "n_estimators": 300,
            "class_weight": "balanced",
            "classification_threshold": 0.5,
            "test_size": TEST_SIZE,
            "random_state": RANDOM_STATE,
            "training_rows": len(X_train),
            "test_rows": len(X_test),
            "feature_count": len(MODEL_FEATURES),
        }
    )

    rf_pipeline.fit(
        X_train,
        y_train,
    )

    evaluate_model(
        model_name="random_forest",
        pipeline=rf_pipeline,
        X_test=X_test,
        y_test=y_test,
        artifact_filename="random_forest_fraud_pipeline.joblib",
        threshold=0.5,
    )



# XGBOOST


negative = int(
    (y_train == 0).sum()
)

positive = int(
    (y_train == 1).sum()
)

scale_pos_weight = (
    negative / positive
)

# Tuned imbalance weight
# Reduce imbalance weight by 25% to avoid over-predicting the fraud class.
optimized_scale_pos_weight = (
    scale_pos_weight * 0.75
)


print("\nXGBoost class information:")
print("Negative training samples:", negative)
print("Positive training samples:", positive)
print("Original scale_pos_weight:", scale_pos_weight)
print(
    "Optimized scale_pos_weight:",
    optimized_scale_pos_weight,
)


xgb_preprocessor = create_preprocessor(
    categorical_features,
    numeric_features,
)


xgb_pipeline = Pipeline(
    steps=[
        (
            "preprocessor",
            xgb_preprocessor,
        ),
        (
            "classifier",
            XGBClassifier(
    objective="binary:logistic",

    n_estimators=500,
    max_depth=4,
    learning_rate=0.04,

    subsample=0.8,
    colsample_bytree=0.6,

    min_child_weight=1,
    gamma=0.05,

    reg_alpha=0.5,
    reg_lambda=2.0,

    scale_pos_weight=optimized_scale_pos_weight,

    eval_metric="logloss",
    random_state=RANDOM_STATE,
    n_jobs=-1,
),
        ),
    ]
)







print("\n========================================")
print("Training Optimized XGBoost...")
print("========================================")


with mlflow.start_run(
    run_name="xgboost_optimized"
):

    mlflow.set_tag(
        "model_family",
        "XGBoost",
    )

    mlflow.set_tag(
        "task",
        "insurance_fraud_detection",
    )

    mlflow.set_tag(
        "model_version",
        "optimized",
    )

    mlflow.log_params(
        {
            "model": "XGBClassifier",

            "objective": "binary:logistic",

            "n_estimators": 500,
            "max_depth": 3,
            "learning_rate": 0.03,

            "subsample": 0.8,
            "colsample_bytree": 0.6,

            "min_child_weight": 1,
            "gamma": 0.05,

            "reg_alpha": 0.5,
            "reg_lambda": 2.0,

            "scale_pos_weight": float(
                optimized_scale_pos_weight
            ),

            "classification_threshold": XGB_THRESHOLD,

            "eval_metric": "logloss",

            "test_size": TEST_SIZE,
            "random_state": RANDOM_STATE,

            "training_rows": len(X_train),
            "test_rows": len(X_test),

            "feature_count": len(MODEL_FEATURES),
        }
    )

    xgb_pipeline.fit(
        X_train,
        y_train,
    )

    evaluate_model(
        model_name="xgboost",
        pipeline=xgb_pipeline,
        X_test=X_test,
        y_test=y_test,
        artifact_filename="xgboost_fraud_pipeline.joblib",
        threshold=XGB_THRESHOLD,
    )



# Complete


print("\n========================================")
print("Training complete")
print("========================================")

print("\nModels saved to:")
print(ARTIFACT_DIR)

print("\nMLflow experiment:")
print(EXPERIMENT_NAME)

print("\nMLflow tracking database:")
print(MLFLOW_DB)

print(
    "\nStart the MLflow UI with:\n"
    f'mlflow ui --backend-store-uri '
    f'"sqlite:///{MLFLOW_DB.as_posix()}" '
    f'--port 5000'
)

print(
    "\nThen open:\n"
    "http://127.0.0.1:5000"
)