# K3s Deployment and Test Plan

## Directory Structure

```
k3s/
├── deployments/
│   ├── backend-deployment.yaml
│   ├── frontend-deployment.yaml
│   └── database-statefulset.yaml
├── services/
│   ├── backend-service.yaml
│   ├── frontend-service.yaml
│   ├── database-service.yaml
│   └── database-headless-service.yaml
├── configmaps/
│   └── configmap.yaml
├── secrets/
│   └── secret.yaml
├── namespace.yaml
├── storageclass.yaml
├── mongo-pvc.yaml
├── ingress.yaml
├── backend-hpa.yaml
├── networkpolicy.yaml
└── deploy-and-test-plan.md
```

## Deployment Steps

1. Ensure the `tasks-app` namespace and `local-path` StorageClass exist.
   ```bash
   kubectl apply -f k3s/namespace.yaml
   kubectl apply -f k3s/storageclass.yaml
   ```

2. Apply shared config, secrets, and storage objects.
   ```bash
   kubectl apply -f k3s/configmaps/
   kubectl apply -f k3s/secrets/
   kubectl apply -f k3s/mongo-pvc.yaml
   ```

3. Apply the database headless service and StatefulSet.
   ```bash
   kubectl apply -f k3s/services/database-headless-service.yaml
   kubectl apply -f k3s/services/database-service.yaml
   kubectl apply -f k3s/deployments/database-statefulset.yaml
   ```

4. Apply backend and frontend workloads and services.
   ```bash
   kubectl apply -f k3s/deployments/backend-deployment.yaml
   kubectl apply -f k3s/services/backend-service.yaml
   kubectl apply -f k3s/deployments/frontend-deployment.yaml
   kubectl apply -f k3s/services/frontend-service.yaml
   ```

5. Apply public ingress, HPA, and NetworkPolicies.
   ```bash
   kubectl apply -f k3s/ingress.yaml
   kubectl apply -f k3s/backend-hpa.yaml
   kubectl apply -f k3s/networkpolicy.yaml
   ```

## Verification

6. Verify rollout with:
   ```bash
   kubectl get pods,svc,ingress,pvc -n tasks-app
   kubectl rollout status sts/database -n tasks-app
   kubectl rollout status deploy/backend deploy/frontend -n tasks-app
   ```

7. Test backend health and CRUD:
   ```bash
   kubectl port-forward -n tasks-app svc/backend 3000:3000
   curl http://localhost:3000/health
   ```

8. Test resilience by deleting one pod and confirming recovery:
   ```bash
   kubectl delete pod -n tasks-app <pod-name>
   kubectl get pods -n tasks-app
   ```

9. Check logs and events:
   ```bash
   kubectl logs -n tasks-app <pod-name>
   kubectl describe pod -n tasks-app <pod-name>
   ```

## Expected Access Points

- Frontend NodePort: `http://<control-plane-external-ip>:30080`
- Ingress host: `tasks.local` (if DNS is configured)
- Backend health: `http://<backend-pod>:3000/health`

## Cleanup

To remove old flat manifest files from the root k3s/ directory, delete:
- k3s/backend-deployment.yaml
- k3s/frontend-deployment.yaml
- k3s/database-deployment.yaml
- k3s/backend-service.yaml
- k3s/frontend-service.yaml
- k3s/database-service.yaml
- k3s/database-headless-service.yaml
- k3s/configmap.yaml
- k3s/secret.yaml
