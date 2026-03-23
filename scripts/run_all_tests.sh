#!/bin/bash
set -e

echo "=========================================="
echo "  VAULTBOX -- FULL TEST SUITE"
echo "=========================================="

echo ""
echo ">>> Step 1: Python Linting (ruff)"
cd backend && ruff check . && cd ..

echo ""
echo ">>> Step 2: Python Type Checking (mypy)"
cd backend && mypy app --ignore-missing-imports && cd ..

echo ""
echo ">>> Step 3: TypeScript Type Checking (app frontend)"
cd frontend-app && npx tsc --noEmit && cd ..

echo ""
echo ">>> Step 4: TypeScript Type Checking (admin frontend)"
cd frontend-admin && npx tsc --noEmit && cd ..

echo ""
echo ">>> Step 5: ESLint (app frontend)"
cd frontend-app && npx eslint src --ext .ts,.tsx && cd ..

echo ""
echo ">>> Step 6: ESLint (admin frontend)"
cd frontend-admin && npx eslint src --ext .ts,.tsx && cd ..

echo ""
echo ">>> Step 7: Backend Unit Tests"
cd backend && python -m pytest tests/unit -v --tb=short && cd ..

echo ""
echo ">>> Step 8: Backend Integration Tests"
cd backend && python -m pytest tests/integration -v --tb=short && cd ..

echo ""
echo ">>> Step 9: Backend E2E Tests"
cd backend && python -m pytest tests/e2e -v --tb=short && cd ..

echo ""
echo ">>> Step 10: Backend Coverage Report"
cd backend && python -m pytest --cov=app --cov-report=term-missing --cov-fail-under=85 && cd ..

echo ""
echo ">>> Step 11: App Frontend Tests"
cd frontend-app && npx vitest run --reporter=verbose && cd ..

echo ""
echo ">>> Step 12: Admin Frontend Tests"
cd frontend-admin && npx vitest run --reporter=verbose && cd ..

echo ""
echo ">>> Step 13: K8s Manifest Validation"
./scripts/validate_k8s.sh

echo ""
echo "=========================================="
echo "  ALL TESTS PASSED"
echo "=========================================="
