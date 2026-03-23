import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useAdminAuth } from './hooks/useAuth';
import { AdminLayout } from './components/AdminLayout';
import { Login } from './pages/Login';
import { Dashboard } from './pages/Dashboard';
import { UserManagement } from './pages/UserManagement';
import { StorageOverview } from './pages/StorageOverview';
import { FileExplorer } from './pages/FileExplorer';
import { ActivityLog } from './pages/ActivityLog';
import { SystemHealth } from './pages/SystemHealth';
import { Settings } from './pages/Settings';

const queryClient = new QueryClient({ defaultOptions: { queries: { retry: 1, staleTime: 30000 } } });

const AppRoutes: React.FC = () => {
  const { isAuthenticated, isLoading, login, logout } = useAdminAuth();
  if (isLoading) return <div className="min-h-screen flex items-center justify-center"><p>Loading...</p></div>;
  if (!isAuthenticated) return <Login onLogin={login} />;
  return (
    <Routes>
      <Route path="/" element={<AdminLayout onLogout={logout} />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="users" element={<UserManagement />} />
        <Route path="storage" element={<StorageOverview />} />
        <Route path="files" element={<FileExplorer />} />
        <Route path="activity" element={<ActivityLog />} />
        <Route path="system" element={<SystemHealth />} />
        <Route path="settings" element={<Settings />} />
      </Route>
    </Routes>
  );
};

const App: React.FC = () => (
  <QueryClientProvider client={queryClient}>
    <BrowserRouter>
      <AppRoutes />
    </BrowserRouter>
  </QueryClientProvider>
);

export default App;
