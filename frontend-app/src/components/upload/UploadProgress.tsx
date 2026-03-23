import React from 'react';
import { X, Check, AlertCircle, Loader2 } from 'lucide-react';
import type { UploadProgress as UploadProgressType } from '../../types/file';

interface UploadProgressProps {
  uploads: UploadProgressType[];
  onCancel: (id: string) => void;
  onClearCompleted: () => void;
}

export const UploadProgress: React.FC<UploadProgressProps> = ({ uploads, onCancel, onClearCompleted }) => {
  if (!uploads.length) return null;
  return (
    <div className="fixed bottom-4 right-4 w-96 bg-white dark:bg-gray-800 rounded-xl shadow-xl border border-gray-200 dark:border-gray-700 overflow-hidden z-40" data-testid="upload-progress">
      <div className="flex items-center justify-between px-4 py-3 bg-gray-50 dark:bg-gray-700 border-b border-gray-200 dark:border-gray-600">
        <span className="text-sm font-medium text-gray-900 dark:text-white">Uploads ({uploads.length})</span>
        <button onClick={onClearCompleted} className="text-xs text-blue-600 hover:underline">Clear completed</button>
      </div>
      <div className="max-h-60 overflow-y-auto divide-y divide-gray-100 dark:divide-gray-700">
        {uploads.map((u) => (
          <div key={u.id} className="flex items-center gap-3 px-4 py-2">
            <div className="flex-1 min-w-0">
              <p className="text-sm text-gray-900 dark:text-white truncate">{u.file.name}</p>
              <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-1.5 mt-1">
                <div className={`h-1.5 rounded-full transition-all ${u.status === 'error' ? 'bg-red-500' : 'bg-blue-500'}`} style={{ width: `${u.progress}%` }} />
              </div>
            </div>
            {u.status === 'uploading' && <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />}
            {u.status === 'complete' && <Check className="h-4 w-4 text-green-500" />}
            {u.status === 'error' && <AlertCircle className="h-4 w-4 text-red-500" />}
            {(u.status === 'pending' || u.status === 'uploading') && (
              <button onClick={() => onCancel(u.id)} className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"><X className="h-3 w-3" /></button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
