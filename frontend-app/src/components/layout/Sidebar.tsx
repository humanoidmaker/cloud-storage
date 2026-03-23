import React from 'react';
import { NavLink } from 'react-router-dom';
import { Files, Share2, Star, Trash2, Tag, Settings, HardDrive } from 'lucide-react';
import { StorageMeter } from './StorageMeter';
import { useAuth } from '../../hooks/useAuth';

const navItems = [
  { to: '/files', icon: Files, label: 'My Files' },
  { to: '/shared', icon: Share2, label: 'Shared with Me' },
  { to: '/starred', icon: Star, label: 'Starred' },
  { to: '/trash', icon: Trash2, label: 'Trash' },
  { to: '/tags', icon: Tag, label: 'Tags' },
];

export const Sidebar: React.FC = () => {
  const { user } = useAuth();

  return (
    <aside className="w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col" data-testid="sidebar">
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-2">
          <HardDrive className="h-6 w-6 text-blue-600" />
          <h1 className="text-xl font-bold text-gray-900 dark:text-white">Cloud Storage</h1>
        </div>
      </div>
      <nav className="flex-1 p-4 space-y-1">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink key={to} to={to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors
              ${isActive ? 'bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300' : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'}`
            }>
            <Icon className="h-5 w-5" />
            {label}
          </NavLink>
        ))}
      </nav>
      <div className="p-4 border-t border-gray-200 dark:border-gray-700">
        {user && <StorageMeter used={user.storage_used} total={user.storage_quota} />}
        <NavLink to="/settings"
          className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 mt-2">
          <Settings className="h-5 w-5" />
          Settings
        </NavLink>
      </div>
    </aside>
  );
};
