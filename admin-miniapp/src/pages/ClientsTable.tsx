import { useState, useMemo } from 'react';
import type { AdminClientItem } from '../types';
import { useAdminClients } from '../hooks/useApi';

interface Props {
  initData: string;
}

function formatDate(iso: string | null): string {
  if (!iso) return '—';
  const [y, m, d] = iso.split('-');
  return `${d}.${m}.${y.slice(2)}`;
}

function clientInitial(pseudo: string): string {
  return pseudo.trim().charAt(0).toUpperCase() || '?';
}

function shortHash(hash: string | null): string {
  if (!hash) return '';
  return hash.slice(0, 8) + '…';
}

export default function ClientsTable({ initData }: Props) {
  const { clients, loading, error } = useAdminClients(initData);
  const [search, setSearch] = useState('');
  const [showManual, setShowManual] = useState(true);

  const filtered = useMemo(() => {
    let list = clients;
    if (!showManual) list = list.filter((c) => !c.is_manual);
    if (search.trim()) {
      const q = search.trim().toLowerCase();
      list = list.filter((c) => c.pseudo.toLowerCase().includes(q));
    }
    return list;
  }, [clients, search, showManual]);

  const stats = useMemo(() => ({
    total: clients.length,
    tg: clients.filter((c) => !c.is_manual).length,
    manual: clients.filter((c) => c.is_manual).length,
    totalBookings: clients.reduce((s, c) => s + c.total_bookings, 0),
  }), [clients]);

  if (loading) return <div className="admin-loading">Загрузка клиентов...</div>;
  if (error) return <div className="admin-error">{error}</div>;

  return (
    <div className="admin-page">
      {/* Stats */}
      <div className="stats-row">
        <div className="stat-card">
          <div className="stat-value">{stats.total}</div>
          <div className="stat-label">Уникальных</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats.tg}</div>
          <div className="stat-label">Telegram</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats.manual}</div>
          <div className="stat-label">Ручные</div>
        </div>
        <div className="stat-card stat-card--accent">
          <div className="stat-value">{stats.totalBookings}</div>
          <div className="stat-label">Записей</div>
        </div>
      </div>

      {/* Search + toggle */}
      <input
        type="search"
        className="admin-search"
        placeholder="Поиск по псевдониму..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />

      <div className="filter-tabs">
        <button
          className={`filter-tab${showManual ? ' active' : ''}`}
          onClick={() => setShowManual(true)}
        >
          Все ({clients.length})
        </button>
        <button
          className={`filter-tab${!showManual ? ' active' : ''}`}
          onClick={() => setShowManual(false)}
        >
          Только Telegram ({stats.tg})
        </button>
      </div>

      {/* List */}
      <div className="admin-list">
        {filtered.length === 0 && (
          <div className="admin-empty">Нет клиентов по фильтру</div>
        )}
        {filtered.map((client, i) => (
          <div key={client.tg_hash || `manual-${i}`} className="client-card-admin">
            <div
              className={`client-avatar-admin${client.is_manual ? ' manual' : ''}`}
            >
              {clientInitial(client.pseudo)}
            </div>
            <div className="client-info-admin">
              <div className="client-name-admin">
                {client.pseudo}
                {client.is_manual && (
                  <span className="badge badge-manual">ручная запись</span>
                )}
              </div>
              <div className="client-meta-admin">
                {client.tg_hash && (
                  <span className="client-hash" title={client.tg_hash}>
                    {shortHash(client.tg_hash)}
                  </span>
                )}
                <span>📅 {client.total_bookings}</span>
                {client.masters_count > 1 && (
                  <span>👤 {client.masters_count} мастера</span>
                )}
                {client.last_booking_date && (
                  <span>Последний: {formatDate(client.last_booking_date)}</span>
                )}
              </div>
              {client.services.length > 0 && (
                <div className="client-services-admin">
                  {client.services.map((s) => (
                    <span key={s} className="service-chip">{s}</span>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
