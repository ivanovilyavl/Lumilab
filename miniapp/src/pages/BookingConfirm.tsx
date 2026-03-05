import { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { createBooking } from '../hooks/useApi';
import type { MasterType } from '../types';

interface Props {
  master: MasterType;
  clientName: string;
  clientPhone: string;
}

export default function BookingConfirm({ master, clientName, clientPhone }: Props) {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const serviceId = params.get('id');
  const date = params.get('date');
  const time = params.get('time');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const service = master.services.find((s) => s.id === Number(serviceId));

  if (!service || !date || !time) {
    return <div className="error">Параметры не указаны</div>;
  }

  const dateObj = new Date(date + 'T00:00:00');
  const displayDate = dateObj.toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'long',
    weekday: 'short',
  });

  // Get Telegram user id if available
  const tgUser = window.Telegram?.WebApp?.initDataUnsafe?.user;

  const handleConfirm = async () => {
    setSubmitting(true);
    setError(null);
    try {
      await createBooking({
        master_id: master.id,
        service_id: service.id,
        date: date,
        start_time: time,
        client_name: clientName,
        client_phone: clientPhone || undefined,
        client_telegram_id: tgUser?.id,
      });
      navigate('/success');
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Ошибка при создании записи';
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div>
      <button
        className="back-link"
        onClick={() => navigate(`/contact?id=${serviceId}&date=${date}&time=${time}`)}
      >
        ← Назад
      </button>

      <div className="section-title">Подтверждение записи</div>

      <div className="summary-card">
        <div className="summary-row">
          <span className="summary-label">Мастер</span>
          <span className="summary-value">{master.display_name}</span>
        </div>
        <div className="summary-row">
          <span className="summary-label">Услуга</span>
          <span className="summary-value">{service.name}</span>
        </div>
        <div className="summary-row">
          <span className="summary-label">Дата</span>
          <span className="summary-value">{displayDate}</span>
        </div>
        <div className="summary-row">
          <span className="summary-label">Время</span>
          <span className="summary-value">{time}</span>
        </div>
        <div className="summary-row">
          <span className="summary-label">Длительность</span>
          <span className="summary-value">{service.duration_min} мин</span>
        </div>
        <div className="summary-row">
          <span className="summary-label">Стоимость</span>
          <span className="summary-value">{service.price} ₽</span>
        </div>
        <div className="summary-row">
          <span className="summary-label">Ваше имя</span>
          <span className="summary-value">{clientName}</span>
        </div>
        {clientPhone && (
          <div className="summary-row">
            <span className="summary-label">Телефон</span>
            <span className="summary-value">{clientPhone}</span>
          </div>
        )}
      </div>

      {error && <div className="error">{error}</div>}

      <button
        className="btn-primary"
        disabled={submitting}
        onClick={handleConfirm}
      >
        {submitting ? 'Отправляем...' : 'Подтвердить запись'}
      </button>
    </div>
  );
}
