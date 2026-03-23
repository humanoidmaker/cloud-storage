import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider, useAuthContext } from './contexts/AuthContext';
import { ThemeProvider } from './contexts/ThemeContext';
import { AppLayout } from './components/layout/AppLayout';
import { Login } from './pages/Login';
import { Register } from './pages/Register';
import { MyFiles } from './pages/MyFiles';
import { SharedWithMe } from './pages/SharedWithMe';
import { Starred } from './pages/Starred';
import { Trash } from './pages/Trash';
import { Search } from './pages/Search';
import { SharedLink } from './pages/SharedLink';
import { Settings } from './pages/Settings';
import { TagFiles } from './pages/TagFiles';
import { Toast } from './components/common/Toast';

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, staleTime: 30000 } },
});

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuthContext();
  if (isLoading) return <div className="min-h-screen flex items-center justify-center"><p>Loading...</p></div>;
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <>{children}</>;
};

const App: React.FC = () => (
  <QueryClientProvider client={queryClient}>
    <ThemeProvider>
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/shared/:token" element={<SharedLink />} />
            <Route path="/" element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
              <Route index element={<Navigate to="/files" replace />} />
              <Route path="files" element={<MyFiles />} />
              <Route path="shared" element={<SharedWithMe />} />
              <Route path="starred" element={<Starred />} />
              <Route path="trash" element={<Trash />} />
              <Route path="search" element={<Search />} />
              <Route path="settings" element={<Settings />} />
              <Route path="tags" element={<TagFiles />} />
              <Route path="tags/:tagId" element={<TagFiles />} />
            </Route>
          </Routes>
          <Toast />
        </AuthProvider>
      </BrowserRouter>
    </ThemeProvider>
  </QueryClientProvider>
);

export default App;
