import { useState, useEffect, useCallback } from 'react';
import type { MasterItem, AdminClientItem } from '../types';

const API_BASE = import.meta.env.VITE_API_URL || '';

async function fetchJson<T>(url: string, initData: string): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, {
    headers: {
      'Content-Type': 'application/json',
      'X-Telegram-Init-Data': initData,
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Network error' }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export function useMasters(initData: string | null) {
  const [masters, setMasters] = useState<MasterItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [trigger, setTrigger] = useState(0);

  const refetch = useCallback(() => setTrigger((n) => n + 1), []);

  useEffect(() => {
    if (!initData) return;
    setLoading(true);
    setError(null);
    fetchJson<MasterItem[]>('/api/admin/masters', initData)
      .then(setMasters)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [initData, trigger]);

  return { masters, loading, error, refetch };
}

export function useAdminClients(initData: string | null) {
  const [clients, setClients] = useState<AdminClientItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [trigger, setTrigger] = useState(0);

  const refetch = useCallback(() => setTrigger((n) => n + 1), []);

  useEffect(() => {
    if (!initData) return;
    setLoading(true);
    setError(null);
    fetchJson<AdminClientItem[]>('/api/admin/clients', initData)
      .then(setClients)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [initData, trigger]);

  return { clients, loading, error, refetch };
}
