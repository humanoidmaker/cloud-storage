import React from 'react';
import { ChevronRight, Home } from 'lucide-react';
import type { BreadcrumbItem } from '../../types/file';

interface FileBreadcrumbProps {
  items: BreadcrumbItem[];
  onNavigate: (folderId: string | null) => void;
}

export const FileBreadcrumb: React.FC<FileBreadcrumbProps> = ({ items, onNavigate }) => (
  <nav className="flex items-center gap-1 text-sm" data-testid="breadcrumb">
    <button onClick={() => onNavigate(null)} className="flex items-center gap-1 text-gray-500 hover:text-blue-600 transition-colors">
      <Home className="h-4 w-4" /> Root
    </button>
    {items.filter((i) => i.id !== null).map((item, idx) => (
      <React.Fragment key={item.id || idx}>
        <ChevronRight className="h-4 w-4 text-gray-400" />
        <button onClick={() => onNavigate(item.id)} className="text-gray-700 dark:text-gray-300 hover:text-blue-600 transition-colors truncate max-w-[150px]">
          {item.name}
        </button>
      </React.Fragment>
    ))}
  </nav>
);
