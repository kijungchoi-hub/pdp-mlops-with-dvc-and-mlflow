# 운영 체크리스트
## 관련 파일

- [Helm 값 파일 - Prod](../infra/helm/mlops-serving/values-prod.yaml)
- [Kubernetes 네임스페이스](../infra/k8s/namespace.yaml)
- [MLflow 스택 매니페스트](../infra/k8s/mlflow-stack.yaml)
- [장애 대응 런북](./incident-response-runbook.md)
- [Argo CD 가이드](./argocd-deployment-guide.md)


## 1. 배포 전 체크

### 코드 및 모델

- `dvc repro`가 성공했는지 확인
- `models/model.joblib`가 최신 학습 결과인지 확인
- `reports/metrics.json`, `reports/eval.json`이 생성됐는지 확인
- MLflow에 학습 메트릭과 파라미터가 정상 기록됐는지 확인

### 이미지 및 레지스트리

- 서빙 이미지가 정상 빌드됐는지 확인
- 이미지가 레지스트리에 push됐는지 확인
- 배포 대상 태그가 `values-prod.yaml`에 반영됐는지 확인

### Kubernetes 및 Helm

- 대상 클러스터에 `kubectl` 접근이 가능한지 확인
- 대상 네임스페이스가 준비됐는지 확인
- `helm template` 결과가 기대한 리소스를 생성하는지 확인
- `kserve.enabled=true`인 경우 KServe CRD와 컨트롤러가 설치되어 있는지 확인

### 설정값

- `infra/helm/mlops-serving/values-prod.yaml`의 이미지 경로가 실제 값인지 확인
- replica 수가 환경 규모에 맞는지 확인
- CPU/메모리 requests, limits가 적절한지 확인
- `MODEL_PATH`가 컨테이너 내부 경로와 일치하는지 확인

## 2. 배포 중 체크

### Helm 배포

- `helm upgrade --install` 명령이 실패 없이 끝났는지 확인
- 새 release revision이 생성됐는지 확인

예시:

```bash
helm list -n mlops
helm status mlops-serving -n mlops
```

### Kubernetes 리소스 상태

- `Deployment`가 정상 생성됐는지 확인
- `Service`가 정상 생성됐는지 확인
- KServe 사용 시 `InferenceService` 상태를 확인

예시:

```bash
kubectl get deployments -n mlops
kubectl get svc -n mlops
kubectl get inferenceservices -n mlops
```

## 3. 배포 후 체크

### 파드 상태

- 모든 파드가 `Running` 또는 정상 ready 상태인지 확인
- CrashLoopBackOff, ImagePullBackOff가 없는지 확인

예시:

```bash
kubectl get pods -n mlops
kubectl describe pod <pod-name> -n mlops
```

### 애플리케이션 상태

- `/health` 응답이 정상인지 확인
- 샘플 요청으로 `/predict` 호출이 되는지 확인

예시:

```bash
kubectl port-forward svc/mlops-serving-mlops-serving 8080:80 -n mlops
curl http://127.0.0.1:8080/health
```

### 로그 및 이벤트

- 애플리케이션 로그에 모델 로드 실패가 없는지 확인
- Kubernetes 이벤트에 스케줄링, 이미지 pull, probe 실패가 없는지 확인

예시:

```bash
kubectl logs deployment/mlops-serving-mlops-serving -n mlops
kubectl get events -n mlops --sort-by=.metadata.creationTimestamp
```

## 4. 장애 대응 체크

### 이미지 관련 문제

- 레지스트리 주소와 태그가 맞는지 확인
- 이미지 pull 권한 또는 secret 문제가 없는지 확인

### 모델 로딩 문제

- `MODEL_PATH` 경로가 올바른지 확인
- 컨테이너 안에 모델 파일이 실제로 존재하는지 확인
- 이미지 빌드 시 모델이 포함됐는지 확인

### 프로브 실패

- `/health` 엔드포인트가 실제로 응답하는지 확인
- readiness/liveness 초기 지연 시간이 충분한지 확인

### KServe 문제

- `InferenceService` 상태 조건을 확인
- KServe controller 로그를 확인
- KServe와 일반 `Deployment`를 동시에 쓸지 정책을 다시 확인

## 5. 롤백 체크

- 이전 Helm revision이 존재하는지 확인
- 문제가 재현되면 바로 이전 revision으로 롤백

예시:

```bash
helm history mlops-serving -n mlops
helm rollback mlops-serving <revision> -n mlops
```

## 6. 일일 운영 점검 항목

- 최근 배포 이력 확인
- 파드 재시작 횟수 확인
- 에러 로그 증가 여부 확인
- 모델 버전과 이미지 태그 일치 여부 확인
- MLflow 기록과 실제 운영 모델 간 차이 여부 확인

## 7. 권장 문서 참조

- `docs/mlops-architecture-and-helm-deployment.md`
- `docs/project-structure.md`
- `infra/helm/mlops-serving/values-prod.yaml`


