#!/bin/bash
set -e

case "$1" in
    api)
        echo "Starting Cloud Storage API server..."
        exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
        ;;
    api-dev)
        echo "Starting Cloud Storage API server (development)..."
        exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
        ;;
    celery-worker)
        echo "Starting Celery worker..."
        exec celery -A app.tasks.celery_app worker --loglevel=info --concurrency=4
        ;;
    celery-beat)
        echo "Starting Celery beat scheduler..."
        exec celery -A app.tasks.celery_app beat --loglevel=info
        ;;
    migrate)
        echo "Running database migrations..."
        exec alembic upgrade head
        ;;
    *)
        exec "$@"
        ;;
esac
