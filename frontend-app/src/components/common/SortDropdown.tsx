import React from 'react';
import type { SortField } from '../../types/file';

interface SortDropdownProps { value: SortField; onChange: (v: SortField) => void; }

export const SortDropdown: React.FC<SortDropdownProps> = ({ value, onChange }) => (
  <select value={value} onChange={(e) => onChange(e.target.value as SortField)} className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-sm text-gray-700 dark:text-gray-300">
    <option value="name">Name</option>
    <option value="size">Size</option>
    <option value="created_at">Date created</option>
    <option value="updated_at">Date modified</option>
  </select>
);
