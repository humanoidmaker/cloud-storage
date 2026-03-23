import { http, HttpResponse } from 'msw';
const API = 'http://localhost:8000';
export const handlers = [
  http.get(API + '/api/auth/me', () => HttpResponse.json({ id: '1', email: 'admin@test.com', name: 'Admin', role: 'superadmin', storage_used: 0, storage_quota: 0, is_active: true })),
  http.post(API + '/api/auth/login', () => HttpResponse.json({ access_token: 'tok', refresh_token: 'ref', token_type: 'bearer' })),
  http.get(API + '/api/admin/dashboard', () => HttpResponse.json({ total_users: 10, active_users: 5, total_storage_used: 1000000, total_files: 100, total_shares: 20, recent_activity: [], user_growth: [], storage_trend: [] })),
  http.get(API + '/api/admin/users', () => HttpResponse.json({ items: [], total: 0 })),
  http.get(API + '/api/admin/storage/breakdown', () => HttpResponse.json([])),
  http.get(API + '/api/admin/storage/top-consumers', () => HttpResponse.json([])),
  http.get(API + '/api/admin/storage/trends', () => HttpResponse.json([])),
  http.get(API + '/api/admin/activity', () => HttpResponse.json({ items: [], total: 0 })),
  http.get(API + '/api/admin/system/health', () => HttpResponse.json({ minio: { status: 'healthy', color: 'green' }, postgres: { status: 'healthy', color: 'green' }, redis: { status: 'healthy', color: 'green' }, celery: { status: 'healthy', color: 'green' }, api: { status: 'healthy', color: 'green' } })),
  http.get(API + '/api/admin/settings', () => HttpResponse.json({ default_quota_bytes: 5368709120, max_upload_size_bytes: 5368709120, allowed_extensions: '', registration_enabled: true, trash_auto_purge_days: 30, max_file_versions: 10 })),
  http.get(API + '/api/admin/files', () => HttpResponse.json([])),
];
