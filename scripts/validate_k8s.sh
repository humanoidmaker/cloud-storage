#!/bin/bash
set -e

echo "=========================================="
echo "  K8s Manifest Validation"
echo "=========================================="

PASS=0
FAIL=0

check() {
    local desc="$1"
    local file="$2"
    if [ -f "$file" ]; then
        if command -v kubectl &> /dev/null; then
            if kubectl apply --dry-run=client -f "$file" > /dev/null 2>&1; then
                echo "  PASS: $desc"
                PASS=$((PASS + 1))
            else
                echo "  FAIL: $desc"
                FAIL=$((FAIL + 1))
            fi
        else
            # No kubectl, just check YAML syntax
            if python3 -c "import yaml; yaml.safe_load(open('$file'))" 2>/dev/null; then
                echo "  PASS: $desc (syntax only)"
                PASS=$((PASS + 1))
            else
                echo "  FAIL: $desc (invalid YAML)"
                FAIL=$((FAIL + 1))
            fi
        fi
    else
        echo "  SKIP: $desc (file not found)"
    fi
}

check "Namespace" "k8s/namespace.yaml"
check "Secrets" "k8s/secrets.yaml"
check "ConfigMap" "k8s/configmap.yaml"
check "PostgreSQL Deployment" "k8s/postgres/deployment.yaml"
check "PostgreSQL Service" "k8s/postgres/service.yaml"
check "PostgreSQL PVC" "k8s/postgres/pvc.yaml"
check "Redis Deployment" "k8s/redis/deployment.yaml"
check "Redis Service" "k8s/redis/service.yaml"
check "MinIO StatefulSet" "k8s/minio/statefulset.yaml"
check "MinIO Service" "k8s/minio/service.yaml"
check "MinIO PVC" "k8s/minio/pvc.yaml"
check "Backend Deployment" "k8s/backend/deployment.yaml"
check "Backend Service" "k8s/backend/service.yaml"
check "Backend HPA" "k8s/backend/hpa.yaml"
check "Celery Worker Deployment" "k8s/celery-worker/deployment.yaml"
check "Celery Worker HPA" "k8s/celery-worker/hpa.yaml"
check "Celery Beat Deployment" "k8s/celery-beat/deployment.yaml"
check "Frontend App Deployment" "k8s/frontend-app/deployment.yaml"
check "Frontend App Service" "k8s/frontend-app/service.yaml"
check "Frontend Admin Deployment" "k8s/frontend-admin/deployment.yaml"
check "Frontend Admin Service" "k8s/frontend-admin/service.yaml"
check "Ingress" "k8s/ingress.yaml"

echo ""
echo "Results: $PASS passed, $FAIL failed"

if [ $FAIL -gt 0 ]; then
    exit 1
fi
