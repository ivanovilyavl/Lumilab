import { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

interface Props {
  clientName: string;
  clientPhone: string;
  onChangeName: (v: string) => void;
  onChangePhone: (v: string) => void;
}

export default function ContactForm({ clientName, clientPhone, onChangeName, onChangePhone }: Props) {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const serviceId = params.get('id');
  const date = params.get('date');
  const time = params.get('time');

  const canProceed = clientName.trim().length >= 2;

  return (
    <div>
      <button
        className="back-link"
        onClick={() => navigate(`/slot?id=${serviceId}&date=${date}`)}
      >
        ← Назад
      </button>

      <div className="section-title">Ваши контакты</div>

      <div className="form-group">
        <label className="form-label">Имя *</label>
        <input
          className="form-input"
          type="text"
          placeholder="Как к вам обращаться?"
          value={clientName}
          onChange={(e) => onChangeName(e.target.value)}
          maxLength={128}
        />
      </div>

      <div className="form-group">
        <label className="form-label">Телефон (необязательно)</label>
        <input
          className="form-input"
          type="tel"
          placeholder="+7 (999) 123-45-67"
          value={clientPhone}
          onChange={(e) => onChangePhone(e.target.value)}
          maxLength={32}
        />
      </div>

      <button
        className="btn-primary"
        disabled={!canProceed}
        onClick={() => navigate(`/confirm?id=${serviceId}&date=${date}&time=${time}`)}
      >
        Далее
      </button>
    </div>
  );
}
