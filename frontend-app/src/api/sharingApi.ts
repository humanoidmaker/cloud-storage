import client from './client';
import type { Share, SharedFile, ShareCreateRequest } from '../types/share';

export const sharingApi = {
  create: (data: ShareCreateRequest) => client.post<Share>('/api/shares', data),
  listForFile: (fileId: string) => client.get<Share[]>(`/api/shares/file/${fileId}`),
  sharedWithMe: () => client.get<SharedFile[]>('/api/shares/shared-with-me'),
  update: (shareId: string, permission: string) => client.put(`/api/shares/${shareId}`, { permission }),
  revoke: (shareId: string) => client.delete(`/api/shares/${shareId}`),
  accessLink: (token: string, password?: string) =>
    client.get(`/api/shares/link/${token}`, { params: password ? { password } : {} }),
};
