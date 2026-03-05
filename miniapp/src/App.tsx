import { useState, useEffect } from 'react';
import { Routes, Route, useSearchParams } from 'react-router-dom';
import { useMaster } from './hooks/useApi';
import MasterProfile from './pages/MasterProfile';
import DatePicker from './pages/DatePicker';
import SlotPicker from './pages/SlotPicker';
import ContactForm from './pages/ContactForm';
import BookingConfirm from './pages/BookingConfirm';
import BookingSuccess from './pages/BookingSuccess';
import './App.css';

export default function App() {
  const [params] = useSearchParams();
  const masterUsername = params.get('master');

  const { master, loading, error } = useMaster(masterUsername);

  // Booking state
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [selectedSlot, setSelectedSlot] = useState<string | null>(null);
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
