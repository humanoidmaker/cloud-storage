import React, { useEffect, useRef } from 'react';
import { Download, Share2, Star, Tag, FolderInput, Copy, Pencil, Trash2, Info, History } from 'lucide-react';

interface FileContextMenuProps {
  x: number;
  y: number;
  onClose: () => void;
  onOpen: () => void;
  onDownload: () => void;
  onShare: () => void;
  onStar: () => void;
  onTag: () => void;
  onMove: () => void;
  onCopy: () => void;
  onRename: () => void;
  onTrash: () => void;
  onDetails: () => void;
  onVersions: () => void;
  isFolder: boolean;
}

export const FileContextMenu: React.FC<FileContextMenuProps> = ({
  x, y, onClose, onOpen, onDownload, onShare, onStar, onTag, onMove, onCopy, onRename, onTrash, onDetails, onVersions, isFolder,
}) => {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => { if (ref.current && !ref.current.contains(e.target as Node)) onClose(); };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [onClose]);

  const items = [
    { icon: Download, label: 'Open', onClick: onOpen },
    ...(!isFolder ? [{ icon: Download, label: 'Download', onClick: onDownload }] : []),
    { icon: Share2, label: 'Share', onClick: onShare },
    { icon: Star, label: 'Star', onClick: onStar },
    { icon: Tag, label: 'Tag', onClick: onTag },
    { icon: FolderInput, label: 'Move', onClick: onMove },
    { icon: Copy, label: 'Copy', onClick: onCopy },
    { icon: Pencil, label: 'Rename', onClick: onRename },
    ...(!isFolder ? [{ icon: History, label: 'Versions', onClick: onVersions }] : []),
    { icon: Info, label: 'Details', onClick: onDetails },
    { icon: Trash2, label: 'Trash', onClick: onTrash },
  ];

  return (
    <div ref={ref} data-testid="context-menu" className="fixed z-50 bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700 py-1 min-w-[180px]" style={{ left: x, top: y }}>
      {items.map(({ icon: Icon, label, onClick }) => (
        <button key={label} onClick={() => { onClick(); onClose(); }}
          className={`w-full flex items-center gap-3 px-4 py-2 text-sm hover:bg-gray-100 dark:hover:bg-gray-700 ${label === 'Trash' ? 'text-red-600' : 'text-gray-700 dark:text-gray-300'}`}>
          <Icon className="h-4 w-4" /> {label}
        </button>
      ))}
    </div>
  );
};
