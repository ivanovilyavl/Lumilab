import { useNavigate, useSearchParams } from 'react-router-dom';
import type { MasterType } from '../types';

interface Props {
  master: MasterType;
}

export default function ConsentScreen({ master }: Props) {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const serviceId = params.get('id');
  const date = params.get('date');
  const time = params.get('time');

  if (!serviceId || !date || !time) {
    return <div className="error">Параметры не указаны</div>;
  }

  const masterName = master.display_name ?? 'мастером';

  return (
    <div>
      <button
        className="back-link"
        onClick={() => navigate(`/slot?id=${serviceId}&date=${date}`)}
      >
        ← Назад
      </button>

      <div className="section-title">Обработка данных</div>

      <div className="consent-block">
        <p className="consent-intro">
          Для работы сервиса мы собираем ваши данные (имя, телефон, Telegram ID).
          Они используются для:
        </p>
        <ul className="consent-list">
          <li>
            организации записи и уведомлений от <b>{masterName}</b>
          </li>
          <li>
            функционирования бота <b>«Plotina bot»</b>: напоминаний, истории визитов и улучшения сервиса
          </li>
        </ul>
        <p className="consent-note">Данные не передаются третьим лицам.</p>
      </div>

      <button
        className="btn-primary"
        onClick={() => navigate(`/contact?id=${serviceId}&date=${date}&time=${time}`)}
      >
        Принять и продолжить
      </button>
    </div>
  );
}
