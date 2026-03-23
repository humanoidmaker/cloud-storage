#!/bin/bash
set -e

echo "=========================================="
echo "  VAULTBOX — Kubernetes Deployment"
echo "=========================================="

echo ">>> Applying namespace..."
kubectl apply -f k8s/namespace.yaml

echo ">>> Applying secrets and configmap..."
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/configmap.yaml

echo ">>> Deploying PostgreSQL..."
kubectl apply -f k8s/postgres/

echo ">>> Deploying Redis..."
kubectl apply -f k8s/redis/

echo ">>> Deploying MinIO..."
kubectl apply -f k8s/minio/

echo ">>> Waiting for databases to be ready..."
kubectl -n cloud_storage wait --for=condition=ready pod -l app=postgres --timeout=120s
kubectl -n cloud_storage wait --for=condition=ready pod -l app=redis --timeout=60s

echo ">>> Deploying Backend API..."
kubectl apply -f k8s/backend/

echo ">>> Deploying Celery Worker..."
kubectl apply -f k8s/celery-worker/

echo ">>> Deploying Celery Beat..."
kubectl apply -f k8s/celery-beat/

echo ">>> Waiting for backend to be ready..."
kubectl -n cloud_storage wait --for=condition=ready pod -l app=backend --timeout=120s

echo ">>> Deploying Frontend App..."
kubectl apply -f k8s/frontend-app/

echo ">>> Deploying Frontend Admin..."
kubectl apply -f k8s/frontend-admin/

echo ">>> Applying Ingress..."
kubectl apply -f k8s/ingress.yaml

echo ""
echo "=========================================="
echo "  Cloud Storage Deployed Successfully!"
echo "=========================================="
echo "  App:     https://app.cloud_storage.local"
echo "  Admin:   https://admin.cloud_storage.local"
echo "  API:     https://api.cloud_storage.local"
echo "  MinIO:   https://storage.cloud_storage.local"
echo "=========================================="
