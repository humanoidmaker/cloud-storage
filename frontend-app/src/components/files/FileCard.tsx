import React from 'react';
import { FileIcon } from './FileIcon';
import type { FileItem } from '../../types/file';
import { formatDistanceToNow } from 'date-fns';

interface FileCardProps {
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

export const FileCard: React.FC<FileCardProps> = ({ file, isSelected, onClick, onDoubleClick, onContextMenu }) => {
  return (
    <div
      data-testid={`file-card-${file.id}`}
      className={`group relative flex flex-col items-center p-4 rounded-xl border-2 cursor-pointer transition-all hover:shadow-md
        ${isSelected ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' : 'border-transparent hover:border-gray-200 dark:hover:border-gray-600'}`}
      onClick={onClick}
      onDoubleClick={onDoubleClick}
      onContextMenu={onContextMenu}
    >
      <div className="w-16 h-16 flex items-center justify-center mb-2">
        <FileIcon mimeType={file.mime_type} isFolder={file.is_folder} className="h-12 w-12" />
      </div>
      <p className="text-sm font-medium text-gray-900 dark:text-white truncate w-full text-center" title={file.name}>
        {file.name}
      </p>
      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
        {file.is_folder ? 'Folder' : formatSize(file.size)}
      </p>
      <p className="text-xs text-gray-400 dark:text-gray-500">
        {file.updated_at ? formatDistanceToNow(new Date(file.updated_at), { addSuffix: true }) : ''}
      </p>
    </div>
  );
};
