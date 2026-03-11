from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Master

router = Router()

NICHE_MAP = {
    "beauty": "💅 Бьюти",
    "tutor": "📚 Репетитор",
    "trainer": "🏋️ Тренер",
    "psychologist": "🧠 Психолог",
    "photo": "📷 Фото",
    "other": "🔧 Другое",
}


class ProfileEditStates(StatesGroup):
    WAITING_NAME = State()
    WAITING_BIO = State()
    WAITING_PHOTO = State()


def _profile_edit_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ Имя", callback_data="profile_edit:name"),
            InlineKeyboardButton(text="📝 Описание", callback_data="profile_edit:bio"),
        ],
        [
            InlineKeyboardButton(text="🖼 Фото", callback_data="profile_edit:photo"),
            InlineKeyboardButton(text="💱 Валюта", callback_data="profile_edit:currency"),
        ],
    ])


@router.message(Command("profile"))
@router.message(F.text == "👤 Профиль")
async def cmd_profile(message: Message, master: Master):
    niche_text = NICHE_MAP.get(master.niche, master.niche or "—")
    text = (
        f"👤 <b>Ваш профиль</b>\n\n"
        f"<b>Имя:</b> {master.display_name}\n"
        f"<b>Username:</b> @{master.username}\n"
        f"<b>Сфера:</b> {niche_text}\n"
        f"<b>Описание:</b> {master.bio or '(не задано)'}\n"
        f"<b>Фото:</b> {'есть' if master.photo_file_id else 'нет'}"
    )
    await message.answer(text, reply_markup=_profile_edit_kb())


# ── /setname ─────────────────────────────────────────────────────

@router.message(Command("setname"))
async def cmd_setname(message: Message, state: FSMContext, master: Master | None):
    if not master:
        return
    await message.answer("Введите новое имя (2–64 символа):\n\nДля отмены — /cancel")
    await state.set_state(ProfileEditStates.WAITING_NAME)


@router.callback_query(F.data == "profile_edit:name")
async def cb_setname(callback, state: FSMContext, master: Master | None):
    if not master:
        return
    await callback.message.answer("Введите новое имя (2–64 символа):\n\nДля отмены — /cancel")
    await state.set_state(ProfileEditStates.WAITING_NAME)
    await callback.answer()


@router.message(ProfileEditStates.WAITING_NAME)
async def process_new_name(message: Message, state: FSMContext, db: AsyncSession, master: Master):
    name = (message.text or "").strip()
    if len(name) < 2 or len(name) > 64:
        await message.answer("Имя должно быть от 2 до 64 символов. Попробуйте ещё раз:")
        return
    master.display_name = name
    await db.commit()
    await state.clear()
    await message.answer(f"✅ Имя обновлено: <b>{name}</b>")


# ── /setbio ──────────────────────────────────────────────────────

@router.message(Command("setbio"))
async def cmd_setbio(message: Message, state: FSMContext, master: Master | None):
    if not master:
        return
    await message.answer(
        "Введите описание профиля (до 500 символов).\n"
        "Клиенты увидят его на странице записи.\n\n"
        "Чтобы удалить описание — отправьте <code>-</code>\n"
        "Для отмены — /cancel"
    )
    await state.set_state(ProfileEditStates.WAITING_BIO)


@router.callback_query(F.data == "profile_edit:bio")
async def cb_setbio(callback, state: FSMContext, master: Master | None):
    if not master:
        return
    await callback.message.answer(
        "Введите описание профиля (до 500 символов).\n"
        "Клиенты увидят его на странице записи.\n\n"
        "Чтобы удалить описание — отправьте <code>-</code>\n"
        "Для отмены — /cancel"
    )
    await state.set_state(ProfileEditStates.WAITING_BIO)
    await callback.answer()


@router.message(ProfileEditStates.WAITING_BIO)
async def process_new_bio(message: Message, state: FSMContext, db: AsyncSession, master: Master):
    text = (message.text or "").strip()
    if text == "-":
        master.bio = None
        await db.commit()
        await state.clear()
        await message.answer("✅ Описание удалено.")
        return
    if len(text) > 500:
        await message.answer("Описание не должно превышать 500 символов. Попробуйте ещё раз:")
        return
    master.bio = text
    await db.commit()
    await state.clear()
    await message.answer("✅ Описание обновлено.")


# ── /setphoto ────────────────────────────────────────────────────

@router.message(Command("setphoto"))
async def cmd_setphoto(message: Message, state: FSMContext, master: Master | None):
    if not master:
        return
    await message.answer(
        "Отправьте фото профиля.\n\n"
        "Чтобы удалить фото — отправьте <code>-</code>\n"
        "Для отмены — /cancel"
    )
    await state.set_state(ProfileEditStates.WAITING_PHOTO)


@router.callback_query(F.data == "profile_edit:photo")
async def cb_setphoto(callback, state: FSMContext, master: Master | None):
    if not master:
        return
    await callback.message.answer(
        "Отправьте фото профиля.\n\n"
        "Чтобы удалить фото — отправьте <code>-</code>\n"
        "Для отмены — /cancel"
    )
    await state.set_state(ProfileEditStates.WAITING_PHOTO)
    await callback.answer()


@router.message(ProfileEditStates.WAITING_PHOTO, F.photo)
async def process_new_photo(message: Message, state: FSMContext, db: AsyncSession, master: Master):
    # Take the highest resolution photo
    photo = message.photo[-1]
    master.photo_file_id = photo.file_id
    await db.commit()
    await state.clear()
    await message.answer("✅ Фото обновлено.")


@router.message(ProfileEditStates.WAITING_PHOTO, F.text)
async def process_photo_text(message: Message, state: FSMContext, db: AsyncSession, master: Master):
    if (message.text or "").strip() == "-":
        master.photo_file_id = None
        await db.commit()
        await state.clear()
        await message.answer("✅ Фото удалено.")
    else:
        await message.answer("Пожалуйста, отправьте фото или <code>-</code> для удаления:")


# ── /cancel в состояниях редактирования ──────────────────────────

@router.message(Command("cancel"), ProfileEditStates())
async def cancel_profile_edit(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Отменено.")


# ── /currency (alias через профиль) ──────────────────────────────

@router.callback_query(F.data == "profile_edit:currency")
async def cb_set_currency(callback, master: Master | None):
    if not master:
        return
    from shared.i18n import t, SUPPORTED_CURRENCIES
    lang = master.language or "ru"
    await callback.message.answer(
        t(lang, "currency_select"),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(
                text=t(lang, f"currency_label_{code}"),
                callback_data=f"changecurrency:{code}",
            )
            for code in ("RUB", "USD", "EUR")
        ]]),
    )
    await callback.answer()
