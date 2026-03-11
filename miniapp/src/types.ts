export interface ServiceType {
  id: number;
  name: string;
  description: string | null;
  price: number | null;
  duration_min: number;
}

export interface QAItemType {
  id: number;
  question: string;
  answer: string;
}

export interface MasterType {
  id: number;
  username: string;
  display_name: string | null;
  bio: string | null;
  photo_file_id: string | null;
  niche: string | null;
  language: string;
  currency: string;
  accepting_bookings: boolean;
  services: ServiceType[];
  qa_items: QAItemType[];
}

export interface SlotType {
  start_time: string; // "HH:MM"
  end_time: string;
}

export interface BookingResult {
  id: number;
  status: string;
  master_name: string;
  service_name: string;
  date: string;
  start_time: string;
  end_time: string;
  client_pseudo: string;
}

export interface ClientItem {
  client_key: string;
  tg_hash: string | null;
  pseudo: string;
  total_bookings: number;
  last_booking_date: string | null;
  next_booking_date: string | null;
  services: string[];
  note: string | null;
  can_message: boolean;
  is_active: boolean;
}

export interface MasterBookingItem {
  id: number;
  date: string;
  start_time: string;
  end_time: string;
  status: string;
  service_name: string;
  client_pseudo: string;
  client_notes: string | null;
}
