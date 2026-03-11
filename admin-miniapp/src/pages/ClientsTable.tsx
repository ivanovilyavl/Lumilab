import { useState, useMemo } from 'react';
import { useAdminClients, sendAdminClientsMessage } from '../hooks/useApi';
import type { MessageResult } from '../types';

interface Props {
  initData: string;
}

type ViewMode = 'cards' | 'table';

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
  const [viewMode, setViewMode] = useState<ViewMode>('cards');
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [showMsg, setShowMsg] = useState(false);
  const [msgText, setMsgText] = useState('');
  const [sending, setSending] = useState(false);
  const [sendResult, setSendResult] = useState<MessageResult | null>(null);

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

  function toggleSelect(tgHash: string, hasConsent: boolean) {
    if (!hasConsent) return;
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(tgHash)) next.delete(tgHash); else next.add(tgHash);
      return next;
    });
  }

  function selectAllConsented() {
    const all = filtered.filter((c) => c.client_consent_given && c.tg_hash).map((c) => c.tg_hash!);
    if (selected.size === all.length && all.every((h) => selected.has(h))) {
      setSelected(new Set());
    } else {
      setSelected(new Set(all));
    }
  }

  async function handleSend() {
    if (!msgText.trim() || selected.size === 0) return;
    setSending(true);
    setSendResult(null);
    try {
      const result = await sendAdminClientsMessage(initData, Array.from(selected), msgText.trim());
      setSendResult(result);
      setMsgText('');
    } catch {
      setSendResult({ sent: 0, failed: selected.size, no_contact: 0 });
    } finally {
      setSending(false);
    }
  }

  const consentedCount = useMemo(
    () => filtered.filter((c) => c.client_consent_given && c.tg_hash).length,
    [filtered],
  );

  if (loading) return <div className="admin-loading">Загрузка клиентов...</div>;
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
                  {sendResult.no_contact > 0 && ` · 🚫 Нет в Redis: ${sendResult.no_contact}`}
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

      {/* Search */}
      <input
        type="search"
        className="admin-search"
        placeholder="Поиск по псевдониму..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />

      {/* Filter tabs + view toggle */}
      <div className="filter-row">
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
            Telegram ({stats.tg})
          </button>
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
        <div className="admin-empty">Нет клиентов по фильтру</div>
      )}

      {consentedCount > 0 && (
        <button className="select-all-btn" onClick={selectAllConsented}>
          {selected.size === consentedCount ? 'Снять выделение' : `Выбрать всех с согласием (${consentedCount})`}
        </button>
      )}

      {/* Cards view */}
      {viewMode === 'cards' && (
        <div className="admin-list">
          {filtered.map((client) => (
            <div
              key={client.tg_hash || `manual:${client.pseudo}`}
              className={`client-card-admin${client.tg_hash && client.client_consent_given && selected.has(client.tg_hash) ? ' selected' : ''}`}
              onClick={() => client.tg_hash && toggleSelect(client.tg_hash, client.client_consent_given)}
            >
              {client.client_consent_given && client.tg_hash && (
                <input
                  type="checkbox"
                  className="admin-card-checkbox"
                  checked={selected.has(client.tg_hash)}
                  onChange={() => toggleSelect(client.tg_hash!, client.client_consent_given)}
                  onClick={(e) => e.stopPropagation()}
                />
              )}
              <div className={`client-avatar-admin${client.is_manual ? ' manual' : ''}`}>
                {clientInitial(client.pseudo)}
              </div>
              <div className="client-info-admin">
                <div className="client-name-admin">
                  {client.pseudo}
                  {client.is_manual && (
                    <span className="badge badge-manual">ручная запись</span>
                  )}
                  {!client.client_consent_given && client.tg_hash && (
                    <span className="badge badge-no-consent">нет согласия</span>
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
      )}

      {/* Table view */}
      {viewMode === 'table' && (
        <div className="data-table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th></th>
                <th>Клиент</th>
                <th>Тип</th>
                <th>Записей</th>
                <th>Мастеров</th>
                <th>Последний</th>
                <th>Услуги</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((client) => (
                <tr
                  key={client.tg_hash || `manual:${client.pseudo}`}
                  className={client.tg_hash && selected.has(client.tg_hash) ? 'row-selected' : ''}
                  onClick={() => client.tg_hash && toggleSelect(client.tg_hash, client.client_consent_given)}
                >
                  <td onClick={(e) => e.stopPropagation()}>
                    {client.client_consent_given && client.tg_hash && (
                      <input
                        type="checkbox"
                        checked={selected.has(client.tg_hash)}
                        onChange={() => toggleSelect(client.tg_hash!, client.client_consent_given)}
                      />
                    )}
                  </td>
                  <td>
                    <div className="td-client">
                      <span>{client.pseudo}</span>
                      {client.tg_hash && (
                        <span className="client-hash" title={client.tg_hash}>
                          {shortHash(client.tg_hash)}
                        </span>
                      )}
                    </div>
                  </td>
                  <td>
                    {client.is_manual
                      ? <span className="badge badge-manual">ручная</span>
                      : <span className="badge badge-active">TG</span>}
                    {!client.client_consent_given && client.tg_hash && (
                      <span className="badge badge-no-consent" style={{ marginLeft: 4 }}>нет согл.</span>
                    )}
                  </td>
                  <td className="td-num">{client.total_bookings}</td>
                  <td className="td-num">{client.masters_count}</td>
                  <td className="td-date">{formatDate(client.last_booking_date)}</td>
                  <td className="td-services">
                    {client.services.slice(0, 2).join(', ')}
                    {client.services.length > 2 && ` +${client.services.length - 2}`}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
