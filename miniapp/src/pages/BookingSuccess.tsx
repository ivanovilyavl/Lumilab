export default function BookingSuccess() {
  const handleShare = () => {
    const tg = window.Telegram?.WebApp;
    if (tg) {
      tg.close();
    }
  };

  return (
    <div className="success-page">
      <div className="success-icon">🎉</div>
      <div className="success-title">Вы записаны!</div>
      <div className="success-text">
        Мастер получил вашу заявку и скоро подтвердит запись.
        <br />
        Вы получите уведомление в Telegram.
      </div>
      <button className="btn-primary" onClick={handleShare}>
        Закрыть
      </button>
    </div>
  );
}
