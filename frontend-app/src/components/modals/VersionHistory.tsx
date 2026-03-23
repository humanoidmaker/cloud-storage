import React from 'react';
import { Download, RotateCcw, Trash2, X } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { versionsApi } from '../../api/versionsApi';

interface VersionHistoryProps { isOpen: boolean; fileId: string; onClose: () => void; }

export const VersionHistory: React.FC<VersionHistoryProps> = ({ isOpen, fileId, onClose }) => {
  const qc = useQueryClient();
  const { data: versions = [] } = useQuery({ queryKey: ['versions', fileId], queryFn: () => versionsApi.list(fileId).then((r) => r.data), enabled: isOpen });
  const restore = useMutation({ mutationFn: (vn: number) => versionsApi.restore(fileId, vn), onSuccess: () => qc.invalidateQueries({ queryKey: ['versions', fileId] }) });
  const del = useMutation({ mutationFn: (vn: number) => versionsApi.delete(fileId, vn), onSuccess: () => qc.invalidateQueries({ queryKey: ['versions', fileId] }) });

  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" data-testid="version-history">
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 w-full max-w-lg max-h-[70vh] flex flex-col" onClick={(e) => e.stopPropagation()}>
        <div className="flex justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Version History</h3>
          <button onClick={onClose}><X className="h-5 w-5" /></button>
        </div>
        <div className="flex-1 overflow-y-auto space-y-2">
          {versions.map((v) => (
            <div key={v.id} className="flex items-center justify-between p-3 rounded-lg border border-gray-200 dark:border-gray-700">
              <div>
                <p className="text-sm font-medium text-gray-900 dark:text-white">Version {v.version_number}</p>
                <p className="text-xs text-gray-500">{new Date(v.created_at).toLocaleString()}</p>
              </div>
              <div className="flex gap-1">
                <button onClick={() => window.open(`/api/files/${fileId}/versions/${v.version_number}/download`)} className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded" title="Download"><Download className="h-4 w-4" /></button>
                <button onClick={() => restore.mutate(v.version_number)} className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded" title="Restore"><RotateCcw className="h-4 w-4" /></button>
                <button onClick={() => del.mutate(v.version_number)} className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded text-red-500" title="Delete"><Trash2 className="h-4 w-4" /></button>
              </div>
            </div>
          ))}
          {!versions.length && <p className="text-center text-gray-500 py-4">No previous versions</p>}
        </div>
      </div>
    </div>
  );
};
