import React from 'react';
import { Toaster } from 'react-hot-toast';

export const Toast: React.FC = () => <Toaster position="bottom-right" toastOptions={{ className: 'text-sm', duration: 3000 }} />;
