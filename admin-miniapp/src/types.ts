export interface MasterItem {
  id: number;
  username: string;
  display_name: string | null;
  niche: string | null;
  subscription_status: string; // "trial" | "active" | "inactive" | "expired"
  is_active: boolean;
  is_onboarded: boolean;
  created_at: string; // "YYYY-MM-DD"
  total_bookings: number;
  total_clients: number;
}

export interface AdminClientItem {
  tg_hash: string | null;
  pseudo: string;
  is_manual: boolean;
  total_bookings: number;
  masters_count: number;
  last_booking_date: string | null;
  services: string[];
}
