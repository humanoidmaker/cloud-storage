import React from 'react';
import { AlertTriangle } from 'lucide-react';

interface DeleteConfirmProps { isOpen: boolean; itemName: string; onClose: () => void; onConfirm: () => void; permanent?: boolean; }

export const DeleteConfirm: React.FC<DeleteConfirmProps> = ({ isOpen, itemName, onClose, onConfirm, permanent }) => {
  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 w-full max-w-md" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center gap-3 mb-4">
          <AlertTriangle className="h-6 w-6 text-red-500" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{permanent ? 'Permanently delete' : 'Move to trash'}?</h3>
        </div>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
          {permanent ? `"${itemName}" will be permanently deleted. This cannot be undone.` : `"${itemName}" will be moved to trash.`}
        </p>
        <div className="flex justify-end gap-2">
          <button onClick={onClose} className="px-4 py-2 text-gray-700 dark:text-gray-300 rounded-lg">Cancel</button>
          <button onClick={() => { onConfirm(); onClose(); }} className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700">Delete</button>
        </div>
      </div>
    </div>
  );
};
