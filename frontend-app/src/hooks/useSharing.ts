import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { sharingApi } from '../api/sharingApi';
import type { ShareCreateRequest } from '../types/share';

export function useSharesForFile(fileId: string) {
  return useQuery({
    queryKey: ['shares', fileId],
    queryFn: () => sharingApi.listForFile(fileId).then((r) => r.data),
    enabled: !!fileId,
  });
}

export function useSharedWithMe() {
  return useQuery({
    queryKey: ['shared-with-me'],
    queryFn: () => sharingApi.sharedWithMe().then((r) => r.data),
  });
}

export function useCreateShare() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: ShareCreateRequest) => sharingApi.create(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['shares'] }),
  });
}
