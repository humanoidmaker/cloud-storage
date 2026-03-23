import client from './client';
import type { Tag } from '../types/common';
import type { FileItem } from '../types/file';

export const tagsApi = {
  create: (name: string, color: string) => client.post<Tag>('/api/tags', { name, color }),
  list: () => client.get<Tag[]>('/api/tags'),
  update: (id: string, data: { name?: string; color?: string }) => client.put(`/api/tags/${id}`, data),
  delete: (id: string) => client.delete(`/api/tags/${id}`),
  tagFile: (fileId: string, tagId: string) => client.post(`/api/tags/files/${fileId}/tags/${tagId}`),
  untagFile: (fileId: string, tagId: string) => client.delete(`/api/tags/files/${fileId}/tags/${tagId}`),
  getFilesByTag: (tagId: string) => client.get<FileItem[]>(`/api/tags/${tagId}/files`),
};
