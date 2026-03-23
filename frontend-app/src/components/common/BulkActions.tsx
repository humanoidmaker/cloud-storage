import React from 'react';
import { Download, FolderInput, Trash2, Share2, Tag, X } from 'lucide-react';

interface BulkActionsProps { count: number; onMove: () => void; onDelete: () => void; onShare: () => void; onTag: () => void; onDownload: () => void; onClear: () => void; }

export const BulkActions: React.FC<BulkActionsProps> = ({ count, onMove, onDelete, onShare, onTag, onDownload, onClear }) => {
  if (count === 0) return null;
  return (
    <div className="flex items-center gap-2 px-4 py-2 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
      <span className="text-sm font-medium text-blue-700 dark:text-blue-300">{count} selected</span>
      <div className="flex gap-1 ml-4">
        {[{ icon: Download, action: onDownload, label: 'Download' }, { icon: FolderInput, action: onMove, label: 'Move' }, { icon: Share2, action: onShare, label: 'Share' }, { icon: Tag, action: onTag, label: 'Tag' }, { icon: Trash2, action: onDelete, label: 'Delete' }].map(({ icon: Icon, action, label }) => (
          <button key={label} onClick={action} className="p-2 hover:bg-blue-100 dark:hover:bg-blue-800/30 rounded text-blue-700 dark:text-blue-300" title={label}><Icon className="h-4 w-4" /></button>
        ))}
      </div>
      <button onClick={onClear} className="ml-auto p-1"><X className="h-4 w-4 text-blue-700" /></button>
    </div>
  );
};
