import React from 'react';
interface ConfirmDialogProps { isOpen: boolean; title: string; message: string; onClose: () => void; onConfirm: () => void; }
export const ConfirmDialog: React.FC<ConfirmDialogProps> = ({ isOpen, title, message, onClose, onConfirm }) => {
  if (!isOpen) return null;
  return (<div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4"><div className="bg-white dark:bg-gray-800 rounded-xl p-6 w-full max-w-md"><h3 className="text-lg font-semibold mb-2">{title}</h3><p className="text-sm text-gray-600 mb-4">{message}</p><div className="flex justify-end gap-2"><button onClick={onClose} className="px-4 py-2 border rounded-lg">Cancel</button><button onClick={() => { onConfirm(); onClose(); }} className="px-4 py-2 bg-red-600 text-white rounded-lg">Confirm</button></div></div></div>);
};
