export interface Share {
  id: string;
  file_id: string;
  shared_by: string;
  shared_with_user_id: string | null;
  shared_with_email: string | null;
  share_token: string | null;
  permission: 'view' | 'edit' | 'admin';
  has_password: boolean;
  expires_at: string | null;
  created_at: string;
}

export interface SharedFile {
  file: {
    id: string;
    name: string;
    mime_type: string | null;
    size: number;
    is_folder: boolean;
  };
  permission: string;
  shared_by_name: string;
  shared_at: string;
}

export interface ShareCreateRequest {
  file_id: string;
  shared_with_email?: string;
  permission: string;
  create_link?: boolean;
  password?: string;
  expires_at?: string;
}
