import React from 'react';
import { Grid3X3, List } from 'lucide-react';
import type { ViewMode } from '../../types/file';

interface ViewToggleProps { view: ViewMode; onChange: (v: ViewMode) => void; }

export const ViewToggle: React.FC<ViewToggleProps> = ({ view, onChange }) => (
  <div className="flex items-center border border-gray-300 dark:border-gray-600 rounded-lg overflow-hidden">
    <button onClick={() => onChange('grid')} className={`p-2 ${view === 'grid' ? 'bg-blue-50 text-blue-600 dark:bg-blue-900/30' : 'text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700'}`}><Grid3X3 className="h-4 w-4" /></button>
    <button onClick={() => onChange('list')} className={`p-2 ${view === 'list' ? 'bg-blue-50 text-blue-600 dark:bg-blue-900/30' : 'text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700'}`}><List className="h-4 w-4" /></button>
  </div>
);
