import { useState, useEffect } from 'react';
import { Routes, Route } from 'react-router-dom';
import { useMaster } from './hooks/useApi';
import MasterProfile from './pages/MasterProfile';
import DatePicker from './pages/DatePicker';
import SlotPicker from './pages/SlotPicker';
import ContactForm from './pages/ContactForm';
import BookingConfirm from './pages/BookingConfirm';
import BookingSuccess from './pages/BookingSuccess';
import './App.css';

function getStartParam(): string | null {
  // 1. Telegram passes startapp value via WebApp API
  const tgParam = window.Telegram?.WebApp?.initDataUnsafe?.start_param;
  if (tgParam) return tgParam;

  // 2. Telegram also appends tgWebAppStartParam to the URL
  const url = new URLSearchParams(window.location.search);
  const urlParam = url.get('tgWebAppStartParam');
  if (urlParam) return urlParam;

  // 3. Fallback: direct ?master= param (for dev/testing)
  return url.get('master');
}

export default function App() {
  const [masterUsername, setMasterUsername] = useState<string | null>(null);

  const { master, loading, error } = useMaster(masterUsername);

  // Booking state
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [, setSelectedSlot] = useState<string | null>(null);
  const [clientName, setClientName] = useState('');
  const [clientPhone, setClientPhone] = useState('');

  // Init Telegram Web App
  useEffect(() => {
    const tg = window.Telegram?.WebApp;
    if (tg) {
      tg.ready();
      tg.expand();
      // Pre-fill name from Telegram user
      const user = tg.initDataUnsafe?.user;
      if (user && !clientName) {
        const name = [user.first_name, user.last_name].filter(Boolean).join(' ');
        setClientName(name);
      }
    }
    setMasterUsername(getStartParam());
  }, []);

  if (!masterUsername) {
    return (
      <div className="app">
        <div className="error">Мастер не указан. Откройте ссылку от мастера.</div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="app">
        <div className="loading">Загрузка...</div>
      </div>
    );
  }

  if (error || !master) {
    return (
      <div className="app">
        <div className="error">Мастер не найден 😔</div>
      </div>
    );
  }

  return (
    <div className="app">
      <Routes>
        <Route path="/" element={<MasterProfile master={master} />} />
        <Route
          path="/service"
          element={
            <DatePicker
              master={master}
              selectedDate={selectedDate}
              onSelectDate={setSelectedDate}
            />
          }
        />
        <Route
          path="/slot"
          element={<SlotPicker master={master} onSelectSlot={setSelectedSlot} />}
        />
        <Route
          path="/contact"
          element={
            <ContactForm
              clientName={clientName}
              clientPhone={clientPhone}
              onChangeName={setClientName}
              onChangePhone={setClientPhone}
            />
          }
        />
        <Route
          path="/confirm"
          element={
            <BookingConfirm
              master={master}
              clientName={clientName}
              clientPhone={clientPhone}
            />
          }
        />
        <Route path="/success" element={<BookingSuccess />} />
      </Routes>
    </div>
  );
}
