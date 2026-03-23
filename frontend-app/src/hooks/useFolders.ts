import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { foldersApi } from '../api/foldersApi';

export function useBreadcrumb(folderId?: string) {
  return useQuery({
    queryKey: ['breadcrumb', folderId],
    queryFn: () => foldersApi.getBreadcrumb(folderId!).then((r) => r.data),
    enabled: !!folderId,
  });
}

export function useFolderTree() {
  return useQuery({
    queryKey: ['folder-tree'],
    queryFn: () => foldersApi.getTree().then((r) => r.data),
  });
}

export function useCreateFolder() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ name, parentId }: { name: string; parentId?: string }) => foldersApi.create(name, parentId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['folder-contents'] }),
  });
}
