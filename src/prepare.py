from pathlib import Path

import pandas as pd
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split

from src.utils import ensure_dirs, load_params


def main() -> None:
    params = load_params()["train"]
    ensure_dirs("data/processed")

    iris = load_iris(as_frame=True)
    df = iris.frame.rename(columns={"target": "label"})

    train_df, test_df = train_test_split(
        df,
        test_size=params["test_size"],
        random_state=params["random_state"],
        stratify=df["label"],
    )

    train_df.to_csv(Path("data/processed/train.csv"), index=False)
    test_df.to_csv(Path("data/processed/test.csv"), index=False)


if __name__ == "__main__":
    main()

