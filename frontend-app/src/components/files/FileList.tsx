import React from 'react';
import { FileRow } from './FileRow';
import { EmptyState } from './EmptyState';
import type { FileItem, SortField, SortOrder } from '../../types/file';
import { ArrowUp, ArrowDown } from 'lucide-react';

interface FileListProps {
  files: FileItem[];
  selectedIds: string[];
  onSelect: (id: string, e: React.MouseEvent) => void;
  onOpen: (file: FileItem) => void;
  onContextMenu: (file: FileItem, e: React.MouseEvent) => void;
  sortBy: SortField;
  sortOrder: SortOrder;
  onSort: (field: SortField) => void;
  isLoading?: boolean;
}

export const FileList: React.FC<FileListProps> = ({ files, selectedIds, onSelect, onOpen, onContextMenu, sortBy, sortOrder, onSort, isLoading }) => {
  if (isLoading) return <div data-testid="file-list-loading" className="space-y-2">{Array.from({ length: 8 }).map((_, i) => <div key={i} className="h-12 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />)}</div>;
  if (!files.length) return <EmptyState message="This folder is empty" />;

  const SortIcon = sortOrder === 'asc' ? ArrowUp : ArrowDown;
  const headers: { label: string; field: SortField; width: string }[] = [
    { label: 'Name', field: 'name', width: 'flex-1' },
    { label: 'Size', field: 'size', width: 'w-24' },
    { label: 'Modified', field: 'updated_at', width: 'w-40' },
  ];

  return (
    <div data-testid="file-list">
      <div className="flex items-center gap-4 px-4 py-2 text-xs font-medium text-gray-500 dark:text-gray-400 border-b border-gray-200 dark:border-gray-700">
        <div className="w-8" />
        {headers.map((h) => (
          <button key={h.field} className={`flex items-center gap-1 ${h.width} hover:text-gray-700`} onClick={() => onSort(h.field)}>
            {h.label} {sortBy === h.field && <SortIcon className="h-3 w-3" />}
          </button>
        ))}
      </div>
      <div className="divide-y divide-gray-100 dark:divide-gray-800">
        {files.map((f) => (
          <FileRow key={f.id} file={f} isSelected={selectedIds.includes(f.id)} onClick={(e) => onSelect(f.id, e)} onDoubleClick={() => onOpen(f)} onContextMenu={(e) => onContextMenu(f, e)} />
        ))}
      </div>
    </div>
  );
};
