import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { filesApi } from '../api/filesApi';
import { foldersApi } from '../api/foldersApi';
import type { SortField, SortOrder } from '../types/file';

export function useFolderContents(folderId?: string, sortBy: SortField = 'name', sortOrder: SortOrder = 'asc', page = 1) {
  return useQuery({
    queryKey: ['folder-contents', folderId, sortBy, sortOrder, page],
    queryFn: () => foldersApi.getContents(folderId, sortBy, sortOrder, page).then((r) => r.data),
  });
}

export function useFileDetails(fileId: string) {
  return useQuery({
    queryKey: ['file', fileId],
    queryFn: () => filesApi.getFile(fileId).then((r) => r.data),
    enabled: !!fileId,
  });
}

export function useDeleteFile() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => filesApi.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['folder-contents'] }),
  });
}

export function useRenameFile() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, name }: { id: string; name: string }) => filesApi.rename(id, name),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['folder-contents'] }),
  });
}

export function useMoveFile() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, targetFolderId }: { id: string; targetFolderId: string | null }) => filesApi.move(id, targetFolderId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['folder-contents'] }),
  });
}

export function useCopyFile() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, targetFolderId }: { id: string; targetFolderId?: string | null }) => filesApi.copy(id, targetFolderId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['folder-contents'] }),
  });
}

export function useBulkDelete() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (ids: string[]) => filesApi.bulkDelete(ids),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['folder-contents'] }),
  });
}
