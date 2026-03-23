import React from 'react';
interface StatsCardProps { title: string; value: string | number; icon: React.ReactNode; color?: string; }
export const StatsCard: React.FC<StatsCardProps> = ({ title, value, icon, color = 'blue' }) => (
  <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700" data-testid="stats-card">
    <div className="flex items-center justify-between"><div className={`p-3 rounded-lg bg-${color}-50 dark:bg-${color}-900/20`}>{icon}</div></div>
    <p className="text-2xl font-bold text-gray-900 dark:text-white mt-4">{value}</p>
    <p className="text-sm text-gray-500 mt-1">{title}</p>
  </div>
);
