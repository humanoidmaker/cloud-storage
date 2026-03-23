import React, { useState } from 'react';
import { X, Plus, Trash2 } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { tagsApi } from '../../api/tagsApi';

interface TagManagerProps { isOpen: boolean; onClose: () => void; fileId?: string; }

export const TagManager: React.FC<TagManagerProps> = ({ isOpen, onClose, fileId }) => {
  const qc = useQueryClient();
  const { data: tags = [] } = useQuery({ queryKey: ['tags'], queryFn: () => tagsApi.list().then((r) => r.data), enabled: isOpen });
  const [name, setName] = useState('');
  const [color, setColor] = useState('#3B82F6');
  const createTag = useMutation({ mutationFn: () => tagsApi.create(name, color), onSuccess: () => { qc.invalidateQueries({ queryKey: ['tags'] }); setName(''); } });
  const deleteTag = useMutation({ mutationFn: (id: string) => tagsApi.delete(id), onSuccess: () => qc.invalidateQueries({ queryKey: ['tags'] }) });
  const tagFile = useMutation({ mutationFn: (tagId: string) => tagsApi.tagFile(fileId!, tagId), onSuccess: () => qc.invalidateQueries({ queryKey: ['folder-contents'] }) });
  const untagFile = useMutation({ mutationFn: (tagId: string) => tagsApi.untagFile(fileId!, tagId), onSuccess: () => qc.invalidateQueries({ queryKey: ['folder-contents'] }) });

  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" data-testid="tag-manager">
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 w-full max-w-md" onClick={(e) => e.stopPropagation()}>
        <div className="flex justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Tags</h3>
          <button onClick={onClose}><X className="h-5 w-5" /></button>
        </div>
        <div className="flex gap-2 mb-4">
          <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Tag name" className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-sm" />
          <input type="color" value={color} onChange={(e) => setColor(e.target.value)} className="w-10 h-10 rounded" />
          <button onClick={() => createTag.mutate()} disabled={!name.trim()} className="p-2 bg-blue-600 text-white rounded-lg"><Plus className="h-4 w-4" /></button>
        </div>
        <div className="space-y-2 max-h-60 overflow-y-auto">
          {tags.map((tag) => (
            <div key={tag.id} className="flex items-center justify-between p-2 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: tag.color }} />
                <span className="text-sm text-gray-900 dark:text-white">{tag.name}</span>
                <span className="text-xs text-gray-500">({tag.file_count})</span>
              </div>
              <div className="flex gap-1">
                {fileId && <button onClick={() => tagFile.mutate(tag.id)} className="text-xs text-blue-600">Assign</button>}
                <button onClick={() => deleteTag.mutate(tag.id)} className="p-1 text-red-500"><Trash2 className="h-3 w-3" /></button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
