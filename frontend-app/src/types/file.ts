export interface FileItem {
  id: string;
  name: string;
  mime_type: string | null;
  size: number;
  storage_key: string | null;
  owner_id: string;
  parent_folder_id: string | null;
  is_folder: boolean;
  content_hash: string | null;
  thumbnail_key: string | null;
  is_trashed: boolean;
  trashed_at: string | null;
  created_at: string;
  updated_at: string;
  is_starred?: boolean;
  share_count?: number;
  version_count?: number;
  tags?: TagInfo[];
}

export interface TagInfo {
  id: string;
  name: string;
  color: string;
}

export interface FileVersion {
  id: string;
  file_id: string;
  version_number: number;
  size: number;
  content_hash: string | null;
  created_by: string;
  created_at: string;
}

export interface BreadcrumbItem {
  id: string | null;
  name: string;
}

export interface FolderTreeNode {
  id: string;
  name: string;
  children: FolderTreeNode[];
}

export interface UploadProgress {
  id: string;
  file: File;
  progress: number;
  status: 'pending' | 'uploading' | 'complete' | 'error';
  error?: string;
}

export type ViewMode = 'grid' | 'list';
export type SortField = 'name' | 'size' | 'created_at' | 'updated_at';
export type SortOrder = 'asc' | 'desc';
