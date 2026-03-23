import React from 'react';
import { File, Folder, Image, Film, Music, FileText, Archive, Code, FileSpreadsheet } from 'lucide-react';

interface FileIconProps {
  mimeType: string | null;
  isFolder: boolean;
  className?: string;
}

export const FileIcon: React.FC<FileIconProps> = ({ mimeType, isFolder, className = 'h-8 w-8' }) => {
  if (isFolder) return <Folder className={`${className} text-blue-500`} />;
  const mime = (mimeType || '').toLowerCase();
  if (mime.startsWith('image/')) return <Image className={`${className} text-green-500`} />;
  if (mime.startsWith('video/')) return <Film className={`${className} text-purple-500`} />;
  if (mime.startsWith('audio/')) return <Music className={`${className} text-pink-500`} />;
  if (mime.includes('pdf') || mime.includes('document') || mime.includes('text/')) return <FileText className={`${className} text-red-500`} />;
  if (mime.includes('zip') || mime.includes('tar') || mime.includes('rar')) return <Archive className={`${className} text-yellow-600`} />;
  if (mime.includes('json') || mime.includes('javascript') || mime.includes('xml')) return <Code className={`${className} text-gray-600`} />;
  if (mime.includes('spreadsheet') || mime.includes('excel')) return <FileSpreadsheet className={`${className} text-green-600`} />;
  return <File className={`${className} text-gray-400`} />;
};
