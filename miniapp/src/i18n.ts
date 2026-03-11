type Strings = Record<string, string>;

const STRINGS: Record<string, Strings> = {
  ru: {
    'back': '← Назад',
    'consent.title': 'Обработка данных',
    'consent.intro': 'Для работы сервиса мы собираем ваши данные (имя, телефон, Telegram ID). Они используются для:',
    'consent.bullet1': 'организации записи и уведомлений от',
    'consent.bullet2': 'функционирования бота «Plotina bot»: напоминаний, истории визитов и улучшения сервиса',
    'consent.note': 'Данные не передаются третьим лицам.',
    'consent.btn': 'Принять и продолжить',
    'contact.title': 'Ваши контакты',
    'contact.name_label': 'Имя *',
    'contact.name_placeholder': 'Как к вам обращаться?',
    'contact.phone_label': 'Телефон (необязательно)',
    'contact.phone_placeholder': '+7 (999) 123-45-67',
    'contact.btn': 'Далее',
    'confirm.title': 'Подтверждение записи',
    'confirm.master': 'Мастер',
    'confirm.service': 'Услуга',
    'confirm.date': 'Дата',
    'confirm.time': 'Время',
    'confirm.duration': 'Длительность',
    'confirm.price': 'Стоимость',
    'confirm.name': 'Ваше имя',
    'confirm.phone': 'Телефон',
    'confirm.btn': 'Подтвердить запись',
    'confirm.sending': 'Отправляем...',
    'price.by_agreement': 'по договорённости',
    'min': 'мин',
    'locale': 'ru-RU',
  },
  en: {
    'back': '← Back',
    'consent.title': 'Data Processing',
    'consent.intro': 'To provide this service, we collect your data (name, phone, Telegram ID). It is used for:',
    'consent.bullet1': 'organising your appointment and notifications from',
    'consent.bullet2': 'running the «Plotina bot» service: reminders, visit history and service improvement',
    'consent.note': 'Your data is not shared with third parties.',
    'consent.btn': 'Accept and continue',
    'contact.title': 'Your details',
    'contact.name_label': 'Name *',
    'contact.name_placeholder': 'How should we address you?',
    'contact.phone_label': 'Phone (optional)',
    'contact.phone_placeholder': '+1 (999) 123-4567',
    'contact.btn': 'Continue',
    'confirm.title': 'Booking confirmation',
    'confirm.master': 'Specialist',
    'confirm.service': 'Service',
    'confirm.date': 'Date',
    'confirm.time': 'Time',
    'confirm.duration': 'Duration',
    'confirm.price': 'Price',
    'confirm.name': 'Your name',
    'confirm.phone': 'Phone',
    'confirm.btn': 'Confirm booking',
    'confirm.sending': 'Sending…',
    'price.by_agreement': 'price on request',
    'min': 'min',
    'locale': 'en-US',
  },
  es: {
    'back': '← Atrás',
    'consent.title': 'Procesamiento de datos',
    'consent.intro': 'Para el funcionamiento del servicio recopilamos tus datos (nombre, teléfono, Telegram ID). Se utilizan para:',
    'consent.bullet1': 'organizar tu cita y notificaciones de',
    'consent.bullet2': 'el funcionamiento del bot «Plotina bot»: recordatorios, historial de visitas y mejora del servicio',
    'consent.note': 'Tus datos no se comparten con terceros.',
    'consent.btn': 'Aceptar y continuar',
    'contact.title': 'Tus datos',
    'contact.name_label': 'Nombre *',
    'contact.name_placeholder': '¿Cómo debo llamarte?',
    'contact.phone_label': 'Teléfono (opcional)',
    'contact.phone_placeholder': '+34 999 123 456',
    'contact.btn': 'Continuar',
    'confirm.title': 'Confirmación de cita',
    'confirm.master': 'Especialista',
    'confirm.service': 'Servicio',
    'confirm.date': 'Fecha',
    'confirm.time': 'Hora',
    'confirm.duration': 'Duración',
    'confirm.price': 'Precio',
    'confirm.name': 'Tu nombre',
    'confirm.phone': 'Teléfono',
    'confirm.btn': 'Confirmar cita',
    'confirm.sending': 'Enviando…',
    'price.by_agreement': 'precio a convenir',
    'min': 'min',
    'locale': 'es-ES',
  },
};

const SUPPORTED = new Set(['ru', 'en', 'es']);

export function useT(lang: string | null | undefined): (key: string) => string {
  const l = lang && SUPPORTED.has(lang) ? lang : 'ru';
  return (key: string) => STRINGS[l][key] ?? STRINGS['ru'][key] ?? key;
}

const CURRENCY_SYMBOLS: Record<string, string> = { RUB: '₽', USD: '$', EUR: '€' };

export function fmtPrice(price: number | null, currency: string, T: (key: string) => string): string {
  if (price === null) return T('price.by_agreement');
  const sym = CURRENCY_SYMBOLS[currency] ?? currency;
  if (currency === 'USD' || currency === 'EUR') return `${sym}${price}`;
  return `${price} ${sym}`;
}
