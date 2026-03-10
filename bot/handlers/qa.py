from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.states.onboarding import AddQAStates
from db.models import Master, QAItem

router = Router()


def qa_list_kb(items: list[QAItem]) -> InlineKeyboardMarkup:
    buttons = []
    for item in items:
        status = "✅" if item.is_active else "🙈"
        short_q = item.question[:40] + "…" if len(item.question) > 40 else item.question
        buttons.append([
            InlineKeyboardButton(
                text=f"{status} {short_q}",
                callback_data=f"qa_view:{item.id}",
            )
        ])
    buttons.append([InlineKeyboardButton(text="➕ Добавить вопрос", callback_data="qa_add")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def qa_actions_kb(qa_id: int, is_active: bool) -> InlineKeyboardMarkup:
    hide_text = "🙈 Скрыть" if is_active else "👁 Показать"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=hide_text, callback_data=f"qa_toggle:{qa_id}"),
                InlineKeyboardButton(text="🗑 Удалить", callback_data=f"qa_del:{qa_id}"),
            ],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="qa_back")],
        ]
    )


@router.message(Command("qa"))
@router.message(F.text == "❓ Вопросы и ответы")
async def cmd_qa(message: Message, db: AsyncSession, master: Master):
    result = await db.execute(
        select(QAItem).where(QAItem.master_id == master.id).order_by(QAItem.sort_order)
    )
    items = list(result.scalars().all())

    if not items:
        await message.answer(
            "У вас пока нет вопросов и ответов.\n"
            "Добавьте FAQ — клиенты увидят их на вашей странице.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="➕ Добавить вопрос", callback_data="qa_add")]]
            ),
        )
        return

    await message.answer("❓ <b>Вопросы и ответы:</b>", reply_markup=qa_list_kb(items))


@router.callback_query(F.data == "qa_back")
async def qa_back(callback: CallbackQuery, db: AsyncSession, master: Master):
    result = await db.execute(
        select(QAItem).where(QAItem.master_id == master.id).order_by(QAItem.sort_order)
    )
    items = list(result.scalars().all())
    await callback.message.edit_text("❓ <b>Вопросы и ответы:</b>", reply_markup=qa_list_kb(items))
    await callback.answer()


@router.callback_query(F.data.startswith("qa_view:"))
async def qa_view(callback: CallbackQuery, db: AsyncSession):
    qa_id = int(callback.data.split(":")[1])
    item = await db.get(QAItem, qa_id)
    if not item:
        await callback.answer("Вопрос не найден", show_alert=True)
        return
    text = (
        f"❓ <b>{item.question}</b>\n\n"
        f"💬 {item.answer}\n\n"
        f"Статус: {'✅ Виден клиентам' if item.is_active else '🙈 Скрыт'}"
    )
    await callback.message.edit_text(text, reply_markup=qa_actions_kb(item.id, item.is_active))
    await callback.answer()


@router.callback_query(F.data.startswith("qa_toggle:"))
async def qa_toggle(callback: CallbackQuery, db: AsyncSession):
    qa_id = int(callback.data.split(":")[1])
    item = await db.get(QAItem, qa_id)
    if not item:
        await callback.answer("Вопрос не найден", show_alert=True)
        return
    item.is_active = not item.is_active
    await db.commit()
    status = "виден клиентам" if item.is_active else "скрыт от клиентов"
    await callback.answer(f"Вопрос {status}")
    text = (
        f"❓ <b>{item.question}</b>\n\n"
        f"💬 {item.answer}\n\n"
        f"Статус: {'✅ Виден клиентам' if item.is_active else '🙈 Скрыт'}"
    )
    await callback.message.edit_text(text, reply_markup=qa_actions_kb(item.id, item.is_active))


@router.callback_query(F.data.startswith("qa_del:"))
async def qa_delete(callback: CallbackQuery, db: AsyncSession, master: Master):
    qa_id = int(callback.data.split(":")[1])
    item = await db.get(QAItem, qa_id)
    if item:
        await db.delete(item)
        await db.commit()
    await callback.answer("Вопрос удалён")
    await qa_back(callback, db, master)


# ── Add QA FSM ──────────────────────────────────────────

@router.callback_query(F.data == "qa_add")
async def qa_add_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите <b>вопрос</b>, который часто задают клиенты:")
    await state.set_state(AddQAStates.QUESTION)
    await callback.answer()


@router.message(AddQAStates.QUESTION)
async def add_qa_question(message: Message, state: FSMContext):
    question = message.text.strip()
    if len(question) < 3 or len(question) > 256:
        await message.answer("Вопрос — от 3 до 256 символов:")
        return
    await state.update_data(question=question)
    await message.answer(f"Вопрос: <b>{question}</b>\n\nТеперь введите <b>ответ</b>:")
    await state.set_state(AddQAStates.ANSWER)


@router.message(AddQAStates.ANSWER)
async def add_qa_answer(message: Message, state: FSMContext, db: AsyncSession, master: Master):
    answer = message.text.strip()
    if len(answer) < 1:
        await message.answer("Ответ не может быть пустым:")
        return
    data = await state.get_data()
    item = QAItem(
        master_id=master.id,
        question=data["question"],
        answer=answer,
    )
    db.add(item)
    await db.commit()
    await state.clear()
    await message.answer(
        f"✅ Вопрос добавлен!\n\n"
        f"❓ <b>{data['question']}</b>\n"
        f"💬 {answer}\n\n"
        "Используйте /qa для управления вопросами."
    )
