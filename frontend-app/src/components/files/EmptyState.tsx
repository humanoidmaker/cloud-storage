import React from 'react';
import { FolderOpen } from 'lucide-react';

interface EmptyStateProps {
  message: string;
  action?: React.ReactNode;
}

export const EmptyState: React.FC<EmptyStateProps> = ({ message, action }) => (
  <div className="flex flex-col items-center justify-center py-16 text-center" data-testid="empty-state">
    <FolderOpen className="h-16 w-16 text-gray-300 dark:text-gray-600 mb-4" />
    <p className="text-gray-500 dark:text-gray-400 text-lg mb-4">{message}</p>
    {action}
  </div>
);
