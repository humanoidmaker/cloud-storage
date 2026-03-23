import client from './client';
import type { FileItem } from '../types/file';

export const starsApi = {
  star: (fileId: string) => client.post(`/api/stars/${fileId}`),
  unstar: (fileId: string) => client.delete(`/api/stars/${fileId}`),
  list: () => client.get<FileItem[]>('/api/stars'),
};
