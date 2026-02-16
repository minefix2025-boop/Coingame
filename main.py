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
    ReplyKeyboardMarkup, KeyboardButton, PreCheckoutQuery, LabeledPrice
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
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
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("❌ ТОКЕН НЕ НАЙДЕН! Добавьте BOT_TOKEN в переменные окружения")

ADMINS = [8136808901, 6479090914, 7716319249]
YOUR_USERNAME = "@RobloxMinePump"

START_BALANCE = 100
DAILY_BALANCE = 500
DAILY_BALANCE_ELITE = 2500
DAILY_BALANCE_DELUXE = 5000
DAILY_ACCELERATORS = 30
DAILY_ACCELERATORS_ELITE = 60
DAILY_ACCELERATORS_DELUXE = 100
START_ACCELERATORS = 10
DAILY_HOURS = 12

STAR_TO_COINS = 10000
ELITE_PRICE = 50
DELUXE_PRICE = 99

DATA_FILE = "bot_data.json"
ROULETTE_MULTIPLIER = 36

MINE_LEVELS = {
    0: {"name": "Золотая шахта", "resource": "Золото", "price_per_unit": 2, "upgrade_cost": 1000000},
    1: {"name": "Рубиновая шахта", "resource": "Рубин", "price_per_unit": 10, "upgrade_cost": 5000000},
    2: {"name": "Алмазная шахта", "resource": "Алмаз", "price_per_unit": 100, "upgrade_cost": 20000000}
}

BUSINESS_TYPES = {
    "shaurma": {"name": "Шаурма", "cost": 100, "base_profit": 10, "profit_period": 30},
    "cafe": {"name": "Кафе", "cost": 1000, "base_profit": 100, "profit_period": 15},
    "space": {"name": "Космическое агентство", "cost": 1000000, "base_profit": 10000, "profit_period": 5}
}

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
        return "∞ (бесконечный)"
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
    builder = ReplyKeyboardBuilder()
    buttons = [
        ["Баланс", "Работа", "Игры"],
        ["Профиль", "Бизнес", "Рудник"],
        ["Банк", "Рулетка", "Донат"],
        ["Админ", "Помощь", "Активация"]
    ]
    for row in buttons:
        builder.row(*[KeyboardButton(text=btn) for btn in row])
    return builder.as_markup(resize_keyboard=True)


def get_jobs_reply_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    buttons = [
        ["Курьер", "Таксист", "Программист"],
        ["Назад в меню"]
    ]
    for row in buttons:
        builder.row(*[KeyboardButton(text=btn) for btn in row])
    return builder.as_markup(resize_keyboard=True)


def get_games_reply_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    buttons = [
        ["Казино", "Монетка", "Мини-игра"],
        ["Назад в меню"]
    ]
    for row in buttons:
        builder.row(*[KeyboardButton(text=btn) for btn in row])
    return builder.as_markup(resize_keyboard=True)


def get_mine_reply_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    buttons = [
        ["Собрать ресурсы", "Улучшить рудник"],
        ["Авто-сбор", "Назад в меню"]
    ]
    for row in buttons:
        builder.row(*[KeyboardButton(text=btn) for btn in row])
    return builder.as_markup(resize_keyboard=True)


def get_business_reply_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    buttons = [
        ["Купить бизнес", "Собрать прибыль"],
        ["Продать бизнес", "Назад в меню"]
    ]
    for row in buttons:
        builder.row(*[KeyboardButton(text=btn) for btn in row])
    return builder.as_markup(resize_keyboard=True)


def get_bank_reply_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    buttons = [
        ["Внести", "Снять", "Баланс"],
        ["Назад в меню"]
    ]
    for row in buttons:
        builder.row(*[KeyboardButton(text=btn) for btn in row])
    return builder.as_markup(resize_keyboard=True)


def get_donate_reply_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    buttons = [
        [f"Купить Элит ({ELITE_PRICE} ⭐)"],
        [f"Купить Делюкс ({DELUXE_PRICE} ⭐)"],
        ["Купить коины"],
        ["Назад в меню"]
    ]
    for row in buttons:
        builder.row(*[KeyboardButton(text=btn) for btn in row])
    return builder.as_markup(resize_keyboard=True)


def get_profile_reply_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    buttons = [
        ["Статистика", "Имущество"],
        ["Назад в меню"]
    ]
    for row in buttons:
        builder.row(*[KeyboardButton(text=btn) for btn in row])
    return builder.as_markup(resize_keyboard=True)


def get_roulette_inline() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for i in range(0, 37):
        builder.add(InlineKeyboardButton(text=str(i), callback_data=f"roulette_num_{i}"))
    builder.adjust(6)
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="roulette_cancel"))
    return builder.as_markup()


def get_simple_roulette_inline() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="Красный", callback_data="simple_red"),
        InlineKeyboardButton(text="Черный", callback_data="simple_black")
    )
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="Отмена", callback_data="simple_cancel"))
    return builder.as_markup()


def get_admin_inline() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    admin_buttons = [
        ("Выдать монеты", "admin_money"),
        ("Выдать ранг", "admin_rank"),
        ("Беск. баланс", "admin_inf"),
        ("Снять беск.", "admin_removeinf"),
        ("Промокод", "admin_promo"),
        ("Сложность", "admin_chance")
    ]
    for text, callback in admin_buttons:
        builder.add(InlineKeyboardButton(text=text, callback_data=callback))
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="Назад", callback_data="back_main"))
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


# ---------------- КОМАНДА /id ----------------
@dp.message(Command("id"))
async def cmd_id(message: Message):
    if message.reply_to_message:
        user = message.reply_to_message.from_user
        await message.reply(
            f"👤 <b>ИНФОРМАЦИЯ О ПОЛЬЗОВАТЕЛЕ</b>\n\n"
            f"Имя: {user.full_name}\n"
            f"Username: @{user.username if user.username else 'нет'}\n"
            f"Telegram ID: <code>{user.id}</code>\n"
            f"Язык: {user.language_code if user.language_code else 'не указан'}"
        )
    else:
        user = message.from_user
        await message.reply(
            f"👤 <b>ТВОЙ ID</b>\n\n"
            f"Имя: {user.full_name}\n"
            f"Username: @{user.username if user.username else 'нет'}\n"
            f"Telegram ID: <code>{user.id}</code>\n"
            f"Язык: {user.language_code if user.language_code else 'не указан'}"
        )


# ---------------- КОМАНДА /mini ----------------
@dp.message(Command("mini"))
async def cmd_mini(message: Message):
    user_id = message.from_user.id
    ensure_user(user_id)

    args = message.text.split()
    if len(args) != 2 or not args[1].isdigit():
        await message.answer(
            "💣 <b>МИНИ-ИГРА: САПЁР</b>\n\n"
            "Правила:\n"
            "• Поле 5×5 (25 клеток)\n"
            "• По умолчанию 5 мин\n"
            "• Каждая открытая клетка ×1.3 к выигрышу\n"
            "• Нашел мину - проигрыш\n\n"
            "Используй: /mini <сумма>\n"
            "Пример: /mini 100",
            reply_markup=get_games_reply_keyboard()
        )
        return

    bet = int(args[1])
    if bet <= 0:
        await message.answer("❌ Ставка должна быть больше 0.", reply_markup=get_games_reply_keyboard())
        return

    if not can_spend(user_id, bet):
        await message.answer("❌ Недостаточно монет для ставки.", reply_markup=get_games_reply_keyboard())
        return

    infinite_user = has_infinite_balance(user_id)
    if not infinite_user:
        spend_balance(user_id, bet)

    if user_id in user_mini_settings and "mines" in user_mini_settings[user_id]:
        mines_count = user_mini_settings[user_id]["mines"]
    else:
        mines_count = MINI_BOMBS

    game_id = f"{user_id}_{int(time.time())}"
    bombs = generate_mini_board(mines_count)
    opened = set()

    mini_games[game_id] = {
        "user_id": user_id,
        "bet": bet,
        "bombs": bombs,
        "opened": opened,
        "started_at": datetime.now().isoformat(),
        "hits": 0,
        "multiplier": 1.0,
        "lost": False,
        "infinite_user": infinite_user
    }

    keyboard = create_mini_keyboard(opened, bombs, game_id)

    await message.answer(
        f"<b>💣 МИНИ-ИГРА: САПЁР</b>\n\n"
        f"💰 Ставка: {bet:,} монет\n"
        f"💣 Мин на поле: {mines_count}\n"
        f"📊 Открыто клеток: 0 | Множитель: 1.0x\n"
        f"🏆 Текущий выигрыш: {bet} монет\n\n"
        f"❌ - закрытая клетка\n"
        f"💣 - мина (проигрыш)\n"
        f"⬜ - пустая клетка (+1.3x)",
        reply_markup=keyboard
    )


# ---------------- КОМАНДА /start ----------------
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
        f"Короткие команды:\n"
        f"• б - баланс\n"
        f"• я - профиль\n"
        f"• /id - показать ID\n\n"
        f"Используйте меню для навигации:",
        reply_markup=get_main_reply_keyboard()
    )


# ---------------- КОМАНДА /help ----------------
@dp.message(Command("help"))
async def cmd_help(message: Message):
    help_text = (
        "<b>📚 ПОЛНАЯ ИНСТРУКЦИЯ</b>\n\n"
        "<b>💰 БАЛАНС И РАБОТА:</b>\n"
        "• Баланс - посмотреть баланс и ускорители\n"
        "• Работа - заработать монеты (тратит ускорители)\n"
        "• /daily - ежедневный бонус\n\n"
        "<b>👤 ПРОФИЛЬ:</b>\n"
        "• Статистика - уровень, опыт, статус\n"
        "• Имущество - рудник, бизнес, банк\n"
        "• /id - показать ID\n\n"
        "<b>🎮 ИГРЫ:</b>\n"
        "• Казино - /bet <сумма> (x2)\n"
        "• Монетка - /coin\n"
        "• Мини-игра - /mini <сумма>\n"
        "• Рулетка - /roulette <сумма> (x36)\n"
        "• Простая рулетка - /rsimple <сумма> (x2)\n\n"
        "<b>⛏️ РУДНИК:</b>\n"
        "• Автоматическая добыча ресурсов\n"
        "• Улучшение для ценных ресурсов\n\n"
        "<b>🏢 БИЗНЕС:</b>\n"
        "• Пассивный доход\n\n"
        "<b>🏦 БАНК:</b>\n"
        "• /bank <сумма> - положить\n"
        "• /bank w <сумма> - снять\n\n"
        "<b>⭐ ДОНАТ:</b>\n"
        f"• 1 ⭐ = {STAR_TO_COINS:,} коинов\n"
        f"• Элит - {ELITE_PRICE} ⭐\n"
        f"• Делюкс - {DELUXE_PRICE} ⭐\n"
        "• /buy_coins <звезды> - купить коины\n"
        "• /buy_elite - купить Элит\n"
        "• /buy_deluxe - купить Делюкс\n"
        "• /donate_history - история покупок\n"
        "• /refund <код> - возврат звёзд\n\n"
        "<b>🎟️ ПРОМОКОДЫ:</b>\n"
        "• Введите #промокод для активации\n\n"
        "<b>⚡ КОРОТКИЕ КОМАНДЫ:</b>\n"
        "• б - баланс\n"
        "• я - профиль\n\n"
        "<b>👑 АДМИН КОМАНДЫ:</b>\n"
        "• /money - выдать монеты\n"
        "• /setmoney - установить баланс\n"
        "• /rank - выдать ранг\n"
        "• /unrank - снять ранг\n"
        "• /inf - бесконечный баланс\n"
        "• /removeinf - снять бесконечность\n"
        "• /createpromo - создать промокод\n"
        "• /chance - сложность мини-игры"
    )
    await message.answer(help_text, reply_markup=get_main_reply_keyboard())


# ---------------- КОМАНДА /daily ----------------
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
        f"🎁 <b>ЕЖЕДНЕВНЫЙ БОНУС!</b>\n\n"
        f"Монеты: +{daily_bonus:,}\n"
        f"Ускорители: +{daily_acc}\n"
        f"Баланс: {format_balance(user_id)}",
        reply_markup=get_main_reply_keyboard()
    )
    save_data()


# ---------------- КОМАНДА /bet ----------------
@dp.message(Command("bet"))
async def cmd_bet(message: Message):
    user_id = message.from_user.id
    ensure_user(user_id)

    args = message.text.split()
    if len(args) != 2 or not args[1].isdigit():
        await message.answer(
            "❌ Используй: /bet <сумма>\nПример: /bet 100",
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


# ---------------- КОМАНДА /coin ----------------
@dp.message(Command("coin"))
async def cmd_coin(message: Message):
    user_id = message.from_user.id
    ensure_user(user_id)
    result = random.choice(['Орёл', 'Решка'])
    await message.answer(
        f"🪙 {result}\nБаланс: {format_balance(user_id)}",
        reply_markup=get_games_reply_keyboard()
    )


# ---------------- КОМАНДА /roulette ----------------
@dp.message(Command("roulette"))
async def cmd_roulette(message: Message):
    user_id = message.from_user.id
    ensure_user(user_id)

    args = message.text.split()
    if len(args) != 2 or not args[1].isdigit():
        await message.answer(
            "❌ Используй: /roulette <сумма>\nПример: /roulette 1000",
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
        f"<b>РУЛЕТКА</b>\n\nСтавка: {bet:,} монет\nВыберите число от 0 до 36:",
        reply_markup=get_roulette_inline()
    )


# ---------------- КОМАНДА /rsimple ----------------
@dp.message(Command("rsimple"))
async def cmd_rsimple(message: Message):
    user_id = message.from_user.id
    ensure_user(user_id)

    args = message.text.split()
    if len(args) != 2 or not args[1].isdigit():
        await message.answer(
            "❌ Используй: /rsimple <сумма>\nПример: /rsimple 100",
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

    roulette_games[f"simple_{user_id}"] = {"bet": bet}

    await message.answer(
        f"<b>ПРОСТАЯ РУЛЕТКА</b>\n\nСтавка: {bet:,} монет\nВыберите цвет:",
        reply_markup=get_simple_roulette_inline()
    )


# ---------------- КОМАНДА /bank ----------------
@dp.message(Command("bank"))
async def cmd_bank(message: Message):
    user_id = message.from_user.id
    ensure_user(user_id)

    args = message.text.split()
    if len(args) == 1:
        await message.answer(
            f"<b>БАНК</b>\n\n"
            f"На кармане: {format_balance(user_id)} монет\n"
            f"В банке: {format_bank_balance(user_id)} монет\n\n"
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


# ---------------- КОМАНДА /donate ----------------
@dp.message(Command("donate"))
async def cmd_donate(message: Message):
    user_id = message.from_user.id
    ensure_user(user_id)

    await message.answer(
        f"<b>ДОНАТ МАГАЗИН</b>\n\n"
        f"1 ⭐ = {STAR_TO_COINS:,} коинов\n"
        f"Элит - {ELITE_PRICE} ⭐\n"
        f"Делюкс - {DELUXE_PRICE} ⭐",
        reply_markup=get_donate_reply_keyboard()
    )


# ---------------- КОМАНДА /buy_coins ----------------
@dp.message(Command("buy_coins"))
async def cmd_buy_coins(message: Message):
    user_id = message.from_user.id

    args = message.text.split()
    if len(args) != 2 or not args[1].isdigit():
        await message.answer("❌ Используй: /buy_coins <количество_звезд>")
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
        "type": "coins",
        "timestamp": time.time()
    }

    await message.answer_invoice(
        title=f"{coins:,} коинов",
        description=f"Покупка {coins:,} игровых коинов за {stars} ⭐",
        payload=invoice_id,
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label=f"{stars} ⭐", amount=stars)]
    )


# ---------------- КОМАНДА /buy_elite ----------------
@dp.message(Command("buy_elite"))
async def cmd_buy_elite(message: Message):
    user_id = message.from_user.id

    invoice_id = f"elite_{user_id}_{int(time.time())}"

    pending_invoices[invoice_id] = {
        "user_id": user_id,
        "stars": ELITE_PRICE,
        "type": "elite",
        "timestamp": time.time()
    }

    await message.answer_invoice(
        title="Статус Элит",
        description="Элит статус НАВСЕГДА!",
        payload=invoice_id,
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label="Элит статус", amount=ELITE_PRICE)]
    )


# ---------------- КОМАНДА /buy_deluxe ----------------
@dp.message(Command("buy_deluxe"))
async def cmd_buy_deluxe(message: Message):
    user_id = message.from_user.id

    invoice_id = f"deluxe_{user_id}_{int(time.time())}"

    pending_invoices[invoice_id] = {
        "user_id": user_id,
        "stars": DELUXE_PRICE,
        "type": "deluxe",
        "timestamp": time.time()
    }

    await message.answer_invoice(
        title="Статус Делюкс",
        description="Делюкс статус НАВСЕГДА!",
        payload=invoice_id,
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label="Делюкс статус", amount=DELUXE_PRICE)]
    )


# ---------------- КОМАНДА /donate_history ----------------
@dp.message(Command("donate_history"))
async def cmd_donate_history(message: Message):
    user_id = message.from_user.id
    ensure_user(user_id)

    if not user_donations[user_id]["transactions"]:
        await message.answer("📭 У вас пока нет донат-транзакций.")
        return

    text = "<b>📊 ИСТОРИЯ ПОКУПОК:</b>\n\n"

    for tx in reversed(user_donations[user_id]["transactions"][-10:]):
        status = "✅ ВОЗВРАЩЕН" if tx.get("refunded", False) else "💎 КУПЛЕНО"

        if tx["type"] == "coins":
            text += f"💰 <b>Коины</b>\n"
            text += f"   ⭐ {tx['stars']} → {tx['coins']:,} коинов\n"
        elif tx["type"] == "elite":
            text += f"✨ <b>Статус Элит</b>\n"
            text += f"   ⭐ {tx['stars']}\n"
        elif tx["type"] == "deluxe":
            text += f"💎 <b>Статус Делюкс</b>\n"
            text += f"   ⭐ {tx['stars']}\n"

        text += f"   ID: <code>{tx['id']}</code>\n"
        text += f"   Дата: {tx['timestamp'][:10]} {status}\n\n"

    text += "🔹 ДЛЯ ВОЗВРАТА ЗВЁЗД ИСПОЛЬЗУЙ:\n"
    text += "<code>/refund код_транзакции</code>"

    await message.answer(text, reply_markup=get_main_reply_keyboard())


# ---------------- КОМАНДА /refund (ИСПРАВЛЕННАЯ) ----------------
@dp.message(Command("refund"))
async def cmd_refund(message: Message):
    user_id = message.from_user.id
    ensure_user(user_id)

    args = message.text.split()
    if len(args) != 2:
        await message.answer(
            "💳 <b>ВОЗВРАТ ЗВЁЗД</b>\n\n"
            "Используй: /refund <код_транзакции>\n"
            "Код транзакции можно найти в /donate_history\n\n"
            "Пример: /refund 12345678901234567890\n\n"
            "⚠️ ВНИМАНИЕ:\n"
            "• Звёзды вернутся на ваш счёт в Telegram\n"
            "• Коины/статус будут списаны\n"
            "• Возврат возможен в течение 7 дней",
            reply_markup=get_main_reply_keyboard()
        )
        return

    transaction_id = args[1]
    found = False

    for tx in user_donations[user_id]["transactions"]:
        if tx["id"] == transaction_id and not tx.get("refunded", False):
            found = True

            if tx["type"] == "coins":
                coins_returned = tx["coins"]

                if can_spend(user_id, coins_returned):
                    spend_balance(user_id, coins_returned)
                    tx["refunded"] = True
                    tx["refunded_at"] = datetime.now().isoformat()
                    user_donations[user_id]["total_coins"] -= coins_returned
                    user_donations[user_id]["total_stars"] -= tx["stars"]

                    try:
                        # Возвращаем звёзды через Telegram
                        await bot.refund_star_payment(
                            user_id=user_id,
                            telegram_payment_charge_id=transaction_id
                        )
                        refund_message = f"✅ Звёзды ({tx['stars']} ⭐) возвращены на ваш счёт!"
                    except Exception as e:
                        logger.error(f"Ошибка возврата звёзд: {e}")
                        refund_message = f"⚠️ Ошибка возврата звёзд. Обратитесь к администратору с кодом: {transaction_id}"

                    await message.answer(
                        f"✅ <b>ВОЗВРАТ ОФОРМЛЕН!</b>\n\n"
                        f"Транзакция: <code>{transaction_id}</code>\n"
                        f"Возвращено звёзд: {tx['stars']}\n"
                        f"Списано коинов: {coins_returned:,}\n"
                        f"Новый баланс: {format_balance(user_id)}\n\n"
                        f"{refund_message}",
                        reply_markup=get_main_reply_keyboard()
                    )
                    save_data()
                else:
                    await message.answer(
                        "❌ <b>НЕДОСТАТОЧНО КОИНОВ ДЛЯ ВОЗВРАТА!</b>\n\n"
                        f"Нужно: {coins_returned:,} коинов\n"
                        f"У вас: {format_balance(user_id)}\n\n"
                        "Потратьте меньше коинов и попробуйте снова.",
                        reply_markup=get_main_reply_keyboard()
                    )

            elif tx["type"] in ["elite", "deluxe"]:
                if user_premium[user_id]["type"] == tx["type"]:
                    user_premium[user_id]["type"] = None
                    tx["refunded"] = True
                    tx["refunded_at"] = datetime.now().isoformat()
                    user_donations[user_id]["total_stars"] -= tx["stars"]

                    try:
                        await bot.refund_star_payment(
                            user_id=user_id,
                            telegram_payment_charge_id=transaction_id
                        )
                        refund_message = f"✅ Звёзды ({tx['stars']} ⭐) возвращены на ваш счёт!"
                    except Exception as e:
                        logger.error(f"Ошибка возврата звёзд: {e}")
                        refund_message = f"⚠️ Ошибка возврата звёзд. Обратитесь к администратору с кодом: {transaction_id}"

                    status_name = "Элит" if tx["type"] == "elite" else "Делюкс"
                    await message.answer(
                        f"✅ <b>ВОЗВРАТ ОФОРМЛЕН!</b>\n\n"
                        f"Транзакция: <code>{transaction_id}</code>\n"
                        f"Возвращено звёзд: {tx['stars']}\n"
                        f"Статус '{status_name}' снят\n\n"
                        f"{refund_message}",
                        reply_markup=get_main_reply_keyboard()
                    )
                    save_data()
                else:
                    await message.answer(
                        "❌ <b>НЕВОЗМОЖНО ВЕРНУТЬ СТАТУС!</b>\n\n"
                        "Статус был изменен или уже возвращен.",
                        reply_markup=get_main_reply_keyboard()
                    )
            break

    if not found:
        await message.answer(
            "❌ <b>ТРАНЗАКЦИЯ НЕ НАЙДЕНА ИЛИ УЖЕ ВОЗВРАЩЕНА!</b>\n\n"
            "Проверьте код транзакции в /donate_history",
            reply_markup=get_main_reply_keyboard()
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

        user_donations[user_id]["total_stars"] += stars
        user_donations[user_id]["total_coins"] += coins
        user_donations[user_id]["transactions"].append({
            "id": payment.telegram_payment_charge_id,
            "invoice_id": invoice_id,
            "type": "coins",
            "stars": stars,
            "coins": coins,
            "timestamp": datetime.now().isoformat(),
            "refunded": False
        })

        await message.answer(
            f"✅ <b>ОПЛАТА УСПЕШНА!</b>\n\n"
            f"ID: <code>{payment.telegram_payment_charge_id}</code>\n"
            f"Звезд: {stars}\n"
            f"Получено коинов: {coins:,}\n"
            f"Баланс: {format_balance(user_id)}\n\n"
            f"Сохраните ID транзакции для возврата звёзд!",
            reply_markup=get_main_reply_keyboard()
        )

    elif invoice_data["type"] == "elite":
        user_premium[user_id] = {
            "type": "elite",
            "expires": None,
            "purchased_at": datetime.now().isoformat()
        }

        user_donations[user_id]["total_stars"] += stars
        user_donations[user_id]["transactions"].append({
            "id": payment.telegram_payment_charge_id,
            "invoice_id": invoice_id,
            "type": "elite",
            "stars": stars,
            "timestamp": datetime.now().isoformat(),
            "refunded": False
        })

        await message.answer(
            f"✨ <b>ПОЗДРАВЛЯЕМ!</b>\n\n"
            f"ID: <code>{payment.telegram_payment_charge_id}</code>\n"
            f"Вам выдан статус ЭЛИТ навсегда!\n\n"
            f"Сохраните ID транзакции для возврата звёзд!",
            reply_markup=get_main_reply_keyboard()
        )

    elif invoice_data["type"] == "deluxe":
        user_premium[user_id] = {
            "type": "deluxe",
            "expires": None,
            "purchased_at": datetime.now().isoformat()
        }

        user_donations[user_id]["total_stars"] += stars
        user_donations[user_id]["transactions"].append({
            "id": payment.telegram_payment_charge_id,
            "invoice_id": invoice_id,
            "type": "deluxe",
            "stars": stars,
            "timestamp": datetime.now().isoformat(),
            "refunded": False
        })

        await message.answer(
            f"💎 <b>ПОЗДРАВЛЯЕМ!</b>\n\n"
            f"ID: <code>{payment.telegram_payment_charge_id}</code>\n"
            f"Вам выдан статус ДЕЛЮКС навсегда!\n\n"
            f"Сохраните ID транзакции для возврата звёзд!",
            reply_markup=get_main_reply_keyboard()
        )

    del pending_invoices[invoice_id]
    save_data()


# ---------------- КОМАНДА /createpromo ----------------
@dp.message(Command("createpromo"))
async def cmd_createpromo(message: Message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        await message.answer("❌ Только админы могут создавать промокоды")
        return

    args = message.text.split()
    if len(args) < 4:
        await message.answer(
            "🎟️ <b>СОЗДАНИЕ ПРОМОКОДА</b>\n\n"
            "/createpromo <m/u> <сумма> <кол-во> <код>\n\n"
            "m - монеты\n"
            "u - ускорители\n\n"
            "Пример: /createpromo m 1000 10 GIFT2024"
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
        f"✅ <b>Промокод создан!</b>\n\n"
        f"Код: <code>{promo_code}</code>\n"
        f"Тип: {'💰 Монеты' if promo_type == 'm' else '⚡ Ускорители'}\n"
        f"Сумма: {amount:,}\n"
        f"Активаций: {activations}",
        reply_markup=get_main_reply_keyboard()
    )

    save_data()


# ---------------- КОМАНДА /money ----------------
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
        return

    await message.answer("❌ Используй: /money <сумма>")


# ---------------- КОМАНДА /setmoney ----------------
@dp.message(Command("setmoney"))
async def cmd_setmoney(message: Message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        await message.answer("❌ Только админы могут использовать эту команду")
        return

    args = message.text.split()
    if message.reply_to_message and len(args) == 2 and args[1].isdigit():
        target_id = message.reply_to_message.from_user.id
        amount = int(args[1])
        ensure_user(target_id)
        user_balances[target_id] = amount
        await message.answer(f"✅ Баланс пользователя установлен на {amount:,}")
        save_data()
        return

    await message.answer("❌ Ответь на сообщение: /setmoney <сумма>")


# ---------------- КОМАНДА /inf ----------------
@dp.message(Command("inf"))
async def cmd_inf(message: Message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        await message.answer("❌ Только админы могут использовать эту команду")
        return

    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
        set_infinite_balance(target_id)
        await message.answer("∞ Пользователю выдан бесконечный баланс")
        save_data()
        return

    await message.answer("❌ Ответь на сообщение: /inf")


# ---------------- КОМАНДА /removeinf ----------------
@dp.message(Command("removeinf"))
async def cmd_removeinf(message: Message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        await message.answer("❌ Только админы могут использовать эту команду")
        return

    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
        remove_infinite_balance(target_id)
        await message.answer("∞ Бесконечный баланс снят")
        save_data()
        return

    await message.answer("❌ Ответь на сообщение: /removeinf")


# ---------------- КОМАНДА /rank ----------------
@dp.message(Command("rank"))
async def cmd_rank(message: Message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        await message.answer("❌ Только админы могут выдавать ранги")
        return

    args = message.text.split()
    if message.reply_to_message and len(args) >= 2:
        rank_type = args[1].lower()
        if rank_type not in ["admin", "moderator", "elite", "deluxe"]:
            await message.answer("Доступные ранги: admin, moderator, elite, deluxe")
            return

        target_id = message.reply_to_message.from_user.id

        if rank_type in ["elite", "deluxe"]:
            user_premium[target_id] = {"type": rank_type, "expires": None,
                                       "purchased_at": datetime.now().isoformat()}
            await message.answer(f"👑 Пользователь теперь {rank_type.capitalize()}!")
        else:
            ranks[target_id] = rank_type.capitalize()
            await message.answer(f"👑 Пользователь теперь {rank_type.capitalize()}!")

        save_data()
        return

    await message.answer("❌ Ответь на сообщение: /rank <admin/moderator/elite/deluxe>")


# ---------------- КОМАНДА /unrank ----------------
@dp.message(Command("unrank"))
async def cmd_unrank(message: Message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        await message.answer("❌ Только админы могут снимать ранги")
        return

    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
        if target_id in ranks:
            old_rank = ranks.pop(target_id)
            await message.answer(f"👑 Ранг '{old_rank}' снят")
            save_data()
        elif user_premium.get(target_id, {}).get("type"):
            old_type = user_premium[target_id]["type"]
            user_premium[target_id]["type"] = None
            await message.answer(f"👑 Статус '{old_type}' снят")
            save_data()
        else:
            await message.answer("ℹ️ Пользователь не имеет ранга/статуса")
        return

    await message.answer("❌ Ответь на сообщение: /unrank")


# ---------------- КОМАНДА /chance ----------------
@dp.message(Command("chance"))
async def cmd_chance(message: Message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        await message.answer("❌ Только админы могут использовать /chance")
        return

    args = message.text.split()
    if message.reply_to_message and len(args) == 2 and args[1].isdigit():
        target_id = message.reply_to_message.from_user.id
        chance = int(args[1])

        if chance < 0 or chance > 100:
            await message.answer("❌ Число должно быть от 0 до 100!")
            return

        if chance == 0:
            mines = 8
            level = "ОЧЕНЬ СЛОЖНО"
        elif chance == 100:
            mines = 0
            level = "ЛЕГКО (нет мин)"
        elif chance >= 75:
            mines = 2
            level = "ЛЕГКО"
        elif chance >= 50:
            mines = 4
            level = "СРЕДНЕ"
        elif chance >= 25:
            mines = 6
            level = "СЛОЖНО"
        else:
            mines = 7
            level = "ОЧЕНЬ СЛОЖНО"

        user_mini_settings[target_id] = {
            "chance": chance,
            "mines": mines
        }

        await message.answer(
            f"✅ <b>НАСТРОЙКИ МИНИ-ИГРЫ</b>\n\n"
            f"• Сложность: {level}\n"
            f"• Значение: {chance}%\n"
            f"• Мин на поле: {mines}",
            reply_markup=get_main_reply_keyboard()
        )

        save_data()
        return

    await message.answer("❌ Ответь на сообщение: /chance <0-100>")


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
    await message.answer("💼 ВЫБЕРИТЕ РАБОТУ:", reply_markup=get_jobs_reply_keyboard())


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
    await message.answer("🎮 ВЫБЕРИТЕ ИГРУ:", reply_markup=get_games_reply_keyboard())


@dp.message(F.text == "Казино")
async def text_casino(message: Message):
    await message.answer(
        "🎰 КАЗИНО\n\nПравила:\n• 50% шанс на выигрыш\n• Выигрыш = ставка × 2\n\nКоманда: /bet <сумма>",
        reply_markup=get_games_reply_keyboard()
    )


@dp.message(F.text == "Монетка")
async def text_coin(message: Message):
    await cmd_coin(message)


@dp.message(F.text == "Мини-игра")
async def text_mini(message: Message):
    await message.answer(
        "💣 МИНИ-ИГРА: САПЁР\n\nПравила:\n• Поле 5×5\n• Каждая пустая клетка ×1.3 к выигрышу\n\nИспользуй: /mini <сумма>",
        reply_markup=get_games_reply_keyboard()
    )


@dp.message(F.text == "Профиль")
async def text_profile(message: Message):
    await message.answer("👤 ВАШ ПРОФИЛЬ\n\nВыберите действие:", reply_markup=get_profile_reply_keyboard())


@dp.message(F.text == "Статистика")
async def text_stats(message: Message):
    user_id = message.from_user.id
    ensure_user(user_id)
    profile = user_profiles[user_id]
    status = get_user_status(user_id)

    text = (
        f"<b>👤 ПРОФИЛЬ</b>\n\n"
        f"ID: <code>{user_id}</code>\n"
        f"Статус: {status}\n"
        f"Уровень: {profile['level']}\n"
        f"Опыт: {profile['xp']:,}/{profile['next_level_xp']:,}\n\n"
        f"Баланс: {format_balance(user_id)} монет\n"
        f"Ускорители: {user_accelerators.get(user_id, 0)}"
    )

    await message.answer(text, reply_markup=get_profile_reply_keyboard())


@dp.message(F.text == "Имущество")
async def text_assets(message: Message):
    user_id = message.from_user.id
    ensure_user(user_id)

    text = "🏠 ВАШЕ ИМУЩЕСТВО:\n\n"

    if user_id in mine_data:
        mine = mine_data[user_id]
        level_info = MINE_LEVELS[mine["level"]]
        mine_value = mine["resources"] * level_info["price_per_unit"]
        text += (
            f"⛏ РУДНИК:\n"
            f"   {level_info['name']}\n"
            f"   Ресурсы: {mine['resources']:,}\n"
            f"   Стоимость: {mine_value:,} монет\n\n"
        )

    if user_id in business_data and business_data[user_id]["type"]:
        business = business_data[user_id]
        biz_info = BUSINESS_TYPES[business["type"]]
        text += (
            f"🏢 БИЗНЕС:\n"
            f"   {biz_info['name']}\n"
            f"   Прибыль: {business['profit']:,} монет\n\n"
        )

    text += f"🏦 БАНК: {format_bank_balance(user_id)} монет"
    await message.answer(text, reply_markup=get_profile_reply_keyboard())


@dp.message(F.text == "Бизнес")
async def text_business(message: Message):
    user_id = message.from_user.id
    ensure_user(user_id)

    business = business_data[user_id]
    if business["type"]:
        biz_info = BUSINESS_TYPES[business["type"]]
        text = (
            f"<b>🏢 ВАШ БИЗНЕС</b>\n\n"
            f"Название: {biz_info['name']}\n"
            f"Прибыль: {business['profit']:,} монет\n"
            f"Прибыль/период: {biz_info['base_profit']:,} монет\n"
            f"Период: {biz_info['profit_period']} сек"
        )
    else:
        text = "🏢 У вас нет бизнеса! Купите в меню."

    await message.answer(text, reply_markup=get_business_reply_keyboard())


@dp.message(F.text == "Купить бизнес")
async def text_buy_business(message: Message):
    biz_list = "🏢 ДОСТУПНЫЕ БИЗНЕСЫ:\n\n"
    for biz_id, biz_info in BUSINESS_TYPES.items():
        biz_list += (
            f"• {biz_info['name']}\n"
            f"  Цена: {biz_info['cost']:,} монет\n"
            f"  Прибыль: {biz_info['base_profit']:,}/{biz_info['profit_period']}сек\n"
            f"  Купить: /buybusiness {biz_id}\n\n"
        )
    await message.answer(biz_list, reply_markup=get_business_reply_keyboard())


@dp.message(F.text == "Собрать прибыль")
async def text_collect_profit(message: Message):
    user_id = message.from_user.id
    ensure_user(user_id)

    business = business_data[user_id]
    if not business["type"]:
        await message.answer("❌ У вас нет бизнеса!", reply_markup=get_business_reply_keyboard())
        return

    if not business["active"]:
        await message.answer("❌ Бизнес не активен!", reply_markup=get_business_reply_keyboard())
        return

    profit = business["profit"]
    if profit > 0:
        add_balance(user_id, profit)
        add_xp(user_id, profit // 100)
        business["profit"] = 0
        business["last_collect"] = datetime.now()
        await message.answer(
            f"💰 Собрано прибыли: {profit:,} монет!\nБаланс: {format_balance(user_id)}",
            reply_markup=get_business_reply_keyboard()
        )
        save_data()
    else:
        await message.answer("ℹ️ Пока нет прибыли для сбора.", reply_markup=get_business_reply_keyboard())


@dp.message(F.text == "Продать бизнес")
async def text_sell_business(message: Message):
    user_id = message.from_user.id
    ensure_user(user_id)

    business = business_data[user_id]
    if not business["type"]:
        await message.answer("❌ У вас нет бизнеса!", reply_markup=get_business_reply_keyboard())
        return

    biz_info = BUSINESS_TYPES[business["type"]]
    sell_price = biz_info["cost"] // 2
    total_received = sell_price + business["profit"]

    add_balance(user_id, total_received)
    add_xp(user_id, total_received // 50)

    await message.answer(
        f"💼 Бизнес продан!\n\n"
        f"{biz_info['name']}\n"
        f"Стоимость: {sell_price:,} монет\n"
        f"Прибыль: {business['profit']:,} монет\n"
        f"Всего: {total_received:,} монет\n"
        f"Баланс: {format_balance(user_id)}",
        reply_markup=get_business_reply_keyboard()
    )

    business_data[user_id] = {"type": None, "profit": 0, "active": False, "last_collect": None}
    save_data()


@dp.message(F.text == "Рудник")
async def text_mine(message: Message):
    user_id = message.from_user.id
    ensure_user(user_id)
    mine_info = get_mine_info(user_id)
    await message.answer(f"<b>⛏ РУДНИК</b>\n\n{mine_info}", reply_markup=get_mine_reply_keyboard())


@dp.message(F.text == "Собрать ресурсы")
async def text_collect_resources(message: Message):
    user_id = message.from_user.id
    ensure_user(user_id)

    mine = mine_data[user_id]
    if mine["resources"] > 0:
        level_info = MINE_LEVELS[mine["level"]]
        total = mine["resources"] * level_info["price_per_unit"]
        add_balance(user_id, total)
        add_xp(user_id, total // 20)
        await message.answer(
            f"💰 Ресурсы собраны!\n"
            f"Добыто: {mine['resources']:,} {level_info['resource']}\n"
            f"Получено: {total:,} монет\n"
            f"Баланс: {format_balance(user_id)}",
            reply_markup=get_mine_reply_keyboard()
        )
        mine["resources"] = 0
        save_data()
    else:
        await message.answer("ℹ️ Нет ресурсов для сбора.", reply_markup=get_mine_reply_keyboard())


@dp.message(F.text == "Улучшить рудник")
async def text_upgrade_mine(message: Message):
    user_id = message.from_user.id
    ensure_user(user_id)

    mine = mine_data[user_id]
    if mine["level"] >= 2:
        await message.answer("🎉 Рудник максимального уровня!", reply_markup=get_mine_reply_keyboard())
        return

    next_level = mine["level"] + 1
    upgrade_cost = MINE_LEVELS[next_level]["upgrade_cost"]

    if not can_spend(user_id, upgrade_cost):
        await message.answer(
            f"❌ Недостаточно монет!\nНужно: {upgrade_cost:,} монет\nУ вас: {format_balance(user_id)}",
            reply_markup=get_mine_reply_keyboard()
        )
        return

    spend_balance(user_id, upgrade_cost)
    mine["level"] = next_level
    add_xp(user_id, upgrade_cost // 100)

    new_level_info = MINE_LEVELS[next_level]
    await message.answer(
        f"🎉 Рудник улучшен!\n\n"
        f"Новый уровень: {new_level_info['name']}\n"
        f"Ресурс: {new_level_info['resource']}\n"
        f"Цена за единицу: {new_level_info['price_per_unit']} монет\n"
        f"Баланс: {format_balance(user_id)}",
        reply_markup=get_mine_reply_keyboard()
    )
    save_data()


@dp.message(F.text == "Авто-сбор")
async def text_auto_collect(message: Message):
    user_id = message.from_user.id
    ensure_user(user_id)

    mine = mine_data[user_id]
    mine["auto_collect"] = not mine["auto_collect"]
    status = "включен" if mine["auto_collect"] else "выключен"
    await message.answer(f"⚡ Авто-сбор ресурсов {status}!", reply_markup=get_mine_reply_keyboard())
    save_data()


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


@dp.message(F.text == "Внести")
async def text_deposit(message: Message):
    await message.answer(
        "🏦 ВНЕСТИ\n\nИспользуйте: /bank <сумма>\nПример: /bank 1000"
    )


@dp.message(F.text == "Снять")
async def text_withdraw(message: Message):
    await message.answer(
        "🏦 СНЯТЬ\n\nИспользуйте: /bank w <сумма>\nПример: /bank w 1000"
    )


@dp.message(F.text == "Рулетка")
async def text_roulette(message: Message):
    await message.answer(
        "🎰 РУЛЕТКА\n\n"
        "Классическая: /roulette <сумма> (x36)\n"
        "Простая: /rsimple <сумма> (x2)",
        reply_markup=get_games_reply_keyboard()
    )


@dp.message(F.text == "Донат")
async def text_donate(message: Message):
    await cmd_donate(message)


@dp.message(F.text.startswith("Купить Элит"))
async def text_buy_elite(message: Message):
    await cmd_buy_elite(message)


@dp.message(F.text.startswith("Купить Делюкс"))
async def text_buy_deluxe(message: Message):
    await cmd_buy_deluxe(message)


@dp.message(F.text == "Купить коины")
async def text_buy_coins(message: Message):
    await message.answer(
        "💰 ПОКУПКА КОИНОВ\n\n"
        "Используйте: /buy_coins <количество_звезд>\n"
        f"1 ⭐ = {STAR_TO_COINS:,} коинов\n\n"
        "Пример: /buy_coins 10"
    )


@dp.message(F.text == "Админ")
async def text_admin(message: Message):
    user_id = message.from_user.id

    if is_admin(user_id):
        await message.answer(
            "<b>👑 АДМИН ПАНЕЛЬ</b>\n\nВыберите действие:",
            reply_markup=get_admin_inline()
        )
    elif has_rank(user_id, "Admin") or has_rank(user_id, "moderator"):
        await message.answer(
            "🛡 ПАНЕЛЬ МОДЕРАТОРА\n\nДоступ ограничен",
            reply_markup=get_main_reply_keyboard()
        )
    else:
        await message.answer(
            "❌ У вас нет админ прав",
            reply_markup=get_main_reply_keyboard()
        )


@dp.message(F.text == "Помощь")
async def text_help(message: Message):
    await cmd_help(message)


@dp.message(F.text == "Активация")
async def text_activation(message: Message):
    await message.answer(
        f"✅ <b>БОТ АКТИВИРОВАН!</b>\n\n"
        f"Система поддержания работы:\n"
        f"• Авто-пинг каждые 10 минут\n"
        f"• Минутные сообщения для @RobloxMinePump\n\n"
        f"Текущее время: {datetime.now().strftime('%H:%M:%S')}"
    )


@dp.message(F.text == "Назад в меню")
async def text_back(message: Message):
    await message.answer("↩️ Главное меню:", reply_markup=get_main_reply_keyboard())


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
        f"Код: {promo_code}\nОсталось активаций: {remaining}",
        reply_markup=get_main_reply_keyboard()
    )

    save_data()


# ---------------- КОРОТКИЕ КОМАНДЫ ----------------
@dp.message(F.text.lower() == "б")
async def short_balance(message: Message):
    user_id = message.from_user.id
    ensure_user(user_id)

    await message.answer(
        f"<b>💰 БАЛАНС</b>\n\n"
        f"Наличные: {format_balance(user_id)} монет\n"
        f"Ускорители: {user_accelerators.get(user_id, 0)}\n"
        f"В банке: {format_bank_balance(user_id)} монет",
        reply_markup=get_main_reply_keyboard()
    )


@dp.message(F.text.lower() == "я")
async def short_profile(message: Message):
    user_id = message.from_user.id
    ensure_user(user_id)

    profile = user_profiles[user_id]
    status = get_user_status(user_id)

    text = (
        f"<b>👤 ПРОФИЛЬ</b>\n\n"
        f"ID: <code>{user_id}</code>\n"
        f"Статус: {status}\n"
        f"Уровень: {profile['level']}\n"
        f"Опыт: {profile['xp']:,}/{profile['next_level_xp']:,}\n\n"
        f"Баланс: {format_balance(user_id)} монет\n"
        f"Ускорители: {user_accelerators.get(user_id, 0)}"
    )

    await message.answer(text, reply_markup=get_main_reply_keyboard())


# ---------------- CALLBACK ОБРАБОТЧИКИ ----------------
@dp.callback_query(F.data == "back_main")
async def callback_back(callback: CallbackQuery):
    await callback.message.edit_text("📋 Главное меню:", reply_markup=None)
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


@dp.callback_query(F.data.startswith("simple_"))
async def callback_simple_roulette(callback: CallbackQuery):
    user_id = callback.from_user.id
    data = callback.data

    if data == "simple_cancel":
        await callback.message.edit_text("❌ Игра отменена.")
        await callback.answer()
        return

    game_key = f"simple_{user_id}"
    if game_key not in roulette_games:
        await callback.message.edit_text("❌ Игра не найдена. Начните заново: /rsimple")
        await callback.answer()
        return

    bet = roulette_games[game_key]["bet"]
    result = random.choice(["red", "black"])
    result_color = "Красный" if result == "red" else "Черный"

    user_choice = "Красный" if data == "simple_red" else "Черный"

    if (data == "simple_red" and result == "red") or (data == "simple_black" and result == "black"):
        win_amount = bet * 2
        if not has_infinite_balance(user_id):
            add_balance(user_id, win_amount)
            add_xp(user_id, win_amount // 50)

        await callback.message.edit_text(
            f"🎉 ПОБЕДА!\n\n"
            f"Выпал: {result_color}\n"
            f"Ты выбрал: {user_choice}\n"
            f"Выигрыш: {win_amount:,} монет\n"
            f"Баланс: {format_balance(user_id)}"
        )
    else:
        await callback.message.edit_text(
            f"💔 ПРОИГРЫШ\n\n"
            f"Выпал: {result_color}\n"
            f"Ты выбрал: {user_choice}\n"
            f"Ставка {bet:,} монет сгорела\n"
            f"Баланс: {format_balance(user_id)}"
        )

    del roulette_games[game_key]
    await callback.answer()
    save_data()


@dp.callback_query(F.data.startswith("mini_"))
async def callback_mini_handler(callback: CallbackQuery):
    data = callback.data
    user_id = callback.from_user.id

    if data.startswith("mini_open_"):
        parts = data.split("_")
        game_id = "_".join(parts[2:-1])
        cell_idx = int(parts[-1])

        if game_id not in mini_games:
            await callback.message.edit_text("❌ Игра не найдена. Начните новую: /mini")
            await callback.answer()
            return

        state = mini_games[game_id]

        if state.get('lost', False):
            await callback.message.edit_text("❌ Игра уже завершена.")
            await callback.answer()
            return

        if state['user_id'] != user_id:
            await callback.answer("❌ Это не ваша игра!", show_alert=True)
            return

        if cell_idx in state['opened']:
            await callback.answer("❌ Эта клетка уже открыта!", show_alert=True)
            return

        state['opened'].add(cell_idx)

        if cell_idx in state['bombs']:
            state['lost'] = True

            all_opened = state['opened'].copy()
            all_opened.update(state['bombs'])

            keyboard = create_mini_keyboard(all_opened, state['bombs'], game_id)

            await callback.message.edit_text(
                f"💥 БОМБА! Вы проиграли!\n"
                f"Ставка: {state['bet']:,} монет сгорела.\n"
                f"Баланс: {format_balance(user_id)}",
                reply_markup=keyboard
            )

            del mini_games[game_id]
            await callback.answer()
            return

        state['hits'] += 1
        state['multiplier'] *= MINI_MULTIPLIER
        win_amount = int(state['bet'] * state['multiplier'])

        keyboard = create_mini_keyboard(state['opened'], state['bombs'], game_id)

        await callback.message.edit_text(
            f"<b>💣 Мини-игра: Сапёр</b>\n"
            f"💰 Ставка: {state['bet']:,} монет\n"
            f"📊 Открыто клеток: {state['hits']} | Множитель: {state['multiplier']:.2f}x\n"
            f"🏆 Выигрыш: {win_amount:,} монет\n\n"
            f"Продолжайте открывать клетки!",
            reply_markup=keyboard
        )
        await callback.answer()

    elif data.startswith("mini_cashout_"):
        game_id = "_".join(data.split("_")[2:])

        if game_id not in mini_games:
            await callback.message.edit_text("❌ Игра не найдена.")
            await callback.answer()
            return

        state = mini_games[game_id]

        if state.get('lost', False):
            await callback.message.edit_text("❌ Игра уже завершена.")
            await callback.answer()
            return

        if state['user_id'] != user_id:
            await callback.answer("❌ Это не ваша игра!", show_alert=True)
            return

        win_amount = int(state['bet'] * state['multiplier'])

        if not state['infinite_user']:
            add_balance(user_id, win_amount)
            add_xp(user_id, win_amount // 50)

        all_opened = state['opened'].copy()
        all_opened.update(state['bombs'])

        keyboard = create_mini_keyboard(all_opened, state['bombs'], game_id)

        await callback.message.edit_text(
            f"🏆 ВЫ ЗАБРАЛИ ВЫИГРЫШ!\n\n"
            f"Открыто клеток: {state['hits']}\n"
            f"Множитель: {state['multiplier']:.2f}x\n"
            f"Выигрыш: {win_amount:,} монет\n"
            f"Баланс: {format_balance(user_id)}",
            reply_markup=keyboard
        )

        del mini_games[game_id]
        await callback.answer()
        save_data()


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

            # Автосохранение
            if random.random() < 0.0167:
                save_data()

            await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Ошибка в фоновых задачах: {e}")
            await asyncio.sleep(1)


# ---------------- МИНУТНЫЙ ПИНГ ДЛЯ ТЕБЯ (ИСПРАВЛЕННЫЙ) ----------------
async def send_minute_ping():
    """Отправляет сообщение каждую минуту пользователю @RobloxMinePump"""
    while True:
        try:
            # Проверяем, существует ли чат
            try:
                chat = await bot.get_chat(YOUR_USERNAME)
                YOUR_USER_ID = chat.id
                
                # Отправляем сообщение
                await bot.send_message(
                    chat_id=YOUR_USER_ID,
                    text=f"✅ Бот активен! Время: {datetime.now().strftime('%H:%M:%S')}"
                )
                logger.info(f"📨 Отправлено минутное сообщение для {YOUR_USERNAME}")
                
            except Exception as e:
                logger.error(f"❌ Не могу отправить сообщение для {YOUR_USERNAME}: {e}")
                logger.info(f"💡 Напиши боту @CoinTGGamebot от @RobloxMinePump и нажми START")
                
                # Пытаемся отправить админам предупреждение
                for admin_id in ADMINS:
                    try:
                        await bot.send_message(
                            chat_id=admin_id,
                            text=f"⚠️ ВНИМАНИЕ! Бот не может писать @RobloxMinePump!\n"
                                 f"Нужно: @RobloxMinePump должен написать боту и нажать START"
                        )
                        break
                    except:
                        pass

            # Ждем 60 секунд
            await asyncio.sleep(60)

        except Exception as e:
            logger.error(f"❌ Критическая ошибка в send_minute_ping: {e}")
            await asyncio.sleep(60)
# ---------------- ПИНГ ДЛЯ RENDER ----------------
async def keep_alive():
    """Функция для поддержания бота в активном состоянии"""
    while True:
        try:
            me = await bot.get_me()
            logger.info(f"💚 Пинг: бот @{me.username} активен")

            if random.random() < 0.1:
                save_data()

            await asyncio.sleep(600)  # 10 минут
        except Exception as e:
            logger.error(f"❌ Ошибка в пинге: {e}")
            await asyncio.sleep(60)


# ---------------- ЗАПУСК ----------------
async def main():
    # Загружаем данные
    load_data()

    # Запускаем фоновые задачи
    asyncio.create_task(background_tasks())
    asyncio.create_task(keep_alive())
    asyncio.create_task(send_minute_ping())  # Отправка сообщений каждую минуту

    logger.info(f"✅ БОТ ЗАПУЩЕН! @{(await bot.me()).username}")
    logger.info(f"✅ Минутные сообщения будут отправляться для {YOUR_USERNAME}")
    print(f"✅ БОТ ЗАПУЩЕН! @{(await bot.me()).username}")
    print(f"✅ Минутные сообщения будут отправляться для {YOUR_USERNAME}")

    # Запускаем polling
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")

