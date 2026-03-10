import { useState, useMemo } from 'react';
import type { MasterBookingItem } from '../types';

const DAY_NAMES = ['Вс', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб'];
const MONTH_NAMES = ['янв', 'фев', 'мар', 'апр', 'май', 'июн', 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек'];

function toYMD(d: Date): string {
  return d.toISOString().slice(0, 10);
}

interface Props {
  bookings: MasterBookingItem[];
}

export default function MasterCalendar({ bookings }: Props) {
  const today = toYMD(new Date());
  const [selectedDate, setSelectedDate] = useState<string>(today);

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

  // Bookings set for dot indicators
  const bookedDates = useMemo(() => new Set(bookings.map((b) => b.date)), [bookings]);

  // Bookings for selected date
  const dayBookings = useMemo(
    () => bookings.filter((b) => b.date === selectedDate),
    [bookings, selectedDate],
  );

  return (
    <div className="calendar-page">
      <div className="section-title">Расписание</div>

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
                <div className="booking-client">{b.client_pseudo}</div>
              </div>
              <span className={`booking-status ${b.status}`}>
                {b.status === 'confirmed' ? 'подтверждено' : 'ожидает'}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
