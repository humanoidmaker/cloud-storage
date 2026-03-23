export interface AdminUser {
  id: string;
  email: string;
  name: string;
  role: string;
  storage_used: number;
  storage_quota: number;
  is_active: boolean;
  created_at: string;
}

export interface DashboardStats {
  total_users: number;
  active_users: number;
  total_storage_used: number;
  total_files: number;
  total_shares: number;
  recent_activity: ActivityEntry[];
  user_growth: DataPoint[];
  storage_trend: DataPoint[];
}

export interface ActivityEntry {
  id: string;
  user_name: string;
  action: string;
  created_at: string;
}

export interface DataPoint {
  date: string;
  value: number;
}

export interface SystemHealth {
  minio: HealthStatus;
  postgres: HealthStatus;
  redis: HealthStatus;
  celery: HealthStatus;
  api: HealthStatus;
}

export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  color: 'green' | 'yellow' | 'red';
  error?: string;
  [key: string]: unknown;
}

export interface AdminSettings {
  default_quota_bytes: number;
  max_upload_size_bytes: number;
  allowed_extensions: string;
  registration_enabled: boolean;
  trash_auto_purge_days: number;
  max_file_versions: number;
}

export interface StorageBreakdownItem {
  user_id: string;
  user_name: string;
  user_email: string;
  files_count: number;
  folders_count: number;
  storage_used: number;
  storage_quota: number;
  utilization_percent: number;
}
