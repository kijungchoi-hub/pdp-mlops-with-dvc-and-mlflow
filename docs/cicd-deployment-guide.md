# CI/CD 배포 가이드
## 관련 파일

- [GitHub Actions 워크플로](../.github/workflows/ci-cd.yaml)
- [파이프라인 정의](../dvc.yaml)
- [API Dockerfile](../infra/docker/api.Dockerfile)
- [Helm 차트](../infra/helm/mlops-serving/Chart.yaml)
- [Argo CD 가이드](./argocd-deployment-guide.md)


## 1. 목적

이 문서는 현재 저장소의 GitHub Actions 기반 CI/CD 흐름과, 향후 Helm 중심 배포로 확장할 때의 기준 절차를 정리합니다.

대상 범위:

- GitHub Actions 워크플로 구조
- 학습, 아티팩트, 이미지 빌드 흐름
- Kubernetes 배포 흐름
- Helm 배포로 전환할 때의 권장 방식

## 2. 현재 CI/CD 아키텍처

현재 워크플로 파일:

- `.github/workflows/ci-cd.yaml`

현재 파이프라인은 3단계입니다.

1. `test-and-train`
   - Python 환경 구성
   - 의존성 설치
   - `dvc repro` 실행
   - 리포트와 모델 아티팩트 업로드
2. `build-and-push`
   - 학습된 모델 아티팩트 다운로드
   - Docker 이미지 빌드
   - GHCR에 이미지 push
3. `validate-helm`
   - dev, staging, prod values 기준 `helm template` 검증
4. `deploy`
   - Kubernetes context 설정
   - Helm 기반 배포 수행

## 3. 현재 워크플로 동작 순서

### Step 1. 코드 checkout

GitHub Actions가 저장소 코드를 checkout합니다.

### Step 2. 학습 파이프라인 실행

`test-and-train` job에서 다음이 수행됩니다.

```bash
pip install -r requirements.txt
dvc repro
```

이 단계 결과:

- `models/model.joblib`
- `reports/metrics.json`
- `reports/eval.json`

### Step 3. 학습 산출물 업로드

학습이 끝나면 다음 아티팩트를 업로드합니다.

- `reports/`
- `models/`

### Step 4. 서빙 이미지 빌드

`build-and-push` job에서 모델 아티팩트를 다시 내려받은 뒤, 아래 Dockerfile로 이미지를 빌드합니다.

- `infra/docker/api.Dockerfile`

이미지 태그 형식:

```text
ghcr.io/<owner>/mlops-api:<git-sha>
```

### Step 5. 이미지 푸시

GitHub Container Registry로 이미지를 push합니다.

필요 권한:

- `packages: write`

### Step 6. Helm template 검증

`validate-helm` job에서 다음 파일들을 기준으로 렌더링 검증을 수행합니다.

- `infra/helm/mlops-serving/values-dev.yaml`
- `infra/helm/mlops-serving/values-staging.yaml`
- `infra/helm/mlops-serving/values-prod.yaml`

### Step 7. Kubernetes 배포

현재 `deploy` job은 Helm 기반입니다.

적용 순서:

- `infra/k8s/namespace.yaml`
- `infra/k8s/mlflow-stack.yaml`
- `helm upgrade --install`

## 4. 현재 CI/CD에 필요한 GitHub Secrets

### 필수

- `KUBECONFIG`
  Kubernetes 클러스터 접근용 kubeconfig

### 기본 제공

- `GITHUB_TOKEN`
  GHCR push에 사용

## 5. 현재 방식의 장점과 한계

### 장점

- 환경별 values 파일로 설정 분리 가능
- 표준 Deployment와 KServe 배포를 같은 chart에서 관리 가능
- ingress, secret, PVC를 values 기반으로 조정 가능

### 한계

- MLflow stack은 아직 raw manifest 기반
- values 구조가 더 커지면 chart 분리가 필요할 수 있음

## 6. Helm 중심 배포로 전환하는 권장 방식

현재 저장소는 이미 Helm 중심 배포로 전환된 상태입니다.

권장 방향:

1. CI
   - `dvc repro`
   - 모델 아티팩트 생성
   - 이미지 로컬 빌드
   - `/health`, `/predict` smoke test
   - GHCR push
2. CD
   - `helm template` 검증
   - `helm upgrade --install` 배포

## 7. Helm 기반 배포 순서

### 1. 모델 학습

CI에서 `dvc repro` 실행

### 2. 모델 포함 이미지 빌드

CI에서 `infra/docker/api.Dockerfile`로 이미지 빌드 후 push

### 3. values 파일에 이미지 태그 반영

예:

- `infra/helm/mlops-serving/values-dev.yaml`
- `infra/helm/mlops-serving/values-staging.yaml`
- `infra/helm/mlops-serving/values-prod.yaml`

수정 항목:

- `image.repository`
- `image.tag`

### 4. Helm 템플릿 검증

```bash
helm template mlops-serving ./infra/helm/mlops-serving -n mlops -f ./infra/helm/mlops-serving/values-prod.yaml
```

### 5. Helm 배포

```bash
helm upgrade --install mlops-serving ./infra/helm/mlops-serving -n mlops --create-namespace -f ./infra/helm/mlops-serving/values-prod.yaml
```

## 8. 현재 GitHub Actions의 Helm 배포 방식

현재 deploy job은 다음 형태로 image 값을 override 하여 배포합니다.

```bash
helm upgrade --install mlops-serving ./infra/helm/mlops-serving \
  -n mlops \
  --create-namespace \
  -f ./infra/helm/mlops-serving/values-prod.yaml \
  --set image.repository=ghcr.io/${GITHUB_REPOSITORY_OWNER}/mlops-api \
  --set image.tag=${GITHUB_SHA}
```

## 9. 권장 운영 방식

### 개발 환경

- raw manifest 또는 기본 `values.yaml`

### 운영 환경

- `values-prod.yaml`
- `helm template` 사전 검증
- `helm upgrade --install` 배포

### KServe 사용 시

- `kserve.enabled=true`
- 클러스터에 KServe 설치 완료 상태여야 함

## 10. 점검 명령

배포 확인:

```bash
helm list -n mlops
helm status mlops-serving -n mlops
kubectl get pods -n mlops
kubectl get svc -n mlops
```

KServe 사용 시:

```bash
kubectl get inferenceservices -n mlops
```

## 11. 다음 개선 권장사항

- MLflow stack도 Helm chart로 전환할지 결정
- staging, production 값을 별도 파일로 분리
- deploy 후 cluster-level smoke test 자동화
- 배포 후 `/health` 및 `/predict` smoke test 자동화
- Helm rollback 절차를 CI/CD 문서와 runbook에 연결

