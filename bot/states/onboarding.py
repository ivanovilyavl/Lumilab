from aiogram.fsm.state import State, StatesGroup


class OnboardingStates(StatesGroup):
    CONSENT = State()        # Шаг 0: welcome + согласие на обработку данных
    LANGUAGE = State()       # Шаг 0b: выбор языка
    CURRENCY = State()       # Шаг 0c: выбор валюты
    NAME = State()           # Шаг 1: имя мастера
    NICHE = State()          # Шаг 2: выбор ниши
    SERVICE_NAME = State()   # Шаг 3a: название услуги
    SERVICE_PRICE = State()  # Шаг 3b: цена
    SERVICE_DURATION = State()  # Шаг 3c: длительность
    SCHEDULE_DAYS = State()  # Шаг 4a: выбор рабочих дней
    SCHEDULE_START = State() # Шаг 4b: время начала
    SCHEDULE_END = State()   # Шаг 4c: время конца
    SCHEDULE_STEP = State()  # Шаг 4d: шаг слотов
    DONE = State()           # Шаг 5: готово


class AddServiceStates(StatesGroup):
    NAME = State()
    PRICE = State()
    DURATION = State()


class EditServiceStates(StatesGroup):
    FIELD = State()   # which field: name / price / duration
    VALUE = State()   # waiting for new value


class EditScheduleStates(StatesGroup):
    SELECT_DAY = State()
    START_TIME = State()
    END_TIME = State()
    STEP = State()


class MasterMessageStates(StatesGroup):
    """FSM for master writing a message to client via bot."""
    TYPING = State()


class MasterRejectReasonStates(StatesGroup):
    """FSM for master providing rejection reason."""
    TYPING = State()


class MasterCancelReasonStates(StatesGroup):
    """FSM for master providing cancellation reason."""
    TYPING = State()


class ClientReplyStates(StatesGroup):
    """FSM for client replying to master via bot."""
    TYPING = State()


class AddQAStates(StatesGroup):
    QUESTION = State()
    ANSWER = State()
