import { useMemo } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import type { MasterType } from '../types';

const DAY_NAMES = ['Вс', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб'];
const MONTH_NAMES = ['янв', 'фев', 'мар', 'апр', 'май', 'июн', 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек'];

function formatDate(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

interface Props {
  master: MasterType;
  selectedDate: string | null;
  onSelectDate: (date: string) => void;
}

export default function DatePicker({ master, selectedDate, onSelectDate }: Props) {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const serviceId = params.get('id');

  const service = master.services.find((s) => s.id === Number(serviceId));

  const days = useMemo(() => {
    const result = [];
    const today = new Date();
    for (let i = 0; i < 14; i++) {
      const d = new Date(today);
      d.setDate(today.getDate() + i);
      result.push(d);
    }
    return result;
  }, []);

  if (!service) {
    return <div className="error">Услуга не найдена</div>;
  }

  return (
    <div>
      <button className="back-link" onClick={() => navigate('/')}>
        ← Назад
      </button>

      <div className="section-title">
        {service.name}{service.price !== null ? ` · ${service.price} ₽` : ' · по договорённости'}
      </div>

      <div className="section-title">Выберите дату</div>
      <div className="date-scroll">
        {days.map((d) => {
          const dateStr = formatDate(d);
          const isSelected = selectedDate === dateStr;
          return (
            <div
              key={dateStr}
              className={`date-chip ${isSelected ? 'selected' : ''}`}
              onClick={() => {
                onSelectDate(dateStr);
                navigate(`/slot?id=${serviceId}&date=${dateStr}`);
              }}
            >
              <div className="day-name">{DAY_NAMES[d.getDay()]}</div>
              <div className="day-num">{d.getDate()}</div>
              <div className="month">{MONTH_NAMES[d.getMonth()]}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
