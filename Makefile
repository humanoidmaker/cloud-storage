.PHONY: dev down build push deploy logs seed init-storage test test-backend test-app test-admin test-cover lint validate-k8s ci clean

dev:
	docker-compose up --build

down:
	docker-compose down -v

build:
	docker build -t vaultbox-backend ./backend
	docker build -t vaultbox-frontend-app ./frontend-app
	docker build -t vaultbox-frontend-admin ./frontend-admin

push:
	docker push vaultbox-backend:latest
	docker push vaultbox-frontend-app:latest
	docker push vaultbox-frontend-admin:latest

deploy:
	./k8s/deploy.sh

logs:
	docker-compose logs -f

seed:
	cd backend && python ../scripts/seed_admin.py

init-storage:
	cd backend && python ../scripts/init_minio_buckets.py

test:
	./scripts/run_all_tests.sh

test-backend:
	cd backend && python -m pytest tests/ -v --cov=app --cov-report=term-missing

test-app:
	cd frontend-app && npx vitest run --reporter=verbose

test-admin:
	cd frontend-admin && npx vitest run --reporter=verbose

test-cover:
	cd backend && python -m pytest --cov=app --cov-report=html --cov-fail-under=85

lint:
	cd backend && ruff check .
	cd frontend-app && npx eslint src --ext .ts,.tsx
	cd frontend-admin && npx eslint src --ext .ts,.tsx

validate-k8s:
	./scripts/validate_k8s.sh

ci: lint test validate-k8s

clean:
	docker-compose down -v --rmi all --remove-orphans
	rm -rf backend/__pycache__ backend/.pytest_cache
	rm -rf frontend-app/node_modules frontend-app/dist
	rm -rf frontend-admin/node_modules frontend-admin/dist
