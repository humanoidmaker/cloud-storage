import React, { useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { authApi } from '../api/authApi';
import { StorageMeter } from '../components/layout/StorageMeter';

export const Settings: React.FC = () => {
  const { user } = useAuth();
  const [currentPw, setCurrentPw] = useState('');
  const [newPw, setNewPw] = useState('');
  const [pwMsg, setPwMsg] = useState('');

  const handleChangePw = async (e: React.FormEvent) => {
    e.preventDefault();
    try { await authApi.changePassword(currentPw, newPw); setPwMsg('Password changed!'); setCurrentPw(''); setNewPw(''); }
    catch { setPwMsg('Failed to change password'); }
  };

  if (!user) return null;
  return (
    <div className="max-w-2xl">
      <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">Settings</h2>
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700 mb-6">
        <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Profile</h3>
        <div className="space-y-2 text-sm"><p><span className="text-gray-500">Name:</span> {user.name}</p><p><span className="text-gray-500">Email:</span> {user.email}</p><p><span className="text-gray-500">Role:</span> {user.role}</p></div>
      </div>
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700 mb-6">
        <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Storage</h3>
        <StorageMeter used={user.storage_used} total={user.storage_quota} />
      </div>
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
        <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Change Password</h3>
        <form onSubmit={handleChangePw} className="space-y-4">
          {pwMsg && <p className="text-sm text-blue-600">{pwMsg}</p>}
          <input type="password" value={currentPw} onChange={(e) => setCurrentPw(e.target.value)} placeholder="Current password" className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700" />
          <input type="password" value={newPw} onChange={(e) => setNewPw(e.target.value)} placeholder="New password" minLength={8} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700" />
          <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded-lg">Change Password</button>
        </form>
      </div>
    </div>
  );
};
