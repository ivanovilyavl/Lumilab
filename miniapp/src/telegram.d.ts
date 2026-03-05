interface TelegramWebAppUser {
  id: number;
  first_name: string;
  last_name?: string;
  username?: string;
}

interface TelegramWebAppInitData {
  user?: TelegramWebAppUser;
}

interface TelegramWebApp {
  initData: string;
  initDataUnsafe: TelegramWebAppInitData;
  ready: () => void;
  expand: () => void;
  close: () => void;
  MainButton: {
    text: string;
    show: () => void;
    hide: () => void;
    onClick: (cb: () => void) => void;
  };
  themeParams: Record<string, string>;
}

interface Window {
  Telegram?: {
    WebApp?: TelegramWebApp;
  };
}
