import json
from pathlib import Path

import joblib
import mlflow
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score
from sklearn.tree import DecisionTreeClassifier

from src.utils import ensure_dirs, get_env, load_params


def main() -> None:
    all_params = load_params()
    params = all_params["train"]
    experiment_name = all_params["mlflow"]["experiment_name"]
    ensure_dirs("models", "reports", "mlruns")

    train_df = pd.read_csv("data/processed/train.csv")
    x_train = train_df.drop(columns=["label"])
    y_train = train_df["label"]

    mlflow.set_tracking_uri(get_env("MLFLOW_TRACKING_URI", "file:./mlruns"))
    mlflow.set_experiment(experiment_name)

    with mlflow.start_run():
        model = DecisionTreeClassifier(
            random_state=params["random_state"],
            max_depth=params["max_depth"],
        )
        model.fit(x_train, y_train)

        preds = model.predict(x_train)
        metrics = {
            "train_accuracy": accuracy_score(y_train, preds),
            "train_f1_macro": f1_score(y_train, preds, average="macro"),
        }

        mlflow.log_params(params)
        mlflow.log_metrics(metrics)

        model_path = Path("models/model.joblib")
        joblib.dump(model, model_path)
        mlflow.log_artifact(str(model_path))

        with open("reports/metrics.json", "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)


if __name__ == "__main__":
    main()
