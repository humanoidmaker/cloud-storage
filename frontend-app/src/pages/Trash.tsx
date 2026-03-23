import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { trashApi } from '../api/trashApi';
import { FileIcon } from '../components/files/FileIcon';
import { RotateCcw, Trash2 } from 'lucide-react';

export const Trash: React.FC = () => {
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({ queryKey: ['trash'], queryFn: () => trashApi.list().then((r) => r.data) });
  const restore = useMutation({ mutationFn: (id: string) => trashApi.restore(id), onSuccess: () => qc.invalidateQueries({ queryKey: ['trash'] }) });
  const permDelete = useMutation({ mutationFn: (id: string) => trashApi.permanentDelete(id), onSuccess: () => qc.invalidateQueries({ queryKey: ['trash'] }) });
  const emptyTrash = useMutation({ mutationFn: () => trashApi.emptyTrash(), onSuccess: () => qc.invalidateQueries({ queryKey: ['trash'] }) });
  const items = data?.items || [];

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Trash</h2>
        {items.length > 0 && <button onClick={() => emptyTrash.mutate()} className="px-4 py-2 text-sm text-red-600 border border-red-600 rounded-lg hover:bg-red-50">Empty Trash</button>}
      </div>
      {isLoading ? <p>Loading...</p> : items.length === 0 ? <p className="text-gray-500">Trash is empty</p> : (
        <div className="space-y-2">{items.map((f) => (
          <div key={f.id} className="flex items-center gap-4 p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
            <FileIcon mimeType={f.mime_type} isFolder={f.is_folder} className="h-8 w-8" />
            <div className="flex-1"><p className="font-medium text-gray-900 dark:text-white">{f.name}</p><p className="text-xs text-gray-500">Trashed {f.trashed_at ? new Date(f.trashed_at).toLocaleDateString() : ''}</p></div>
            <button onClick={() => restore.mutate(f.id)} className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded" title="Restore"><RotateCcw className="h-4 w-4 text-green-600" /></button>
            <button onClick={() => permDelete.mutate(f.id)} className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded" title="Delete forever"><Trash2 className="h-4 w-4 text-red-600" /></button>
          </div>
        ))}</div>
      )}
    </div>
  );
};
