import client from './client';
import type { FileItem } from '../types/file';
import type { PaginatedResponse } from '../types/common';

export const trashApi = {
  list: (page = 1, pageSize = 20) =>
    client.get<PaginatedResponse<FileItem>>('/api/trash', { params: { page, page_size: pageSize } }),
  restore: (fileId: string) => client.post(`/api/trash/${fileId}/restore`),
  permanentDelete: (fileId: string) => client.delete(`/api/trash/${fileId}`),
  emptyTrash: () => client.post('/api/trash/empty'),
};
