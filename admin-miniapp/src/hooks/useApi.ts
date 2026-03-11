import { useState, useEffect, useCallback } from 'react';
import type { MasterItem, AdminClientItem, MessageResult } from '../types';

const API_BASE = import.meta.env.VITE_API_URL || '';

async function fetchJson<T>(url: string, initData: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, {
    ...options,
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

export async function sendAdminMastersMessage(
  initData: string,
  masterIds: number[],
  text: string,
): Promise<MessageResult> {
  return fetchJson<MessageResult>('/api/admin/masters/message', initData, {
    method: 'POST',
    body: JSON.stringify({ master_ids: masterIds, text }),
  });
}

export async function sendAdminClientsMessage(
  initData: string,
  tgHashes: string[],
  text: string,
): Promise<MessageResult> {
  return fetchJson<MessageResult>('/api/admin/clients/message', initData, {
    method: 'POST',
    body: JSON.stringify({ tg_hashes: tgHashes, text }),
  });
}
