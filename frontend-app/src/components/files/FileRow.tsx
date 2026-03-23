import React from 'react';
import { FileIcon } from './FileIcon';
import type { FileItem } from '../../types/file';
import { formatDistanceToNow } from 'date-fns';

interface FileRowProps {
  file: FileItem;
  isSelected: boolean;
  onClick: (e: React.MouseEvent) => void;
  onDoubleClick: () => void;
  onContextMenu: (e: React.MouseEvent) => void;
}

function formatSize(bytes: number): string {
  if (bytes === 0) return '--';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

export const FileRow: React.FC<FileRowProps> = ({ file, isSelected, onClick, onDoubleClick, onContextMenu }) => (
  <div className={`flex items-center gap-4 px-4 py-2 cursor-pointer transition-colors ${isSelected ? 'bg-blue-50 dark:bg-blue-900/20' : 'hover:bg-gray-50 dark:hover:bg-gray-800'}`}
    onClick={onClick} onDoubleClick={onDoubleClick} onContextMenu={onContextMenu} data-testid={`file-row-${file.id}`}>
    <div className="w-8"><FileIcon mimeType={file.mime_type} isFolder={file.is_folder} className="h-5 w-5" /></div>
    <div className="flex-1 truncate text-sm text-gray-900 dark:text-white">{file.name}</div>
    <div className="w-24 text-xs text-gray-500">{file.is_folder ? '--' : formatSize(file.size)}</div>
    <div className="w-40 text-xs text-gray-500">{file.updated_at ? formatDistanceToNow(new Date(file.updated_at), { addSuffix: true }) : ''}</div>
  </div>
);
