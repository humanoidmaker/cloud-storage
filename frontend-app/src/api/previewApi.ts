import client from './client';

export const previewApi = {
  getThumbnail: (fileId: string) => client.get<{ thumbnail_url: string }>(`/api/files/${fileId}/thumbnail`),
  getPreview: (fileId: string) =>
    client.get<{ preview_url: string; mime_type: string; name: string; size: number }>(`/api/files/${fileId}/preview`),
};
