export interface ServiceType {
  id: number;
  name: string;
  description: string | null;
  price: number;
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
  display_name: string;
  bio: string | null;
  photo_file_id: string | null;
  niche: string | null;
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
