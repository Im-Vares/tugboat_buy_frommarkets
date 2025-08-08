
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from db.db_class import DB
from config.config import settings
from aportals_api.client import filter_floors

router = Router()
db = DB()

def _allowed(uid: int) -> bool:
    return (not settings.ALLOWED_USERS) or (uid in settings.ALLOWED_USERS)

class NewFilter(StatesGroup):
    collection = State()
    models = State()
    backdrops = State()
    max_price = State()
    qty = State()
    confirm = State()

class EditFilter(NewFilter):
    fid = State()

async def _cancel_if_not_allowed(message: Message):
    if not _allowed(message.from_user.id):
        await message.answer("Доступ запрещён.")
        return True
    return False

@router.message(Command("add_filter"))
async def add_filter_start(message: Message, state: FSMContext):
    if await _cancel_if_not_allowed(message): return
    await state.clear()
    await state.set_state(NewFilter.collection)
    await message.answer("Введи название коллекции (как на Fragment).")

@router.message(NewFilter.collection)
async def add_filter_collection(message: Message, state: FSMContext):
    name = message.text.strip()
    # Можно валидировать через filter_floors
    try:
        floors = await filter_floors(gift_name=name)
        models = sorted({m["value"] for m in floors.get("models", [])})
        backs = sorted({b["value"] for b in floors.get("backdrops", [])})
    except Exception:
        models, backs = [], []
    await state.update_data(collection=name, models_choices=models, backs_choices=backs, picked_models=set(), picked_backs=set())
    # Кнопка: продолжить/пропустить если нет вариантов
    if models:
        kb = InlineKeyboardBuilder()
        for m in models[:48]:
            kb.button(text=f"• {m}", callback_data=f"pick_m:{m}")
        kb.button(text="Продолжить ▶", callback_data="m_next")
        kb.button(text="Пропустить", callback_data="m_skip")
        kb.adjust(3)
        await state.set_state(NewFilter.models)
        await message.answer("Выбери одну или несколько моделей (жми по кнопкам). Когда готов — 'Продолжить'.", reply_markup=kb.as_markup())
    else:
        await state.set_state(NewFilter.models)
        await message.answer("Модели не найдены для этой коллекции. Можно пропустить. Напиши 'пропустить' или отправь любой текст для перехода.")

@router.callback_query(NewFilter.models, F.data.startswith("pick_m:"))
async def pick_model(cb: CallbackQuery, state: FSMContext):
    m = cb.data.split(":",1)[1]
    data = await state.get_data()
    picked = set(data.get("picked_models", set()))
    if m in picked: picked.remove(m)
    else: picked.add(m)
    await state.update_data(picked_models=picked)
    await cb.answer(f"Выбрано: {len(picked)}")

@router.callback_query(NewFilter.models, F.data == "m_next")
async def models_next(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    backs = data.get("backs_choices", [])
    if backs:
        kb = InlineKeyboardBuilder()
        for b in backs[:48]:
            kb.button(text=f"• {b}", callback_data=f"pick_b:{b}")
        kb.button(text="Продолжить ▶", callback_data="b_next")
        kb.button(text="Пропустить", callback_data="b_skip")
        kb.adjust(3)
        await state.set_state(NewFilter.backdrops)
        await cb.message.edit_text("Выбери один или несколько фонов. Когда готов — 'Продолжить'.", reply_markup=kb.as_markup())
    else:
        await state.set_state(NewFilter.backdrops)
        await cb.message.edit_text("Фоны не найдены. Введи максимальную цену (TON):")
        await state.set_state(NewFilter.max_price)

@router.callback_query(NewFilter.models, F.data == "m_skip")
async def models_skip(cb: CallbackQuery, state: FSMContext):
    await state.update_data(picked_models=set())
    await cb.message.edit_text("Модели пропущены. Теперь фоны (или пропусти).")
    await models_next(cb, state)

@router.callback_query(NewFilter.backdrops, F.data.startswith("pick_b:"))
async def pick_back(cb: CallbackQuery, state: FSMContext):
    b = cb.data.split(":",1)[1]
    data = await state.get_data()
    picked = set(data.get("picked_backs", set()))
    if b in picked: picked.remove(b)
    else: picked.add(b)
    await state.update_data(picked_backs=picked)
    await cb.answer(f"Выбрано: {len(picked)}")

@router.callback_query(NewFilter.backdrops, F.data.in_(["b_next","b_skip"]))
async def backs_next(cb: CallbackQuery, state: FSMContext):
    if cb.data == "b_skip":
        await state.update_data(picked_backs=set())
    await state.set_state(NewFilter.max_price)
    await cb.message.edit_text("Введи максимальную цену в TON (число, например 3.5):")

@router.message(NewFilter.max_price)
async def add_filter_price(message: Message, state: FSMContext):
    try:
        price = float(message.text.replace(",", ".").strip())
        if price <= 0: raise ValueError()
    except Exception:
        return await message.answer("Нужно положительное число, например 2.75")
    await state.update_data(max_price=price)
    await state.set_state(NewFilter.qty)
    await message.answer("Сколько штук покупать максимум одним лотом? (целое число)")

@router.message(NewFilter.qty)
async def add_filter_qty(message: Message, state: FSMContext):
    try:
        qty = int(message.text.strip())
        if qty <= 0:
            raise ValueError()
    except Exception:
        return await message.answer("Нужно целое число > 0.")

    await state.update_data(qty=qty)
    data = await state.get_data()

    models = ", ".join(sorted(data.get("picked_models", []))) or "любой"
    backs  = ", ".join(sorted(data.get("picked_backs", []))) or "любой"

    text = (
        f"Проверим:\n"
        f"Коллекция: {data['collection']}\n"
        f"Модели: {models}\n"
        f"Фоны: {backs}\n"
        f"Макс. цена: {data['max_price']} TON\n"
        f"Количество: {qty}\n\n"
        f"Подтвердить? /save или /cancel"
    )

    await state.set_state(NewFilter.confirm)
    await message.answer(text)

@router.message(NewFilter.confirm, Command("save"))
async def add_filter_save(message: Message, state: FSMContext):
    data = await state.get_data()
    user_id = message.from_user.id
    # ensure user exists
    from db.db import get_pool
    pool = await get_pool()
    await pool.execute("INSERT INTO users(telegram_id) VALUES($1) ON CONFLICT (telegram_id) DO NOTHING", user_id)
    fid = await db.add_filter(
        user_id=(await pool.fetchval("SELECT id FROM users WHERE telegram_id=$1", user_id)),
        collection=data["collection"],
        model=list(data.get("picked_models", [])) or None,
        backdrop=list(data.get("picked_backs", [])) or None,
        max_price=data["max_price"],
        quantity=data["qty"],
        active=True
    )
    await db.log("bot", "add_filter", "ok", filter_id=fid, user_id=user_id, details="fsm save")
    await message.answer(f"Сохранено. ID фильтра: {fid}")
    await state.clear()

@router.message(NewFilter.confirm, Command("cancel"))
async def add_filter_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Отменено.")

# --- Simple /edit_filter and /delete_filter via inline list ---
@router.message(Command("filters"))
async def list_filters(message: Message):
    if await _cancel_if_not_allowed(message): return
    from db.db import get_pool
    pool = await get_pool()
    uid = await pool.fetchval("SELECT id FROM users WHERE telegram_id=$1", message.from_user.id)
    if not uid:
        return await message.answer("Фильтров нет.")
    rows = await pool.fetch("SELECT * FROM filters WHERE user_id=$1 ORDER BY id DESC", uid)
    if not rows:
        return await message.answer("Фильтров нет.")
    text_lines = []
    kb = InlineKeyboardBuilder()
    for r in rows:
        text_lines.append(f"#{r['id']} {r['collection']} | price≤{r['max_price']} | qty={r['quantity']} | {'ON' if r['active'] else 'OFF'}")
        kb.button(text=f"✏️ {r['id']}", callback_data=f"edit:{r['id']}")
        kb.button(text=f"🗑 {r['id']}", callback_data=f"del:{r['id']}")
    kb.adjust(4)
    await message.answer("\n".join(text_lines), reply_markup=kb.as_markup())

@router.callback_query(F.data.startswith("del:"))
async def delete_filter_cb(cb: CallbackQuery):
    fid = int(cb.data.split(":")[1])
    await db.delete_filter(fid)
    await db.log("bot", "delete_filter", "ok", filter_id=fid, user_id=cb.from_user.id)
    await cb.answer("Удалено")
    await cb.message.edit_text("Удалено.")
