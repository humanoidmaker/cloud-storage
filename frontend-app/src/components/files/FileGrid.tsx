import React from 'react';
import { FileCard } from './FileCard';
import { EmptyState } from './EmptyState';
import type { FileItem } from '../../types/file';

interface FileGridProps {
  files: FileItem[];
  selectedIds: string[];
  onSelect: (id: string, e: React.MouseEvent) => void;
  onOpen: (file: FileItem) => void;
  onContextMenu: (file: FileItem, e: React.MouseEvent) => void;
  isLoading?: boolean;
}

export const FileGrid: React.FC<FileGridProps> = ({ files, selectedIds, onSelect, onOpen, onContextMenu, isLoading }) => {
  if (isLoading) return <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4" data-testid="file-grid-loading">{Array.from({ length: 12 }).map((_, i) => <div key={i} className="h-40 bg-gray-200 dark:bg-gray-700 rounded-xl animate-pulse" />)}</div>;
  if (!files.length) return <EmptyState message="This folder is empty" />;
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4" data-testid="file-grid">
      {files.map((f) => (
        <FileCard key={f.id} file={f} isSelected={selectedIds.includes(f.id)} onClick={(e) => onSelect(f.id, e)} onDoubleClick={() => onOpen(f)} onContextMenu={(e) => onContextMenu(f, e)} />
      ))}
    </div>
  );
};
