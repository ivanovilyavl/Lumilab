import { useNavigate, useSearchParams } from 'react-router-dom';
import { useT } from '../i18n';

interface Props {
  lang: string;
  clientName: string;
  clientPhone: string;
  onChangeName: (v: string) => void;
  onChangePhone: (v: string) => void;
}

export default function ContactForm({ lang, clientName, clientPhone, onChangeName, onChangePhone }: Props) {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const serviceId = params.get('id');
  const date = params.get('date');
  const time = params.get('time');
  const T = useT(lang);

  const canProceed = clientName.trim().length >= 2;

  return (
    <div>
      <button
        className="back-link"
        onClick={() => navigate(`/consent?id=${serviceId}&date=${date}&time=${time}`)}
      >
        {T('back')}
      </button>

      <div className="section-title">{T('contact.title')}</div>

      <div className="form-group">
        <label className="form-label">{T('contact.name_label')}</label>
        <input
          className="form-input"
          type="text"
          placeholder={T('contact.name_placeholder')}
          value={clientName}
          onChange={(e) => onChangeName(e.target.value)}
          maxLength={128}
        />
      </div>

      <div className="form-group">
        <label className="form-label">{T('contact.phone_label')}</label>
        <input
          className="form-input"
          type="tel"
          placeholder={T('contact.phone_placeholder')}
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
        {T('contact.btn')}
      </button>
    </div>
  );
}
