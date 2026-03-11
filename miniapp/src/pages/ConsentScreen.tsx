import { useNavigate, useSearchParams } from 'react-router-dom';
import type { MasterType } from '../types';
import { useT } from '../i18n';

interface Props {
  master: MasterType;
}

export default function ConsentScreen({ master }: Props) {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const serviceId = params.get('id');
  const date = params.get('date');
  const time = params.get('time');
  const T = useT(master.language);

  if (!serviceId || !date || !time) {
    return <div className="error">{T('error.missing_params')}</div>;
  }

  const masterName = master.display_name ?? 'мастером';

  return (
    <div>
      <button
        className="back-link"
        onClick={() => navigate(`/slot?id=${serviceId}&date=${date}`)}
      >
        {T('back')}
      </button>

      <div className="section-title">{T('consent.title')}</div>

      <div className="consent-block">
        <p className="consent-intro">{T('consent.intro')}</p>
        <ul className="consent-list">
          <li>
            {T('consent.bullet1')} <b>{masterName}</b>
          </li>
          <li>{T('consent.bullet2')}</li>
        </ul>
        <p className="consent-note">{T('consent.note')}</p>
      </div>

      <button
        className="btn-primary"
        onClick={() => navigate(`/contact?id=${serviceId}&date=${date}&time=${time}`)}
      >
        {T('consent.btn')}
      </button>
    </div>
  );
}
