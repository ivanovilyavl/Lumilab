import { useNavigate, useSearchParams } from 'react-router-dom';
import { useSlots } from '../hooks/useApi';
import type { MasterType } from '../types';

interface Props {
  master: MasterType;
  onSelectSlot: (time: string) => void;
}

export default function SlotPicker({ master, onSelectSlot }: Props) {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const serviceId = params.get('id');
  const date = params.get('date');

  const { slots, loading } = useSlots(master.id, date, serviceId ? Number(serviceId) : null);

  const service = master.services.find((s) => s.id === Number(serviceId));

  if (!service || !date) {
    return <div className="error">Параметры не указаны</div>;
  }

  // Format date for display
  const dateObj = new Date(date + 'T00:00:00');
  const displayDate = dateObj.toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'long',
    weekday: 'short',
  });

  return (
    <div>
      <button className="back-link" onClick={() => navigate(`/service?id=${serviceId}`)}>
        ← Назад
      </button>

      <div className="section-title">
        {service.name} · {displayDate}
      </div>

      <div className="section-title">Выберите время</div>

      {loading && <div className="loading">Загрузка слотов...</div>}

      {!loading && slots.length === 0 && (
        <div className="no-slots">На эту дату нет свободного времени. Попробуйте другую дату.</div>
      )}

      {!loading && slots.length > 0 && (
        <div className="slot-grid">
          {slots.map((slot) => (
            <button
              key={slot.start_time}
              className="slot-btn"
              onClick={() => {
                onSelectSlot(slot.start_time);
                navigate(`/consent?id=${serviceId}&date=${date}&time=${slot.start_time}`);
              }}
            >
              {slot.start_time}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
