import React from 'react';
import { Upload } from 'lucide-react';

interface DropZoneProps {
  isDragging: boolean;
}

export const DropZone: React.FC<DropZoneProps> = ({ isDragging }) => {
  if (!isDragging) return null;
  return (
    <div data-testid="drop-zone" className="fixed inset-0 z-50 bg-blue-600/20 backdrop-blur-sm flex items-center justify-center pointer-events-none">
      <div className="bg-white dark:bg-gray-800 rounded-2xl p-12 shadow-2xl border-4 border-dashed border-blue-500">
        <Upload className="h-16 w-16 text-blue-500 mx-auto mb-4" />
        <p className="text-xl font-semibold text-gray-900 dark:text-white">Drop files to upload</p>
      </div>
    </div>
  );
};
