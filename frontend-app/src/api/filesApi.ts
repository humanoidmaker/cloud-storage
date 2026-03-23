import client from './client';
import type { FileItem } from '../types/file';

export const filesApi = {
  upload: (file: File, parentFolderId?: string, onProgress?: (pct: number) => void) => {
    const formData = new FormData();
    formData.append('file', file);
    if (parentFolderId) formData.append('parent_folder_id', parentFolderId);
    return client.post<FileItem>('/api/files/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (e) => { if (onProgress && e.total) onProgress(Math.round((e.loaded * 100) / e.total)); },
    });
  },
  getFile: (id: string) => client.get<FileItem>(`/api/files/${id}`),
  download: (id: string) => client.get(`/api/files/${id}/download`, { maxRedirects: 0, validateStatus: (s) => s === 302 }),
  rename: (id: string, name: string) => client.put<FileItem>(`/api/files/${id}`, { name }),
  move: (id: string, targetFolderId: string | null) => client.post(`/api/files/${id}/move`, { target_folder_id: targetFolderId }),
  copy: (id: string, targetFolderId?: string | null, newName?: string) =>
    client.post(`/api/files/${id}/copy`, { target_folder_id: targetFolderId, new_name: newName }),
  delete: (id: string) => client.delete(`/api/files/${id}`),
  bulkDelete: (fileIds: string[]) => client.post('/api/files/bulk/delete', { file_ids: fileIds }),
  bulkMove: (fileIds: string[], targetFolderId: string | null) =>
    client.post('/api/files/bulk/move', { file_ids: fileIds, target_folder_id: targetFolderId }),
  bulkDownload: (fileIds: string[]) => client.post('/api/files/bulk/download', { file_ids: fileIds }),
};
