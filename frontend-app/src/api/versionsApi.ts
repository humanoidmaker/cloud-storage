import client from './client';
import type { FileVersion } from '../types/file';

export const versionsApi = {
  list: (fileId: string) => client.get<FileVersion[]>(`/api/files/${fileId}/versions`),
  download: (fileId: string, versionNumber: number) =>
    client.get(`/api/files/${fileId}/versions/${versionNumber}/download`, { maxRedirects: 0, validateStatus: (s) => s === 302 }),
  restore: (fileId: string, versionNumber: number) =>
    client.post(`/api/files/${fileId}/versions/${versionNumber}/restore`),
  delete: (fileId: string, versionNumber: number) =>
    client.delete(`/api/files/${fileId}/versions/${versionNumber}`),
};
