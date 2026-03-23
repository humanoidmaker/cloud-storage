import React from 'react';

interface StorageMeterProps {
  used: number;
  total: number;
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

export const StorageMeter: React.FC<StorageMeterProps> = ({ used, total }) => {
  const percentage = total > 0 ? Math.min((used / total) * 100, 100) : 0;

  const getColor = () => {
    if (percentage >= 95) return 'bg-red-500';
    if (percentage >= 80) return 'bg-yellow-500';
    return 'bg-blue-500';
  };

  return (
    <div data-testid="storage-meter">
      <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mb-1">
        <span>{formatBytes(used)} used</span>
        <span>{total > 0 ? formatBytes(total) : 'Unlimited'}</span>
      </div>
      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
        <div className={`h-2 rounded-full transition-all ${getColor()}`} style={{ width: `${percentage}%` }} role="progressbar" aria-valuenow={percentage} aria-valuemin={0} aria-valuemax={100} />
      </div>
      {total > 0 && <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{percentage.toFixed(1)}% used</p>}
    </div>
  );
};
