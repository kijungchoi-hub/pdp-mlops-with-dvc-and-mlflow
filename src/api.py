from pathlib import Path

import joblib
from fastapi import FastAPI
from fastapi import HTTPException
from pydantic import BaseModel


class IrisRequest(BaseModel):
    sepal_length: float
    sepal_width: float
    petal_length: float
    petal_width: float


app = FastAPI(title="MLOps Inference API")


def load_model():
    model_path = Path("models/model.joblib")
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    return joblib.load(model_path)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/predict")
def predict(payload: IrisRequest) -> dict[str, int]:
    try:
        model = load_model()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    features = [[
        payload.sepal_length,
        payload.sepal_width,
        payload.petal_length,
        payload.petal_width,
    ]]
    prediction = int(model.predict(features)[0])
    return {"prediction": prediction}
