import React, { useState } from 'react';

interface RenameDialogProps { isOpen: boolean; currentName: string; onClose: () => void; onRename: (name: string) => void; }

export const RenameDialog: React.FC<RenameDialogProps> = ({ isOpen, currentName, onClose, onRename }) => {
  const [name, setName] = useState(currentName);
  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 w-full max-w-md" onClick={(e) => e.stopPropagation()}>
        <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Rename</h3>
        <input value={name} onChange={(e) => setName(e.target.value)} autoFocus className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg mb-4 bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
        <div className="flex justify-end gap-2">
          <button onClick={onClose} className="px-4 py-2 text-gray-700 dark:text-gray-300 rounded-lg">Cancel</button>
          <button onClick={() => { onRename(name); onClose(); }} className="px-4 py-2 bg-blue-600 text-white rounded-lg">Rename</button>
        </div>
      </div>
    </div>
  );
};
