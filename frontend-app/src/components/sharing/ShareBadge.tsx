import React from 'react';
import { Share2 } from 'lucide-react';

export const ShareBadge: React.FC = () => (
  <span className="inline-flex items-center gap-1 px-1.5 py-0.5 text-xs font-medium text-blue-600 bg-blue-50 dark:text-blue-400 dark:bg-blue-900/30 rounded">
    <Share2 className="h-3 w-3" /> Shared
  </span>
);
