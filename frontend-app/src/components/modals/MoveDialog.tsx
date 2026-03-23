import React, { useState } from 'react';
import { Folder, ChevronRight } from 'lucide-react';
import { useFolderTree } from '../../hooks/useFolders';
import type { FolderTreeNode } from '../../types/file';

interface MoveDialogProps { isOpen: boolean; onClose: () => void; onMove: (folderId: string | null) => void; currentFolderId?: string; }

const TreeItem: React.FC<{ node: FolderTreeNode; selected: string | null; onSelect: (id: string) => void; disabled?: string }> = ({ node, selected, onSelect, disabled }) => {
  const [expanded, setExpanded] = useState(false);
  const isDisabled = node.id === disabled;
  return (
    <div>
      <button onClick={() => isDisabled ? null : onSelect(node.id)}
        className={`flex items-center gap-2 w-full px-2 py-1 text-sm rounded ${selected === node.id ? 'bg-blue-100 dark:bg-blue-900/30' : 'hover:bg-gray-100 dark:hover:bg-gray-700'} ${isDisabled ? 'opacity-50' : ''}`}>
        {node.children.length > 0 && <button onClick={(e) => { e.stopPropagation(); setExpanded(!expanded); }}><ChevronRight className={`h-3 w-3 transition-transform ${expanded ? 'rotate-90' : ''}`} /></button>}
        <Folder className="h-4 w-4 text-blue-500" /> {node.name}
      </button>
      {expanded && node.children.map((c) => <div key={c.id} className="ml-4"><TreeItem node={c} selected={selected} onSelect={onSelect} disabled={disabled} /></div>)}
    </div>
  );
};

export const MoveDialog: React.FC<MoveDialogProps> = ({ isOpen, onClose, onMove, currentFolderId }) => {
  const [selected, setSelected] = useState<string | null>(null);
  const { data: tree = [] } = useFolderTree();
  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" data-testid="move-dialog">
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 w-full max-w-md max-h-[70vh] flex flex-col" onClick={(e) => e.stopPropagation()}>
        <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Move to</h3>
        <button onClick={() => setSelected(null)} className={`flex items-center gap-2 px-2 py-1 text-sm rounded mb-2 ${selected === null ? 'bg-blue-100' : 'hover:bg-gray-100'}`}>
          <Folder className="h-4 w-4" /> Root
        </button>
        <div className="flex-1 overflow-y-auto space-y-1">{tree.map((n) => <TreeItem key={n.id} node={n} selected={selected} onSelect={setSelected} disabled={currentFolderId} />)}</div>
        <div className="flex justify-end gap-2 mt-4">
          <button onClick={onClose} className="px-4 py-2 text-gray-700 dark:text-gray-300 rounded-lg">Cancel</button>
          <button onClick={() => { onMove(selected); onClose(); }} className="px-4 py-2 bg-blue-600 text-white rounded-lg">Move</button>
        </div>
      </div>
    </div>
  );
};
