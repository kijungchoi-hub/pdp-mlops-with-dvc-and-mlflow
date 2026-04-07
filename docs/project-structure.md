# Project Structure

This repository uses a concise MLOps-oriented layout.

## Top-Level Layout

- `configs/`: pipeline and runtime configuration
- `data/`: pipeline datasets and processed outputs
- `docs/`: project documentation
- `infra/`: Docker and Kubernetes deployment assets
- `models/`: trained model artifacts
- `mlruns/`: local MLflow tracking data
- `reports/`: training and evaluation reports
- `scripts/`: local operational scripts
- `src/`: application code

## Source Layout

- `src/common/`: shared utilities
- `src/pipelines/`: data prep, training, evaluation entrypoints
- `src/serving/`: FastAPI inference service

## Infrastructure Layout

- `infra/helm/mlops-serving/`: Helm chart for model serving
- `infra/helm/mlops-serving/values-dev.yaml`: development Helm values
- `infra/helm/mlops-serving/values-staging.yaml`: staging Helm values
- `infra/helm/mlops-serving/values-prod.yaml`: production-oriented Helm values
- `infra/docker/api.Dockerfile`: API image build
- `infra/docker/mlflow.Dockerfile`: MLflow image build
- `infra/k8s/`: Kubernetes manifests
- `infra/k8s/model-serving-inferenceservice.yaml`: KServe custom resource for model serving

## Key Documents

- `docs/mlops-architecture-and-helm-deployment.md`: MLOps architecture and Helm deployment order
- `docs/operations-checklist.md`: deployment and runtime operations checklist
- `docs/incident-response-runbook.md`: incident diagnosis, recovery, and rollback guide
- `docs/cicd-deployment-guide.md`: GitHub Actions and Helm-based deployment guide
