import { useState, useEffect } from 'react';
import MastersTable from './pages/MastersTable';
import ClientsTable from './pages/ClientsTable';

type Tab = 'masters' | 'clients';

export default function App() {
  const [initData, setInitData] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>('masters');

  useEffect(() => {
    const tg = window.Telegram?.WebApp;
    if (tg) {
      tg.ready();
      tg.expand();
      setInitData(tg.initData || null);
    }
  }, []);

  if (!initData) {
    return (
      <div className="admin-app">
        <div className="admin-auth-error">
          <span className="placeholder-icon">🔒</span>
          <p>Доступ только через аналитик-бот</p>
        </div>
      </div>
    );
  }

  return (
    <div className="admin-app">
      <div className="admin-header">
        <div className="admin-title">Аналитика</div>
      </div>

      <nav className="admin-tabs">
        <button
          className={`admin-tab${activeTab === 'masters' ? ' active' : ''}`}
          onClick={() => setActiveTab('masters')}
        >
          Мастера
        </button>
        <button
          className={`admin-tab${activeTab === 'clients' ? ' active' : ''}`}
          onClick={() => setActiveTab('clients')}
        >
          Клиенты
        </button>
      </nav>

      <div className="admin-content">
        {activeTab === 'masters' ? (
          <MastersTable initData={initData} />
        ) : (
          <ClientsTable initData={initData} />
        )}
      </div>
    </div>
  );
}
