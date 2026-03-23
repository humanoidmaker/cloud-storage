import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { adminApi } from '../api/adminApi';

export const SystemHealth: React.FC = () => {
  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">SystemHealth</h2>
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
        <p className="text-gray-500">Loading SystemHealth data...</p>
      </div>
    </div>
  );
};
