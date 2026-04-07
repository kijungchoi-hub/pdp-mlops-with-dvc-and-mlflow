import json

import joblib
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, f1_score

from src.common.utils import ensure_dirs


def main() -> None:
    ensure_dirs("reports")

    test_df = pd.read_csv("data/processed/test.csv")
    x_test = test_df.drop(columns=["label"])
    y_test = test_df["label"]

    model = joblib.load("models/model.joblib")
    preds = model.predict(x_test)

    metrics = {
        "test_accuracy": accuracy_score(y_test, preds),
        "test_f1_macro": f1_score(y_test, preds, average="macro"),
        "classification_report": classification_report(y_test, preds, output_dict=True),
    }

    with open("reports/eval.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)


if __name__ == "__main__":
    main()
