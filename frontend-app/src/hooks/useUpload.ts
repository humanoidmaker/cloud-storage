import { useState, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { filesApi } from '../api/filesApi';
import type { UploadProgress } from '../types/file';

export function useUpload() {
  const [uploads, setUploads] = useState<UploadProgress[]>([]);
  const qc = useQueryClient();

  const uploadFile = useCallback(async (file: File, parentFolderId?: string) => {
    const id = `${Date.now()}-${file.name}`;
    const entry: UploadProgress = { id, file, progress: 0, status: 'pending' };
    setUploads((prev) => [...prev, entry]);

    try {
      setUploads((prev) => prev.map((u) => (u.id === id ? { ...u, status: 'uploading' } : u)));
      await filesApi.upload(file, parentFolderId, (pct) => {
        setUploads((prev) => prev.map((u) => (u.id === id ? { ...u, progress: pct } : u)));
      });
      setUploads((prev) => prev.map((u) => (u.id === id ? { ...u, progress: 100, status: 'complete' } : u)));
      qc.invalidateQueries({ queryKey: ['folder-contents'] });
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Upload failed';
      setUploads((prev) => prev.map((u) => (u.id === id ? { ...u, status: 'error', error: msg } : u)));
    }
  }, [qc]);

  const uploadFiles = useCallback(async (files: File[], parentFolderId?: string) => {
    for (const file of files) {
      await uploadFile(file, parentFolderId);
    }
  }, [uploadFile]);

  const cancelUpload = useCallback((id: string) => {
    setUploads((prev) => prev.filter((u) => u.id !== id));
  }, []);

  const clearCompleted = useCallback(() => {
    setUploads((prev) => prev.filter((u) => u.status !== 'complete'));
  }, []);

  return { uploads, uploadFile, uploadFiles, cancelUpload, clearCompleted };
}
