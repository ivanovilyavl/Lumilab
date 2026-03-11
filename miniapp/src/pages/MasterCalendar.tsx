import { useState, useMemo } from 'react';
import type { MasterBookingItem, MasterType } from '../types';
import { createMasterBooking } from '../hooks/useApi';

const DAY_NAMES = ['Вс', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб'];
const MONTH_NAMES = ['янв', 'фев', 'мар', 'апр', 'май', 'июн', 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек'];

function toYMD(d: Date): string {
  return d.toISOString().slice(0, 10);
}

interface Props {
  bookings: MasterBookingItem[];
  master: MasterType;
  initData: string;
  onBookingCreated: () => void;
}

export default function MasterCalendar({ bookings, master, initData, onBookingCreated }: Props) {
  const today = toYMD(new Date());
  const [selectedDate, setSelectedDate] = useState<string>(today);
  const [showModal, setShowModal] = useState(false);

  // Form state
  const [serviceId, setServiceId] = useState<number>(master.services[0]?.id ?? 0);
  const [formDate, setFormDate] = useState<string>(today);
  const [formTime, setFormTime] = useState<string>('10:00');
  const [clientName, setClientName] = useState<string>('');
  const [clientPhone, setClientPhone] = useState<string>('');
  const [isRecurring, setIsRecurring] = useState<boolean>(false);
  const [recurringEnd, setRecurringEnd] = useState<string>('');
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  // Build 30-day strip
  const days = useMemo(() => {
    const result: Date[] = [];
    const base = new Date();
    base.setHours(0, 0, 0, 0);
    for (let i = 0; i < 30; i++) {
      const d = new Date(base);
      d.setDate(base.getDate() + i);
      result.push(d);
    }
    return result;
  }, []);

  const bookedDates = useMemo(() => new Set(bookings.map((b) => b.date)), [bookings]);
  const dayBookings = useMemo(
    () => bookings.filter((b) => b.date === selectedDate),
    [bookings, selectedDate],
  );

  function openModal() {
    setFormDate(selectedDate);
    setFormTime('10:00');
    setClientName('');
    setClientPhone('');
    setIsRecurring(false);
    setRecurringEnd('');
    setServiceId(master.services[0]?.id ?? 0);
    setFormError(null);
    setShowModal(true);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!clientName.trim()) {
      setFormError('Укажите имя клиента');
      return;
    }
    if (isRecurring && !recurringEnd) {
      setFormError('Укажите дату окончания повтора');
      return;
    }
    setSubmitting(true);
    setFormError(null);
    try {
      const result = await createMasterBooking(master.username, initData, {
        service_id: serviceId,
        date: formDate,
        start_time: formTime,
        client_name: clientName.trim(),
        client_phone: clientPhone.trim() || undefined,
        is_recurring: isRecurring,
        recurrence_end_date: isRecurring ? recurringEnd : undefined,
      });
      setShowModal(false);
      setSelectedDate(formDate);
      onBookingCreated();
      if (result.created === 0) {
        // All slots had conflicts — surface a note? Already handled by API skipping
      }
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : 'Ошибка при создании записи');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="calendar-page">
      <div className="calendar-header">
        <div className="section-title">Расписание</div>
        {master.services.length > 0 && (
          <button className="fab-add" onClick={openModal} aria-label="Добавить запись">
            +
          </button>
        )}
      </div>

      {/* Date strip */}
      <div className="date-scroll">
        {days.map((d) => {
          const ymd = toYMD(d);
          const isSelected = ymd === selectedDate;
          const hasBookings = bookedDates.has(ymd);
          return (
            <button
              key={ymd}
              className={`date-chip${isSelected ? ' selected' : ''}`}
              onClick={() => setSelectedDate(ymd)}
            >
              <div className="day-name">{DAY_NAMES[d.getDay()]}</div>
              <div className="day-num">{d.getDate()}</div>
              <div className="month">{MONTH_NAMES[d.getMonth()]}</div>
              {hasBookings && !isSelected && <div className="booking-dot" />}
            </button>
          );
        })}
      </div>

      {/* Bookings list */}
      {dayBookings.length === 0 ? (
        <div className="no-slots">Нет записей на этот день</div>
      ) : (
        <div className="booking-list">
          {dayBookings.map((b) => (
            <div key={b.id} className="booking-card">
              <div className="booking-time">
                {b.start_time} – {b.end_time}
              </div>
              <div className="booking-info">
                <div className="booking-service">{b.service_name}</div>
                <div className="booking-client">
                  {b.client_pseudo}
                  {b.client_notes && <span className="booking-phone"> · {b.client_notes}</span>}
                </div>
              </div>
              <span className={`booking-status ${b.status}`}>
                {b.status === 'confirmed' ? 'подтверждено' : 'ожидает'}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Add Booking Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-title">Добавить запись</div>
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label className="form-label">Услуга</label>
                <select
                  className="form-input"
                  value={serviceId}
                  onChange={(e) => setServiceId(Number(e.target.value))}
                >
                  {master.services.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name} · {s.duration_min} мин · {s.price} ₽
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Дата</label>
                  <input
                    type="date"
                    className="form-input"
                    value={formDate}
                    min={today}
                    onChange={(e) => setFormDate(e.target.value)}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Время</label>
                  <input
                    type="time"
                    className="form-input"
                    value={formTime}
                    onChange={(e) => setFormTime(e.target.value)}
                    required
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Имя клиента</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="Например: Анна Иванова"
                  value={clientName}
                  onChange={(e) => setClientName(e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Телефон (необязательно)</label>
                <input
                  type="tel"
                  className="form-input"
                  placeholder="+7 999 123-45-67"
                  value={clientPhone}
                  onChange={(e) => setClientPhone(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label className="toggle-label">
                  <input
                    type="checkbox"
                    checked={isRecurring}
                    onChange={(e) => setIsRecurring(e.target.checked)}
                  />
                  <span>Еженедельно</span>
                </label>
              </div>

              {isRecurring && (
                <div className="form-group">
                  <label className="form-label">Повторять до</label>
                  <input
                    type="date"
                    className="form-input"
                    value={recurringEnd}
                    min={formDate}
                    onChange={(e) => setRecurringEnd(e.target.value)}
                    required
                  />
                </div>
              )}

              {formError && <div className="form-error">{formError}</div>}

              <div className="modal-actions">
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => setShowModal(false)}
                >
                  Отмена
                </button>
                <button
                  type="submit"
                  className="btn-primary-inline"
                  disabled={submitting}
                >
                  {submitting ? 'Создание...' : 'Добавить'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
