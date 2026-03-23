# Cloud Storage - Self-Hosted Cloud Storage Service

A production-grade, self-hosted file management platform with sharing, collaboration, real-time sync, and full admin controls.

## Tech Stack

- **Backend**: Python 3.12, FastAPI, SQLAlchemy (async), PostgreSQL 16, Redis 7, Celery
- **Storage**: MinIO (S3-compatible object storage)
- **User Frontend**: React 18, TypeScript, Vite, TailwindCSS
- **Admin Dashboard**: React 18, TypeScript, Vite, TailwindCSS, Recharts
- **Infrastructure**: Docker, Docker Compose, Kubernetes

## Quick Start

```bash
# Start all services with Docker Compose
make dev

# Seed admin user
make seed

# Initialize MinIO buckets
make init-storage
```

Services:
- **API**: http://localhost:8000
- **User App**: http://localhost:3000
- **Admin Dashboard**: http://localhost:3001
- **MinIO Console**: http://localhost:9001

Default admin: `admin@cloud_storage.local` / `admin123`

## Development

```bash
# Run all tests
make test

# Run backend tests only
make test-backend

# Run linting
make lint

# Run full CI pipeline
make ci
```

## Project Structure

```
cloud_storage/
├── backend/          # FastAPI backend
├── frontend-app/     # User-facing file manager
├── frontend-admin/   # Admin dashboard
├── k8s/              # Kubernetes manifests
├── scripts/          # Utility scripts
├── docker-compose.yml
└── Makefile
```

## Features

- File upload/download with chunked upload support
- Folder management with unlimited nesting
- File sharing (users + public links with password/expiry)
- File versioning
- Thumbnail generation
- Full-text search
- Stars and tags
- Trash with auto-purge
- Activity logging
- Admin dashboard with user management, storage analytics, system health
- JWT authentication with role-based access control

## Kubernetes Deployment

```bash
make deploy
```

## Environment Variables

See `backend/app/config.py` for all configuration options. All settings can be overridden via environment variables with the `VAULTBOX_` prefix.
