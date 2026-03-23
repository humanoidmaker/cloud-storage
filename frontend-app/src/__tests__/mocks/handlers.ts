import { http, HttpResponse } from 'msw';

const API = 'http://localhost:8000';

export const handlers = [
  http.get(`${API}/api/auth/me`, () => HttpResponse.json({ id: '1', email: 'test@test.com', name: 'Test', role: 'user', storage_used: 1000, storage_quota: 5368709120, is_active: true, created_at: '2024-01-01', updated_at: '2024-01-01' })),
  http.post(`${API}/api/auth/login`, () => HttpResponse.json({ access_token: 'test-token', refresh_token: 'test-refresh', token_type: 'bearer' })),
  http.post(`${API}/api/auth/register`, () => HttpResponse.json({ id: '2', email: 'new@test.com', name: 'New' }, { status: 201 })),
  http.get(`${API}/api/folders/contents`, () => HttpResponse.json({ items: [
    { id: '1', name: 'Documents', is_folder: true, size: 0, mime_type: null, owner_id: '1', parent_folder_id: null, is_trashed: false, created_at: '2024-01-01', updated_at: '2024-01-01', thumbnail_key: null },
    { id: '2', name: 'photo.jpg', is_folder: false, size: 1024, mime_type: 'image/jpeg', owner_id: '1', parent_folder_id: null, is_trashed: false, created_at: '2024-01-01', updated_at: '2024-01-01', thumbnail_key: null },
  ], total: 2, page: 1, page_size: 50, total_pages: 1 })),
  http.get(`${API}/api/folders/tree`, () => HttpResponse.json([{ id: '1', name: 'Documents', children: [] }])),
  http.get(`${API}/api/stars`, () => HttpResponse.json([])),
  http.get(`${API}/api/trash`, () => HttpResponse.json({ items: [], total: 0, page: 1, page_size: 20 })),
  http.get(`${API}/api/tags`, () => HttpResponse.json([])),
  http.get(`${API}/api/shares/shared-with-me`, () => HttpResponse.json([])),
  http.get(`${API}/api/search`, () => HttpResponse.json({ items: [], total: 0, page: 1, page_size: 20, query: '' })),
  http.post(`${API}/api/shares`, () => HttpResponse.json({ id: 's1', file_id: '1', shared_by: '1', permission: 'view', share_token: 'abc123', has_password: false, created_at: '2024-01-01' }, { status: 201 })),
  http.post(`${API}/api/folders`, () => HttpResponse.json({ id: '3', name: 'New', is_folder: true }, { status: 201 })),
  http.post(`${API}/api/files/upload`, () => HttpResponse.json({ id: '3', name: 'test.txt', size: 100 }, { status: 201 })),
  http.get(`${API}/api/files/:id/versions`, () => HttpResponse.json([])),
  http.post(`${API}/api/auth/change-password`, () => HttpResponse.json({ message: 'OK' })),
];
