import { useState, useMemo } from 'react';
import { useMasters, sendAdminMastersMessage } from '../hooks/useApi';
import type { MessageResult } from '../types';

interface Props {
  initData: string;
}

type SubFilter = 'all' | 'trial' | 'active' | 'inactive' | 'onboarded';
type ViewMode = 'cards' | 'table';

const SUB_LABELS: Record<string, string> = {
  trial: 'Триал',
  active: 'Платный',
  inactive: 'Неактивный',
  expired: 'Истёк',
};

const LANG_FLAGS: Record<string, string> = {
  ru: '🇷🇺',
  en: '🇬🇧',
  es: '🇪🇸',
};

const CURRENCY_SYMBOLS: Record<string, string> = {
  RUB: '₽',
  USD: '$',
  EUR: '€',
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
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [showMsg, setShowMsg] = useState(false);
  const [msgText, setMsgText] = useState('');
  const [sending, setSending] = useState(false);
  const [sendResult, setSendResult] = useState<MessageResult | null>(null);

  const filtered = useMemo(() => {
    let list = masters;
    if (filter === 'trial') list = list.filter((m) => m.subscription_status === 'trial');
    else if (filter === 'active') list = list.filter((m) => m.subscription_status === 'active');
    else if (filter === 'inactive') list = list.filter((m) => ['inactive', 'expired'].includes(m.subscription_status));
    else if (filter === 'onboarded') list = list.filter((m) => m.is_onboarded);
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

  function toggleSelect(id: number, hasConsent: boolean) {
    if (!hasConsent) return;
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  }

  function selectAllConsented() {
    const allConsented = filtered.filter((m) => m.consent_given).map((m) => m.id);
    if (selected.size === allConsented.length && allConsented.every((id) => selected.has(id))) {
      setSelected(new Set());
    } else {
      setSelected(new Set(allConsented));
    }
  }

  async function handleSend() {
    if (!msgText.trim() || selected.size === 0) return;
    setSending(true);
    setSendResult(null);
    try {
      const result = await sendAdminMastersMessage(initData, Array.from(selected), msgText.trim());
      setSendResult(result);
      setMsgText('');
    } catch {
      setSendResult({ sent: 0, failed: selected.size, no_contact: 0 });
    } finally {
      setSending(false);
    }
  }

  const consentedCount = useMemo(() => filtered.filter((m) => m.consent_given).length, [filtered]);

  if (loading) return <div className="admin-loading">Загрузка мастеров...</div>;
  if (error) return <div className="admin-error">{error}</div>;

  return (
    <div className="admin-page">
      {/* Send bar */}
      {selected.size > 0 && (
        <div className="admin-send-bar">
          {!showMsg ? (
            <>
              <span className="send-bar-count">Выбрано: {selected.size}</span>
              <button className="send-bar-btn" onClick={() => { setShowMsg(true); setSendResult(null); }}>
                ✉️ Написать
              </button>
              <button className="send-bar-clear" onClick={() => setSelected(new Set())}>✕</button>
            </>
          ) : (
            <div className="send-bar-compose">
              <textarea
                className="send-bar-textarea"
                placeholder="Текст сообщения..."
                value={msgText}
                onChange={(e) => setMsgText(e.target.value)}
                maxLength={2000}
                rows={3}
              />
              {sendResult && (
                <div className="send-bar-result">
                  ✅ Отправлено: {sendResult.sent} · ❌ Ошибок: {sendResult.failed}
                  {sendResult.no_contact > 0 && ` · 🚫 Без согласия: ${sendResult.no_contact}`}
                </div>
              )}
              <div className="send-bar-actions">
                <button className="send-bar-cancel" onClick={() => { setShowMsg(false); setMsgText(''); setSendResult(null); }}>
                  Отмена
                </button>
                <button
                  className="send-bar-send"
                  onClick={handleSend}
                  disabled={sending || !msgText.trim()}
                >
                  {sending ? 'Отправка...' : `Отправить (${selected.size})`}
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Stats — click to filter, click active card again to reset */}
      <div className="stats-row">
        <div
          className={`stat-card stat-card--clickable${filter === 'all' ? ' stat-card--active' : ''}`}
          onClick={() => setFilter('all')}
        >
          <div className="stat-value">{stats.total}</div>
          <div className="stat-label">Все</div>
        </div>
        <div
          className={`stat-card stat-card--clickable${filter === 'onboarded' ? ' stat-card--active' : ''}`}
          onClick={() => setFilter(filter === 'onboarded' ? 'all' : 'onboarded')}
        >
          <div className="stat-value">{stats.onboarded}</div>
          <div className="stat-label">Онбординг</div>
        </div>
        <div
          className={`stat-card stat-card--clickable${filter === 'trial' ? ' stat-card--active' : ''}`}
          onClick={() => setFilter(filter === 'trial' ? 'all' : 'trial')}
        >
          <div className="stat-value">{stats.trial}</div>
          <div className="stat-label">Триал</div>
        </div>
        <div
          className={`stat-card stat-card--accent stat-card--clickable${filter === 'active' ? ' stat-card--active' : ''}`}
          onClick={() => setFilter(filter === 'active' ? 'all' : 'active')}
        >
          <div className="stat-value">{stats.paying}</div>
          <div className="stat-label">Платных</div>
        </div>
      </div>

      {/* Search + view toggle */}
      <div className="filter-row">
        <input
          type="search"
          className="admin-search"
          placeholder="Поиск по имени или @username..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <button
          className={`view-toggle${viewMode === 'table' ? ' active' : ''}`}
          onClick={() => setViewMode(viewMode === 'cards' ? 'table' : 'cards')}
          title={viewMode === 'cards' ? 'Таблица' : 'Карточки'}
        >
          {viewMode === 'cards' ? '⊞' : '☰'}
        </button>
      </div>

      {(filter !== 'all' || search.trim()) && (
        <div className="filter-hint">
          Показано: <b>{filtered.length}</b> из <b>{masters.length}</b>
          {' '}
          <button className="filter-reset-btn" onClick={() => { setFilter('all'); setSearch(''); }}>
            сбросить
          </button>
        </div>
      )}

      {consentedCount > 0 && (
        <button className="select-all-btn" onClick={selectAllConsented}>
          {selected.size === consentedCount ? 'Снять выделение' : `Выбрать всех с согласием (${consentedCount})`}
        </button>
      )}

      {filtered.length === 0 && (
        <div className="admin-empty">Нет мастеров по фильтру</div>
      )}

      {/* Cards view */}
      {viewMode === 'cards' && (
        <div className="admin-list">
          {filtered.map((master) => (
            <div
              key={master.id}
              className={`master-card${!master.is_active ? ' inactive' : ''}${selected.has(master.id) ? ' selected' : ''}`}
              onClick={() => toggleSelect(master.id, master.consent_given)}
            >
              {master.consent_given && (
                <input
                  type="checkbox"
                  className="admin-card-checkbox"
                  checked={selected.has(master.id)}
                  onChange={() => toggleSelect(master.id, master.consent_given)}
                  onClick={(e) => e.stopPropagation()}
                />
              )}
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
                    <span title={master.language}>{LANG_FLAGS[master.language] ?? master.language}</span>
                    <span title={master.currency} className="badge badge-inactive" style={{ fontFamily: 'monospace' }}>{CURRENCY_SYMBOLS[master.currency] ?? master.currency}</span>
                    {!master.is_onboarded && (
                      <span className="badge badge-pending">не онбордился</span>
                    )}
                    {!master.consent_given && (
                      <span className="badge badge-no-consent">нет согласия</span>
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
                <th></th>
                <th>@username</th>
                <th>Имя</th>
                <th>Ниша</th>
                <th>Статус</th>
                <th>Язык</th>
                <th>Записей</th>
                <th>Клиентов</th>
                <th>С</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((master) => (
                <tr
                  key={master.id}
                  className={`${!master.is_active ? 'row-inactive' : ''}${selected.has(master.id) ? ' row-selected' : ''}`}
                  onClick={() => toggleSelect(master.id, master.consent_given)}
                >
                  <td onClick={(e) => e.stopPropagation()}>
                    {master.consent_given && (
                      <input
                        type="checkbox"
                        checked={selected.has(master.id)}
                        onChange={() => toggleSelect(master.id, master.consent_given)}
                      />
                    )}
                  </td>
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
                    {!master.consent_given && (
                      <span className="badge badge-no-consent" style={{ marginLeft: 4 }}>нет согл.</span>
                    )}
                  </td>
                  <td title={`${master.language} / ${master.currency}`}>
                    {LANG_FLAGS[master.language] ?? master.language}&nbsp;{CURRENCY_SYMBOLS[master.currency] ?? master.currency}
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
