import React from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { LayoutDashboard, Users, HardDrive, FolderOpen, Activity, Server, Settings, LogOut, Shield } from 'lucide-react';

const navItems = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/users', icon: Users, label: 'Users' },
  { to: '/storage', icon: HardDrive, label: 'Storage' },
  { to: '/files', icon: FolderOpen, label: 'Files' },
  { to: '/activity', icon: Activity, label: 'Activity' },
  { to: '/system', icon: Server, label: 'System Health' },
  { to: '/settings', icon: Settings, label: 'Settings' },
];

export const AdminLayout: React.FC<{ onLogout: () => void }> = ({ onLogout }) => {
  const navigate = useNavigate();
  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-900">
      <aside className="w-64 bg-gray-900 text-white flex flex-col">
        <div className="p-4 border-b border-gray-800 flex items-center gap-2">
          <Shield className="h-6 w-6 text-blue-400" />
          <h1 className="text-lg font-bold">Cloud Storage Admin</h1>
        </div>
        <nav className="flex-1 p-4 space-y-1">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink key={to} to={to} className={({ isActive }) => `flex items-center gap-3 px-3 py-2 rounded-lg text-sm ${isActive ? 'bg-blue-600 text-white' : 'text-gray-400 hover:bg-gray-800 hover:text-white'}`}>
              <Icon className="h-5 w-5" /> {label}
            </NavLink>
          ))}
        </nav>
        <div className="p-4 border-t border-gray-800">
          <button onClick={() => { onLogout(); navigate('/login'); }} className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-gray-400 hover:bg-gray-800 hover:text-white w-full">
            <LogOut className="h-5 w-5" /> Logout
          </button>
        </div>
      </aside>
      <main className="flex-1 overflow-auto p-6"><Outlet /></main>
    </div>
  );
};
