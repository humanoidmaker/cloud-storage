export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ApiError {
  detail: string;
  error_code?: string;
}

export interface Tag {
  id: string;
  name: string;
  color: string;
  user_id: string;
  created_at: string;
  file_count: number;
}

export interface ActivityLog {
  id: string;
  user_id: string;
  user_name?: string;
  action: string;
  file_id: string | null;
  file_name?: string;
  details_json: string | null;
  ip_address: string | null;
  created_at: string;
}
