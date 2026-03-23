import React, { useState } from 'react';
import { Shield, Loader2 } from 'lucide-react';
interface LoginProps { onLogin: (email: string, password: string) => Promise<void>; }
export const Login: React.FC<LoginProps> = ({ onLogin }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault(); setError(''); setLoading(true);
    try { await onLogin(email, password); } catch { setError('Invalid credentials'); } finally { setLoading(false); }
  };
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-900 p-4">
      <div className="w-full max-w-md bg-gray-800 rounded-2xl p-8">
        <div className="flex items-center justify-center gap-2 mb-8"><Shield className="h-8 w-8 text-blue-400" /><h1 className="text-2xl font-bold text-white">Cloud Storage Admin</h1></div>
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && <div className="p-3 bg-red-900/20 text-red-400 text-sm rounded-lg">{error}</div>}
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Admin email" required className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" />
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" required className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" />
          <button type="submit" disabled={loading} className="w-full py-2 bg-blue-600 text-white rounded-lg flex items-center justify-center gap-2">{loading && <Loader2 className="h-4 w-4 animate-spin" />} Sign In</button>
        </form>
      </div>
    </div>
  );
};
