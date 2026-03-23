import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { starsApi } from '../api/starsApi';
import { FileIcon } from '../components/files/FileIcon';
import { Star } from 'lucide-react';

export const Starred: React.FC = () => {
  const { data: items = [], isLoading } = useQuery({ queryKey: ['starred'], queryFn: () => starsApi.list().then((r) => r.data) });
  const qc = useQueryClient();
  const unstar = useMutation({ mutationFn: (id: string) => starsApi.unstar(id), onSuccess: () => qc.invalidateQueries({ queryKey: ['starred'] }) });

  return (
    <div>
      <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">Starred</h2>
      {isLoading ? <p className="text-gray-500">Loading...</p> : items.length === 0 ? <p className="text-gray-500">No starred files</p> : (
        <div className="space-y-2">{items.map((f: Record<string, string | boolean | number | null>) => (
          <div key={f.id as string} className="flex items-center gap-4 p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
            <FileIcon mimeType={f.mime_type as string | null} isFolder={f.is_folder as boolean} className="h-8 w-8" />
            <div className="flex-1"><p className="font-medium text-gray-900 dark:text-white">{f.name as string}</p></div>
            <button onClick={() => unstar.mutate(f.id as string)} className="p-1 text-yellow-500 hover:text-gray-400"><Star className="h-5 w-5 fill-current" /></button>
          </div>
        ))}</div>
      )}
    </div>
  );
};
