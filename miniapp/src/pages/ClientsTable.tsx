import { useState, useMemo } from 'react';
import type { ClientItem, MasterType } from '../types';
import { useClients, updateClientNote, sendClientsMessage } from '../hooks/useApi';

interface Props {
  master: MasterType;
  initData: string;
}

type FilterTab = 'all' | 'active' | 'inactive';
type ViewMode = 'cards' | 'table';

function formatDate(iso: string | null): string {
  if (!iso) return '—';
  const [y, m, d] = iso.split('-');
  return `${d}.${m}.${y.slice(2)}`;
}

function clientInitial(pseudo: string): string {
  return pseudo.trim().charAt(0).toUpperCase() || '?';
}

export default function ClientsTable({ master, initData }: Props) {
  const { clients, loading, refetch } = useClients(master.username, initData);

  const [filter, setFilter] = useState<FilterTab>('all');
  const [search, setSearch] = useState('');
  const [viewMode, setViewMode] = useState<ViewMode>('cards');
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [editingKey, setEditingKey] = useState<string | null>(null);
  const [editingNote, setEditingNote] = useState('');
  const [savingNote, setSavingNote] = useState(false);
  const [showMsg, setShowMsg] = useState(false);
  const [msgText, setMsgText] = useState('');
  const [sending, setSending] = useState(false);
  const [sendResult, setSendResult] = useState<{ sent: number; failed: number; no_contact: number } | null>(null);

  const filtered = useMemo(() => {
    let list = clients;
    if (filter === 'active') list = list.filter((c) => c.is_active);
    if (filter === 'inactive') list = list.filter((c) => !c.is_active);
    if (search.trim()) {
      const q = search.trim().toLowerCase();
      list = list.filter((c) => c.pseudo.toLowerCase().includes(q));
    }
    return list;
  }, [clients, filter, search]);

  function toggleSelect(key: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }

  function toggleAll() {
    if (selected.size === filtered.length) {
      setSelected(new Set());
    } else {
      setSelected(new Set(filtered.map((c) => c.client_key)));
    }
  }

  function startEditNote(client: ClientItem) {
    setEditingKey(client.client_key);
    setEditingNote(client.note || '');
  }

  async function saveNote(clientKey: string) {
    setSavingNote(true);
    try {
      await updateClientNote(master.username, initData, clientKey, editingNote.trim() || null);
      refetch();
    } finally {
      setSavingNote(false);
      setEditingKey(null);
    }
  }

  async function handleSend() {
    if (!msgText.trim()) return;
    setSending(true);
    setSendResult(null);
    try {
      const keys = Array.from(selected);
      const result = await sendClientsMessage(master.username, initData, keys, msgText.trim());
      setSendResult(result);
      setMsgText('');
    } catch {
      setSendResult({ sent: 0, failed: selected.size, no_contact: 0 });
    } finally {
      setSending(false);
    }
  }

  const selectedCanMessage = useMemo(() => {
    return clients.filter((c) => selected.has(c.client_key) && c.can_message).length;
  }, [clients, selected]);

  if (loading) {
    return <div className="loading">Загрузка клиентов...</div>;
  }

  if (clients.length === 0) {
    return (
      <div className="client-calendar-placeholder">
        <span className="placeholder-icon">👥</span>
        <h3>Клиентов пока нет</h3>
        <p>Здесь появятся все клиенты, которые записывались к вам.</p>
      </div>
    );
  }

  return (
    <div className="clients-page">
      {/* Header */}
      <div className="clients-header">
        <div className="section-title">
          Клиенты <span className="clients-count">{clients.length}</span>
        </div>
      </div>

      {/* Search */}
      <input
        type="search"
        className="clients-search form-input"
        placeholder="Поиск по имени..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />

      {/* Filter tabs + view toggle */}
      <div className="clients-controls-row">
        <div className="clients-filter-tabs">
          {(['all', 'active', 'inactive'] as FilterTab[]).map((t) => (
            <button
              key={t}
              className={`clients-filter-tab${filter === t ? ' active' : ''}`}
              onClick={() => setFilter(t)}
            >
              {t === 'all' ? 'Все' : t === 'active' ? '🟢 Активные' : '⚫ Неактивные'}
            </button>
          ))}
        </div>
        <button
          className={`clients-view-toggle${viewMode === 'table' ? ' active' : ''}`}
          onClick={() => setViewMode(viewMode === 'cards' ? 'table' : 'cards')}
          title={viewMode === 'cards' ? 'Таблица' : 'Карточки'}
        >
          {viewMode === 'cards' ? '⊞' : '☰'}
        </button>
      </div>

      {/* Select all row */}
      {filtered.length > 0 && (
        <div className="clients-select-all">
          <label className="client-checkbox-label">
            <input
              type="checkbox"
              checked={selected.size === filtered.length && filtered.length > 0}
              onChange={toggleAll}
            />
            <span className="clients-select-all-text">
              {selected.size > 0 ? `Выбрано: ${selected.size}` : 'Выбрать всех'}
            </span>
          </label>
        </div>
      )}

      {filtered.length === 0 && (
        <div className="no-slots">Нет клиентов по фильтру</div>
      )}

      {/* Cards view */}
      {viewMode === 'cards' && (
        <div className="clients-list">
          {filtered.map((client) => (
            <div
              key={client.client_key}
              className={`client-card${selected.has(client.client_key) ? ' selected' : ''}`}
            >
              {/* Main row */}
              <div className="client-card-main">
                <label className="client-checkbox-label" onClick={(e) => e.stopPropagation()}>
                  <input
                    type="checkbox"
                    checked={selected.has(client.client_key)}
                    onChange={() => toggleSelect(client.client_key)}
                  />
                </label>

                <div className={`client-avatar${client.is_active ? ' active' : ' inactive'}`}>
                  {clientInitial(client.pseudo)}
                </div>

                <div className="client-info">
                  <div className="client-name">
                    {client.pseudo}
                    <span className={`client-status-badge${client.is_active ? ' active' : ''}`}>
                      {client.is_active ? 'активный' : 'неактивный'}
                    </span>
                  </div>

                  <div className="client-meta">
                    <span title="Всего визитов">📅 {client.total_bookings}</span>
                    {client.last_booking_date && (
                      <span title="Последний визит">Был: {formatDate(client.last_booking_date)}</span>
                    )}
                    {client.next_booking_date && (
                      <span title="Следующий визит" className="client-next">
                        →&nbsp;{formatDate(client.next_booking_date)}
                      </span>
                    )}
                  </div>

                  {client.services.length > 0 && (
                    <div className="client-services">
                      {client.services.map((s) => (
                        <span key={s} className="client-service-chip">{s}</span>
                      ))}
                    </div>
                  )}
                </div>

                <button
                  className="client-note-btn"
                  title={client.note ? 'Редактировать комментарий' : 'Добавить комментарий'}
                  onClick={() => startEditNote(client)}
                >
                  {client.note ? '📝' : '✏️'}
                </button>
              </div>

              {/* Note display */}
              {client.note && editingKey !== client.client_key && (
                <div className="client-note-text" onClick={() => startEditNote(client)}>
                  💬 {client.note}
                </div>
              )}

              {/* Inline note editor */}
              {editingKey === client.client_key && (
                <div className="client-note-editor">
                  <textarea
                    className="client-note-textarea"
                    placeholder="Добавьте комментарий о клиенте..."
                    value={editingNote}
                    onChange={(e) => setEditingNote(e.target.value)}
                    autoFocus
                    rows={2}
                    maxLength={500}
                  />
                  <div className="client-note-actions">
                    <button
                      className="btn-secondary"
                      onClick={() => setEditingKey(null)}
                      disabled={savingNote}
                    >
                      Отмена
                    </button>
                    <button
                      className="btn-primary-inline"
                      onClick={() => saveNote(client.client_key)}
                      disabled={savingNote}
                    >
                      {savingNote ? 'Сохранение...' : 'Сохранить'}
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Table view */}
      {viewMode === 'table' && (
        <div className="clients-table-wrap">
          <table className="clients-table">
            <thead>
              <tr>
                <th>
                  <input
                    type="checkbox"
                    checked={selected.size === filtered.length && filtered.length > 0}
                    onChange={toggleAll}
                  />
                </th>
                <th>Имя</th>
                <th>Статус</th>
                <th>Визитов</th>
                <th>Был</th>
                <th>Следующий</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((client) => (
                <>
                  <tr
                    key={client.client_key}
                    className={`${selected.has(client.client_key) ? 'row-selected' : ''}${!client.is_active ? ' row-inactive' : ''}`}
                  >
                    <td>
                      <input
                        type="checkbox"
                        checked={selected.has(client.client_key)}
                        onChange={() => toggleSelect(client.client_key)}
                      />
                    </td>
                    <td>
                      <div className="td-client-name">
                        {client.pseudo}
                        {client.note && <span className="td-note-dot" title={client.note}>💬</span>}
                      </div>
                      {client.services.length > 0 && (
                        <div className="td-services-mini">
                          {client.services.slice(0, 2).join(', ')}
                          {client.services.length > 2 && ` +${client.services.length - 2}`}
                        </div>
                      )}
                    </td>
                    <td>
                      <span className={`client-status-badge${client.is_active ? ' active' : ''}`}>
                        {client.is_active ? 'акт.' : 'неакт.'}
                      </span>
                    </td>
                    <td className="td-num">{client.total_bookings}</td>
                    <td className="td-date">{formatDate(client.last_booking_date)}</td>
                    <td className="td-date">{formatDate(client.next_booking_date)}</td>
                    <td>
                      <button
                        className="client-note-btn"
                        title={client.note ? 'Редактировать комментарий' : 'Добавить комментарий'}
                        onClick={() => editingKey === client.client_key ? setEditingKey(null) : startEditNote(client)}
                      >
                        {client.note ? '📝' : '✏️'}
                      </button>
                    </td>
                  </tr>
                  {editingKey === client.client_key && (
                    <tr key={`${client.client_key}-note`} className="row-note-editor">
                      <td colSpan={7}>
                        <div className="client-note-editor">
                          <textarea
                            className="client-note-textarea"
                            placeholder="Добавьте комментарий о клиенте..."
                            value={editingNote}
                            onChange={(e) => setEditingNote(e.target.value)}
                            autoFocus
                            rows={2}
                            maxLength={500}
                          />
                          <div className="client-note-actions">
                            <button
                              className="btn-secondary"
                              onClick={() => setEditingKey(null)}
                              disabled={savingNote}
                            >
                              Отмена
                            </button>
                            <button
                              className="btn-primary-inline"
                              onClick={() => saveNote(client.client_key)}
                              disabled={savingNote}
                            >
                              {savingNote ? 'Сохранение...' : 'Сохранить'}
                            </button>
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Sticky send bar */}
      {selected.size > 0 && (
        <div className="clients-send-bar">
          <div className="clients-send-bar-info">
            Выбрано: {selected.size}
            {selectedCanMessage < selected.size && (
              <span className="clients-send-hint">
                {' '}(напишем {selectedCanMessage}, ручные записи без Telegram)
              </span>
            )}
          </div>
          <div className="clients-send-bar-actions">
            <button className="btn-secondary" onClick={() => setSelected(new Set())}>
              Снять
            </button>
            <button
              className="btn-primary-inline"
              onClick={() => { setSendResult(null); setShowMsg(true); }}
              disabled={selectedCanMessage === 0}
            >
              ✉️ Написать
            </button>
          </div>
        </div>
      )}

      {/* Message modal */}
      {showMsg && (
        <div className="modal-overlay" onClick={() => !sending && setShowMsg(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-title">
              Сообщение {selectedCanMessage} клиент{selectedCanMessage === 1 ? 'у' : 'ам'}
            </div>

            {sendResult ? (
              <div className="send-result">
                {sendResult.sent > 0 && <p>✅ Отправлено: {sendResult.sent}</p>}
                {sendResult.failed > 0 && <p>❌ Не доставлено: {sendResult.failed}</p>}
                {sendResult.no_contact > 0 && (
                  <p>⚫ Без Telegram (ручные записи): {sendResult.no_contact}</p>
                )}
                <div className="modal-actions" style={{ marginTop: 16 }}>
                  <button
                    className="btn-primary-inline"
                    onClick={() => { setShowMsg(false); setSelected(new Set()); }}
                  >
                    Готово
                  </button>
                </div>
              </div>
            ) : (
              <>
                <textarea
                  className="client-note-textarea"
                  placeholder="Введите сообщение для клиентов..."
                  value={msgText}
                  onChange={(e) => setMsgText(e.target.value)}
                  rows={4}
                  maxLength={2000}
                  autoFocus
                />
                <div className="msg-char-count">{msgText.length}/2000</div>
                {selectedCanMessage === 0 && (
                  <div className="form-error">
                    Среди выбранных нет клиентов с Telegram
                  </div>
                )}
                <div className="modal-actions">
                  <button
                    className="btn-secondary"
                    onClick={() => setShowMsg(false)}
                    disabled={sending}
                  >
                    Отмена
                  </button>
                  <button
                    className="btn-primary-inline"
                    onClick={handleSend}
                    disabled={sending || !msgText.trim() || selectedCanMessage === 0}
                  >
                    {sending ? 'Отправка...' : 'Отправить'}
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
