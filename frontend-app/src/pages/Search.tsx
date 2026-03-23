import React from 'react';
import { useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { searchApi } from '../api/searchApi';
import { FileIcon } from '../components/files/FileIcon';

export const Search: React.FC = () => {
  const [params] = useSearchParams();
  const q = params.get('q') || '';
  const { data, isLoading } = useQuery({ queryKey: ['search', q], queryFn: () => searchApi.search({ q }).then((r) => r.data), enabled: !!q });
  const items = data?.items || [];

  return (
    <div>
      <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">Search results for "{q}"</h2>
      <p className="text-sm text-gray-500 mb-6">{data?.total || 0} results</p>
      {isLoading ? <p>Searching...</p> : items.length === 0 ? <p className="text-gray-500">No results found</p> : (
        <div className="space-y-2">{items.map((f: Record<string, string | boolean | number | null>) => (
          <div key={f.id as string} className="flex items-center gap-4 p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
            <FileIcon mimeType={f.mime_type as string | null} isFolder={f.is_folder as boolean} className="h-8 w-8" />
            <div className="flex-1"><p className="font-medium text-gray-900 dark:text-white">{f.name as string}</p></div>
          </div>
        ))}</div>
      )}
    </div>
  );
};
