import React from 'react';
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { tagsApi } from '../api/tagsApi';
import { FileIcon } from '../components/files/FileIcon';

export const TagFiles: React.FC = () => {
  const { tagId } = useParams<{ tagId: string }>();
  const { data: files = [], isLoading } = useQuery({ queryKey: ['tag-files', tagId], queryFn: () => tagsApi.getFilesByTag(tagId!).then((r) => r.data), enabled: !!tagId });

  return (
    <div>
      <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">Tagged Files</h2>
      {isLoading ? <p>Loading...</p> : files.length === 0 ? <p className="text-gray-500">No files with this tag</p> : (
        <div className="space-y-2">{files.map((f: Record<string, string | boolean | number | null>) => (
          <div key={f.id as string} className="flex items-center gap-4 p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
            <FileIcon mimeType={f.mime_type as string | null} isFolder={f.is_folder as boolean} className="h-8 w-8" />
            <p className="font-medium text-gray-900 dark:text-white">{f.name as string}</p>
          </div>
        ))}</div>
      )}
    </div>
  );
};
