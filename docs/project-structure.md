# 프로젝트 구조
## 관련 파일

- [저장소 개요](../README.md)
- [Argo CD 자산](../infra/argocd/)
- [Helm 차트](../infra/helm/mlops-serving/Chart.yaml)
- [Kubernetes 매니페스트](../infra/k8s/)

이 저장소는 간결한 MLOps 중심 구조를 사용합니다.

## 최상위 구조

- `configs/`: 파이프라인 및 실행 설정
- `data/`: 파이프라인 데이터셋과 처리 결과
- `docs/`: 프로젝트 문서
- `infra/`: Docker, Kubernetes, Helm 배포 자산
- `models/`: 학습된 모델 아티팩트
- `mlruns/`: 로컬 MLflow 추적 데이터
- `reports/`: 학습 및 평가 리포트
- `scripts/`: 로컬 운영 스크립트
- `src/`: 애플리케이션 코드

## 소스 구조

- `src/common/`: 공통 유틸리티
- `src/pipelines/`: 데이터 준비, 학습, 평가, KFP 진입점
- `src/serving/`: FastAPI 추론 서비스

## 인프라 구조

- `infra/helm/mlops-serving/`: 모델 서빙용 Helm 차트
- `infra/helm/mlops-serving/values-dev.yaml`: 개발 환경용 Helm 값
- `infra/helm/mlops-serving/values-staging.yaml`: 스테이징 환경용 Helm 값
- `infra/helm/mlops-serving/values-prod.yaml`: 운영 환경용 Helm 값
- `infra/argocd/`: Argo CD 프로젝트, 루트 앱, 환경별 애플리케이션
- `infra/docker/api.Dockerfile`: API 이미지 빌드 정의
- `infra/docker/mlflow.Dockerfile`: MLflow 이미지 빌드 정의
- `infra/k8s/`: Kubernetes 매니페스트
- `infra/k8s/model-serving-inferenceservice.yaml`: 모델 서빙용 KServe 커스텀 리소스
- `infra/kubeflow/`: Kubeflow Pipelines 파이프라인 및 standalone 설치 자산
- `infra/monitoring/`: Prometheus, Grafana 모니터링 설정

## 주요 문서

- `docs/mlops-architecture-and-helm-deployment.md`: MLOps 아키텍처와 Helm 배포 순서
- `docs/operations-checklist.md`: 배포 및 운영 체크리스트
- `docs/incident-response-runbook.md`: 장애 진단, 복구, 롤백 가이드
- `docs/cicd-deployment-guide.md`: GitHub Actions 및 Helm 기반 배포 가이드
- `docs/argocd-deployment-guide.md`: Argo CD app-of-apps 및 환경별 배포 가이드
- `docs/kubeflow-pipelines-guide.md`: Kubeflow Pipelines 구성 및 실행 가이드
