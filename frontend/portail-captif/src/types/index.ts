// Types pour l'application Captive Portal

export interface Promotion {
  id: number
  code: string
  name: string
  description?: string | null
  year?: number | null
  is_active: boolean
  user_count?: number
  active_user_count?: number
  created_at?: string
  updated_at?: string
}

export interface PromotionList {
  id: number
  code: string
  name: string
  is_active: boolean
}

export interface User {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
  promotion?: number | null  // ID de la promotion
  promotion_detail?: PromotionList | null  // Détails de la promotion
  matricule?: string | null
  phone_number: string | null
  mac_address: string | null
  ip_address: string | null
  is_voucher_user: boolean
  voucher_code: string | null
  is_active: boolean
  is_staff?: boolean
  is_superuser?: boolean
  is_radius_activated?: boolean
  is_radius_enabled?: boolean  // Nouveau: statut RADIUS
  role_name?: string  // 'admin' | 'user'
  date_joined: string
  created_at: string
  updated_at: string
}

export interface AuthTokens {
  access: string
  refresh: string
}

export interface LoginResponse {
  user: User
  tokens: AuthTokens
  message: string
}

export interface RegisterData {
  username: string
  email: string
  password: string
  password2: string
  first_name?: string
  last_name?: string
  phone_number?: string
}

export interface LoginCredentials {
  username: string
  password: string
}

export interface Device {
  id: number
  user: number
  mac_address: string
  device_type: 'mobile' | 'desktop' | 'tablet' | 'other'
  hostname: string | null
  user_agent: string | null
  ip_address: string | null
  is_active: boolean
  first_seen: string
  last_seen: string
}

export interface Session {
  id: number
  user: number
  device: number
  session_id: string
  ip_address: string
  mac_address: string
  status: 'active' | 'expired' | 'terminated'
  start_time: string
  end_time: string | null
  timeout_duration: number
  bytes_in: number
  bytes_out: number
  packets_in: number
  packets_out: number
  total_bytes: number
  is_expired: boolean
}

export interface SessionStatistics {
  total_sessions: number
  active_sessions: number
  total_data_transferred: number
  average_session_duration_seconds: number
  average_session_duration_minutes: number
}

export interface Voucher {
  id: number
  code: string
  status: 'active' | 'used' | 'expired' | 'revoked'
  duration: number
  max_devices: number
  used_count: number
  valid_from: string
  valid_until: string
  used_by: number | null
  used_at: string | null
  created_by: number
  created_by_username?: string
  created_at: string
  notes: string | null
  is_valid: boolean
}

export interface VoucherValidation {
  valid: boolean
  voucher?: Voucher
}

export interface MikrotikRouter {
  id: number
  name: string
  host: string
  port: number
  username: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface APIError {
  detail?: string
  message?: string
  errors?: Record<string, string[]>
}

export interface BlockedSite {
  id: number
  url: string
  type: 'blacklist' | 'whitelist'
  reason: string | null
  is_active: boolean
  added_by: number | null
  added_by_username?: string
  added_date: string
  updated_at: string
}

export interface UserQuota {
  id: number
  user: number
  user_username?: string
  daily_limit: number
  weekly_limit: number
  monthly_limit: number
  daily_limit_gb: number
  weekly_limit_gb: number
  monthly_limit_gb: number
  used_today: number
  used_week: number
  used_month: number
  used_today_gb: number
  used_week_gb: number
  used_month_gb: number
  daily_usage_percent: number
  weekly_usage_percent: number
  monthly_usage_percent: number
  last_daily_reset: string
  last_weekly_reset: string
  last_monthly_reset: string
  is_active: boolean
  is_exceeded: boolean
  created_at: string
  updated_at: string
}

export interface ActivatedUser {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
  promotion: string
  matricule: string
  radius_password: string
  session_timeout: string
  bandwidth_limit: string
  message: string
}

export interface FailedUser {
  id: number
  username?: string
  error: string
}

export interface RadiusActivationResponse {
  success: boolean
  message: string
  activated_users: ActivatedUser[]
  failed_users: FailedUser[]
  summary: {
    total_requested: number
    activated: number
    failed: number
  }
  important_note: string
}
