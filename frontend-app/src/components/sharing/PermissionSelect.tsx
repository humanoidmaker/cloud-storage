import React from 'react';

interface PermissionSelectProps { value: string; onChange: (v: string) => void; }

export const PermissionSelect: React.FC<PermissionSelectProps> = ({ value, onChange }) => (
  <div>
    <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Permission</label>
    <select value={value} onChange={(e) => onChange(e.target.value)} className="w-full mt-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
      <option value="view">View only</option>
      <option value="edit">Can edit</option>
      <option value="admin">Admin (full access)</option>
    </select>
  </div>
);
