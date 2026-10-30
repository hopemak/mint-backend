import json, os, pickle, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODEL_DIR = Path(os.getenv("MODEL_DIR", ROOT / "company_models"))
LOGREG_PATH = MODEL_DIR / "logreg.pkl"
_bundle = None


def feature_names():
    data = json.loads((MODEL_DIR / "feature_names.json").read_text())
    if isinstance(data, dict):
        data = data.get("features") or data.get("feature_names")
    return list(data)


def train(csv_path, label_col="success"):
    import pandas as pd
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, recall_score, roc_auc_score

    names = feature_names()
    df = pd.read_csv(csv_path)
    missing = [c for c in names + [label_col] if c not in df.columns]
    if missing:
        raise SystemExit(f"CSV is missing columns: {missing}")
    X = df[names].astype(float).values
    y = df[label_col].astype(int).values
    Xtr, Xte, ytr, yte = train_test_split(
        X, y, test_size=0.25, stratify=y, random_state=42)
    model = make_pipeline(
        StandardScaler(),
        LogisticRegression(penalty="l2", C=1.0, class_weight="balanced", max_iter=1000))
    model.fit(Xtr, ytr)
    p = model.predict_proba(Xte)[:, 1]
    pred = (p >= 0.5).astype(int)
    metrics = {"accuracy": float(accuracy_score(yte, pred)),
               "recall": float(recall_score(yte, pred)),
               "auc": float(roc_auc_score(yte, p)),
               "n_train": int(len(ytr)), "n_test": int(len(yte))}
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOGREG_PATH, "wb") as f:
        pickle.dump({"model": model, "features": names, "metrics": metrics}, f)
    print("saved", LOGREG_PATH, metrics)


def _load():
    global _bundle
    if _bundle is None and LOGREG_PATH.exists():
        with open(LOGREG_PATH, "rb") as f:
            _bundle = pickle.load(f)
    return _bundle


def predict(values):
    b = _load()
    if b is None:
        return None
    missing = [n for n in b["features"] if values.get(n) in (None, "")]
    row = [[float(values.get(n) or 0) for n in b["features"]]]
    p = float(b["model"].predict_proba(row)[0][1])
    return {"model": "logistic_regression", "probability": round(p, 3),
            "missing_features": missing, "metrics": b["metrics"]}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("usage: python -m app.ml.success_logistic labelled.csv")
    train(sys.argv[1])
