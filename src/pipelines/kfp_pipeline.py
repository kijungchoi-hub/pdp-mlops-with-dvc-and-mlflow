from typing import NamedTuple

from kfp import compiler, dsl
from kfp.dsl import Dataset, Input, Metrics, Model, Output


@dsl.component(
    base_image="python:3.11-slim",
    packages_to_install=[
        "joblib",
        "numpy",
        "pandas",
        "pyyaml",
        "scikit-learn",
    ],
)
def prepare_op(
    test_size: float,
    random_state: int,
    train_dataset: Output[Dataset],
    test_dataset: Output[Dataset],
) -> None:
    import pandas as pd
    from sklearn.datasets import load_iris
    from sklearn.model_selection import train_test_split

    iris = load_iris(as_frame=True)
    df = iris.frame.rename(columns={"target": "label"})

    train_df, test_df = train_test_split(
        df,
        test_size=test_size,
        random_state=random_state,
        stratify=df["label"],
    )

    train_df.to_csv(train_dataset.path, index=False)
    test_df.to_csv(test_dataset.path, index=False)


@dsl.component(
    base_image="python:3.11-slim",
    packages_to_install=[
        "joblib",
        "mlflow==2.22.0",
        "numpy",
        "pandas",
        "scikit-learn",
    ],
)
def train_op(
    train_dataset: Input[Dataset],
    random_state: int,
    max_depth: int,
    enable_mlflow: bool,
    mlflow_tracking_uri: str,
    experiment_name: str,
    model_artifact: Output[Model],
    train_metrics: Output[Metrics],
) -> None:
    import joblib
    import mlflow
    import pandas as pd
    from sklearn.metrics import accuracy_score, f1_score
    from sklearn.tree import DecisionTreeClassifier

    train_df = pd.read_csv(train_dataset.path)
    x_train = train_df.drop(columns=["label"])
    y_train = train_df["label"]

    model = DecisionTreeClassifier(
        random_state=random_state,
        max_depth=max_depth,
    )
    model.fit(x_train, y_train)

    preds = model.predict(x_train)
    metrics = {
        "train_accuracy": float(accuracy_score(y_train, preds)),
        "train_f1_macro": float(f1_score(y_train, preds, average="macro")),
    }

    for key, value in metrics.items():
        train_metrics.log_metric(key, value)

    if enable_mlflow:
        mlflow.set_tracking_uri(mlflow_tracking_uri)
        mlflow.set_experiment(experiment_name)
        with mlflow.start_run():
            mlflow.log_params({
                "random_state": random_state,
                "max_depth": max_depth,
            })
            mlflow.log_metrics(metrics)

    joblib.dump(model, model_artifact.path)


@dsl.component(
    base_image="python:3.11-slim",
    packages_to_install=[
        "joblib",
        "numpy",
        "pandas",
        "scikit-learn",
    ],
)
def evaluate_op(
    test_dataset: Input[Dataset],
    model_artifact: Input[Model],
    eval_metrics: Output[Metrics],
) -> NamedTuple("EvaluateOutputs", [("test_accuracy", float), ("test_f1_macro", float)]):
    import joblib
    import pandas as pd
    from sklearn.metrics import accuracy_score, f1_score

    test_df = pd.read_csv(test_dataset.path)
    x_test = test_df.drop(columns=["label"])
    y_test = test_df["label"]

    model = joblib.load(model_artifact.path)
    preds = model.predict(x_test)

    metrics = {
        "test_accuracy": float(accuracy_score(y_test, preds)),
        "test_f1_macro": float(f1_score(y_test, preds, average="macro")),
    }

    for key, value in metrics.items():
        eval_metrics.log_metric(key, value)

    from collections import namedtuple

    outputs = namedtuple("EvaluateOutputs", ["test_accuracy", "test_f1_macro"])
    return outputs(metrics["test_accuracy"], metrics["test_f1_macro"])


@dsl.component(
    base_image="python:3.11-slim",
)
def register_deploy_candidate_op(
    test_accuracy: float,
    threshold_accuracy: float,
    image_repository: str,
    image_tag: str,
    namespace: str,
    release_name: str,
    values_file: str,
    deployment_plan: Output[Dataset],
) -> str:
    import json

    plan = {
        "approved": True,
        "reason": "accuracy_threshold_met",
        "test_accuracy": test_accuracy,
        "threshold_accuracy": threshold_accuracy,
        "image_repository": image_repository,
        "image_tag": image_tag,
        "namespace": namespace,
        "release_name": release_name,
        "values_file": values_file,
        "next_step": "승인된 이미지 값으로 helm upgrade --install 을 실행합니다.",
    }

    with open(deployment_plan.path, "w", encoding="utf-8") as f:
        json.dump(plan, f, indent=2)

    return (
        f"Deployment candidate approved: accuracy={test_accuracy:.4f}, "
        f"threshold={threshold_accuracy:.4f}, release={release_name}"
    )


@dsl.container_component
def helm_deploy_op(
    repo_url: str,
    repo_revision: str,
    chart_path: str,
    release_name: str,
    namespace: str,
    values_file: str,
    image_repository: str,
    image_tag: str,
):
    return dsl.ContainerSpec(
        image="alpine/helm:3.15.4",
        command=[
            "sh",
            "-ec",
            (
                "apk add --no-cache git >/dev/null && "
                "rm -rf /tmp/mlops-repo && "
                "git clone --depth 1 --branch \"$1\" \"$2\" /tmp/mlops-repo && "
                "helm upgrade --install \"$3\" \"/tmp/mlops-repo/$4\" "
                "--namespace \"$5\" --create-namespace "
                "-f \"/tmp/mlops-repo/$6\" "
                "--set image.repository=\"$7\" "
                "--set image.tag=\"$8\""
            ),
        ],
        args=[
            "_",
            repo_revision,
            repo_url,
            release_name,
            chart_path,
            namespace,
            values_file,
            image_repository,
            image_tag,
        ],
    )


@dsl.pipeline(
    name="iris-training-pipeline",
    description="prepare, train, evaluate 단계를 실행하는 Kubeflow Pipelines v2 워크플로입니다.",
)
def iris_training_pipeline(
    test_size: float = 0.2,
    random_state: int = 42,
    max_depth: int = 4,
    enable_mlflow: bool = False,
    mlflow_tracking_uri: str = "http://mlflow-server.mlops.svc.cluster.local:5000",
    experiment_name: str = "iris-kfp",
    enable_deploy_candidate: bool = False,
    threshold_accuracy: float = 0.90,
    image_repository: str = "ghcr.io/your-org/mlops-api",
    image_tag: str = "stable",
    namespace: str = "mlops",
    release_name: str = "mlops-serving",
    values_file: str = "infra/helm/mlops-serving/values-prod.yaml",
    enable_helm_deploy: bool = False,
    repo_url: str = "https://github.com/REPLACE_WITH_OWNER/REPLACE_WITH_REPO.git",
    repo_revision: str = "main",
    chart_path: str = "infra/helm/mlops-serving",
):
    prepare_task = prepare_op(
        test_size=test_size,
        random_state=random_state,
    )

    train_task = train_op(
        train_dataset=prepare_task.outputs["train_dataset"],
        random_state=random_state,
        max_depth=max_depth,
        enable_mlflow=enable_mlflow,
        mlflow_tracking_uri=mlflow_tracking_uri,
        experiment_name=experiment_name,
    )

    eval_task = evaluate_op(
        test_dataset=prepare_task.outputs["test_dataset"],
        model_artifact=train_task.outputs["model_artifact"],
    )

    with dsl.If(enable_deploy_candidate == True):
        with dsl.If(eval_task.outputs["test_accuracy"] >= threshold_accuracy):
            register_task = register_deploy_candidate_op(
                test_accuracy=eval_task.outputs["test_accuracy"],
                threshold_accuracy=threshold_accuracy,
                image_repository=image_repository,
                image_tag=image_tag,
                namespace=namespace,
                release_name=release_name,
                values_file=values_file,
            )

            with dsl.If(enable_helm_deploy == True):
                helm_deploy_op(
                    repo_url=repo_url,
                    repo_revision=repo_revision,
                    chart_path=chart_path,
                    release_name=release_name,
                    namespace=namespace,
                    values_file=values_file,
                    image_repository=image_repository,
                    image_tag=image_tag,
                ).after(register_task)


def compile_pipeline(output_path: str = "infra/kubeflow/pipelines/iris-training-pipeline.yaml") -> None:
    compiler.Compiler().compile(
        pipeline_func=iris_training_pipeline,
        package_path=output_path,
    )


if __name__ == "__main__":
    compile_pipeline()
