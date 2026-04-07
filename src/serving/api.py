from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

from src.common.utils import get_env

CLASS_NAMES = {
    0: "setosa",
    1: "versicolor",
    2: "virginica",
}
FEATURE_COLUMNS = [
    "sepal length (cm)",
    "sepal width (cm)",
    "petal length (cm)",
    "petal width (cm)",
]


class IrisRequest(BaseModel):
    sepal_length: float = Field(..., gt=0)
    sepal_width: float = Field(..., gt=0)
    petal_length: float = Field(..., gt=0)
    petal_width: float = Field(..., gt=0)


def get_model_path() -> Path:
    return Path(get_env("MODEL_PATH", "models/model.joblib"))


def load_model() -> Any:
    model_path = get_model_path()
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    return joblib.load(model_path)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.model = None
    app.state.model_path = str(get_model_path())
    app.state.model_error = None

    try:
        app.state.model = load_model()
    except Exception as exc:  # pragma: no cover - surfaced via health/predict
        app.state.model_error = str(exc)

    yield


app = FastAPI(
    title="MLOps Inference API",
    description="FastAPI service for serving the trained Iris classifier.",
    version="1.0.0",
    lifespan=lifespan,
)


def get_loaded_model(request: Request) -> Any:
    model = request.app.state.model
    if model is None:
        detail = request.app.state.model_error or "Model is not loaded."
        raise HTTPException(status_code=503, detail=detail)
    return model


def get_class_name(prediction: int) -> str:
    return CLASS_NAMES.get(prediction, f"class_{prediction}")


@app.get("/")
def read_root() -> dict[str, str]:
    return {
        "service": "mlops-inference-api",
        "docs": "/docs",
        "health": "/health",
        "predict": "/predict",
    }


@app.get("/health")
def health(request: Request) -> dict[str, Any]:
    return {
        "status": "ok" if request.app.state.model is not None else "degraded",
        "model_loaded": request.app.state.model is not None,
        "model_path": request.app.state.model_path,
        "detail": request.app.state.model_error,
    }


@app.post("/predict")
def predict(payload: IrisRequest, request: Request) -> dict[str, Any]:
    model = get_loaded_model(request)
    features = pd.DataFrame([{
        "sepal length (cm)": payload.sepal_length,
        "sepal width (cm)": payload.sepal_width,
        "petal length (cm)": payload.petal_length,
        "petal width (cm)": payload.petal_width,
    }], columns=FEATURE_COLUMNS)
    prediction = int(model.predict(features)[0])

    response: dict[str, Any] = {
        "prediction": prediction,
        "class_name": get_class_name(prediction),
    }

    if hasattr(model, "predict_proba"):
        probabilities = model.predict_proba(features)[0]
        response["probabilities"] = {
            get_class_name(int(class_id)): float(probability)
            for class_id, probability in zip(model.classes_, probabilities)
        }

    return response
