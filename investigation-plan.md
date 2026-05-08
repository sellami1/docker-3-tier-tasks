# K3s App Deployment: Investigation & Implementation Plan

## 1. Issue: Frontend and Backend Pods (`ErrImageNeverPull`)

**Observation**: 
The frontend and backend pods immediately fail with the `ErrImageNeverPull` status.

**Root Cause Hypothesis**: 
The manifests for the frontend and backend deployments use `imagePullPolicy: Never`. While you noted that the images are available locally on each node, K3s uses `containerd` as its default container runtime, which maintains a completely separate image registry from the `docker` daemon. 
If the images were built using `docker build` (or pulled with `docker pull`), they reside in Docker's local cache. Because K3s's containerd (`k8s.io` namespace) cannot see Docker's images, Kubelet cannot find them and immediately errors out.

**Investigation Steps**:
1. Check if the images are actually in the K3s containerd registry:
   ```bash
   sudo k3s crictl images | grep docker-3-tier-tasks
   # OR
   sudo k3s ctr images ls -n k8s.io | grep docker-3-tier-tasks
   ```
2. Verify if the images are located in the Docker registry instead:
   ```bash
   sudo docker images | grep docker-3-tier-tasks
   ```
3. Inspect the Pod events to confirm Kubelet's exact error:
   ```bash
   kubectl describe pod -l app.kubernetes.io/component=backend -n tasks-app
   ```

**Solutions**:
* **Option A (Recommended): Import Docker images into K3s containerd**.
  Export the images from Docker and import them directly into K3s's containerd on each worker/control-plane node where the pods might run:
  ```bash
  docker save docker-3-tier-tasks-frontend:latest | sudo k3s ctr images import -
  docker save docker-3-tier-tasks-backend:latest | sudo k3s ctr images import -
  ```
* **Option B: Push to a Local/Private Registry**.
  Tag your images and push them to a local registry (like a registry container running on your LAN) and update the manifests to pull from there, removing `imagePullPolicy: Never`.

---

## 2. Issue: Database Pod (`ContainerCreating`)

**Observation**: 
The `database-0` pod is stuck in the `ContainerCreating` state for over 2 minutes. The `mongo-data` PVC is already Bound, meaning storage provisioning is successful.

**Root Cause Hypothesis**:
1. **Image Pulling Delay**: The `database-statefulset.yaml` uses `image: mongo:7.0` with `imagePullPolicy: IfNotPresent`. Just like the frontend/backend images, if `mongo:7.0` was only pulled via Docker, K3s containerd cannot see it. Because the policy is `IfNotPresent` (instead of `Never`), K3s will attempt to download the ~700MB image from Docker Hub over the internet. On a VM network, this can easily take several minutes, causing it to sit in `ContainerCreating`.
2. **Volume Permission Issue**: The StatefulSet enforces `runAsNonRoot: true` and `fsGroup: 999`. If the K3s local-path provisioner has trouble applying the `fsGroup` permissions to the underlying host directory, Kubelet will be unable to mount the volume.

**Investigation Steps**:
1. Describe the pod to read the bottom event log:
   ```bash
   kubectl describe pod database-0 -n tasks-app
   ```
   *If the events show `Pulling image "mongo:7.0"`, K3s is just downloading it and you need to wait. If it shows `FailedMount`, it's a permission issue.*
2. Verify if the `mongo:7.0` image exists in K3s containerd:
   ```bash
   sudo k3s crictl images | grep mongo
   ```

**Solutions**:
* **If it's an image pulling issue**:
  Simply wait for the download to finish, OR speed it up by importing the image from Docker to K3s manually:
  ```bash
  docker save mongo:7.0 | sudo k3s ctr images import -
  ```
* **If it's a volume permission issue**:
  Ensure the host path underlying the `app-local-path` storage class supports `chown` operations, or adjust the pod's `securityContext` if the provisioner requires an init container to fix directory permissions.

---

## 3. General Validation Steps (Post-Fix)

Once the images are properly loaded into K3s containerd:
1. Delete the failed pods to force a rapid restart:
   ```bash
   kubectl delete pods --all -n tasks-app
   ```
2. Monitor pod startup to ensure they reach the `Running` state:
   ```bash
   kubectl get pods -n tasks-app -w
   ```
3. Check application logs for any internal runtime errors (like DB connection failures):
   ```bash
   kubectl logs -l app.kubernetes.io/component=backend -n tasks-app
   ```
4. Verify ingress access by navigating to `http://tasks.local` from a machine that has `tasks.local` mapped to the K3s ingress node IP.
