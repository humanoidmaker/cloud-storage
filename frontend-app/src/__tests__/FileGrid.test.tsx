import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';
import { FileGrid } from '../components/files/FileGrid';

const mockFiles = [
  { id: '1', name: 'Documents', is_folder: true, size: 0, mime_type: null, owner_id: 'u1', parent_folder_id: null, is_trashed: false, storage_key: null, content_hash: null, thumbnail_key: null, trashed_at: null, created_at: '2024-01-01T00:00:00Z', updated_at: '2024-01-01T00:00:00Z' },
  { id: '2', name: 'photo.jpg', is_folder: false, size: 1024, mime_type: 'image/jpeg', owner_id: 'u1', parent_folder_id: null, is_trashed: false, storage_key: 'k', content_hash: null, thumbnail_key: null, trashed_at: null, created_at: '2024-01-01T00:00:00Z', updated_at: '2024-01-01T00:00:00Z' },
];

describe('FileGrid', () => {
  it('renders grid of file cards', () => {
    render(<FileGrid files={mockFiles} selectedIds={[]} onSelect={vi.fn()} onOpen={vi.fn()} onContextMenu={vi.fn()} />);
    expect(screen.getByTestId('file-grid')).toBeDefined();
  });

  it('handles empty state', () => {
    render(<FileGrid files={[]} selectedIds={[]} onSelect={vi.fn()} onOpen={vi.fn()} onContextMenu={vi.fn()} />);
    expect(screen.getByTestId('empty-state')).toBeDefined();
  });

  it('handles loading state', () => {
    render(<FileGrid files={[]} selectedIds={[]} onSelect={vi.fn()} onOpen={vi.fn()} onContextMenu={vi.fn()} isLoading />);
    expect(screen.getByTestId('file-grid-loading')).toBeDefined();
  });
});
