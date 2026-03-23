import React from 'react';
import { useSharedWithMe } from '../hooks/useSharing';
import { FileIcon } from '../components/files/FileIcon';

export const SharedWithMe: React.FC = () => {
  const { data: shared = [], isLoading } = useSharedWithMe();
  return (
    <div>
      <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">Shared with Me</h2>
      {isLoading ? <p className="text-gray-500">Loading...</p> : shared.length === 0 ? <p className="text-gray-500">No files shared with you</p> : (
        <div className="space-y-2">
          {shared.map((item, i) => (
            <div key={i} className="flex items-center gap-4 p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
              <FileIcon mimeType={item.file?.mime_type || null} isFolder={item.file?.is_folder || false} className="h-8 w-8" />
              <div className="flex-1">
                <p className="font-medium text-gray-900 dark:text-white">{item.file?.name || 'Unknown'}</p>
                <p className="text-xs text-gray-500">Shared by {item.shared_by_name} - {item.permission}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
