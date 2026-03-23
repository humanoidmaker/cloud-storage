import React from 'react';
import { X } from 'lucide-react';
import { FileIcon } from './FileIcon';
import type { FileItem } from '../../types/file';

interface FileDetailsProps {
  file: FileItem;
  onClose: () => void;
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

export const FileDetails: React.FC<FileDetailsProps> = ({ file, onClose }) => (
  <div className="w-80 bg-white dark:bg-gray-800 border-l border-gray-200 dark:border-gray-700 p-6 overflow-y-auto">
    <div className="flex items-center justify-between mb-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Details</h3>
      <button onClick={onClose} className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"><X className="h-5 w-5" /></button>
    </div>
    <div className="flex flex-col items-center mb-6">
      <FileIcon mimeType={file.mime_type} isFolder={file.is_folder} className="h-16 w-16" />
      <p className="text-sm font-medium text-gray-900 dark:text-white mt-2 text-center break-words">{file.name}</p>
    </div>
    <div className="space-y-4 text-sm">
      <div><span className="text-gray-500">Type:</span> <span className="text-gray-900 dark:text-white ml-2">{file.is_folder ? 'Folder' : file.mime_type || 'Unknown'}</span></div>
      {!file.is_folder && <div><span className="text-gray-500">Size:</span> <span className="text-gray-900 dark:text-white ml-2">{formatBytes(file.size)}</span></div>}
      <div><span className="text-gray-500">Created:</span> <span className="text-gray-900 dark:text-white ml-2">{new Date(file.created_at).toLocaleString()}</span></div>
      <div><span className="text-gray-500">Modified:</span> <span className="text-gray-900 dark:text-white ml-2">{new Date(file.updated_at).toLocaleString()}</span></div>
    </div>
  </div>
);
