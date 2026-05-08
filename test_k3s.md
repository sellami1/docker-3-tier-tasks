Here are the `kubectl` commands and expected outputs to verify each checklist point in `tasks-app`:

## 1. 3 distinct workloads (Deployments + StatefulSet for DB)

```bash
kubectl get deployments,statefulsets -n tasks-app
```

**Expected:**
```
NAME                       READY   UP-TO-DATE   AVAILABLE
deployment.apps/backend    2/2     2            2
deployment.apps/frontend  2/2     2            2

NAME                     READY   AGE
statefulset.apps/database 1/1    ...
```

---

## 2. Resource requests and limits on all containers

```bash
kubectl get deployment backend -n tasks-app -o jsonpath='{range .spec.template.spec.containers[*]}{.name}{"\trequests: "}{.resources.requests}{"\tlimits: "}{.resources.limits}{"\n"}{end}'
kubectl get deployment frontend -n tasks-app -o jsonpath='{range .spec.template.spec.containers[*]}{.name}{"\trequests: "}{.resources.requests}{"\tlimits: "}{.resources.limits}{"\n"}{end}'
kubectl get statefulset database -n tasks-app -o jsonpath='{range .spec.template.spec.containers[*]}{.name}{"\trequests: "}{.resources.requests}{"\tlimits: "}{.resources.limits}{"\n"}{end}'
```

**Expected:** Non-empty `cpu`/`memory` under both `requests` and `limits` for `backend`, `frontend`, and `database`.

---

## 3. Liveness and Readiness Probes

```bash
kubectl get deployment backend -n tasks-app -o jsonpath='{range .spec.template.spec.containers[*]}{.name}{"\n  liveness: "}{.livenessProbe}{"\n  readiness: "}{.readinessProbe}{"\n"}{end}'
kubectl get deployment frontend -n tasks-app -o jsonpath='{range .spec.template.spec.containers[*]}{.name}{"\n  liveness: "}{.livenessProbe}{"\n  readiness: "}{.readinessProbe}{"\n"}{end}'
kubectl get statefulset database -n tasks-app -o jsonpath='{range .spec.template.spec.containers[*]}{.name}{"\n  liveness: "}{.livenessProbe}{"\n  readiness: "}{.readinessProbe}{"\n"}{end}'
```

**Expected:** Both `livenessProbe` and `readinessProbe` fields present for all three containers.

---

## 4. RollingUpdate strategy:

In a Kubernetes Deployment, the `RollingUpdate` strategy is the default strategy for updating pods. It works by creating new pods with the updated configuration, and then gradually replacing old pods with the new ones. This ensures that a constant number of pods are available during the update, as controlled by the `maxSurge` setting. In addition, the `maxUnavailable` setting controls how many pods can be unavailable during the update (e.g., can be `0` to ensure no pods are unavailable). This is achieved by keeping the number of available pods (i.e., the number of pods that are not being updated) constant during the update.

Here's an example of how to update a deployment with a rolling update strategy:
```bash
# 1. Mise à jour de l'image du backend (déclenche un rolling update)
kubectl set image deployment/backend backend=tasks-backend:v2.0.0 -n tasks-app
 
# 2. Ou via apply avec un manifest modifié
kubectl apply -f k3s/deployments/backend-deployment.yaml
```


```bash
kubectl get deployment backend -n tasks-app -o jsonpath='{.spec.strategy}'
kubectl get deployment frontend -n tasks-app -o jsonpath='{.spec.strategy}'
kubectl get statefulset database -n tasks-app -o jsonpath='{.spec.updateStrategy}'
```

**Expected:** `type: RollingUpdate` with `maxSurge`/`maxUnavailable` set for Deployments; `type: RollingUpdate` for StatefulSet.

---

## 5. Non-root securityContext

```bash
kubectl get deployment backend -n tasks-app -o jsonpath='{ .spec.template.spec.securityContext }{"\ncontainer: "}{.spec.template.spec.containers[0].securityContext }{"\n"}'
kubectl get deployment frontend -n tasks-app -o jsonpath='{ .spec.template.spec.securityContext }{"\ncontainer: "}{.spec.template.spec.containers[0].securityContext }{"\n"}'
kubectl get statefulset database -n tasks-app -o jsonpath='{ .spec.template.spec.securityContext }{"\ncontainer: "}{.spec.template.spec.containers[0].securityContext }{"\n"}'
```

**Expected:** `runAsNonRoot: true` at pod level for `backend`/`frontend`; `runAsUser`/`runAsGroup` set (e.g. `999` for DB, `1001` for app containers).

---

## 6. Replicas ≥ 2 for critical services

```bash
kubectl get deployment backend frontend -n tasks-app -o custom-columns=NAME:.metadata.name,REPLICAS:.spec.replicas
```

**Expected:**
```
NAME       REPLICAS
backend    2
frontend   2
```

**Note:** `database` StatefulSet intentionally has `replicas: 1` (MongoDB single-node), so this criterion applies to the critical app-tier workloads only.

---

## Quick all-in-one verification

```bash
echo "=== Workloads ===" && kubectl get deploy,sts -n tasks-app
echo "=== Replicas ===" && kubectl get deploy -n tasks-app -o custom-columns=NAME:.metadata.name,REPLICAS:.spec.replicas
echo "=== Resources & Probes ===" && kubectl get deploy backend -n tasks-app -o jsonpath='{ .spec.template.spec.containers[0].resources }{"\n"}{ .spec.template.spec.containers[0].livenessProbe }{"\n"}{ .spec.template.spec.containers[0].readinessProbe }{"\n"}'
```