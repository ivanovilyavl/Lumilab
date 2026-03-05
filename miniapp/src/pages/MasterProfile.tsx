import { useNavigate } from 'react-router-dom';
import type { MasterType } from '../types';

const nicheIcons: Record<string, string> = {
  beauty: '💅',
  tutor: '📚',
  trainer: '🏋️',
  psychologist: '🧠',
  photo: '📷',
  other: '⭐',
};

interface Props {
  master: MasterType;
}

export default function MasterProfile({ master }: Props) {
  const navigate = useNavigate();
  const initial = master.display_name.charAt(0).toUpperCase();
  const nicheIcon = nicheIcons[master.niche || 'other'] || '⭐';

  return (
    <div>
      <div className="master-header">
        <div className="master-avatar">{initial}</div>
        <div className="master-name">{master.display_name}</div>
        <div className="master-niche">{nicheIcon} {master.niche || ''}</div>
        {master.bio && <div className="master-bio">{master.bio}</div>}
      </div>

      <div className="section-title">Услуги</div>
      {master.services.map((service) => (
        <div
          key={service.id}
          className="service-card"
          onClick={() => navigate(`/service?id=${service.id}`)}
        >
          <div className="service-name">{service.name}</div>
          <div className="service-meta">
            <span>{service.duration_min} мин</span>
            <span className="service-price">{service.price} ₽</span>
          </div>
          {service.description && (
            <div style={{ fontSize: 13, color: 'var(--tg-theme-hint-color)', marginTop: 4 }}>
              {service.description}
            </div>
          )}
        </div>
      ))}

      {master.services.length === 0 && (
        <div className="no-slots">Мастер пока не добавил услуг</div>
      )}
    </div>
  );
}
