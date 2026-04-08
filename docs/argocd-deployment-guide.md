# Argo CD 배포 가이드
## 관련 파일

- [Argo CD 프로젝트](../infra/argocd/project.yaml)
- [Argo CD 루트 애플리케이션](../infra/argocd/root-application.yaml)
- [Argo CD 애플리케이션](../infra/argocd/apps/)
- [Helm 값 파일 - Dev](../infra/helm/mlops-serving/values-dev.yaml)
- [Helm 값 파일 - Staging](../infra/helm/mlops-serving/values-staging.yaml)
- [Helm 값 파일 - Prod](../infra/helm/mlops-serving/values-prod.yaml)

이 저장소는 서빙 환경과 공용 MLflow 스택을 GitOps 방식으로 배포할 수 있도록 Argo CD 구성을 포함합니다.

## 구성

- `infra/argocd/project.yaml`: Argo CD `AppProject`
- `infra/argocd/root-application.yaml`: app-of-apps 부트스트랩용 루트 앱
- `infra/argocd/apps/mlflow-stack.yaml`: 공용 MLflow, PostgreSQL, MinIO 애플리케이션
- `infra/argocd/apps/mlops-serving-dev.yaml`: 개발 서빙 환경
- `infra/argocd/apps/mlops-serving-staging.yaml`: 스테이징 서빙 환경
- `infra/argocd/apps/mlops-serving-prod.yaml`: 운영 서빙 환경
- `infra/argocd/apps/kubeflow-pipelines.yaml`: Kubeflow Pipelines standalone 애플리케이션

## 환경

- `mlops-dev`: `values-dev.yaml`을 사용하는 Helm 차트
- `mlops-staging`: `values-staging.yaml`을 사용하는 Helm 차트
- `mlops-prod`: `values-prod.yaml`을 사용하는 Helm 차트
- `mlops`: raw `mlflow-stack.yaml` 매니페스트를 사용하는 공용 네임스페이스
- `kubeflow`: Kubeflow Pipelines standalone 네임스페이스

## 사전 준비

1. `argocd` 네임스페이스에 Argo CD가 설치되어 있어야 합니다.
2. Argo CD가 현재 저장소에 접근 가능해야 합니다.
3. 모든 `repoURL` placeholder를 실제 저장소 주소로 바꿔야 합니다.

```yaml
https://github.com/REPLACE_WITH_OWNER/REPLACE_WITH_REPO.git
```

4. Helm values 파일의 이미지 경로와 태그를 실제 레지스트리 값으로 바꿔야 합니다.

## 초기 적용

Argo CD 프로젝트와 루트 애플리케이션을 먼저 적용합니다.

```bash
kubectl apply -f infra/argocd/project.yaml
kubectl apply -f infra/argocd/root-application.yaml
```

적용 후 Argo CD는 다음 애플리케이션을 생성하고 동기화합니다.

- `mlflow-stack`
- `mlops-serving-dev`
- `mlops-serving-staging`
- `mlops-serving-prod`
- `kubeflow-pipelines`

## 운영 메모

- 서빙 애플리케이션은 `CreateNamespace=true`를 사용하므로 `mlops-dev`, `mlops-staging`, `mlops-prod` 네임스페이스를 자동으로 생성합니다.
- MLflow 스택은 현재 raw manifest가 `mlops` 네임스페이스를 고정 사용하므로 공용 배포로 유지됩니다.
- 현재 GitHub Actions 워크플로는 여전히 직접 Helm 배포를 수행합니다. 완전한 GitOps로 전환하려면 이미지 태그 갱신을 Git commit 기반으로 바꾸거나 Argo CD Image Updater를 추가해야 합니다.
- `values-prod.yaml`은 현재 `mode: kserve`를 사용하므로 운영 Argo CD 앱을 동기화할 때 대상 클러스터에 KServe가 설치되어 있어야 합니다.
