import React, { useState } from 'react';
interface UserFormProps { onSubmit: (data: { email: string; name: string; password: string; role: string }) => void; onCancel: () => void; }
export const UserForm: React.FC<UserFormProps> = ({ onSubmit, onCancel }) => {
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('user');
  return (
    <div className="space-y-4">
      <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Name" className="w-full px-3 py-2 border rounded-lg" />
      <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" className="w-full px-3 py-2 border rounded-lg" />
      <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" className="w-full px-3 py-2 border rounded-lg" />
      <select value={role} onChange={(e) => setRole(e.target.value)} className="w-full px-3 py-2 border rounded-lg"><option value="user">User</option><option value="admin">Admin</option><option value="superadmin">Superadmin</option></select>
      <div className="flex gap-2"><button onClick={() => onSubmit({ email, name, password, role })} className="px-4 py-2 bg-blue-600 text-white rounded-lg">Create</button><button onClick={onCancel} className="px-4 py-2 border rounded-lg">Cancel</button></div>
    </div>
  );
};
