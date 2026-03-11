import { useState, useEffect } from 'react';
import { Routes, Route, useLocation, useNavigate } from 'react-router-dom';
import { useMaster, useMasterSchedule } from './hooks/useApi';
import MasterProfile from './pages/MasterProfile';
import DatePicker from './pages/DatePicker';
import SlotPicker from './pages/SlotPicker';
import ContactForm from './pages/ContactForm';
import BookingConfirm from './pages/BookingConfirm';
import BookingSuccess from './pages/BookingSuccess';
import MasterCalendar from './pages/MasterCalendar';
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

const TAB_ROUTES = ['/', '/calendar'];

function TabBar({ active }: { active: string }) {
  const navigate = useNavigate();
  return (
    <nav className="tab-bar">
      <button
        className={`tab-bar-item${active === '/' ? ' active' : ''}`}
        onClick={() => navigate('/')}
      >
        <span className="tab-icon">📋</span>
        <span>Запись</span>
      </button>
      <button
        className={`tab-bar-item${active === '/calendar' ? ' active' : ''}`}
        onClick={() => navigate('/calendar')}
      >
        <span className="tab-icon">📅</span>
        <span>Мой календарь</span>
      </button>
    </nav>
  );
}

function ClientCalendarPlaceholder() {
  return (
    <div className="client-calendar-placeholder">
      <span className="placeholder-icon">📅</span>
      <h3>Мой календарь</h3>
      <p>
        Этот раздел доступен только для мастеров.<br />
        Зарегистрируйтесь через <b>/start</b> в боте, чтобы принимать записи и видеть своё расписание.
      </p>
    </div>
  );
}

export default function App() {
  const [masterUsername, setMasterUsername] = useState<string | null>(null);
  const [initData, setInitData] = useState<string | null>(null);

  const { master, loading, error } = useMaster(masterUsername);
  const { bookings, isOwner, refetch } = useMasterSchedule(masterUsername, initData);

  // Booking state
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [, setSelectedSlot] = useState<string | null>(null);
  const [clientName, setClientName] = useState('');
  const [clientPhone, setClientPhone] = useState('');

  const location = useLocation();
  const showTabBar = TAB_ROUTES.includes(location.pathname);

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
      setInitData(tg.initData || null);
    }
    setMasterUsername(getStartParam());
  }, []);

  if (!masterUsername) {
    return (
      <div className="app">
        <div className="master-cabinet-notice">
          <span className="placeholder-icon">🔒</span>
          <p>Сейчас тут личный кабинет мастера — для доступа зарегистрируйтесь через <b>/start</b></p>
        </div>
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
    <div className={`app${showTabBar ? ' with-tabs' : ''}`}>
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
        <Route
          path="/calendar"
          element={
            isOwner && master && initData ? (
              <MasterCalendar
                bookings={bookings}
                master={master}
                initData={initData}
                onBookingCreated={refetch}
              />
            ) : (
              <ClientCalendarPlaceholder />
            )
          }
        />
      </Routes>

      {showTabBar && <TabBar active={location.pathname} />}
    </div>
  );
}
