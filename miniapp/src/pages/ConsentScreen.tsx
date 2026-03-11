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
          Для завершения записи вам потребуется указать имя и телефон. Эти данные будут переданы:
        </p>
        <ul className="consent-list">
          <li>
            <b>{masterName}</b> — для организации и подтверждения вашей записи
          </li>
          <li>
            <b>Команде бота «Plotina bot»</b> — для работы сервиса онлайн-записи
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
