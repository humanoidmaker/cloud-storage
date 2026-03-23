import client from './client';
import type { FileItem, BreadcrumbItem, FolderTreeNode } from '../types/file';
import type { PaginatedResponse } from '../types/common';

export const foldersApi = {
  create: (name: string, parentFolderId?: string) =>
    client.post('/api/folders', { name, parent_folder_id: parentFolderId }),
  getContents: (folderId?: string, sortBy = 'name', sortOrder = 'asc', page = 1, pageSize = 50) => {
    const path = folderId ? `/api/folders/${folderId}/contents` : '/api/folders/contents';
    return client.get<PaginatedResponse<FileItem>>(path, { params: { sort_by: sortBy, sort_order: sortOrder, page, page_size: pageSize } });
  },
  getBreadcrumb: (folderId: string) => client.get<BreadcrumbItem[]>(`/api/folders/${folderId}/breadcrumb`),
  getTree: () => client.get<FolderTreeNode[]>('/api/folders/tree'),
  rename: (id: string, name: string) => client.put(`/api/folders/${id}`, { name }),
  move: (id: string, targetFolderId: string | null) => client.post(`/api/folders/${id}/move`, { target_folder_id: targetFolderId }),
  delete: (id: string) => client.delete(`/api/folders/${id}`),
};
