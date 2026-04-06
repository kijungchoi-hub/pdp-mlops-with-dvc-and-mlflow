# MLOps with Git, DVC, MLflow, and Kubernetes

`Git + DVC + MLflow + Kubernetes`를 연결한 최소 실행형 MLOps 템플릿입니다. 로컬에서는 Docker Compose로 MLflow, PostgreSQL, MinIO를 올리고, 학습 파이프라인은 DVC로 재현하며, 배포는 Kubernetes와 GitHub Actions를 기준으로 구성합니다.

## Stack

- `Git`: 코드 변경 이력 관리
- `DVC`: 데이터, 모델, 파이프라인 버전 관리
- `MLflow`: 실험 추적 서버와 모델 아티팩트 관리
- `MinIO`: S3 호환 artifact store, DVC remote 저장소
- `PostgreSQL`: MLflow backend store
- `Kubernetes`: MLflow 및 추론 API 배포
- `GitHub Actions`: CI/CD 자동화

## Repository Layout

- `src/prepare.py`: Iris 데이터를 학습/평가 데이터셋으로 분리
- `src/train.py`: 모델 학습, MLflow 로깅, 모델 저장
- `src/evaluate.py`: 평가 결과 리포트 생성
- `src/api.py`: FastAPI 기반 추론 API
- `dvc.yaml`: 데이터 준비, 학습, 평가 파이프라인
- `docker-compose.yml`: 로컬 MLflow, PostgreSQL, MinIO 실행
- `k8s/mlflow-stack.yaml`: K8s용 MLflow, PostgreSQL, MinIO 배포
- `k8s/api-deployment.yaml`: 추론 API 배포
- `.github/workflows/ci-cd.yaml`: CI/CD 워크플로
- `scripts/bootstrap.ps1`: 로컬 초기 설정
- `scripts/configure_dvc_remote.ps1`: DVC remote 설정
- `scripts/run_pipeline.ps1`: `.env` 로드 후 DVC 파이프라인 실행

## 1. Local Bootstrap

Windows PowerShell 기준:

```powershell
.\scripts\bootstrap.ps1
Copy-Item .env.example .env
docker compose up -d
.\scripts\configure_dvc_remote.ps1
.\scripts\run_pipeline.ps1
```

수동으로 실행하면 다음 순서입니다.

```powershell
git init
dvc init
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
docker compose up -d
dvc remote add -d storage s3://dvc
dvc remote modify --local storage endpointurl http://localhost:9000
dvc remote modify --local storage access_key_id minio
dvc remote modify --local storage secret_access_key minio123
```

## 2. DVC Remote

기본 remote는 MinIO를 기준으로 설계되어 있습니다.

- bucket: `dvc`
- endpoint: `http://localhost:9000`
- access key: `minio`
- secret key: `minio123`

실행 예시:

```powershell
.\scripts\configure_dvc_remote.ps1
dvc push
dvc pull
```

운영 환경에서 S3를 쓰려면 endpoint 설정만 제거하고 실제 버킷 URL을 사용하면 됩니다.

## 3. MLflow Production Layout

로컬 개발:

```powershell
docker compose up -d
```

접속 정보:

- MLflow: `http://localhost:5000`
- MinIO API: `http://localhost:9000`
- MinIO Console: `http://localhost:9001`
- PostgreSQL: `localhost:5432`

학습 코드인 `src/train.py`는 `MLFLOW_TRACKING_URI` 환경변수를 읽습니다. 로컬 기본값은 `file:./mlruns`이고, `.env`를 사용하면 MLflow 서버로 바로 전송할 수 있습니다.

## 4. Kubernetes Deploy

네임스페이스 및 스택 배포:

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/mlflow-stack.yaml
kubectl apply -f k8s/api-deployment.yaml
```

배포 전 [k8s/api-deployment.yaml](./k8s/api-deployment.yaml)의 `your-registry/mlops-api:latest` 이미지를 실제 레지스트리 주소로 바꿔야 합니다.

주의:

- `k8s/mlflow-stack.yaml`의 Secret은 예시값입니다.
- 운영에서는 Secret, PVC, Ingress, TLS, 별도 DB 백업 전략을 추가해야 합니다.

## 5. GitHub Actions CI/CD

워크플로는 세 단계입니다.

1. 의존성 설치 후 `dvc repro` 실행
2. API 이미지를 GHCR에 푸시
3. `KUBECONFIG` 시크릿을 사용해 Kubernetes 배포

필요한 GitHub Secrets:

- `KUBECONFIG`

기본적으로 컨테이너 이미지는 아래 형식으로 푸시됩니다.

```text
ghcr.io/<owner>/mlops-api:<git-sha>
```

## Typical Flow

1. 코드 변경 후 Git commit
2. `dvc repro`로 파이프라인 재실행
3. `dvc push`로 데이터와 모델 아티팩트 업로드
4. MLflow에서 실험 비교
5. `main` 브랜치 푸시 시 GitHub Actions가 이미지 빌드와 배포 수행

## Next Hardening

- MinIO와 PostgreSQL에 Persistent Volume 추가
- MLflow 인증/Ingress 추가
- API 추론 전용 모델 다운로드 로직 추가
- GitHub Actions에 테스트, 린트, 이미지 스캔 단계 추가
