from fastapi.testclient import TestClient

from src.serving.api import app


def test_ready_and_predict_with_default_model() -> None:
    with TestClient(app) as client:
        ready_response = client.get("/ready")
        assert ready_response.status_code == 200
        assert ready_response.json()["model_loaded"] is True

        predict_response = client.post(
            "/predict",
            json={
                "sepal_length": 5.1,
                "sepal_width": 3.5,
                "petal_length": 1.4,
                "petal_width": 0.2,
            },
        )

    assert predict_response.status_code == 200
    body = predict_response.json()
    assert body["prediction"] == 0
    assert body["class_name"] == "setosa"
    assert "probabilities" in body


def test_readiness_fails_when_model_is_missing(monkeypatch) -> None:
    monkeypatch.setenv("MODEL_PATH", "models/does-not-exist.joblib")

    with TestClient(app) as client:
        live_response = client.get("/live")
        ready_response = client.get("/ready")
        health_response = client.get("/health")

    assert live_response.status_code == 200
    assert ready_response.status_code == 503
    assert health_response.status_code == 200
    assert health_response.json()["status"] == "degraded"
