from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
import time
import asyncio

from db.db_class import DB
from config.config import settings
from aportalsmp.auth import update_auth
from aportalsmp.gifts import collections as gifts_collections, filterFloors as gifts_filterFloors, search as gifts_search

router = Router()
db = DB()


# cache for collections list (10 minutes)
_COLL_CACHE = {"ts": 0, "names": []}
_CACHE_TTL = 600
_FALLBACK_PAGES_LIGHT = 10   # ~1000 позиций
_FALLBACK_PAGES_DEEP = 40    # ~4000 позиций


def _allowed(uid: int) -> bool:
    return (not settings.ALLOWED_USERS) or (uid in settings.ALLOWED_USERS)


class NewFilter(StatesGroup):
    collection = State()
    models = State()
    backdrops = State()
    max_price = State()
    qty = State()
    confirm = State()


def make_toggle_keyboard(items, picked, prefix: str, page: int = 0, page_size: int = 24):
    items = list(items or [])
    picked = set(picked or [])
    total = len(items)
    start = page * page_size
    end = min(total, start + page_size)
    kb = InlineKeyboardBuilder()
    for it in items[start:end]:
        mark = "✅" if it in picked else "•"
        kb.button(text=f"{mark} {it}", callback_data=f"pick_{prefix}:{it}")
    if start > 0:
        kb.button(text="◀️", callback_data=f"{prefix}_page:{page-1}")
    kb.button(text="Пропустить", callback_data=f"{prefix}_skip")
    kb.button(text="Продолжить ▶", callback_data=f"{prefix}_next")
    if end < total:
        kb.button(text="▶️", callback_data=f"{prefix}_page:{page+1}")
    kb.adjust(3)
    return kb.as_markup()


async def _get_auth():
    """Build/refresh authData for aportalsmp using env settings."""
    return await update_auth(
        api_id=settings.TG_API_ID,
        api_hash=settings.TG_API_HASH,
        session_path=settings.SESSION_PATH,
        session_name=settings.SESSION_NAME,
    )


async def _all_collection_names(deep: bool = False):
    # use cached list if it's fresh and not a deep refresh
    now = time.time()
    if (not deep) and _COLL_CACHE["names"] and (now - _COLL_CACHE["ts"] < _CACHE_TTL):
        return _COLL_CACHE["names"]

    auth = await _get_auth()
    names = set()

    # A) try official endpoint first
    try:
        cols = await gifts_collections(limit=1000, authData=auth)
        d = cols.toDict() if hasattr(cols, "toDict") else {}
        for it in (d.get("collections") or []):
            if isinstance(it, dict):
                nm = it.get("name")
                if nm:
                    names.add(nm)
        if not names and hasattr(cols, "collections"):
            for it in getattr(cols, "collections") or []:
                nm = getattr(it, "name", None) or (it.get("name") if isinstance(it, dict) else None)
                if nm:
                    names.add(nm)
    except Exception:
        pass

    # B) fallback: collect unique names from market listings via search() with multiple sorts
    if not names:
        LIMIT = 100
        pages = _FALLBACK_PAGES_DEEP if deep else _FALLBACK_PAGES_LIGHT
        sorts = ("price_asc", "latest", "gift_id_asc", "price_desc")
        for s in sorts:
            for page in range(pages):
                try:
                    batch = await gifts_search(sort=s, offset=page*LIMIT, limit=LIMIT, authData=auth)
                except Exception:
                    break
                if not batch:
                    break
                for g in batch:
                    nm = getattr(g, "name", None) or (g.get("name") if isinstance(g, dict) else None)
                    if nm:
                        names.add(nm)
                await asyncio.sleep(0.1)  # бережно к API

    out = sorted(names)
    _COLL_CACHE.update(ts=now, names=out)
    return out


async def _models_backs(name: str):
    auth = await _get_auth()
    floors = await gifts_filterFloors(gift_name=name, authData=auth)
    models = sorted((getattr(floors, "models", {}) or {}).keys())
    backs = sorted((getattr(floors, "backdrops", {}) or {}).keys())
    return models, backs


@router.message(Command("collections"))
async def cmd_collections(message: Message):
    if not _allowed(message.from_user.id):
        return await message.answer("Доступ запрещён.")
    parts = message.text.split(maxsplit=1)
    q = parts[1].strip() if len(parts) > 1 else ""
    deep = q.lower() in {"all", "refresh", "*", "обновить", "все"}
    names = await _all_collection_names(deep=deep)
    if q and not deep:
        ql = q.lower()
        names = [n for n in names if ql in n.lower()]
    if not names:
        return await message.answer("Коллекции не найдены.")
    view = "\n".join("• " + n for n in names[:200])
    more = "" if len(names) <= 200 else f"\n… и ещё {len(names)-200}"
    await message.answer("Коллекции (Portals):\n" + view + more)


@router.message(Command("add_filter"))
async def add_filter_start(message: Message, state: FSMContext):
    if not _allowed(message.from_user.id):
        return await message.answer("Доступ запрещён.")
    await state.clear()
    await state.set_state(NewFilter.collection)
    await message.answer("Введи точное название коллекции (Portals). Подсказки: /collections <текст>")


@router.message(NewFilter.collection)
async def step_collection(message: Message, state: FSMContext):
    col = message.text.strip()
    names = await _all_collection_names()
    if col not in names:
        q = col.lower()
        sug = [n for n in names if q in n.lower()][:10]
        if sug:
            sug_text = "\n• " + "\n• ".join(sug)
            return await message.answer("Коллекция не найдена. Похожие:" + sug_text + "\n\nВведи точное имя.")
        return await message.answer("Коллекция не найдена. Введи точное имя.")
    await state.update_data(collection=col, m_page=0, b_page=0, picked_models=[], picked_backs=[])
    models, backs = await _models_backs(col)
    await state.update_data(all_models=models, all_backs=backs)
    await state.set_state(NewFilter.models)
    await message.answer("Выбери модели (можно несколько) или нажми «Пропустить».",
                         reply_markup=make_toggle_keyboard(models, [], prefix="m"))


@router.callback_query(NewFilter.models, F.data.startswith("pick_m:"))
async def pick_model(cb: CallbackQuery, state: FSMContext):
    m = cb.data.split(":", 1)[1]
    data = await state.get_data()
    picked = set(data.get("picked_models", []))
    picked.remove(m) if m in picked else picked.add(m)
    await state.update_data(picked_models=list(picked))
    page = data.get("m_page", 0)
    await cb.message.edit_reply_markup(make_toggle_keyboard(data.get("all_models", []), list(picked), prefix="m", page=page))
    await cb.answer(f"Выбрано: {len(picked)}")


@router.callback_query(NewFilter.models, F.data.startswith("m_page:"))
async def page_models(cb: CallbackQuery, state: FSMContext):
    page = int(cb.data.split(":", 1)[1])
    await state.update_data(m_page=page)
    data = await state.get_data()
    await cb.message.edit_reply_markup(make_toggle_keyboard(data.get("all_models", []), data.get("picked_models", []), prefix="m", page=page))
    await cb.answer("Страница переключена")


@router.callback_query(NewFilter.models, F.data == "m_skip")
async def skip_models(cb: CallbackQuery, state: FSMContext):
    await state.update_data(picked_models=[])
    await _go_backdrops(cb, state)


@router.callback_query(NewFilter.models, F.data == "m_next")
async def next_models(cb: CallbackQuery, state: FSMContext):
    await _go_backdrops(cb, state)


async def _go_backdrops(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    backs = data.get("all_backs", [])
    await state.set_state(NewFilter.backdrops)
    await cb.message.edit_text("Выбери фоны (можно несколько) или нажми «Пропустить».",
                               reply_markup=make_toggle_keyboard(backs, [], prefix="b"))


@router.callback_query(NewFilter.backdrops, F.data.startswith("pick_b:"))
async def pick_back(cb: CallbackQuery, state: FSMContext):
    b = cb.data.split(":", 1)[1]
    data = await state.get_data()
    picked = set(data.get("picked_backs", []))
    picked.remove(b) if b in picked else picked.add(b)
    await state.update_data(picked_backs=list(picked))
    page = data.get("b_page", 0)
    await cb.message.edit_reply_markup(make_toggle_keyboard(data.get("all_backs", []), list(picked), prefix="b", page=page))
    await cb.answer(f"Выбрано: {len(picked)}")


@router.callback_query(NewFilter.backdrops, F.data.startswith("b_page:"))
async def page_backs(cb: CallbackQuery, state: FSMContext):
    page = int(cb.data.split(":", 1)[1])
    await state.update_data(b_page=page)
    data = await state.get_data()
    await cb.message.edit_reply_markup(make_toggle_keyboard(data.get("all_backs", []), data.get("picked_backs", []), prefix="b", page=page))
    await cb.answer("Страница переключена")


@router.callback_query(NewFilter.backdrops, F.data == "b_skip")
async def skip_backs(cb: CallbackQuery, state: FSMContext):
    await state.update_data(picked_backs=[])
    await _ask_price(cb, state)


@router.callback_query(NewFilter.backdrops, F.data == "b_next")
async def next_backs(cb: CallbackQuery, state: FSMContext):
    await _ask_price(cb, state)


async def _ask_price(cb: CallbackQuery, state: FSMContext):
    await state.set_state(NewFilter.max_price)
    await cb.message.edit_text("Введи максимальную цену в TON (например 3.5).")


@router.message(NewFilter.max_price)
async def step_price(message: Message, state: FSMContext):
    try:
        price = float(message.text.replace(",", ".").strip())
        if price <= 0:
            raise ValueError()
    except Exception:
        return await message.answer("Нужно положительное число, например 2.75")
    await state.update_data(max_price=price)
    await state.set_state(NewFilter.qty)
    await message.answer("Сколько штук покупать максимум одним лотом? (целое число > 0)")


@router.message(NewFilter.qty)
async def step_qty(message: Message, state: FSMContext):
    try:
        qty = int(message.text.strip())
        if qty <= 0:
            raise ValueError()
    except Exception:
        return await message.answer("Нужно целое число > 0.")
    await state.update_data(qty=qty)
    data = await state.get_data()
    models = ", ".join(sorted(data.get("picked_models", []))) or "любой"
    backs = ", ".join(sorted(data.get("picked_backs", []))) or "любой"
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
async def step_save(message: Message, state: FSMContext):
    data = await state.get_data()
    from db.db import get_pool
    pool = await get_pool()
    await pool.execute("INSERT INTO users(telegram_id) VALUES($1) ON CONFLICT (telegram_id) DO NOTHING", message.from_user.id)
    user_id = await pool.fetchval("SELECT id FROM users WHERE telegram_id=$1", message.from_user.id)
    fid = await db.add_filter(
        user_id=user_id,
        collection=data["collection"],
        model=(data.get("picked_models") or None),
        backdrop=(data.get("picked_backs") or None),
        max_price=data["max_price"],
        quantity=data["qty"],
        active=True,
    )
    await db.log("bot", "add_filter", "ok", filter_id=fid, user_id=message.from_user.id, details="fsm save")
    await state.clear()
    await message.answer(f"Сохранено. ID фильтра: {fid}")


@router.message(NewFilter.confirm, Command("cancel"))
async def step_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Отменено.")