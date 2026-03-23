import React from 'react';
import { useNavigate } from 'react-router-dom';
import { LogOut, Moon, Sun, User } from 'lucide-react';
import { SearchBar } from '../common/SearchBar';
import { useAuth } from '../../hooks/useAuth';
import { useTheme } from '../../contexts/ThemeContext';

export const Header: React.FC = () => {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <header className="h-16 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between px-6">
      <div className="flex-1 max-w-xl">
        <SearchBar />
      </div>
      <div className="flex items-center gap-4">
        <button onClick={toggleTheme} className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700" aria-label="Toggle theme">
          {theme === 'light' ? <Moon className="h-5 w-5 text-gray-600" /> : <Sun className="h-5 w-5 text-yellow-400" />}
        </button>
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center">
            <User className="h-4 w-4 text-white" />
          </div>
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">{user?.name}</span>
        </div>
        <button onClick={handleLogout} className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700" aria-label="Logout">
          <LogOut className="h-5 w-5 text-gray-600 dark:text-gray-400" />
        </button>
      </div>
    </header>
  );
};
