import React, { useRef } from 'react';
import { Upload, FolderPlus } from 'lucide-react';

interface UploadButtonProps {
  onUploadFiles: (files: File[]) => void;
  onNewFolder: () => void;
}

export const UploadButton: React.FC<UploadButtonProps> = ({ onUploadFiles, onNewFolder }) => {
  const fileRef = useRef<HTMLInputElement>(null);
  return (
    <div className="flex items-center gap-2">
      <input ref={fileRef} type="file" multiple className="hidden" onChange={(e) => { if (e.target.files) onUploadFiles(Array.from(e.target.files)); e.target.value = ''; }} />
      <button onClick={() => fileRef.current?.click()} className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium">
        <Upload className="h-4 w-4" /> Upload
      </button>
      <button onClick={onNewFolder} className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors text-sm font-medium">
        <FolderPlus className="h-4 w-4" /> New Folder
      </button>
    </div>
  );
};
