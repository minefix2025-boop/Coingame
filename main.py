import asyncio
import json
import os
import logging
import random
import string
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Set, List, Tuple, Optional

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, PreCheckoutQuery, LabeledPrice,
    FSInputFile
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

# Отключаем лишние логи
logging.getLogger("httpx").setLevel(logging.WARNING)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ---------------- НАСТРОЙКИ ----------------
BOT_TOKEN = "8202743130:AAGdu2M59Byz0oZ5A-y-JX6iU30qlbR-g6A"
ADMINS = [8136808901, 6479090914, 7716319249, 7406866574]
START_BALANCE = 100
DAILY_BALANCE = 500
DAILY_BALANCE_ELITE = 2500
DAILY_BALANCE_DELUXE = 5000
DAILY_ACCELERATORS = 30
DAILY_ACCELERATORS_ELITE = 60
DAILY_ACCELERATORS_DELUXE = 100
START_ACCELERATORS = 10
DAILY_HOURS = 12

# ---------------- НАСТРОЙКИ ДОНАТА ----------------
STAR_TO_COINS = 10000
ELITE_PRICE = 50
DELUXE_PRICE = 99

# ---------------- ФАЙЛ ДЛЯ ХРАНЕНИЯ ДАННЫХ ----------------
DATA_FILE = "bot_data.json"

# ---------------- НАСТРОЙКИ РУЛЕТКИ ----------------
ROULETTE_MULTIPLIER = 36

# ---------------- НАСТРОЙКИ РУДНИКА ----------------
MINE_LEVELS = {
    0: {"name": "Золотая шахта", "resource": "Золото", "price_per_unit": 2, "upgrade_cost": 1000000},
    1: {"name": "Рубиновая шахта", "resource": "Рубин", "price_per_unit": 10, "upgrade_cost": 5000000},
    2: {"name": "Алмазная шахта", "resource": "Алмаз", "price_per_unit": 100, "upgrade_cost": 20000000}
}

# ---------------- НАСТРОЙКИ БИЗНЕСА ----------------
BUSINESS_TYPES = {
    "shaurma": {"name": "Шаурма", "cost": 100, "base_profit": 10, "profit_period": 30},
    "cafe": {"name": "Кафе", "cost": 1000, "base_profit": 100, "profit_period": 15},
    "space": {"name": "Космическое агентство", "cost": 1000000, "base_profit": 10000, "profit_period": 5}
}

# ---------------- НАСТРОЙКИ МИНИ-ИГРЫ ----------------
MINI_ROWS = 5
MINI_COLS = 5
MINI_CELLS = MINI_ROWS * MINI_COLS
MINI_BOMBS = 5
MINI_MULTIPLIER = 1.3

# ---------------- ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ----------------
user_balances = {}
daily_used = {}
ranks = {}
user_accelerators = {}
mine_data = {}
business_data = {}
user_bank = {}
promo_codes = {}
user_profiles = {}
mini_games = {}
user_donations = {}
user_premium = {}
roulette_games = {}
pending_invoices = {}
user_mini_settings = {}

INFINITE_BALANCE = "INFINITE"

# Инициализация бота
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


# ---------------- ФУНКЦИИ ДЛЯ РАБОТЫ С ФАЙЛАМИ ----------------
def save_data():
    try:
        data = {
            "user_balances": {str(k): v for k, v in user_balances.items()},
            "daily_used": {str(k): v.isoformat() if v else None for k, v in daily_used.items()},
            "ranks": {str(k): v for k, v in ranks.items()},
            "user_accelerators": {str(k): v for k, v in user_accelerators.items()},
            "mine_data": {str(k): v for k, v in mine_data.items()},
            "business_data": {str(k): v for k, v in business_data.items()},
            "user_bank": {str(k): v for k, v in user_bank.items()},
            "promo_codes": {k: {**v, "used_by": list(v["used_by"]) if isinstance(v["used_by"], set) else v["used_by"]}
                            for k, v in promo_codes.items()},
            "user_profiles": {str(k): v for k, v in user_profiles.items()},
            "user_donations": {str(k): v for k, v in user_donations.items()},
            "user_premium": {str(k): v for k, v in user_premium.items()},
            "user_mini_settings": {str(k): v for k, v in user_mini_settings.items()}
        }

        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)

        logger.info("✅ Данные успешно сохранены")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения данных: {e}")
        return False


def load_data():
    global user_balances, daily_used, ranks, user_accelerators, mine_data
    global business_data, user_bank, promo_codes, user_profiles
    global user_donations, user_premium, user_mini_settings

    if not os.path.exists(DATA_FILE):
        logger.info("📁 Файл данных не найден, создаем новый")
        return False

    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)

        user_balances = {int(k): v for k, v in data.get("user_balances", {}).items()}

        daily_used_data = data.get("daily_used", {})
        for k, v in daily_used_data.items():
            if v:
                try:
                    daily_used[int(k)] = datetime.fromisoformat(v)
                except:
                    daily_used[int(k)] = None

        ranks = {int(k): v for k, v in data.get("ranks", {}).items()}
        user_accelerators = {int(k): v for k, v in data.get("user_accelerators", {}).items()}
        mine_data = {int(k): v for k, v in data.get("mine_data", {}).items()}
        business_data = {int(k): v for k, v in data.get("business_data", {}).items()}
        user_bank = {int(k): v for k, v in data.get("user_bank", {}).items()}

        promo_codes_data = data.get("promo_codes", {})
        promo_codes = {}
        for code, promo in promo_codes_data.items():
            promo_copy = promo.copy()
            if isinstance(promo_copy.get("used_by"), list):
                promo_copy["used_by"] = set(promo_copy["used_by"])
            promo_codes[code] = promo_copy

        user_profiles = {int(k): v for k, v in data.get("user_profiles", {}).items()}
        user_donations = {int(k): v for k, v in data.get("user_donations", {}).items()}
        user_premium = {int(k): v for k, v in data.get("user_premium", {}).items()}
        user_mini_settings = {int(k): v for k, v in data.get("user_mini_settings", {}).items()}

        logger.info("✅ Данные успешно загружены")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки данных: {e}")
        return False


# ---------------- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ----------------
def ensure_user(u_id: int):
    if u_id not in user_balances:
        user_balances[u_id] = START_BALANCE
    if u_id not in user_accelerators:
        user_accelerators[u_id] = START_ACCELERATORS
    if u_id not in mine_data:
        mine_data[u_id] = {"level": 0, "resources": 0, "auto_collect": False}
    if u_id not in business_data:
        business_data[u_id] = {"type": None, "profit": 0, "active": False, "last_collect": None}
    if u_id not in user_bank:
        user_bank[u_id] = 0
    if u_id not in user_profiles:
        user_profiles[u_id] = {"level": 1, "xp": 0, "next_level_xp": 100}
    if u_id not in user_donations:
        user_donations[u_id] = {"total_stars": 0, "total_coins": 0, "transactions": []}
    if u_id not in user_premium:
        user_premium[u_id] = {"type": None, "expires": None, "purchased_at": None}


def get_premium_status(user_id: int) -> str:
    ensure_user(user_id)
    premium = user_premium[user_id]

    if premium["type"] == "deluxe":
        return "Делюкс"
    elif premium["type"] == "elite":
        return "Элит"
    else:
        return "Обычный"


def get_daily_bonus(user_id: int) -> tuple:
    status = get_premium_status(user_id)
    if status == "Делюкс":
        return DAILY_BALANCE_DELUXE, DAILY_ACCELERATORS_DELUXE
    elif status == "Элит":
        return DAILY_BALANCE_ELITE, DAILY_ACCELERATORS_ELITE
    else:
        return DAILY_BALANCE, DAILY_ACCELERATORS


def get_balance(u_id: int):
    return user_balances.get(u_id, START_BALANCE)


def has_infinite_balance(u_id: int) -> bool:
    return user_balances.get(u_id) == INFINITE_BALANCE


def format_balance(u_id: int) -> str:
    balance = get_balance(u_id)
    if balance == INFINITE_BALANCE:
        return "∞"
    if isinstance(balance, (int, float)):
        return f"{balance:,}"
    return str(balance)


def format_bank_balance(u_id: int) -> str:
    balance = user_bank.get(u_id, 0)
    return f"{balance:,}"


def can_spend(u_id: int, amount: int) -> bool:
    if has_infinite_balance(u_id):
        return True
    balance = get_balance(u_id)
    if isinstance(balance, (int, float)):
        return balance >= amount
    return False


def spend_balance(u_id: int, amount: int):
    if has_infinite_balance(u_id):
        return
    if u_id in user_balances and isinstance(user_balances[u_id], (int, float)):
        user_balances[u_id] -= amount


def add_balance(u_id: int, amount: int):
    if has_infinite_balance(u_id):
        return
    if u_id not in user_balances:
        user_balances[u_id] = START_BALANCE + amount
    else:
        if isinstance(user_balances[u_id], (int, float)):
            user_balances[u_id] += amount
        else:
            user_balances[u_id] = START_BALANCE + amount
        add_xp(u_id, amount // 100)


def set_infinite_balance(u_id: int):
    user_balances[u_id] = INFINITE_BALANCE


def remove_infinite_balance(u_id: int):
    user_balances[u_id] = START_BALANCE


def is_admin(user_id: int) -> bool:
    return user_id in ADMINS


def has_rank(user_id: int, required_rank: str = None) -> bool:
    if is_admin(user_id):
        return True
    user_rank = ranks.get(user_id)
    if not user_rank:
        return False
    if required_rank == "Admin":
        return user_rank == "Admin"
    elif required_rank == "moderator":
        return user_rank in ["moderator", "Admin"]
    elif required_rank in ["elite", "deluxe"]:
        return user_premium.get(user_id, {}).get("type") == required_rank
    return False


def get_user_status(user_id: int) -> str:
    if is_admin(user_id):
        return "Администратор"
    elif ranks.get(user_id) == "Admin":
        return "Админ"
    elif ranks.get(user_id) == "moderator":
        return "Модератор"
    else:
        return get_premium_status(user_id)


def can_work(user_id: int) -> bool:
    return user_accelerators.get(user_id, 0) > 0 or has_infinite_balance(user_id)


def use_accelerator(user_id: int, amount: int = 1):
    if has_infinite_balance(user_id):
        return
    if user_accelerators.get(user_id, 0) >= amount:
        user_accelerators[user_id] = user_accelerators.get(user_id, 0) - amount


def add_accelerator(user_id: int, amount: int):
    user_accelerators[user_id] = user_accelerators.get(user_id, 0) + amount


def add_xp(user_id: int, xp_amount: int):
    if user_id not in user_profiles:
        user_profiles[user_id] = {"level": 1, "xp": 0, "next_level_xp": 100}
    if xp_amount <= 0:
        return
    user_profiles[user_id]["xp"] += xp_amount

    while user_profiles[user_id]["xp"] >= user_profiles[user_id]["next_level_xp"]:
        user_profiles[user_id]["level"] += 1
        user_profiles[user_id]["xp"] -= user_profiles[user_id]["next_level_xp"]
        user_profiles[user_id]["next_level_xp"] = user_profiles[user_id]["next_level_xp"] * 2
        reward = user_profiles[user_id]["level"] * 1000
        add_balance(user_id, reward)
        add_accelerator(user_id, user_profiles[user_id]["level"] * 5)


def get_mine_info(user_id: int) -> str:
    if user_id not in mine_data:
        ensure_user(user_id)
    mine = mine_data.get(user_id, {"level": 0, "resources": 0, "auto_collect": False})

    level = mine["level"]
    if level > 2:
        level = 2

    level_info = MINE_LEVELS[level]

    info = f"{level_info['name']}\n"
    info += f"Ресурс: {level_info['resource']}\n"
    info += f"Количество: {mine['resources']:,}\n"
    info += f"Стоимость: {level_info['price_per_unit']} монет за 1 ед.\n"
    info += f"Общая стоимость: {mine['resources'] * level_info['price_per_unit']:,} монет\n"
    info += f"Авто-сбор: {'Вкл' if mine['auto_collect'] else 'Выкл'}\n"

    if level < 2:
        next_level = MINE_LEVELS[level + 1]
        info += f"\nУлучшение до {next_level['name']}:\n"
        info += f"Стоимость: {next_level['upgrade_cost']:,} монет\n"
        info += f"Новый ресурс: {next_level['resource']}\n"
        info += f"Новая цена: {next_level['price_per_unit']} монет за 1 ед."

    return info


# ---------------- КЛАВИАТУРЫ ----------------
def get_main_reply_keyboard() -> ReplyKeyboardMarkup:
    """Главная reply клавиатура"""
    builder = ReplyKeyboardBuilder()

    buttons = [
        "Баланс", "Работа", "Игры",
        "Профиль", "Бизнес", "Рудник",
        "Банк", "Рулетка", "Донат",
        "Админ", "Помощь"
    ]

    for btn in buttons:
        builder.add(KeyboardButton(text=btn))

    builder.adjust(3, 3, 3, 2)
    return builder.as_markup(resize_keyboard=True)


def get_jobs_reply_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для работы"""
    builder = ReplyKeyboardBuilder()

    buttons = [
        "Курьер", "Таксист", "Программист",
        "Назад в меню"
    ]

    for btn in buttons:
        builder.add(KeyboardButton(text=btn))

    builder.adjust(3, 1)
    return builder.as_markup(resize_keyboard=True)


def get_games_reply_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для игр"""
    builder = ReplyKeyboardBuilder()

    buttons = [
        "Казино", "Монетка", "Мини-игра",
        "Назад в меню"
    ]

    for btn in buttons:
        builder.add(KeyboardButton(text=btn))

    builder.adjust(3, 1)
    return builder.as_markup(resize_keyboard=True)


def get_mine_reply_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для рудника"""
    builder = ReplyKeyboardBuilder()

    buttons = [
        "Собрать ресурсы", "Улучшить рудник",
        "Авто-сбор", "Назад в меню"
    ]

    for btn in buttons:
        builder.add(KeyboardButton(text=btn))

    builder.adjust(2, 2)
    return builder.as_markup(resize_keyboard=True)


def get_business_reply_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для бизнеса"""
    builder = ReplyKeyboardBuilder()

    buttons = [
        "Купить бизнес", "Собрать прибыль",
        "Продать бизнес", "Назад в меню"
    ]

    for btn in buttons:
        builder.add(KeyboardButton(text=btn))

    builder.adjust(2, 2)
    return builder.as_markup(resize_keyboard=True)


def get_bank_reply_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для банка"""
    builder = ReplyKeyboardBuilder()

    buttons = [
        "Внести", "Снять", "Баланс",
        "Назад в меню"
    ]

    for btn in buttons:
        builder.add(KeyboardButton(text=btn))

    builder.adjust(3, 1)
    return builder.as_markup(resize_keyboard=True)


def get_donate_reply_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для доната"""
    builder = ReplyKeyboardBuilder()

    buttons = [
        "Купить Элит (50 ⭐)",
        "Купить Делюкс (99 ⭐)",
        "Купить коины",
        "Назад в меню"
    ]

    for btn in buttons:
        builder.add(KeyboardButton(text=btn))

    builder.adjust(1, 1, 1, 1)
    return builder.as_markup(resize_keyboard=True)


def get_profile_reply_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для профиля"""
    builder = ReplyKeyboardBuilder()

    buttons = [
        "Статистика", "Имущество",
        "Назад в меню"
    ]

    for btn in buttons:
        builder.add(KeyboardButton(text=btn))

    builder.adjust(2, 1)
    return builder.as_markup(resize_keyboard=True)


# ---------------- СИНИЕ INLINE КЛАВИАТУРЫ (style="primary") ----------------
def get_primary_inline_menu() -> InlineKeyboardMarkup:
    """Главное меню с синими кнопками"""
    builder = InlineKeyboardBuilder()

    buttons = [
        ("Баланс", "balance"),
        ("Работа", "work"),
        ("Игры", "games"),
        ("Профиль", "profile"),
        ("Бизнес", "business"),
        ("Рудник", "mine"),
        ("Банк", "bank"),
        ("Рулетка", "roulette"),
        ("Донат", "donate"),
        ("Админ", "admin"),
        ("Помощь", "help")
    ]

    for text, callback in buttons:
        builder.add(InlineKeyboardButton(
            text=text,
            callback_data=callback,
            style="primary"
        ))

    builder.adjust(3, 3, 3, 2)
    return builder.as_markup()


def get_work_inline() -> InlineKeyboardMarkup:
    """Меню работы с синими кнопками"""
    builder = InlineKeyboardBuilder()

    jobs = [
        ("Курьер", "job_courier"),
        ("Таксист", "job_taxi"),
        ("Программист", "job_programmer")
    ]

    for text, callback in jobs:
        builder.add(InlineKeyboardButton(
            text=text,
            callback_data=callback,
            style="primary"
        ))

    builder.adjust(3)
    builder.row(InlineKeyboardButton(
        text="Назад",
        callback_data="back_main",
        style="primary"
    ))

    return builder.as_markup()


def get_games_inline() -> InlineKeyboardMarkup:
    """Меню игр с синими кнопками"""
    builder = InlineKeyboardBuilder()

    games = [
        ("Казино", "game_casino"),
        ("Монетка", "game_coin"),
        ("Мини-игра", "game_mini")
    ]

    for text, callback in games:
        builder.add(InlineKeyboardButton(
            text=text,
            callback_data=callback,
            style="primary"
        ))

    builder.adjust(3)
    builder.row(InlineKeyboardButton(
        text="Назад",
        callback_data="back_main",
        style="primary"
    ))

    return builder.as_markup()


def get_roulette_inline() -> InlineKeyboardMarkup:
    """Клавиатура для рулетки с числами"""
    builder = InlineKeyboardBuilder()

    # Числа от 0 до 36
    for i in range(0, 37):
        builder.add(InlineKeyboardButton(
            text=str(i),
            callback_data=f"roulette_num_{i}",
            style="primary"
        ))

    builder.adjust(6)
    builder.row(InlineKeyboardButton(
        text="Отмена",
        callback_data="roulette_cancel",
        style="primary"
    ))

    return builder.as_markup()


def get_mine_inline() -> InlineKeyboardMarkup:
    """Меню рудника с синими кнопками"""
    builder = InlineKeyboardBuilder()

    actions = [
        ("Собрать ресурсы", "mine_collect"),
        ("Улучшить рудник", "mine_upgrade"),
        ("Авто-сбор", "mine_auto")
    ]

    for text, callback in actions:
        builder.add(InlineKeyboardButton(
            text=text,
            callback_data=callback,
            style="primary"
        ))

    builder.adjust(2, 1)
    builder.row(InlineKeyboardButton(
        text="Назад",
        callback_data="back_main",
        style="primary"
    ))

    return builder.as_markup()


def get_business_inline() -> InlineKeyboardMarkup:
    """Меню бизнеса с синими кнопками"""
    builder = InlineKeyboardBuilder()

    for biz_id, biz_info in BUSINESS_TYPES.items():
        builder.add(InlineKeyboardButton(
            text=f"{biz_info['name']} ({biz_info['cost']} монет)",
            callback_data=f"buy_{biz_id}",
            style="primary"
        ))

    builder.adjust(1)
    builder.row(
        InlineKeyboardButton(text="Собрать прибыль", callback_data="business_collect", style="primary"),
        InlineKeyboardButton(text="Продать бизнес", callback_data="business_sell", style="primary")
    )
    builder.row(InlineKeyboardButton(
        text="Назад",
        callback_data="back_main",
        style="primary"
    ))

    return builder.as_markup()


def get_bank_inline() -> InlineKeyboardMarkup:
    """Меню банка с синими кнопками"""
    builder = InlineKeyboardBuilder()

    builder.add(
        InlineKeyboardButton(text="Внести", callback_data="bank_deposit", style="primary"),
        InlineKeyboardButton(text="Снять", callback_data="bank_withdraw", style="primary"),
        InlineKeyboardButton(text="Баланс", callback_data="bank_balance", style="primary")
    )

    builder.adjust(3)
    builder.row(InlineKeyboardButton(
        text="Назад",
        callback_data="back_main",
        style="primary"
    ))

    return builder.as_markup()


def get_donate_inline() -> InlineKeyboardMarkup:
    """Меню доната с синими кнопками"""
    builder = InlineKeyboardBuilder()

    builder.add(
        InlineKeyboardButton(text=f"Купить Элит ({ELITE_PRICE} ⭐)", callback_data="buy_elite", style="primary"),
        InlineKeyboardButton(text=f"Купить Делюкс ({DELUXE_PRICE} ⭐)", callback_data="buy_deluxe", style="primary"),
        InlineKeyboardButton(text="Купить коины", callback_data="buy_coins", style="primary")
    )

    builder.adjust(1)
    builder.row(InlineKeyboardButton(
        text="Назад",
        callback_data="back_main",
        style="primary"
    ))

    return builder.as_markup()


def get_profile_inline() -> InlineKeyboardMarkup:
    """Меню профиля с синими кнопками"""
    builder = InlineKeyboardBuilder()

    builder.add(
        InlineKeyboardButton(text="Статистика", callback_data="profile_stats", style="primary"),
        InlineKeyboardButton(text="Имущество", callback_data="profile_assets", style="primary")
    )

    builder.adjust(2)
    builder.row(InlineKeyboardButton(
        text="Назад",
        callback_data="back_main",
        style="primary"
    ))

    return builder.as_markup()


def get_admin_inline() -> InlineKeyboardMarkup:
    """Админ меню с синими кнопками"""
    builder = InlineKeyboardBuilder()

    admin_buttons = [
        ("Выдать монеты", "admin_money"),
        ("Выдать ранг", "admin_rank"),
        ("Беск. баланс", "admin_inf"),
        ("Снять беск.", "admin_remove_inf"),
        ("Промокод", "admin_promo"),
        ("Сложность", "admin_chance")
    ]

    for text, callback in admin_buttons:
        builder.add(InlineKeyboardButton(
            text=text,
            callback_data=callback,
            style="primary"
        ))

    builder.adjust(2)
    builder.row(InlineKeyboardButton(
        text="Назад",
        callback_data="back_main",
        style="primary"
    ))

    return builder.as_markup()


# ---------------- МИНИ-ИГРА ----------------
def generate_mini_board(mines_count: int = MINI_BOMBS) -> Set[int]:
    bombs = set()
    while len(bombs) < mines_count:
        bombs.add(random.randint(1, MINI_CELLS))
    return bombs


def index_to_coords(idx: int) -> Tuple[int, int]:
    i = idx - 1
    return divmod(i, MINI_COLS)


def coords_to_index(r: int, c: int) -> int:
    return r * MINI_COLS + c + 1


def neighbors_indices(idx: int) -> List[int]:
    r, c = index_to_coords(idx)
    res = []
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            nr, nc = r + dr, c + dc
            if 0 <= nr < MINI_ROWS and 0 <= nc < MINI_COLS:
                res.append(coords_to_index(nr, nc))
    return res


def create_mini_keyboard(opened: Set[int], bombs: Set[int], game_id: str = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for row in range(MINI_ROWS):
        row_buttons = []
        for col in range(MINI_COLS):
            idx = coords_to_index(row, col)
            cell_id = f"{game_id}_{idx}" if game_id else str(idx)

            if idx in opened:
                if idx in bombs:
                    row_buttons.append(InlineKeyboardButton("💣", callback_data=f"mini_bomb_{cell_id}"))
                else:
                    row_buttons.append(InlineKeyboardButton("⬜", callback_data=f"mini_empty_{cell_id}"))
            else:
                row_buttons.append(InlineKeyboardButton("❌", callback_data=f"mini_open_{cell_id}"))

        builder.row(*row_buttons)

    if game_id:
        builder.row(InlineKeyboardButton("Забрать выигрыш", callback_data=f"mini_cashout_{game_id}"))

    return builder.as_markup()


# ---------------- КОМАНДЫ ----------------
@dp.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    ensure_user(user_id)

    daily_bonus, daily_acc = get_daily_bonus(user_id)

    await message.answer(
        f"<b>ДОБРО ПОЖАЛОВАТЬ В БОТ-ИГРУ!</b>\n\n"
        f"Статус: {get_user_status(user_id)}\n"
        f"Баланс: {format_balance(user_id)} монет\n"
        f"Ускорители: {user_accelerators.get(user_id, 0)}\n\n"
        f"Ежедневный бонус: /daily (+{daily_bonus:,} монет, +{daily_acc} ускорителей)\n\n"
        f"Используйте меню для навигации:",
        reply_markup=get_main_reply_keyboard()
    )

    await message.answer(
        "Или выберите действие:",
        reply_markup=get_primary_inline_menu()
    )


@dp.message(Command("help"))
async def cmd_help(message: Message):
    help_text = (
        "<b>ПОЛНАЯ ИНСТРУКЦИЯ</b>\n\n"
        "БАЛАНС И РАБОТА:\n"
        "• Баланс - посмотреть баланс и ускорители\n"
        "• Работа - заработать монеты (тратит ускорители)\n"
        "• /daily - ежедневный бонус\n\n"
        "ПРОФИЛЬ:\n"
        "• Статистика - уровень, опыт, статус\n"
        "• Имущество - рудник, бизнес, банк\n\n"
        "ИГРЫ:\n"
        "• Казино - /bet <сумма> (x2)\n"
        "• Монетка - /coin\n"
        "• Мини-игра - /mini <сумма>\n"
        "• Рулетка - /roulette <сумма> (x36)\n\n"
        "РУДНИК:\n"
        "• Автоматическая добыча ресурсов\n"
        "• Улучшение для более ценных ресурсов\n\n"
        "БИЗНЕС:\n"
        "• Пассивный доход\n"
        "• Разные уровни бизнеса\n\n"
        "БАНК:\n"
        "• /bank <сумма> - положить\n"
        "• /bank w <сумма> - снять\n\n"
        "ДОНАТ:\n"
        "• /buy_coins <звезды> - купить коины\n"
        "• /buy_elite - купить Элит\n"
        "• /buy_deluxe - купить Делюкс\n\n"
        "ПРОМОКОДЫ:\n"
        "• Введите #промокод для активации"
    )

    await message.answer(help_text, reply_markup=get_main_reply_keyboard())


@dp.message(Command("daily"))
async def cmd_daily(message: Message):
    user_id = message.from_user.id
    ensure_user(user_id)

    now = datetime.now()

    if user_id in daily_used and daily_used[user_id]:
        last = daily_used[user_id]
        if now - last < timedelta(hours=DAILY_HOURS):
            remaining = timedelta(hours=DAILY_HOURS) - (now - last)
            hours = remaining.seconds // 3600
            minutes = (remaining.seconds % 3600) // 60
            await message.answer(
                f"⏳ Ещё рано!\nСледующий бонус через: {hours}ч {minutes}м",
                reply_markup=get_main_reply_keyboard()
            )
            return

    daily_bonus, daily_acc = get_daily_bonus(user_id)

    if not has_infinite_balance(user_id):
        add_balance(user_id, daily_bonus)
        add_accelerator(user_id, daily_acc)
        add_xp(user_id, 100)
    else:
        add_accelerator(user_id, daily_acc)

    daily_used[user_id] = now

    await message.answer(
        f"<b>🎁 ЕЖЕДНЕВНЫЙ БОНУС!</b>\n\n"
        f"Монеты: +{daily_bonus:,}\n"
        f"Ускорители: +{daily_acc}\n"
        f"Баланс: {format_balance(user_id)}\n"
        f"Всего ускорителей: {user_accelerators.get(user_id, 0)}",
        reply_markup=get_main_reply_keyboard()
    )

    save_data()


@dp.message(Command("bet"))
async def cmd_bet(message: Message):
    user_id = message.from_user.id
    ensure_user(user_id)

    args = message.text.split()
    if len(args) != 2 or not args[1].isdigit():
        await message.answer(
            "Используй: /bet <сумма>\nПример: /bet 100",
            reply_markup=get_games_reply_keyboard()
        )
        return

    amount = int(args[1])
    if amount <= 0:
        await message.answer("❌ Сумма должна быть больше 0!", reply_markup=get_games_reply_keyboard())
        return

    if not can_spend(user_id, amount):
        await message.answer(
            f"❌ Недостаточно монет!\nБаланс: {format_balance(user_id)}",
            reply_markup=get_games_reply_keyboard()
        )
        return

    infinite_user = has_infinite_balance(user_id)
    win = random.choice([True, False])

    if win:
        if not infinite_user:
            add_balance(user_id, amount)
            add_xp(user_id, amount // 50)
        result = f"🎉 ПОБЕДА! +{amount:,} монет"
    else:
        if not infinite_user:
            spend_balance(user_id, amount)
        result = f"💔 ПРОИГРЫШ -{amount:,} монет"

    await message.answer(
        f"{result}\nБаланс: {format_balance(user_id)}",
        reply_markup=get_games_reply_keyboard()
    )

    save_data()


@dp.message(Command("coin"))
async def cmd_coin(message: Message):
    user_id = message.from_user.id
    ensure_user(user_id)
    result = random.choice(['Орёл', 'Решка'])
    await message.answer(
        f"🪙 {result}\nБаланс: {format_balance(user_id)}",
        reply_markup=get_games_reply_keyboard()
    )


@dp.message(Command("roulette"))
async def cmd_roulette(message: Message):
    user_id = message.from_user.id
    ensure_user(user_id)

    args = message.text.split()
    if len(args) != 2 or not args[1].isdigit():
        await message.answer(
            "Используй: /roulette <сумма>\nПример: /roulette 1000",
            reply_markup=get_games_reply_keyboard()
        )
        return

    bet = int(args[1])
    if bet <= 0:
        await message.answer("❌ Ставка должна быть больше 0!", reply_markup=get_games_reply_keyboard())
        return

    if not can_spend(user_id, bet):
        await message.answer(
            f"❌ Недостаточно монет!\nБаланс: {format_balance(user_id)}",
            reply_markup=get_games_reply_keyboard()
        )
        return

    roulette_games[user_id] = {"bet": bet}

    if not has_infinite_balance(user_id):
        spend_balance(user_id, bet)

    await message.answer(
        f"РУЛЕТКА\n\nСтавка: {bet:,} монет\nВыберите число от 0 до 36:",
        reply_markup=get_roulette_inline()
    )


@dp.message(Command("bank"))
async def cmd_bank(message: Message):
    user_id = message.from_user.id
    ensure_user(user_id)

    args = message.text.split()
    if len(args) == 1:
        await message.answer(
            f"<b>БАНК</b>\n\n"
            f"На кармане: {format_balance(user_id)}\n"
            f"В банке: {format_bank_balance(user_id)}\n\n"
            f"/bank <сумма> - положить\n"
            f"/bank w <сумма> - снять",
            reply_markup=get_bank_reply_keyboard()
        )
        return

    if len(args) == 2 and args[1].isdigit():
        amount = int(args[1])
        if amount <= 0:
            await message.answer("❌ Сумма должна быть больше 0!")
            return

        if not can_spend(user_id, amount):
            await message.answer(f"❌ Недостаточно монет!\nБаланс: {format_balance(user_id)}")
            return

        spend_balance(user_id, amount)
        user_bank[user_id] = user_bank.get(user_id, 0) + amount

        await message.answer(
            f"✅ Вы положили {amount:,} монет в банк\n\n"
            f"На кармане: {format_balance(user_id)}\n"
            f"В банке: {format_bank_balance(user_id)}",
            reply_markup=get_bank_reply_keyboard()
        )
        save_data()

    elif len(args) >= 2 and args[1].lower() in ['w', 'withdraw'] and len(args) == 3 and args[2].isdigit():
        amount = int(args[2])
        bank_balance = user_bank.get(user_id, 0)

        if amount <= 0:
            await message.answer("❌ Неверная сумма")
            return

        if amount > bank_balance:
            await message.answer(f"❌ Недостаточно средств в банке!\nДоступно: {bank_balance:,}")
            return

        user_bank[user_id] -= amount
        add_balance(user_id, amount)

        await message.answer(
            f"✅ Вы сняли {amount:,} монет из банка\n\n"
            f"На кармане: {format_balance(user_id)}\n"
            f"В банке: {format_bank_balance(user_id)}",
            reply_markup=get_bank_reply_keyboard()
        )
        save_data()


@dp.message(Command("donate"))
async def cmd_donate(message: Message):
    user_id = message.from_user.id
    ensure_user(user_id)

    await message.answer(
        "<b>ДОНАТ МАГАЗИН</b>\n\n"
        f"1 ⭐ = {STAR_TO_COINS:,} коинов\n"
        f"Элит - {ELITE_PRICE} ⭐\n"
        f"Делюкс - {DELUXE_PRICE} ⭐",
        reply_markup=get_donate_reply_keyboard()
    )


@dp.message(Command("buy_coins"))
async def cmd_buy_coins(message: Message):
    user_id = message.from_user.id

    args = message.text.split()
    if len(args) != 2 or not args[1].isdigit():
        await message.answer("Используй: /buy_coins <количество_звезд>")
        return

    stars = int(args[1])
    if stars <= 0:
        await message.answer("❌ Количество звезд должно быть больше 0!")
        return

    coins = stars * STAR_TO_COINS
    invoice_id = f"coins_{user_id}_{int(time.time())}"

    pending_invoices[invoice_id] = {
        "user_id": user_id,
        "stars": stars,
        "coins": coins,
        "type": "coins"
    }

    await message.answer_invoice(
        title=f"{coins:,} коинов",
        description=f"Покупка {coins:,} игровых коинов",
        payload=invoice_id,
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label=f"{stars} ⭐", amount=stars)]
    )


@dp.message(Command("buy_elite"))
async def cmd_buy_elite(message: Message):
    user_id = message.from_user.id

    invoice_id = f"elite_{user_id}_{int(time.time())}"

    pending_invoices[invoice_id] = {
        "user_id": user_id,
        "stars": ELITE_PRICE,
        "type": "elite"
    }

    await message.answer_invoice(
        title="Статус Элит",
        description="Элит статус НАВСЕГДА!",
        payload=invoice_id,
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label="Элит статус", amount=ELITE_PRICE)]
    )


@dp.message(Command("buy_deluxe"))
async def cmd_buy_deluxe(message: Message):
    user_id = message.from_user.id

    invoice_id = f"deluxe_{user_id}_{int(time.time())}"

    pending_invoices[invoice_id] = {
        "user_id": user_id,
        "stars": DELUXE_PRICE,
        "type": "deluxe"
    }

    await message.answer_invoice(
        title="Статус Делюкс",
        description="Делюкс статус НАВСЕГДА!",
        payload=invoice_id,
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label="Делюкс статус", amount=DELUXE_PRICE)]
    )


@dp.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):
    invoice_id = pre_checkout_query.invoice_payload
    if invoice_id in pending_invoices:
        await pre_checkout_query.answer(ok=True)
    else:
        await pre_checkout_query.answer(ok=False, error_message="❌ Счет не найден")


@dp.message(F.successful_payment)
async def successful_payment_handler(message: Message):
    user_id = message.from_user.id
    ensure_user(user_id)

    payment = message.successful_payment
    invoice_id = payment.invoice_payload
    stars = payment.total_amount

    if invoice_id not in pending_invoices:
        await message.answer("❌ Ошибка: счет не найден")
        return

    invoice_data = pending_invoices[invoice_id]

    if invoice_data["type"] == "coins":
        coins = invoice_data["coins"]
        add_balance(user_id, coins)
        add_xp(user_id, coins // 100)

        await message.answer(
            f"✅ ОПЛАТА УСПЕШНА!\n\n"
            f"Получено коинов: {coins:,}\n"
            f"Баланс: {format_balance(user_id)}",
            reply_markup=get_main_reply_keyboard()
        )

    elif invoice_data["type"] == "elite":
        user_premium[user_id] = {
            "type": "elite",
            "expires": None,
            "purchased_at": datetime.now().isoformat()
        }

        await message.answer(
            f"✨ ПОЗДРАВЛЯЕМ!\n\n"
            f"Вам выдан статус ЭЛИТ навсегда!",
            reply_markup=get_main_reply_keyboard()
        )

    elif invoice_data["type"] == "deluxe":
        user_premium[user_id] = {
            "type": "deluxe",
            "expires": None,
            "purchased_at": datetime.now().isoformat()
        }

        await message.answer(
            f"💎 ПОЗДРАВЛЯЕМ!\n\n"
            f"Вам выдан статус ДЕЛЮКС навсегда!",
            reply_markup=get_main_reply_keyboard()
        )

    del pending_invoices[invoice_id]
    save_data()


@dp.message(Command("createpromo"))
async def cmd_createpromo(message: Message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        await message.answer("❌ Только админы могут создавать промокоды")
        return

    args = message.text.split()
    if len(args) < 3:
        await message.answer(
            "🎟️ СОЗДАНИЕ ПРОМОКОДА:\n\n"
            "/createpromo <m/u> <сумма> <кол-во активаций> <код (опционально)>"
        )
        return

    promo_type = args[1].lower()
    if promo_type not in ['m', 'u']:
        await message.answer("❌ Тип должен быть 'm' (монеты) или 'u' (ускорители)")
        return

    if not args[2].isdigit() or not args[3].isdigit():
        await message.answer("❌ Сумма и количество активаций должны быть числами")
        return

    amount = int(args[2])
    activations = int(args[3])

    if len(args) >= 5:
        promo_code = args[4].upper()
        if promo_code in promo_codes:
            await message.answer("❌ Такой промокод уже существует")
            return
    else:
        promo_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

    promo_codes[promo_code] = {
        "type": promo_type,
        "amount": amount,
        "max_activations": activations,
        "used_by": set(),
        "created_by": user_id,
        "created_at": datetime.now().isoformat()
    }

    await message.answer(
        f"✅ Промокод создан!\n\nКод: {promo_code}\n"
        f"Тип: {'Монеты' if promo_type == 'm' else 'Ускорители'}\n"
        f"Сумма: {amount:,}\nАктиваций: {activations}"
    )

    save_data()


@dp.message(Command("money"))
async def cmd_money(message: Message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        await message.answer("❌ Только админы могут использовать эту команду")
        return

    args = message.text.split()
    if len(args) == 2 and args[1].isdigit():
        amount = int(args[1])
        ensure_user(user_id)
        add_balance(user_id, amount)
        await message.answer(f"✅ Вы получили {amount:,} монет\nБаланс: {format_balance(user_id)}")
        save_data()


@dp.message(Command("rank"))
async def cmd_rank(message: Message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        await message.answer("❌ Только админы могут выдавать ранги")
        return

    args = message.text.split()
    if len(args) >= 3:
        rank_type = args[1].lower()
        if rank_type not in ["admin", "moderator", "elite", "deluxe"]:
            await message.answer("Доступные ранги: admin, moderator, elite, deluxe")
            return

        try:
            target_id = int(args[2])

            if rank_type in ["elite", "deluxe"]:
                user_premium[target_id] = {"type": rank_type, "expires": None,
                                           "purchased_at": datetime.now().isoformat()}
                await message.answer(f"👑 Пользователь теперь {rank_type.capitalize()}!")
            else:
                ranks[target_id] = rank_type.capitalize()
                await message.answer(f"👑 Пользователь теперь {rank_type.capitalize()}!")

            save_data()
        except:
            await message.answer("❌ Не удалось найти пользователя")


# ---------------- ТЕКСТОВЫЕ ОБРАБОТЧИКИ ----------------
@dp.message(F.text == "Баланс")
async def text_balance(message: Message):
    user_id = message.from_user.id
    ensure_user(user_id)

    await message.answer(
        f"<b>💰 ВАШ БАЛАНС</b>\n\n"
        f"Наличные: {format_balance(user_id)} монет\n"
        f"Ускорители: {user_accelerators.get(user_id, 0)}\n"
        f"В банке: {format_bank_balance(user_id)} монет",
        reply_markup=get_main_reply_keyboard()
    )


@dp.message(F.text == "Работа")
async def text_work(message: Message):
    user_id = message.from_user.id

    if not can_work(user_id):
        await message.answer(
            "❌ У вас закончились ускорители!\nПолучите ускорители через /daily или промокоды.",
            reply_markup=get_main_reply_keyboard()
        )
        return

    await message.answer(
        "💼 Выберите работу:",
        reply_markup=get_jobs_reply_keyboard()
    )


@dp.message(F.text.in_(["Курьер", "Таксист", "Программист"]))
async def text_do_work(message: Message):
    user_id = message.from_user.id
    job = message.text

    if not can_work(user_id):
        await message.answer("❌ Нет ускорителей!", reply_markup=get_jobs_reply_keyboard())
        return

    earnings = {
        "Курьер": random.randint(10, 30),
        "Таксист": random.randint(20, 50),
        "Программист": random.randint(50, 120)
    }

    earn = earnings.get(job, 10)
    use_accelerator(user_id, 1)
    add_balance(user_id, earn)
    add_xp(user_id, earn // 10)

    await message.answer(
        f"{job}!\n"
        f"+{earn} монет\n"
        f"Использован 1 ускоритель\n"
        f"Баланс: {format_balance(user_id)}\n"
        f"Осталось ускорителей: {user_accelerators.get(user_id, 0)}",
        reply_markup=get_jobs_reply_keyboard()
    )
    save_data()


@dp.message(F.text == "Игры")
async def text_games(message: Message):
    await message.answer(
        "🎮 ВЫБЕРИТЕ ИГРУ:",
        reply_markup=get_games_reply_keyboard()
    )


@dp.message(F.text == "Профиль")
async def text_profile(message: Message):
    user_id = message.from_user.id
    ensure_user(user_id)

    await message.answer(
        "👤 ВАШ ПРОФИЛЬ\n\nВыберите действие:",
        reply_markup=get_profile_reply_keyboard()
    )


@dp.message(F.text == "Бизнес")
async def text_business(message: Message):
    user_id = message.from_user.id
    ensure_user(user_id)

    business = business_data[user_id]
    if business["type"]:
        biz_info = BUSINESS_TYPES[business["type"]]
        text = (
            f"🏢 ВАШ БИЗНЕС:\n\n"
            f"Название: {biz_info['name']}\n"
            f"Прибыль: {business['profit']:,} монет\n"
            f"Прибыль/период: {biz_info['base_profit']:,} монет\n"
            f"Период: {biz_info['profit_period']} сек"
        )
    else:
        text = "🏢 У вас нет бизнеса! Купите в меню."

    await message.answer(text, reply_markup=get_business_reply_keyboard())


@dp.message(F.text == "Рудник")
async def text_mine(message: Message):
    user_id = message.from_user.id
    ensure_user(user_id)

    mine_info = get_mine_info(user_id)
    await message.answer(mine_info, reply_markup=get_mine_reply_keyboard())


@dp.message(F.text == "Банк")
async def text_bank(message: Message):
    user_id = message.from_user.id
    ensure_user(user_id)

    await message.answer(
        f"<b>🏦 БАНК</b>\n\n"
        f"На кармане: {format_balance(user_id)} монет\n"
        f"В банке: {format_bank_balance(user_id)} монет",
        reply_markup=get_bank_reply_keyboard()
    )


@dp.message(F.text == "Рулетка")
async def text_roulette(message: Message):
    await message.answer(
        "🎰 РУЛЕТКА\n\n"
        "Используй: /roulette <сумма>\n"
        "Или: /rsimple <сумма> для простой рулетки",
        reply_markup=get_games_reply_keyboard()
    )


@dp.message(F.text == "Донат")
async def text_donate(message: Message):
    await cmd_donate(message)


@dp.message(F.text == "Админ")
async def text_admin(message: Message):
    user_id = message.from_user.id

    if is_admin(user_id):
        text = "👑 АДМИН ПАНЕЛЬ"
    elif has_rank(user_id, "Admin") or has_rank(user_id, "moderator"):
        text = "🛡️ ПАНЕЛЬ МОДЕРАТОРА"
    else:
        text = "❌ У вас нет админ прав"

    await message.answer(text, reply_markup=get_main_reply_keyboard())


@dp.message(F.text == "Помощь")
async def text_help(message: Message):
    await cmd_help(message)


@dp.message(F.text == "Назад в меню")
async def text_back(message: Message):
    await message.answer(
        "↩️ Главное меню:",
        reply_markup=get_main_reply_keyboard()
    )


@dp.message(F.text.startswith("#"))
async def text_promo(message: Message):
    user_id = message.from_user.id
    promo_code = message.text[1:].upper()

    if promo_code not in promo_codes:
        await message.answer("❌ Неверный промокод")
        return

    promo = promo_codes[promo_code]

    if len(promo["used_by"]) >= promo["max_activations"]:
        await message.answer("❌ Промокод уже использован максимальное количество раз")
        return

    if user_id in promo["used_by"]:
        await message.answer("❌ Вы уже активировали этот промокод")
        return

    promo["used_by"].add(user_id)

    if promo["type"] == 'm':
        add_balance(user_id, promo["amount"])
        reward_text = f"{promo['amount']:,} монет"
    else:
        add_accelerator(user_id, promo["amount"])
        reward_text = f"{promo['amount']} ускорителей"

    remaining = promo["max_activations"] - len(promo["used_by"])

    await message.answer(
        f"✅ Промокод активирован!\n\nВы получили: {reward_text}\n"
        f"Осталось активаций: {remaining}",
        reply_markup=get_main_reply_keyboard()
    )

    save_data()


# ---------------- CALLBACK ОБРАБОТЧИКИ ----------------
@dp.callback_query(F.data == "back_main")
async def callback_back(callback: CallbackQuery):
    await callback.message.edit_text(
        "Выберите действие:",
        reply_markup=get_primary_inline_menu()
    )
    await callback.answer()


@dp.callback_query(F.data == "balance")
async def callback_balance(callback: CallbackQuery):
    user_id = callback.from_user.id
    ensure_user(user_id)

    await callback.message.edit_text(
        f"<b>💰 ВАШ БАЛАНС</b>\n\n"
        f"Наличные: {format_balance(user_id)} монет\n"
        f"Ускорители: {user_accelerators.get(user_id, 0)}\n"
        f"В банке: {format_bank_balance(user_id)} монет",
        reply_markup=get_primary_inline_menu()
    )
    await callback.answer()


@dp.callback_query(F.data == "work")
async def callback_work(callback: CallbackQuery):
    user_id = callback.from_user.id

    if user_accelerators.get(user_id, 0) <= 0:
        await callback.message.edit_text(
            "❌ У вас закончились ускорители!",
            reply_markup=get_primary_inline_menu()
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        "💼 Выберите работу:",
        reply_markup=get_work_inline()
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("job_"))
async def callback_do_work(callback: CallbackQuery):
    user_id = callback.from_user.id
    job_type = callback.data.split("_")[1]

    if user_accelerators.get(user_id, 0) <= 0:
        await callback.answer("❌ Нет ускорителей!", show_alert=True)
        return

    earnings = {
        "courier": random.randint(10, 30),
        "taxi": random.randint(20, 50),
        "programmer": random.randint(50, 120)
    }

    job_names = {
        "courier": "Курьер",
        "taxi": "Таксист",
        "programmer": "Программист"
    }

    earn = earnings.get(job_type, 10)
    use_accelerator(user_id, 1)
    add_balance(user_id, earn)
    add_xp(user_id, earn // 10)

    await callback.message.edit_text(
        f"{job_names.get(job_type, 'Работа')}!\n"
        f"+{earn} монет\n"
        f"Использован 1 ускоритель\n"
        f"Баланс: {format_balance(user_id)}\n"
        f"Осталось ускорителей: {user_accelerators.get(user_id, 0)}",
        reply_markup=get_work_inline()
    )
    await callback.answer()
    save_data()


@dp.callback_query(F.data == "games")
async def callback_games(callback: CallbackQuery):
    await callback.message.edit_text(
        "🎮 Выберите игру:",
        reply_markup=get_games_inline()
    )
    await callback.answer()


@dp.callback_query(F.data == "profile")
async def callback_profile(callback: CallbackQuery):
    user_id = callback.from_user.id
    ensure_user(user_id)

    profile = user_profiles[user_id]
    status = get_premium_status(user_id)

    text = (
        f"<b>👤 ПРОФИЛЬ</b>\n\n"
        f"ID: <code>{user_id}</code>\n"
        f"Статус: {status}\n"
        f"Уровень: {profile['level']}\n"
        f"Опыт: {profile['xp']}/{profile['next_level_xp']}\n\n"
        f"Баланс: {format_balance(user_id)} монет\n"
        f"Ускорители: {user_accelerators.get(user_id, 0)}"
    )

    await callback.message.edit_text(text, reply_markup=get_profile_inline())
    await callback.answer()


@dp.callback_query(F.data == "business")
async def callback_business(callback: CallbackQuery):
    user_id = callback.from_user.id
    ensure_user(user_id)

    business = business_data[user_id]
    if business["type"]:
        biz_info = BUSINESS_TYPES[business["type"]]
        text = (
            f"<b>🏢 ВАШ БИЗНЕС</b>\n\n"
            f"Название: {biz_info['name']}\n"
            f"Накопленная прибыль: {business['profit']:,} монет\n"
            f"Прибыль/период: {biz_info['base_profit']:,} монет\n"
            f"Период: {biz_info['profit_period']} сек"
        )
    else:
        text = "🏢 У вас нет бизнеса! Купите в меню."

    await callback.message.edit_text(text, reply_markup=get_business_inline())
    await callback.answer()


@dp.callback_query(F.data == "mine")
async def callback_mine(callback: CallbackQuery):
    user_id = callback.from_user.id
    ensure_user(user_id)

    mine_info = get_mine_info(user_id)
    await callback.message.edit_text(mine_info, reply_markup=get_mine_inline())
    await callback.answer()


@dp.callback_query(F.data == "bank")
async def callback_bank(callback: CallbackQuery):
    user_id = callback.from_user.id
    ensure_user(user_id)

    await callback.message.edit_text(
        f"<b>🏦 БАНК</b>\n\n"
        f"На кармане: {format_balance(user_id)} монет\n"
        f"В банке: {format_bank_balance(user_id)} монет",
        reply_markup=get_bank_inline()
    )
    await callback.answer()


@dp.callback_query(F.data == "roulette")
async def callback_roulette(callback: CallbackQuery):
    await callback.message.edit_text(
        "🎰 Выберите режим рулетки:",
        reply_markup=get_games_inline()
    )
    await callback.answer()


@dp.callback_query(F.data == "donate")
async def callback_donate(callback: CallbackQuery):
    user_id = callback.from_user.id
    ensure_user(user_id)

    await callback.message.edit_text(
        f"<b>⭐ ДОНАТ МАГАЗИН</b>\n\n"
        f"1 ⭐ = {STAR_TO_COINS:,} коинов\n"
        f"Элит - {ELITE_PRICE} ⭐\n"
        f"Делюкс - {DELUXE_PRICE} ⭐",
        reply_markup=get_donate_inline()
    )
    await callback.answer()


@dp.callback_query(F.data == "admin")
async def callback_admin(callback: CallbackQuery):
    user_id = callback.from_user.id

    if not is_admin(user_id):
        await callback.message.edit_text("❌ У вас нет админ прав")
        await callback.answer()
        return

    await callback.message.edit_text(
        "<b>👑 АДМИН ПАНЕЛЬ</b>",
        reply_markup=get_admin_inline()
    )
    await callback.answer()


@dp.callback_query(F.data == "help")
async def callback_help(callback: CallbackQuery):
    help_text = (
        "<b>ПОЛНАЯ ИНСТРУКЦИЯ</b>\n\n"
        "БАЛАНС И РАБОТА:\n"
        "• Баланс - посмотреть баланс\n"
        "• Работа - заработать монеты\n"
        "• /daily - ежедневный бонус\n\n"
        "ИГРЫ:\n"
        "• Казино - /bet <сумма> (x2)\n"
        "• Монетка - /coin\n"
        "• Рулетка - /roulette <сумма> (x36)"
    )

    await callback.message.edit_text(help_text, reply_markup=get_primary_inline_menu())
    await callback.answer()


@dp.callback_query(F.data.startswith("roulette_num_"))
async def callback_roulette_number(callback: CallbackQuery):
    user_id = callback.from_user.id
    data = callback.data

    if user_id not in roulette_games:
        await callback.message.edit_text("❌ Игра не найдена. Начните заново: /roulette")
        await callback.answer()
        return

    selected_number = int(data.split("_")[2])
    game = roulette_games[user_id]
    bet = game["bet"]
    winning_number = random.randint(0, 36)

    if selected_number == winning_number:
        win_amount = bet * ROULETTE_MULTIPLIER
        if not has_infinite_balance(user_id):
            add_balance(user_id, win_amount)
        add_xp(user_id, win_amount // 50)

        result_text = (
            f"🎉 ПОБЕДА!\n\nВаше число: {selected_number}\n"
            f"Выигрышное число: {winning_number}\n"
            f"Выигрыш: {win_amount:,} монет\nБаланс: {format_balance(user_id)}"
        )
    else:
        result_text = (
            f"💔 ПРОИГРЫШ\n\nВаше число: {selected_number}\n"
            f"Выигрышное число: {winning_number}\n"
            f"Ставка {bet:,} монет сгорела\nБаланс: {format_balance(user_id)}"
        )

    del roulette_games[user_id]
    await callback.message.edit_text(result_text)
    await callback.answer()
    save_data()


@dp.callback_query(F.data == "roulette_cancel")
async def callback_roulette_cancel(callback: CallbackQuery):
    user_id = callback.from_user.id

    if user_id in roulette_games:
        bet = roulette_games[user_id]["bet"]
        if not has_infinite_balance(user_id):
            add_balance(user_id, bet)
        del roulette_games[user_id]

    await callback.message.edit_text("❌ Игра отменена. Ставка возвращена.")
    await callback.answer()


# ---------------- ФОНОВЫЕ ЗАДАЧИ ----------------
async def background_tasks():
    while True:
        try:
            now = datetime.now()

            # Обновление рудника
            for user_id, mine in mine_data.items():
                if mine.get("auto_collect", False):
                    mine["resources"] = mine.get("resources", 0) + 3

            # Обновление бизнеса
            for user_id, business in business_data.items():
                if business.get("type") and business.get("active"):
                    biz_info = BUSINESS_TYPES[business["type"]]

                    if business.get("last_collect"):
                        last = business["last_collect"]
                        if isinstance(last, str):
                            last = datetime.fromisoformat(last)

                        elapsed = (now - last).total_seconds()
                        if elapsed >= biz_info["profit_period"]:
                            cycles = int(elapsed // biz_info["profit_period"])
                            profit_to_add = biz_info["base_profit"] * cycles
                            business["profit"] = business.get("profit", 0) + profit_to_add
                            business["last_collect"] = now
                    else:
                        business["last_collect"] = now

            # Автосохранение раз в 5 минут
            if random.random() < 0.0167:
                save_data()

            await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Ошибка в фоновых задачах: {e}")
            await asyncio.sleep(1)


# ---------------- ЗАПУСК БОТА ----------------
async def main():
    load_data()

    asyncio.create_task(background_tasks())

    logger.info("✅ БОТ ЗАПУЩЕН! ВСЕ INLINE КНОПКИ СИНИЕ (style=primary)")
    print("✅ БОТ ЗАПУЩЕН! ВСЕ INLINE КНОПКИ СИНИЕ (style=primary)")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())