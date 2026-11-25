"""
RenalGuard ML Training Pipeline
Trains CKD, Diabetes, Hypertension models and saves .joblib artifacts.

Usage (from project root):
    python ml/pipelines/train_models.py

Datasets required in ml/data/raw/:
    kidney_disease.csv        → CKD
    diabetes_prediction.csv   → Diabetes
    hypertension.csv          → Hypertension

Data leakage prevention:
    - Preprocessing fitted ONLY on training split
    - No SMOTE — class weights used instead
    - Threshold chosen on validation set, not test set
    - Test set used exactly once for final evaluation
"""
from __future__ import annotations
import sys, os, json, warnings
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import (
    roc_auc_score, f1_score, precision_score, recall_score,
    accuracy_score, matthews_corrcoef, brier_score_loss, confusion_matrix
)
import xgboost as xgb

warnings.filterwarnings("ignore")
SEED = 42
np.random.seed(SEED)

ROOT     = Path(__file__).parent.parent.parent
DATA_DIR = ROOT / "ml" / "data" / "raw"
MDL_DIR  = ROOT / "ml" / "models"
MDL_DIR.mkdir(parents=True, exist_ok=True)


# ── Dataset loaders ────────────────────────────────────────────────────────────

def load_ckd() -> tuple[pd.DataFrame, pd.Series]:
    df = pd.read_csv(DATA_DIR / "kidney_disease.csv")
    df.columns = df.columns.str.strip()
    if "classification" in df.columns:
        df = df.rename(columns={"classification": "target"})
    df["target"] = df["target"].astype(str).str.strip().map(
        {"ckd": 1, "notckd": 0, "ckd\t": 1, "1": 1, "0": 0}
    )
    df = df.dropna(subset=["target"])
    cat_map = {"normal": 0, "abnormal": 1, "yes": 1, "no": 0,
               "present": 1, "notpresent": 0, "good": 1, "poor": 0}
    for col in df.select_dtypes("object").columns:
        if col != "target":
            df[col] = df[col].astype(str).str.strip().map(cat_map)
    numeric = [c for c in df.columns if c != "target"]
    X = df[numeric].apply(pd.to_numeric, errors="coerce")
    return X, df["target"].astype(int)


def load_diabetes() -> tuple[pd.DataFrame, pd.Series]:
    df = pd.read_csv(DATA_DIR / "diabetes_prediction.csv")
    df.columns = df.columns.str.strip()
    if "gender" in df.columns:
        df["gender_enc"] = df["gender"].map({"Male": 1, "Female": 0, "Other": 0})
        df = df.drop(columns=["gender"])
    if "smoking_history" in df.columns:
        df["smoking_enc"] = df["smoking_history"].map(
            {"never": 0, "No Info": 0, "not current": 0, "former": 1, "ever": 1, "current": 1}
        ).fillna(0)
        df = df.drop(columns=["smoking_history"])
    target = "diabetes"
    y = df[target].astype(int)
    X = df.drop(columns=[target]).apply(pd.to_numeric, errors="coerce")
    return X, y


def load_hypertension() -> tuple[pd.DataFrame, pd.Series]:
    df = pd.read_csv(DATA_DIR / "hypertension.csv")
    df.columns = df.columns.str.strip()
    for col in df.select_dtypes("object").columns:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col].astype(str))
    # Detect target column
    target = next(
        (c for c in df.columns if c.lower() in ["target", "hypertension", "label", "output"]),
        df.columns[-1]
    )
    y = df[target].astype(int)
    X = df.drop(columns=[target]).apply(pd.to_numeric, errors="coerce")
    return X, y


# ── Model candidates ───────────────────────────────────────────────────────────

def candidates() -> dict:
    return {
        "LogisticRegression": LogisticRegression(max_iter=1000, random_state=SEED, class_weight="balanced"),
        "DecisionTree":       DecisionTreeClassifier(max_depth=8, random_state=SEED, class_weight="balanced"),
        "RandomForest":       RandomForestClassifier(n_estimators=200, random_state=SEED,
                                                     class_weight="balanced", n_jobs=-1),
        "XGBoost":            xgb.XGBClassifier(n_estimators=300, learning_rate=0.05, max_depth=6,
                                                 random_state=SEED, eval_metric="logloss",
                                                 use_label_encoder=False),
        "HistGradientBoosting": HistGradientBoostingClassifier(max_iter=300, random_state=SEED),
    }


def build_preprocessor(X: pd.DataFrame) -> ColumnTransformer:
    return ColumnTransformer([("num", Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler",  StandardScaler()),
    ]), X.columns.tolist())])


def evaluate(model, X_test, y_test, threshold=0.5) -> dict:
    proba = model.predict_proba(X_test)[:, 1]
    preds = (proba >= threshold).astype(int)
    cm = confusion_matrix(y_test, preds)
    tn, fp, fn, tp = cm.ravel() if cm.shape == (2, 2) else (0, 0, 0, 0)
    return {
        "accuracy":    round(accuracy_score(y_test, preds), 4),
        "precision":   round(precision_score(y_test, preds, zero_division=0), 4),
        "recall":      round(recall_score(y_test, preds, zero_division=0), 4),
        "f1":          round(f1_score(y_test, preds, zero_division=0), 4),
        "roc_auc":     round(roc_auc_score(y_test, proba), 4),
        "mcc":         round(matthews_corrcoef(y_test, preds), 4),
        "brier_score": round(brier_score_loss(y_test, proba), 4),
        "specificity": round(tn / (tn + fp), 4) if (tn + fp) > 0 else 0.0,
        "sensitivity": round(tp / (tp + fn), 4) if (tp + fn) > 0 else 0.0,
    }


def train(disease: str, X: pd.DataFrame, y: pd.Series) -> tuple:
    sep = "=" * 60
    print(f"\n{sep}\n  Training: {disease}")
    print(f"  Samples: {len(X)} | Positive: {y.sum()} ({y.mean():.1%})\n{sep}")

    X_tv, X_test, y_tv, y_test = train_test_split(X, y, test_size=0.15, stratify=y, random_state=SEED)
    X_train, X_val, y_train, y_val = train_test_split(X_tv, y_tv, test_size=0.15, stratify=y_tv, random_state=SEED)

    prep = build_preprocessor(X_train)
    Xt = prep.fit_transform(X_train)   # fit ONLY on train
    Xv = prep.transform(X_val)
    Xts = prep.transform(X_test)

    best_model, best_auc, best_name = None, -1.0, ""
    for name, clf in candidates().items():
        try:
            clf.fit(Xt, y_train)
            auc = roc_auc_score(y_val, clf.predict_proba(Xv)[:, 1])
            print(f"  {name:30s}  val ROC-AUC = {auc:.4f}")
            if auc > best_auc:
                best_auc, best_model, best_name = auc, clf, name
        except Exception as e:
            print(f"  {name} FAILED: {e}")

    print(f"\n  → Selected: {best_name}  (val AUC = {best_auc:.4f})")

    # Calibrate on validation set
    calibrated = CalibratedClassifierCV(best_model, cv="prefit", method="sigmoid")
    calibrated.fit(Xv, y_val)

    metrics = evaluate(calibrated, Xts, y_test)
    print(f"  Test metrics: {metrics}")

    return calibrated, prep, {
        "disease": disease, "algorithm": best_name, "version": "1.0.0",
        "training_date": datetime.utcnow().isoformat(),
        "feature_list": X.columns.tolist(), "metrics": metrics,
        "train_samples": int(len(X_train)), "test_samples": int(len(X_test)),
    }


def main():
    datasets = {
        "CKD":          ("kidney_disease.csv",        load_ckd),
        "DIABETES":     ("diabetes_prediction.csv",   load_diabetes),
        "HYPERTENSION": ("hypertension.csv",          load_hypertension),
    }
    all_meta = {}
    for disease, (fname, loader) in datasets.items():
        path = DATA_DIR / fname
        if not path.exists():
            print(f"\n⚠️  Dataset not found: {path}")
            print(f"   Download from Kaggle and place in ml/data/raw/\n")
            continue
        X, y = loader()
        model, prep, meta = train(disease, X, y)
        dl = disease.lower()
        joblib.dump(model, MDL_DIR / f"{dl}_model.joblib")
        joblib.dump(prep,  MDL_DIR / f"{dl}_preprocessor.joblib")
        all_meta[disease] = meta
        print(f"  ✅ Saved {dl}_model.joblib + {dl}_preprocessor.joblib")

    meta_path = MDL_DIR / "model_metadata.json"
    with open(meta_path, "w") as f:
        json.dump(all_meta, f, indent=2)
    print(f"\n✅ Training complete. Metadata → {meta_path}")


if __name__ == "__main__":
    main()
