
# K3s Implementation Runbook (1 control-plane + 2 workers)

This runbook deploys the manifests in `k8s/` onto the K3s lab cluster described in `infra.md`.

## Assumptions (from infra.md)

- Nodes
	- Control-plane: `k3s-cp`
		- Host-only/internal: `192.168.204.129`
		- Bridged/LAN: `192.168.1.20`
	- Workers: `k3s-w1` (`192.168.204.130`), `k3s-w2` (`192.168.204.131`)
- Cluster networking backbone is **host-only** (`192.168.204.0/24`).
- LAN access is via the control-plane bridged IP (`192.168.1.20`).
- Ingress controller is **Traefik** (default in K3s).

## What will be deployed

From `k8s/`:

- Namespace: `tasks-app`
- MongoDB (`mongo:7.0`) + PVC (`mongo-data`) + StorageClass (`app-local-path`)
- Backend Deployment (`tasks-backend:latest`) + Service (ClusterIP) + HPA
- Frontend Deployment (`tasks-frontend:latest`) + Service (NodePort 30080)
- Ingress: host `tasks.local` -> frontend service

Important detail: `tasks-backend:latest` and `tasks-frontend:latest` are **local images**. They must exist in the container runtime on each node that might schedule the pods.

---

## 0) Decide where you run `kubectl`

You have two solid options:

### Option A (simplest): run everything on the control-plane

- Use K3s built-in kubectl:
	- `sudo k3s kubectl ...`

### Option B: run `kubectl` from your PC

- Copy `/etc/rancher/k3s/k3s.yaml` from `k3s-cp` and adjust the server IP to `https://192.168.1.20:6443` (LAN) or `https://192.168.204.129:6443` (host-only).

This runbook assumes **Option A**.

---

## 1) Pre-flight checks (on `k3s-cp`)

```bash
sudo k3s kubectl get nodes -o wide
sudo k3s kubectl -n kube-system get pods | egrep 'traefik|metrics-server' || true
```

### Metrics-server (required for HPA)

If `metrics-server` is not present/healthy, HPA will not scale.

Install it (only if needed):

```bash
sudo k3s kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
sudo k3s kubectl -n kube-system rollout status deploy/metrics-server
```

---

## 2) Transfer manifests from PC to control-plane (LAN)

From your PC (same LAN as `192.168.1.20`):

```bash
scp -r ./k8s <USER>@192.168.1.20:~/tasks-k8s
```

On `k3s-cp`:

```bash
cd ~/tasks-k8s/k8s
ls -1
```

---

## 3) Set secrets (recommended)

The default secret values in `k8s/secret.yaml` include `change-me`. Replace them before deploying.

### Option A: edit file and apply

Edit `k8s/secret.yaml` and set strong values.

### Option B: create/replace secret without editing files

```bash
sudo k3s kubectl apply -f namespace.yaml

sudo k3s kubectl -n tasks-app create secret generic db-secrets \
	--from-literal=DB_ROOT_USER=admin \
	--from-literal=DB_ROOT_PASSWORD='<strong-root-pw>' \
	--from-literal=DB_APP_USER=appuser \
	--from-literal=DB_APP_PASSWORD='<strong-app-pw>' \
	--dry-run=client -o yaml | sudo k3s kubectl apply -f -
```

---

## 4) Apply manifests (ordered)

Run on `k3s-cp`:

```bash
cd ~/tasks-k8s/k8s

# 1) Namespace
sudo k3s kubectl apply -f namespace.yaml

# 2) Storage (local-path provisioner)
sudo k3s kubectl apply -f storageclass.yaml

# 3) Config + secrets
sudo k3s kubectl apply -f configmap.yaml
sudo k3s kubectl apply -f secret.yaml

# 4) PVC
sudo k3s kubectl apply -f mongo-pvc.yaml

# 5) Database
sudo k3s kubectl apply -f database-service.yaml
sudo k3s kubectl apply -f database-deployment.yaml

# 6) Backend
sudo k3s kubectl apply -f backend-service.yaml
sudo k3s kubectl apply -f backend-deployment.yaml
sudo k3s kubectl apply -f backend-hpa.yaml

# 7) Frontend
sudo k3s kubectl apply -f frontend-service.yaml
sudo k3s kubectl apply -f frontend-deployment.yaml

# 8) Ingress
sudo k3s kubectl apply -f ingress.yaml
```

Wait for rollout:

```bash
sudo k3s kubectl -n tasks-app rollout status deploy/database
sudo k3s kubectl -n tasks-app rollout status deploy/backend
sudo k3s kubectl -n tasks-app rollout status deploy/frontend
```

---

## 5) Build and move images PC → cluster (LAN)

Because the manifests reference `tasks-backend:latest` and `tasks-frontend:latest`, you must load those images into **containerd on each node**.

### 5.1 Build and export on your PC

From the repository root on your PC:

```bash
docker build -t tasks-backend:latest ./express-tasks-backend
docker build -t tasks-frontend:latest ./react-tasks-frontend

docker save -o /tmp/tasks-backend.tar tasks-backend:latest
docker save -o /tmp/tasks-frontend.tar tasks-frontend:latest
```

### 5.2 Copy tarballs to the control-plane over LAN

```bash
scp /tmp/tasks-backend.tar /tmp/tasks-frontend.tar <USER>@192.168.1.20:/tmp/
```

### 5.3 Import on control-plane containerd

On `k3s-cp`:

```bash
sudo k3s ctr images import /tmp/tasks-backend.tar
sudo k3s ctr images import /tmp/tasks-frontend.tar
sudo k3s ctr images ls | egrep 'tasks-(backend|frontend)'
```

### 5.4 Copy tarballs to workers (via host-only) and import

From `k3s-cp`:

```bash
scp /tmp/tasks-backend.tar /tmp/tasks-frontend.tar <USER>@192.168.204.130:/tmp/
scp /tmp/tasks-backend.tar /tmp/tasks-frontend.tar <USER>@192.168.204.131:/tmp/
```

On each worker (`k3s-w1`, then `k3s-w2`):

```bash
sudo k3s ctr images import /tmp/tasks-backend.tar
sudo k3s ctr images import /tmp/tasks-frontend.tar
sudo k3s ctr images ls | egrep 'tasks-(backend|frontend)'
```

Notes:

- This uses the LAN only between PC → `k3s-cp`. Workers can remain host-only.
- If you later add a private registry, you can switch to `imagePullPolicy: Always` with `image: registry.local/...`.

---

## 6) Access the application

You have two ways:

### A) Ingress (recommended)

`k8s/ingress.yaml` routes `tasks.local` to the `frontend` service.

On your PC, add a hosts entry pointing to the **control-plane LAN IP**:

```bash
echo '192.168.1.20 tasks.local' | sudo tee -a /etc/hosts
```

Then browse:

- `http://tasks.local`

### B) NodePort

`k8s/frontend-service.yaml` exposes NodePort `30080`:

- `http://192.168.1.20:30080`

---

## 7) Load-balancing & node placement strategy (1 master + 2 workers)

Goal: spread stateless workloads across workers, keep stateful DB stable.

### 7.1 Keep application pods off the control-plane

If you want the control-plane to run only system workloads, taint it:

```bash
sudo k3s kubectl taint node k3s-cp node-role.kubernetes.io/control-plane=true:NoSchedule
```

(Your app pods have no tolerations, so they will schedule on workers.)

### 7.2 Spread backend/frontend replicas across workers

You already have:

- frontend replicas: 2
- backend replicas: 2 + HPA 2..5 (CPU 70%)

To encourage even spreading, add `topologySpreadConstraints` to **both** `backend` and `frontend` pod specs.

#### Backend snippet (add under `spec.template.spec` in `k8s/backend-deployment.yaml`)

```yaml
      topologySpreadConstraints:
        - maxSkew: 1
          topologyKey: kubernetes.io/hostname
          whenUnsatisfiable: ScheduleAnyway
          labelSelector:
            matchLabels:
              app.kubernetes.io/name: tasks
              app.kubernetes.io/component: backend
```

#### Frontend snippet (add under `spec.template.spec` in `k8s/frontend-deployment.yaml`)

```yaml
      topologySpreadConstraints:
        - maxSkew: 1
          topologyKey: kubernetes.io/hostname
          whenUnsatisfiable: ScheduleAnyway
          labelSelector:
            matchLabels:
              app.kubernetes.io/name: tasks
              app.kubernetes.io/component: frontend
```

Validate placement:

```bash
sudo k3s kubectl -n tasks-app get pods -o wide
```

### 7.3 Pin MongoDB to a chosen worker (recommended with local-path + RWO PVC)

Because the PVC uses local-path storage, it’s best to keep MongoDB on a stable node.

1) Label one worker (example: `k3s-w1`):

```bash
sudo k3s kubectl label node k3s-w1 tasks-db=true
```

2) Add a nodeSelector in `k8s/database-deployment.yaml` under `spec.template.spec`:

```yaml
      nodeSelector:
        tasks-db: "true"
```

This minimizes surprise reschedules that would land the DB on a different node.

---

## 8) Operational checks / troubleshooting

### Check all objects

```bash
sudo k3s kubectl -n tasks-app get all
sudo k3s kubectl -n tasks-app get ingress
sudo k3s kubectl -n tasks-app get events --sort-by=.lastTimestamp | tail -n 50
```

### If pods are stuck in ImagePullBackOff

- Confirm images exist on the node:
	- `sudo k3s ctr images ls | egrep 'tasks-(backend|frontend)'`
- Confirm the image name matches manifests exactly:
	- backend: `tasks-backend:latest`
	- frontend: `tasks-frontend:latest`

### If MongoDB is Pending

- Check PVC and StorageClass:

```bash
sudo k3s kubectl -n tasks-app get pvc
sudo k3s kubectl get storageclass
sudo k3s kubectl -n tasks-app describe pvc mongo-data
```

### If HPA shows “unknown” metrics

```bash
sudo k3s kubectl -n tasks-app get hpa
sudo k3s kubectl -n kube-system get pods | grep metrics-server
```

---

## 9) Clean removal

```bash
sudo k3s kubectl delete ns tasks-app
```

If you changed node labels/taints and want to revert:

```bash
sudo k3s kubectl label node k3s-w1 tasks-db-
sudo k3s kubectl taint node k3s-cp node-role.kubernetes.io/control-plane-
```
