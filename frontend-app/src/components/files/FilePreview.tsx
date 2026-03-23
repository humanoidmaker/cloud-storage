import React from 'react';
import { X, Download } from 'lucide-react';
import type { FileItem } from '../../types/file';

interface FilePreviewProps {
  file: FileItem;
  previewUrl: string | null;
  onClose: () => void;
  onDownload: () => void;
}

export const FilePreview: React.FC<FilePreviewProps> = ({ file, previewUrl, onClose, onDownload }) => {
  const mime = (file.mime_type || '').toLowerCase();
  const renderContent = () => {
    if (!previewUrl) return <p className="text-gray-500">Loading preview...</p>;
    if (mime.startsWith('image/')) return <img src={previewUrl} alt={file.name} className="max-w-full max-h-[70vh] object-contain" />;
    if (mime.startsWith('video/')) return <video src={previewUrl} controls className="max-w-full max-h-[70vh]" />;
    if (mime.startsWith('audio/')) return <audio src={previewUrl} controls className="w-full" />;
    if (mime === 'application/pdf') return <iframe src={previewUrl} className="w-full h-[70vh]" title={file.name} />;
    return (
      <div className="text-center">
        <p className="text-gray-500 mb-4">Preview not available for this file type</p>
        <button onClick={onDownload} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">Download to view</button>
      </div>
    );
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4" data-testid="file-preview" onClick={onClose}>
      <div className="relative max-w-4xl w-full bg-white dark:bg-gray-800 rounded-xl p-6" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white truncate">{file.name}</h3>
          <div className="flex items-center gap-2">
            <button onClick={onDownload} className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"><Download className="h-5 w-5" /></button>
            <button onClick={onClose} className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"><X className="h-5 w-5" /></button>
          </div>
        </div>
        <div className="flex items-center justify-center min-h-[200px]">{renderContent()}</div>
      </div>
    </div>
  );
};
