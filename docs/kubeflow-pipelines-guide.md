# Kubeflow Pipelines 가이드
## 관련 파일

- [KFP 파이프라인 소스](../src/pipelines/kfp_pipeline.py)
- [KFP 컴파일 스크립트](../scripts/compile_kfp_pipeline.ps1)
- [컴파일된 파이프라인 YAML](../infra/kubeflow/pipelines/iris-training-pipeline.yaml)
- [KFP Helm RBAC](../infra/k8s/kfp-helm-deployer-rbac.yaml)
- [아키텍처 가이드](./mlops-architecture-and-helm-deployment.md)

## 1. 목적

이 문서는 현재 저장소의 학습 흐름을 `Kubeflow Pipelines (KFP) v2`로 실행하고, 평가 지표를 기준으로 Helm 배포까지 연결하는 방법을 정리합니다.

대상 범위:

- KFP SDK 기반 파이프라인 정의
- 파이프라인 컴파일 방법
- Kubeflow Pipelines standalone 설치 방법
- 업로드 및 실행 방법
- Helm 배포 권한 구성

## 2. 현재 구성

저장소에는 다음 KFP 자산이 포함되어 있습니다.

- `src/pipelines/kfp_pipeline.py`
  - `prepare`, `train`, `evaluate`를 KFP component로 정의
  - 평가 기준을 통과하면 조건부 배포 게이트와 Helm 배포 step 실행
- `scripts/compile_kfp_pipeline.ps1`
  - 파이프라인 YAML 컴파일 스크립트
- `infra/kubeflow/pipelines/iris-training-pipeline.yaml`
  - KFP UI에 업로드 가능한 컴파일 결과물
- `infra/kubeflow/standalone/kustomization.yaml`
  - KFP standalone 설치용 Kustomize overlay
- `infra/argocd/apps/kubeflow-pipelines.yaml`
  - Argo CD로 KFP를 동기화할 수 있는 선택적 Application 매니페스트
- `infra/k8s/kfp-helm-deployer-rbac.yaml`
  - KFP 런타임이 `mlops` 네임스페이스에 Helm 배포를 수행하기 위한 RBAC 예시

## 3. KFP SDK 설치

Kubeflow 공식 문서는 KFP v2 사용을 위해 `pip install kfp`를 안내합니다.

현재 저장소에서는 다음으로 설치합니다.

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 4. 파이프라인 컴파일

```powershell
.\scripts\compile_kfp_pipeline.ps1
```

컴파일 결과:

- `infra/kubeflow/pipelines/iris-training-pipeline.yaml`

## 5. Kubeflow Pipelines 설치

Kubeflow 공식 standalone 설치 가이드는 Kustomize 기반 설치를 안내합니다.

현재 저장소에는 아래 standalone 설치 자산이 포함되어 있습니다.

- `infra/kubeflow/standalone/kustomization.yaml`
- `infra/kubeflow/standalone/namespace.yaml`

직접 설치:

```bash
kubectl apply -k infra/kubeflow/standalone
```

설치 후 UI 접속:

```bash
kubectl port-forward -n kubeflow svc/ml-pipeline-ui 8080:80
```

브라우저에서 `http://localhost:8080` 접속

Argo CD를 사용할 경우:

- `infra/argocd/apps/kubeflow-pipelines.yaml`의 `repoURL`을 실제 저장소 주소로 변경
- root application이 `infra/argocd/apps`를 바라보므로 함께 동기화 가능

## 6. Helm 배포 권한 구성

KFP에서 실제 `helm upgrade --install`을 실행하려면 파이프라인 실행 서비스어카운트가 대상 네임스페이스에 배포 권한을 가져야 합니다.

현재 저장소에는 다음 RBAC 예시가 포함되어 있습니다.

- `infra/k8s/kfp-helm-deployer-rbac.yaml`

적용:

```bash
kubectl apply -f infra/k8s/kfp-helm-deployer-rbac.yaml
```

이 매니페스트는 다음을 구성합니다.

- `kubeflow` 네임스페이스에 `kfp-helm-deployer` ServiceAccount 생성
- `mlops` 네임스페이스에 Helm 배포용 Role 생성
- 위 ServiceAccount를 `mlops` 네임스페이스 Role에 바인딩

KFP run 또는 experiment에서 `kfp-helm-deployer` 서비스어카운트를 사용하도록 설정해야 합니다.

## 7. 파이프라인 업로드와 실행

KFP UI에서 다음 파일을 업로드합니다.

- `infra/kubeflow/pipelines/iris-training-pipeline.yaml`

기본 파라미터:

- `test_size=0.2`
- `random_state=42`
- `max_depth=4`
- `enable_mlflow=false`
- `mlflow_tracking_uri=http://mlflow-server.mlops.svc.cluster.local:5000`
- `experiment_name=iris-kfp`
- `enable_deploy_candidate=false`
- `enable_helm_deploy=false`
- `threshold_accuracy=0.90`
- `image_repository=ghcr.io/your-org/mlops-api`
- `image_tag=stable`
- `namespace=mlops`
- `release_name=mlops-serving`
- `values_file=infra/helm/mlops-serving/values-prod.yaml`
- `repo_url=https://github.com/REPLACE_WITH_OWNER/REPLACE_WITH_REPO.git`
- `repo_revision=main`
- `chart_path=infra/helm/mlops-serving`

MLflow까지 연결하려면:

- 클러스터 내부에서 접근 가능한 MLflow 서비스 주소를 `mlflow_tracking_uri`로 지정
- `enable_mlflow=true`로 실행

조건부 배포 게이트를 쓰려면:

- `enable_deploy_candidate=true`로 실행
- `test_accuracy >= threshold_accuracy`일 때만 deploy candidate step이 생성됩니다.
- 해당 step은 Helm 배포에 필요한 파라미터를 deployment plan artifact로 기록합니다.

실제 Helm 배포까지 실행하려면:

- `enable_deploy_candidate=true`
- `enable_helm_deploy=true`
- `repo_url`, `repo_revision`, `chart_path`를 실제 저장소 기준으로 지정
- 파이프라인 런타임의 서비스어카운트로 `kfp-helm-deployer`를 사용하거나 동등한 권한을 부여해야 합니다.
- 실행 컨테이너가 Git 저장소에 네트워크로 접근 가능해야 합니다.

## 8. 현재 제약

- 현재 KFP 파이프라인은 저장소의 DVC 파이프라인과 별도로 동작합니다.
- KFP component는 lightweight Python component이므로 artifact는 KFP artifact store를 통해 전달됩니다.
- 현재 구성은 학습용 이미지 재사용이 아니라 component 실행 시 Python 패키지를 설치하는 방식입니다.
- `infra/kubeflow/standalone/kustomization.yaml`은 Kubeflow Pipelines GitHub 원격 리소스 `ref=2.15.0`에 의존합니다.
- 실제 Helm 배포 step은 `alpine/helm` 기반 컨테이너에서 Git 저장소를 clone한 뒤 `helm upgrade --install`을 실행합니다.
- 사설 저장소를 사용할 경우 Git 인증 방식과 secret 주입을 별도로 구성해야 합니다.

## 9. 다음 확장 권장사항

- 학습 전용 컨테이너 이미지를 만들어 KFP component base image로 전환
- MinIO artifact store와 KFP artifact store를 명시적으로 연동
- Helm 배포 전 smoke test, manual approval, rollout verification step 추가
- Katib, Notebook, KFServing/KServe와 연계한 Kubeflow 전체 스택으로 확장
