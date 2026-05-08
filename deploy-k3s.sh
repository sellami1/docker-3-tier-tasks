#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

kubectl apply -f "$ROOT_DIR/k3s/namespace.yaml"
kubectl apply -f "$ROOT_DIR/k3s/storageclass.yaml"

kubectl apply -f "$ROOT_DIR/k3s/configmaps/"
kubectl apply -f "$ROOT_DIR/k3s/secrets/"
kubectl apply -f "$ROOT_DIR/k3s/mongo-pvc.yaml"

kubectl apply -f "$ROOT_DIR/k3s/services/database-headless-service.yaml"
kubectl apply -f "$ROOT_DIR/k3s/services/database-service.yaml"
kubectl apply -f "$ROOT_DIR/k3s/deployments/database-statefulset.yaml"

kubectl apply -f "$ROOT_DIR/k3s/deployments/backend-deployment.yaml"
kubectl apply -f "$ROOT_DIR/k3s/services/backend-service.yaml"
kubectl apply -f "$ROOT_DIR/k3s/deployments/frontend-deployment.yaml"
kubectl apply -f "$ROOT_DIR/k3s/services/frontend-service.yaml"

kubectl apply -f "$ROOT_DIR/k3s/ingress.yaml"
kubectl apply -f "$ROOT_DIR/k3s/backend-hpa.yaml"
kubectl apply -f "$ROOT_DIR/k3s/networkpolicy.yaml"