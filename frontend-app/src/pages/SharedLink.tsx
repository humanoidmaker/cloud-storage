import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { sharingApi } from '../api/sharingApi';
import { FileIcon } from '../components/files/FileIcon';
import { Lock } from 'lucide-react';

export const SharedLink: React.FC = () => {
  const { token } = useParams<{ token: string }>();
  const [password, setPassword] = useState('');
  const [submittedPassword, setSubmittedPassword] = useState<string | undefined>();
  const { data, error, isLoading } = useQuery({
    queryKey: ['shared-link', token, submittedPassword],
    queryFn: () => sharingApi.accessLink(token!, submittedPassword).then((r) => r.data),
    enabled: !!token, retry: false,
  });
  const errStatus = (error as { response?: { status?: number } })?.response?.status;

  if (isLoading) return <div className="min-h-screen flex items-center justify-center"><p>Loading...</p></div>;
  if (errStatus === 403) return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
      <div className="bg-white dark:bg-gray-800 rounded-xl p-8 max-w-md w-full">
        <Lock className="h-8 w-8 text-gray-400 mx-auto mb-4" />
        <h2 className="text-lg font-semibold text-center mb-4">Password required</h2>
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Enter password" className="w-full px-3 py-2 border rounded-lg mb-4" />
        <button onClick={() => setSubmittedPassword(password)} className="w-full py-2 bg-blue-600 text-white rounded-lg">Access</button>
      </div>
    </div>
  );
  if (errStatus === 410) return <div className="min-h-screen flex items-center justify-center"><p className="text-red-500">This link has expired</p></div>;
  if (error) return <div className="min-h-screen flex items-center justify-center"><p className="text-red-500">Link not found</p></div>;

  const file = data?.file;
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-xl p-8 max-w-md w-full text-center">
        {file && <>
          <FileIcon mimeType={file.mime_type} isFolder={file.is_folder} className="h-16 w-16 mx-auto mb-4" />
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">{file.name}</h2>
          <p className="text-sm text-gray-500 mb-4">Permission: {data.permission}</p>
        </>}
      </div>
    </div>
  );
};
