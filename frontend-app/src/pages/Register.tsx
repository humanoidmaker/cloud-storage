import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { HardDrive, Loader2 } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';

export const Register: React.FC = () => {
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault(); setError(''); setIsLoading(true);
    try { await register(email, name, password); navigate('/login'); } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Registration failed'; setError(msg);
    } finally { setIsLoading(false); }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 p-4">
      <div className="w-full max-w-md bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-8">
        <div className="flex items-center justify-center gap-2 mb-8"><HardDrive className="h-8 w-8 text-blue-600" /><h1 className="text-2xl font-bold text-gray-900 dark:text-white">Cloud Storage</h1></div>
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && <div className="p-3 bg-red-50 text-red-600 text-sm rounded-lg">{error}</div>}
          <div><label className="text-sm font-medium text-gray-700 dark:text-gray-300">Name</label><input value={name} onChange={(e) => setName(e.target.value)} required className="w-full mt-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white" /></div>
          <div><label className="text-sm font-medium text-gray-700 dark:text-gray-300">Email</label><input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required className="w-full mt-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white" /></div>
          <div><label className="text-sm font-medium text-gray-700 dark:text-gray-300">Password</label><input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={8} className="w-full mt-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white" /></div>
          <button type="submit" disabled={isLoading} className="w-full py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center gap-2">{isLoading && <Loader2 className="h-4 w-4 animate-spin" />} Register</button>
        </form>
        <p className="text-center text-sm text-gray-500 mt-4">Already have an account? <Link to="/login" className="text-blue-600 hover:underline">Sign In</Link></p>
      </div>
    </div>
  );
};
