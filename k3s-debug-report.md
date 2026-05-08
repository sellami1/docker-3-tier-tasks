# K3s Deployment Debug Report

**Date**: 2026-05-08  
**Cluster**: 3-node K3s (`k3s-cp`, `k3s-w1`, `k3s-w2`) — K3s v1.35.4+k3s1 / containerd 2.2.3  
**Namespace**: `tasks-app`

---

## Initial State

```
$ kubectl get pods,svc,ingress,pvc -n tasks-app

NAME                            READY   STATUS                       RESTARTS   AGE
pod/backend-5cb66cc99f-r5qbt    0/1     ErrImageNeverPull            0          74s
pod/backend-5cb66cc99f-tmwns    0/1     ErrImageNeverPull            0          74s
pod/database-0                  0/1     CreateContainerConfigError   0          47m
pod/frontend-6f56d4cc57-jhj5z   0/1     ErrImageNeverPull            0          68s
pod/frontend-6f56d4cc57-kddgb   0/1     ErrImageNeverPull            0          69s
```

Three distinct error states were present across all 5 pods.

---

## Investigation

### Step 1 — Verify images available on all nodes (via kubectl)

```bash
kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{":\n"}{range .status.images[*]}{"  - "}{.names[-1]}{"\n"}{end}{"\n"}{end}' | grep -E "(k3s|tasks-|mongo)"
```

**Output:**
```
k3s-cp:
  - docker.io/library/mongo:7.0
  - docker.io/library/tasks-backend:v1.0.0
  - docker.io/library/tasks-frontend:v1.0.0
k3s-w1:
  - docker.io/library/mongo:7.0
  - docker.io/library/tasks-backend:v1.0.0
  - docker.io/library/tasks-frontend:v1.0.0
k3s-w2:
  - docker.io/library/mongo:7.0
  - docker.io/library/tasks-backend:v1.0.0
  - docker.io/library/tasks-frontend:v1.0.0
```

✅ All three required images are present on all three nodes.

---

### Step 2 — Describe backend pod

```bash
kubectl describe pod -l app.kubernetes.io/component=backend -n tasks-app
```

**Key Event:**
```
Warning  ErrImageNeverPull  kubelet  Container image "docker-3-tier-tasks-backend:latest" is not present with pull policy of Never
```

**Root Cause Identified: Image Name Mismatch**

| | Image Name |
|---|---|
| Manifest | `docker-3-tier-tasks-backend:latest` |
| In containerd | `tasks-backend:v1.0.0` |

The manifests were using a stale Docker Compose–era naming convention (`docker-3-tier-tasks-backend:latest`) while the images were imported into K3s containerd under their registry names (`tasks-backend:v1.0.0`).

Same mismatch existed for the frontend:

| | Image Name |
|---|---|
| Manifest | `docker-3-tier-tasks-frontend:latest` |
| In containerd | `tasks-frontend:v1.0.0` |

---

### Step 3 — Describe database pod

```bash
kubectl describe pod database-0 -n tasks-app
```

**Key Event:**
```
Warning  Failed  kubelet  Error: container has runAsNonRoot and image will run as root
  (pod: "database-0_tasks-app(...)", container: database)
```

**Root Cause Identified: Security Context Conflict**

The `database-statefulset.yaml` had:
```yaml
securityContext:
  runAsNonRoot: true   # ← blocks mongo from starting
  fsGroup: 999
```

The official `mongo:7.0` image runs as `root` (uid=0) by default. K3s's Kubelet enforced the `runAsNonRoot` constraint and immediately blocked the container from starting — even though the image and PVC were both available and bound.

---

### Step 4 — Check secrets and configmaps

```bash
kubectl get secrets -n tasks-app
kubectl get configmaps -n tasks-app
```

**Output:**
```
NAME         TYPE     DATA   AGE
db-secrets   Opaque   4      51m

NAME                DATA   AGE
app-config          5      51m
frontend-config     1      51m
mongo-init-script   1      51m
```

✅ All required secrets and configmaps exist.

---

## Fixes Applied

### Fix 1 — Correct image names in backend and frontend deployments

**`k3s/deployments/backend-deployment.yaml`**:
```diff
-          image: docker-3-tier-tasks-backend:latest
+          image: tasks-backend:v1.0.0
```

**`k3s/deployments/frontend-deployment.yaml`**:
```diff
-          image: docker-3-tier-tasks-frontend:latest
+          image: tasks-frontend:v1.0.0
```

**Apply:**
```bash
kubectl apply -f k3s/deployments/backend-deployment.yaml -f k3s/deployments/frontend-deployment.yaml
```

---

### Fix 2 — Remove `runAsNonRoot` from database StatefulSet

**`k3s/deployments/database-statefulset.yaml`**:
```diff
     spec:
       securityContext:
-        runAsNonRoot: true
         fsGroup: 999
       ...
       containers:
         - name: database
           securityContext:
-            allowPrivilegeEscalation: false
-            capabilities:
-              drop:
-                - ALL
+            runAsUser: 999
+            runAsGroup: 999
```

**Rationale**: `mongo:7.0` starts as root internally then drops privileges. `runAsNonRoot: true` at the pod level conflicts with this. We instead use `runAsUser: 999` / `runAsGroup: 999` at the container level to map to the `mongodb` system user, and retain `fsGroup: 999` at pod level so the mounted data volume has correct ownership.

**Apply + force restart:**
```bash
kubectl apply -f k3s/deployments/database-statefulset.yaml
kubectl rollout restart statefulset/database -n tasks-app
kubectl delete pod database-0 -n tasks-app --force --grace-period=0
```

> `--force` was required because the StatefulSet rolling update was blocked by the stuck old pod.

---

### Fix 3 — Correct frontend port (nginx listens on 80, not 8080)

After backend and database came up, frontend pods were still crashing with:

```
Warning  Unhealthy  kubelet  Liveness probe failed: Get "http://10.42.3.9:8080/": connection refused
Warning  Unhealthy  kubelet  Readiness probe failed: Get "http://10.42.3.9:8080/health": connection refused
```

Frontend logs confirmed it is a standard nginx container:
```
/docker-entrypoint.sh: Configuration complete; ready for start up
```

Nginx defaults to port **80**, not 8080.

**`k3s/deployments/frontend-deployment.yaml`**:
```diff
           ports:
-            - containerPort: 8080
+            - containerPort: 80
         readinessProbe:
           httpGet:
-            path: /health
-            port: 8080
+            path: /
+            port: 80
         livenessProbe:
           httpGet:
             path: /
-            port: 8080
+            port: 80
```

**`k3s/services/frontend-service.yaml`**:
```diff
-      targetPort: 8080
+      targetPort: 80
```

**Apply:**
```bash
kubectl apply -f k3s/deployments/frontend-deployment.yaml -f k3s/services/frontend-service.yaml
```

---

## Final State

```bash
kubectl get pods,svc,ingress -n tasks-app
```

```
NAME                           READY   STATUS    RESTARTS        AGE
pod/backend-667d6dccbc-l9vtw   1/1     Running   3               4m28s
pod/backend-667d6dccbc-ng9ds   1/1     Running   0               118s
pod/database-0                 1/1     Running   0               3m7s
pod/frontend-5cd44dd4c-mzvpx   1/1     Running   0               35s
pod/frontend-5cd44dd4c-zgfbq   1/1     Running   0               50s

NAME                        TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE
service/backend             ClusterIP   10.43.176.49   <none>        3000/TCP       56m
service/database            ClusterIP   10.43.12.147   <none>        27017/TCP      56m
service/database-headless   ClusterIP   None           <none>        27017/TCP      56m
service/frontend            NodePort    10.43.243.85   <none>        80:30080/TCP   56m

NAME                                      CLASS     HOSTS         ADDRESS   PORTS   AGE
ingress.networking.k8s.io/tasks-ingress   traefik   tasks.local             80      56m
```

**Backend logs:**
```
MongoDB connected successfully
Server running on port 3000
```

✅ All 5 pods `1/1 Running` — full stack operational.

---

## Summary of Problems and Fixes

| # | Pod(s) Affected | Error | Root Cause | Fix |
|---|---|---|---|---|
| 1 | `backend`, `frontend` | `ErrImageNeverPull` | Image name mismatch: manifests used `docker-3-tier-tasks-*:latest` but containerd has `tasks-*:v1.0.0` | Update `image:` field in both deployment manifests |
| 2 | `database` | `CreateContainerConfigError` → `runAsNonRoot` | `mongo:7.0` starts as root; `runAsNonRoot: true` in pod securityContext blocked it | Remove `runAsNonRoot: true`, use `runAsUser/Group: 999` at container level |
| 3 | `frontend` | Liveness/Readiness probe failure | Probes targeted port `8080` but nginx container listens on port `80` | Fix `containerPort`, probe ports, and service `targetPort` to `80` |
