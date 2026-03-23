import React, { useState } from 'react';
import { Link, Copy, Lock, X } from 'lucide-react';
import { useCreateShare } from '../../hooks/useSharing';
import { PermissionSelect } from './PermissionSelect';

interface ShareDialogProps { isOpen: boolean; onClose: () => void; fileId: string; }

export const ShareDialog: React.FC<ShareDialogProps> = ({ isOpen, onClose, fileId }) => {
  const [email, setEmail] = useState('');
  const [permission, setPermission] = useState('view');
  const [createLink, setCreateLink] = useState(false);
  const [password, setPassword] = useState('');
  const [expiresAt, setExpiresAt] = useState('');
  const [shareLink, setShareLink] = useState('');
  const createShare = useCreateShare();

  if (!isOpen) return null;

  const handleShare = async () => {
    try {
      const result = await createShare.mutateAsync({
        file_id: fileId, shared_with_email: email || undefined, permission, create_link: createLink,
        password: password || undefined, expires_at: expiresAt || undefined,
      });
      if (result.data.share_token) setShareLink(`${window.location.origin}/shared/${result.data.share_token}`);
      if (!createLink) { setEmail(''); onClose(); }
    } catch { /* handled by mutation */ }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" data-testid="share-dialog">
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 w-full max-w-lg" onClick={(e) => e.stopPropagation()}>
        <div className="flex justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Share</h3>
          <button onClick={onClose}><X className="h-5 w-5" /></button>
        </div>
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Share with email</label>
            <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="user@example.com" className="w-full mt-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
          </div>
          <PermissionSelect value={permission} onChange={setPermission} />
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={createLink} onChange={(e) => setCreateLink(e.target.checked)} className="rounded" />
            <Link className="h-4 w-4" /> Generate share link
          </label>
          {createLink && (
            <>
              <div>
                <label className="text-sm font-medium text-gray-700 dark:text-gray-300"><Lock className="h-4 w-4 inline mr-1" />Password (optional)</label>
                <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} className="w-full mt-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700" />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Expires at (optional)</label>
                <input type="datetime-local" value={expiresAt} onChange={(e) => setExpiresAt(e.target.value)} className="w-full mt-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700" />
              </div>
            </>
          )}
          {shareLink && (
            <div className="flex items-center gap-2 p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
              <input readOnly value={shareLink} className="flex-1 text-sm bg-transparent" />
              <button onClick={() => navigator.clipboard.writeText(shareLink)} className="p-1"><Copy className="h-4 w-4" /></button>
            </div>
          )}
          <div className="flex justify-end gap-2">
            <button onClick={onClose} className="px-4 py-2 text-gray-700 dark:text-gray-300 rounded-lg">Cancel</button>
            <button onClick={handleShare} disabled={!email && !createLink} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50">Share</button>
          </div>
        </div>
      </div>
    </div>
  );
};
