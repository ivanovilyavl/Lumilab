import { useState, useEffect } from 'react';
import type { MasterType, SlotType, BookingResult, MasterBookingItem } from '../types';

const API_BASE = import.meta.env.VITE_API_URL || '';

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Network error' }));
    throw new Error(error.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export function useMaster(username: string | null) {
  const [master, setMaster] = useState<MasterType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!username) return;
    setLoading(true);
    fetchJson<MasterType>(`/api/master/${username}`)
      .then(setMaster)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [username]);

  return { master, loading, error };
}

export function useSlots(masterId: number | null, date: string | null, serviceId: number | null) {
  const [slots, setSlots] = useState<SlotType[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!masterId || !date || !serviceId) return;
    setLoading(true);
    fetchJson<SlotType[]>(`/api/master/${masterId}/slots?date=${date}&service_id=${serviceId}`)
      .then(setSlots)
      .catch(() => setSlots([]))
      .finally(() => setLoading(false));
  }, [masterId, date, serviceId]);

  return { slots, loading };
}

export function useMasterSchedule(username: string | null, initData: string | null) {
  const [bookings, setBookings] = useState<MasterBookingItem[]>([]);
  const [isOwner, setIsOwner] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!username || !initData) return;
    setLoading(true);
    fetch(`${API_BASE}/api/master/${username}/schedule`, {
      headers: {
        'Content-Type': 'application/json',
        'X-Telegram-Init-Data': initData,
      },
    })
      .then((res) => {
        if (!res.ok) throw new Error('not owner');
        return res.json() as Promise<{ bookings: MasterBookingItem[] }>;
      })
      .then((data) => {
        setBookings(data.bookings);
        setIsOwner(true);
      })
      .catch(() => {
        setIsOwner(false);
      })
      .finally(() => setLoading(false));
  }, [username, initData]);

  return { bookings, isOwner, loading };
}

export async function createBooking(data: {
  master_id: number;
  service_id: number;
  date: string;
  start_time: string;
  client_name: string;
  client_phone?: string;
  client_telegram_id?: number;
}): Promise<BookingResult> {
  return fetchJson<BookingResult>('/api/bookings', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}
