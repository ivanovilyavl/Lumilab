import { useState, useMemo } from 'react';
import { useMasters } from '../hooks/useApi';

interface Props {
  initData: string;
}

type SubFilter = 'all' | 'trial' | 'active' | 'inactive';
type ViewMode = 'cards' | 'table';

const SUB_LABELS: Record<string, string> = {
  trial: 'Триал',
  active: 'Платный',
  inactive: 'Неактивный',
  expired: 'Истёк',
};

const SUB_CLASS: Record<string, string> = {
  trial: 'badge-trial',
  active: 'badge-active',
  inactive: 'badge-inactive',
  expired: 'badge-inactive',
};

function formatDate(iso: string): string {
  const [y, m, d] = iso.split('-');
  return `${d}.${m}.${y.slice(2)}`;
}

function masterInitial(name: string | null, username: string): string {
  return (name || username).trim().charAt(0).toUpperCase();
}

export default function MastersTable({ initData }: Props) {
  const { masters, loading, error } = useMasters(initData);
  const [filter, setFilter] = useState<SubFilter>('all');
  const [search, setSearch] = useState('');
  const [viewMode, setViewMode] = useState<ViewMode>('cards');

  const filtered = useMemo(() => {
    let list = masters;
    if (filter === 'trial') list = list.filter((m) => m.subscription_status === 'trial');
    else if (filter === 'active') list = list.filter((m) => m.subscription_status === 'active');
    else if (filter === 'inactive') list = list.filter((m) => ['inactive', 'expired'].includes(m.subscription_status));
    if (search.trim()) {
      const q = search.trim().toLowerCase();
      list = list.filter(
        (m) =>
          m.username.toLowerCase().includes(q) ||
          (m.display_name || '').toLowerCase().includes(q),
      );
    }
    return list;
  }, [masters, filter, search]);

  const stats = useMemo(() => ({
    total: masters.length,
    trial: masters.filter((m) => m.subscription_status === 'trial').length,
    paying: masters.filter((m) => m.subscription_status === 'active').length,
    inactive: masters.filter((m) => ['inactive', 'expired'].includes(m.subscription_status)).length,
    onboarded: masters.filter((m) => m.is_onboarded).length,
  }), [masters]);

  if (loading) return <div className="admin-loading">Загрузка мастеров...</div>;
  if (error) return <div className="admin-error">{error}</div>;

  return (
    <div className="admin-page">
      {/* Stats */}
      <div className="stats-row">
        <div className="stat-card">
          <div className="stat-value">{stats.total}</div>
          <div className="stat-label">Всего</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats.onboarded}</div>
          <div className="stat-label">Онбординг</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats.trial}</div>
          <div className="stat-label">Триал</div>
        </div>
        <div className="stat-card stat-card--accent">
          <div className="stat-value">{stats.paying}</div>
          <div className="stat-label">Платных</div>
        </div>
      </div>

      {/* Search */}
      <input
        type="search"
        className="admin-search"
        placeholder="Поиск по имени или @username..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />

      {/* Filter tabs + view toggle */}
      <div className="filter-row">
        <div className="filter-tabs">
          {(['all', 'trial', 'active', 'inactive'] as SubFilter[]).map((t) => (
            <button
              key={t}
              className={`filter-tab${filter === t ? ' active' : ''}`}
              onClick={() => setFilter(t)}
            >
              {t === 'all' ? `Все (${masters.length})` :
               t === 'trial' ? `Триал (${stats.trial})` :
               t === 'active' ? `Платные (${stats.paying})` :
               `Неакт. (${stats.inactive})`}
            </button>
          ))}
        </div>
        <button
          className={`view-toggle${viewMode === 'table' ? ' active' : ''}`}
          onClick={() => setViewMode(viewMode === 'cards' ? 'table' : 'cards')}
          title={viewMode === 'cards' ? 'Таблица' : 'Карточки'}
        >
          {viewMode === 'cards' ? '⊞' : '☰'}
        </button>
      </div>

      {filtered.length === 0 && (
        <div className="admin-empty">Нет мастеров по фильтру</div>
      )}

      {/* Cards view */}
      {viewMode === 'cards' && (
        <div className="admin-list">
          {filtered.map((master) => (
            <div key={master.id} className={`master-card${!master.is_active ? ' inactive' : ''}`}>
              <div className="master-card-main">
                <div className={`master-avatar${master.is_active ? '' : ' inactive'}`}>
                  {masterInitial(master.display_name, master.username)}
                </div>
                <div className="master-info">
                  <div className="master-name">
                    <span className="master-username">@{master.username}</span>
                    {master.display_name && (
                      <span className="master-display-name">{master.display_name}</span>
                    )}
                    <span className={`badge ${SUB_CLASS[master.subscription_status] || 'badge-inactive'}`}>
                      {SUB_LABELS[master.subscription_status] || master.subscription_status}
                    </span>
                    {!master.is_onboarded && (
                      <span className="badge badge-pending">не онбордился</span>
                    )}
                  </div>
                  <div className="master-meta">
                    {master.niche && <span className="niche-chip">{master.niche}</span>}
                    <span>📅 {master.total_bookings} записей</span>
                    <span>👥 {master.total_clients} клиентов</span>
                    <span className="master-date">с {formatDate(master.created_at)}</span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Table view */}
      {viewMode === 'table' && (
        <div className="data-table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>@username</th>
                <th>Имя</th>
                <th>Ниша</th>
                <th>Статус</th>
                <th>Записей</th>
                <th>Клиентов</th>
                <th>С</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((master) => (
                <tr key={master.id} className={!master.is_active ? 'row-inactive' : ''}>
                  <td className="td-mono">@{master.username}</td>
                  <td>{master.display_name || '—'}</td>
                  <td>{master.niche || '—'}</td>
                  <td>
                    <span className={`badge ${SUB_CLASS[master.subscription_status] || 'badge-inactive'}`}>
                      {SUB_LABELS[master.subscription_status] || master.subscription_status}
                    </span>
                    {!master.is_onboarded && (
                      <span className="badge badge-pending" style={{ marginLeft: 4 }}>·</span>
                    )}
                  </td>
                  <td className="td-num">{master.total_bookings}</td>
                  <td className="td-num">{master.total_clients}</td>
                  <td className="td-date">{formatDate(master.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
