# 장애 대응 Runbook

## 1. 목적

이 문서는 모델 서빙 운영 중 장애가 발생했을 때 빠르게 상태를 확인하고, 원인을 좁히고, 복구하기 위한 절차를 정리합니다.

대상 범위:

- FastAPI 서빙 장애
- Kubernetes 배포 장애
- 이미지 pull 실패
- 모델 로드 실패
- readiness/liveness probe 실패
- KServe `InferenceService` 관련 장애
- Helm 롤백

## 2. 공통 초기 확인

장애가 발생하면 먼저 아래를 확인합니다.

```bash
kubectl get pods -n mlops
kubectl get deployments -n mlops
kubectl get svc -n mlops
kubectl get events -n mlops --sort-by=.metadata.creationTimestamp
```

KServe 사용 시:

```bash
kubectl get inferenceservices -n mlops
```

Helm 배포 상태:

```bash
helm list -n mlops
helm status mlops-serving -n mlops
helm history mlops-serving -n mlops
```

## 3. 증상별 대응

### 3.1 Pod가 뜨지 않음

확인:

```bash
kubectl get pods -n mlops
kubectl describe pod <pod-name> -n mlops
```

주요 원인:

- 잘못된 이미지 이름 또는 태그
- 이미지 pull 권한 부족
- 리소스 부족으로 스케줄링 실패
- 잘못된 manifest 또는 Helm values

대응:

1. `values-prod.yaml`의 `image.repository`, `image.tag` 확인
2. 이미지가 레지스트리에 실제로 존재하는지 확인
3. `kubectl describe pod`의 이벤트에서 `ImagePullBackOff`, `ErrImagePull`, `FailedScheduling` 여부 확인
4. 필요 시 imagePullSecret 또는 노드 리소스 상태 점검

### 3.2 ImagePullBackOff 또는 ErrImagePull

확인:

```bash
kubectl describe pod <pod-name> -n mlops
```

대응:

1. 이미지 경로와 태그가 정확한지 확인
2. 프라이빗 레지스트리라면 pull secret 설정 여부 확인
3. CI에서 push한 이미지 태그와 Helm values 값이 일치하는지 확인

빠른 점검 포인트:

- `ghcr.io/<owner>/mlops-api:<tag>`가 실제 존재하는지
- 클러스터가 해당 레지스트리에 접근 가능한지

### 3.3 컨테이너는 떴지만 Ready가 안 됨

확인:

```bash
kubectl get pods -n mlops
kubectl describe pod <pod-name> -n mlops
kubectl logs <pod-name> -n mlops
```

주요 원인:

- `/health` 응답 실패
- 모델 로드 실패
- 앱 시작 시간이 probe 설정보다 길음

대응:

1. 로그에서 모델 파일 로드 실패 메시지 확인
2. `MODEL_PATH` 값 확인
3. readiness/liveness 초기 지연 시간 조정 검토

### 3.4 모델 로드 실패

주요 증상:

- `/health`가 degraded 상태
- `/predict`가 503 반환
- 로그에 model not found 또는 deserialization 오류

확인:

```bash
kubectl logs deployment/mlops-serving-mlops-serving -n mlops
```

필요 시 컨테이너 내부 확인:

```bash
kubectl exec -it deployment/mlops-serving-mlops-serving -n mlops -- sh
ls /app/models
```

대응:

1. 이미지 빌드 시 `models/model.joblib`가 포함됐는지 확인
2. `MODEL_PATH`가 `/app/models/model.joblib`와 일치하는지 확인
3. 학습 후 생성된 모델 파일이 최신 이미지 빌드에 포함됐는지 확인

### 3.5 /predict 실패

확인:

```bash
kubectl port-forward svc/mlops-serving-mlops-serving 8080:80 -n mlops
curl http://127.0.0.1:8080/health
```

샘플 호출:

```bash
curl -X POST http://127.0.0.1:8080/predict \
  -H "Content-Type: application/json" \
  -d '{"sepal_length":5.1,"sepal_width":3.5,"petal_length":1.4,"petal_width":0.2}'
```

대응:

1. 먼저 `/health`가 정상인지 확인
2. 요청 payload 형식이 맞는지 확인
3. 앱 로그에 validation 오류 또는 모델 예측 오류가 있는지 확인

### 3.6 KServe InferenceService가 Ready가 안 됨

확인:

```bash
kubectl get inferenceservices -n mlops
kubectl describe inferenceservice iris-model -n mlops
```

대응:

1. KServe CRD와 컨트롤러 설치 여부 확인
2. `InferenceService` 이벤트와 condition 확인
3. KServe controller 로그 확인
4. 현재 chart가 일반 `Deployment`도 함께 만들 수 있으므로 운영 정책상 중복 배포 여부 점검

### 3.7 Helm 배포 후 이상 동작

확인:

```bash
helm status mlops-serving -n mlops
helm history mlops-serving -n mlops
```

대응:

1. 최근 revision에서 어떤 값이 바뀌었는지 확인
2. 잘못된 values 파일이 적용됐는지 확인
3. 필요 시 직전 revision으로 롤백

롤백:

```bash
helm rollback mlops-serving <revision> -n mlops
```

## 4. 우선순위별 대응 순서

### P1. 완전 장애

예시:

- 모든 Pod 비정상
- 서비스 응답 불가
- InferenceService Ready 실패

대응 순서:

1. Helm release 상태 확인
2. Pod 이벤트와 로그 확인
3. 이미지 태그 및 모델 경로 확인
4. 즉시 복구가 어려우면 직전 revision 롤백

### P2. 부분 장애

예시:

- 일부 Pod만 재시작 반복
- probe 실패 증가
- 응답은 있으나 예측 실패 발생

대응 순서:

1. 문제 Pod 식별
2. 로그와 이벤트 비교
3. 리소스, probe, 모델 파일 상태 점검
4. 필요 시 replica 축소 또는 재배포

## 5. 복구 후 확인

복구 후에는 반드시 아래를 확인합니다.

```bash
kubectl get pods -n mlops
kubectl get svc -n mlops
kubectl logs deployment/mlops-serving-mlops-serving -n mlops
```

추가 확인:

- `/health` 정상 응답
- 샘플 `/predict` 호출 성공
- 에러 로그가 더 이상 증가하지 않음
- KServe 사용 시 `InferenceService` 상태가 Ready

## 6. 사후 조치

장애 복구 후 다음을 남깁니다.

1. 장애 발생 시간
2. 영향 범위
3. 근본 원인
4. 수행한 조치
5. 재발 방지 항목

권장 재발 방지 예시:

- Helm values 검증 절차 강화
- CI에서 `helm template` 자동 검증 추가
- 모델 파일 존재 여부를 빌드 단계에서 검증
- readiness/liveness probe 튜닝

## 7. 함께 보면 좋은 문서

- `docs/mlops-architecture-and-helm-deployment.md`
- `docs/operations-checklist.md`
- `infra/helm/mlops-serving/values-prod.yaml`
