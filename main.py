# bot.py
import asyncio
import json
import os
import logging
import random
import string
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Set, List, Tuple, Optional
from functools import wraps

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.types import (
    Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile,
    PreCheckoutQuery, LabeledPrice, SuccessfulPayment
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest
from aiogram.utils.formatting import Text, Bold, Italic, Code
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# ---------------- НАСТРОЙКИ ЛОГИРОВАНИЯ ----------------
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
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMINS = [int(id) for id in os.getenv("ADMINS", "8136808901,6479090914,7716319249,7406866574").split(",")]

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
user_last_command = {}
roulette_games = {}
pending_invoices = {}
user_mini_settings = {}

INFINITE_BALANCE = "INFINITE"

# ---------------- FSM СОСТОЯНИЯ ----------------
class RouletteStates(StatesGroup):
    waiting_for_number = State()

class SimpleRouletteStates(StatesGroup):
    waiting_for_color = State()

class BankStates(StatesGroup):
    waiting_for_amount = State()
    waiting_for_withdraw = State()

# ---------------- ИНИЦИАЛИЗАЦИЯ БОТА ----------------
bot = Bot(token=BOT_TOKEN)
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


# ---------------- АВТОСОХРАНЕНИЕ ----------------
async def auto_save():
    while True:
        await asyncio.sleep(300)  # 5 минут
        save_data()


# ---------------- ДЕКОРАТОР ДЛЯ RATE LIMITING ----------------
def rate_limit(seconds: int = 1):
    def decorator(func):
        @wraps(func)
        async def wrapper(message: Message, *args, **kwargs):
            if not message or not message.from_user:
                return await func(message, *args, **kwargs)

            user_id = message.from_user.id
            now = time.time()
            command = func.__name__

            if user_id not in user_last_command:
                user_last_command[user_id] = {}

            if command in user_last_command[user_id]:
                last_call = user_last_command[user_id][command]
                if now - last_call < seconds:
                    return None

            user_last_command[user_id][command] = now
            return await func(message, *args, **kwargs)

        return wrapper

    return decorator


# ---------------- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ----------------
def ensure_user(user_id: int):
    if user_id not in user_balances:
        user_balances[user_id] = START_BALANCE
    if user_id not in user_accelerators:
        user_accelerators[user_id] = START_ACCELERATORS
    if user_id not in mine_data:
        mine_data[user_id] = {"level": 0, "resources": 0, "auto_collect": False}
    if user_id not in business_data:
        business_data[user_id] = {"type": None, "profit": 0, "active": False, "last_collect": None}
    if user_id not in user_bank:
        user_bank[user_id] = 0
    if user_id not in user_profiles:
        user_profiles[user_id] = {"level": 1, "xp": 0, "next_level_xp": 100}
    if user_id not in user_donations:
        user_donations[user_id] = {"total_stars": 0, "total_coins": 0, "transactions": []}
    if user_id not in user_premium:
        user_premium[user_id] = {"type": None, "expires": None, "purchased_at": None}


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


def get_balance(user_id: int):
    return user_balances.get(user_id, START_BALANCE)


def has_infinite_balance(user_id: int) -> bool:
    return user_balances.get(user_id) == INFINITE_BALANCE


def format_balance(user_id: int) -> str:
    balance = get_balance(user_id)
    if balance == INFINITE_BALANCE:
        return "∞ (бесконечный)"
    if isinstance(balance, (int, float)):
        return f"{balance:,}"
    return str(balance)


def format_bank_balance(user_id: int) -> str:
    balance = user_bank.get(user_id, 0)
    return f"{balance:,}"


def can_spend(user_id: int, amount: int) -> bool:
    if has_infinite_balance(user_id):
        return True
    balance = get_balance(user_id)
    if isinstance(balance, (int, float)):
        return balance >= amount
    return False


def spend_balance(user_id: int, amount: int):
    if has_infinite_balance(user_id):
        return
    if user_id in user_balances and isinstance(user_balances[user_id], (int, float)):
        user_balances[user_id] -= amount


def add_balance(user_id: int, amount: int):
    if has_infinite_balance(user_id):
        return
    if user_id not in user_balances:
        user_balances[user_id] = START_BALANCE + amount
    else:
        if isinstance(user_balances[user_id], (int, float)):
            user_balances[user_id] += amount
        else:
            user_balances[user_id] = START_BALANCE + amount
        add_xp(user_id, amount // 100)


def set_infinite_balance(user_id: int):
    user_balances[user_id] = INFINITE_BALANCE


def remove_infinite_balance(user_id: int):
    user_balances[user_id] = START_BALANCE


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

    info = f"⛏️ {level_info['name']}\n"
    info += f"Ресурс: {level_info['resource']}\n"
    info += f"Количество: {mine['resources']:,}\n"
    info += f"Стоимость: {level_info['price_per_unit']} монет за 1 ед.\n"
    info += f"Общая стоимость: {mine['resources'] * level_info['price_per_unit']:,} монет\n"
    info += f"Авто-сбор: {'✅ Вкл' if mine['auto_collect'] else '❌ Выкл'}\n"

    if level < 2:
        next_level = MINE_LEVELS[level + 1]
        info += f"\n📈 Улучшение до {next_level['name']}:\n"
        info += f"💰 Стоимость: {next_level['upgrade_cost']:,} монет\n"
        info += f"🎁 Новый ресурс: {next_level['resource']}\n"
        info += f"💎 Новая цена: {next_level['price_per_unit']} монет за 1 ед."

    return info


# ---------------- КЛАВИАТУРЫ ----------------
def main_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="Баланс"),
        KeyboardButton(text="Работа"),
        KeyboardButton(text="Игры")
    )
    builder.row(
        KeyboardButton(text="Профиль"),
        KeyboardButton(text="Бизнес"),
        KeyboardButton(text="Рудник")
    )
    builder.row(
        KeyboardButton(text="Банк"),
        KeyboardButton(text="Рулетка"),
        KeyboardButton(text="Донат")
    )
    builder.row(
        KeyboardButton(text="Админ"),
        KeyboardButton(text="Помощь")
    )
    return builder.as_markup(resize_keyboard=True)


def profile_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="Статистика"),
        KeyboardButton(text="Имущество")
    )
    builder.row(KeyboardButton(text="Назад в меню"))
    return builder.as_markup(resize_keyboard=True)


def jobs_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="Курьер"),
        KeyboardButton(text="Таксист"),
        KeyboardButton(text="Программист")
    )
    builder.row(KeyboardButton(text="Назад в меню"))
    return builder.as_markup(resize_keyboard=True)


def games_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="Казино"),
        KeyboardButton(text="Монетка"),
        KeyboardButton(text="Мини-игра")
    )
    builder.row(KeyboardButton(text="Назад в меню"))
    return builder.as_markup(resize_keyboard=True)


def mine_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="Собрать ресурсы"),
        KeyboardButton(text="Улучшить рудник")
    )
    builder.row(
        KeyboardButton(text="Авто-сбор"),
        KeyboardButton(text="Назад в меню")
    )
    return builder.as_markup(resize_keyboard=True)


def business_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="Купить бизнес"),
        KeyboardButton(text="Собрать прибыль")
    )
    builder.row(
        KeyboardButton(text="Продать бизнес"),
        KeyboardButton(text="Назад в меню")
    )
    return builder.as_markup(resize_keyboard=True)


def bank_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="Внести"),
        KeyboardButton(text="Снять"),
        KeyboardButton(text="Баланс")
    )
    builder.row(KeyboardButton(text="Назад в меню"))
    return builder.as_markup(resize_keyboard=True)


def donate_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="Купить Элит (50 ⭐)"))
    builder.row(KeyboardButton(text="Купить Делюкс (99 ⭐)"))
    builder.row(KeyboardButton(text="Купить коины"))
    builder.row(KeyboardButton(text="Назад в меню"))
    return builder.as_markup(resize_keyboard=True)


def roulette_keyboard():
    builder = InlineKeyboardBuilder()
    row = []
    for i in range(0, 37):
        row.append(InlineKeyboardButton(text=str(i), callback_data=f"roulette_num_{i}"))
        if len(row) == 6:
            builder.row(*row)
            row = []
    if row:
        builder.row(*row)
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="roulette_cancel"))
    return builder.as_markup()


# ---------------- МИНИ-ИГРА: САПЁР ----------------
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
                    row_buttons.append(InlineKeyboardButton(text="💣", callback_data=f"mini_bomb_{cell_id}"))
                else:
                    row_buttons.append(InlineKeyboardButton(text="⬜", callback_data=f"mini_empty_{cell_id}"))
            else:
                row_buttons.append(InlineKeyboardButton(text="❌", callback_data=f"mini_open_{cell_id}"))

        builder.row(*row_buttons)

    if game_id:
        builder.row(InlineKeyboardButton(text="💰 Забрать выигрыш", callback_data=f"mini_cashout_{game_id}"))

    return builder.as_markup()


# ---------------- КОМАНДА /ID ----------------
@dp.message(Command("id"))
@rate_limit(1)
async def cmd_id(message: Message):
    """Команда /id - показывает ID пользователя"""
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    username = f"@{message.from_user.username}" if message.from_user.username else "нет"

    # Если это ответ на сообщение
    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
        target_id = target_user.id
        target_name = target_user.first_name
        target_username = f"@{target_user.username}" if target_user.username else "нет"

        await message.answer(
            f"👤 <b>Информация о пользователе:</b>\n\n"
            f"Имя: {target_name}\n"
            f"Username: {target_username}\n"
            f"🆔 ID: <code>{target_id}</code>\n\n"
            f"💬 <i>Скопируйте ID для использования в командах</i>",
            parse_mode="HTML"
        )
    else:
        # Свой ID
        await message.answer(
            f"👤 <b>Ваш профиль:</b>\n\n"
            f"Имя: {first_name}\n"
            f"Username: {username}\n"
            f"🆔 <b>Ваш ID:</b> <code>{user_id}</code>",
            parse_mode="HTML"
        )


# ---------------- КОМАНДА /CHANCE ----------------
@dp.message(Command("chance"))
@rate_limit(2)
async def cmd_chance(message: Message, command: CommandObject):
    user_id = message.from_user.id

    if not (is_admin(user_id) or has_rank(user_id, "Admin")):
        await message.answer("❌ Только админы могут использовать /chance")
        return

    args = command.args
    if not args:
        await message.answer(
            "📌 <b>ИСПОЛЬЗОВАНИЕ /chance:</b>\n\n"
            "1. Ответь на сообщение: <code>/chance 30</code>\n"
            "2. По ID: <code>/chance 123456789 30</code>\n\n"
            "Число от 0 до 100:\n"
            "• 0 = 8 мин (очень сложно)\n"
            "• 25 = 6 мин (сложно)\n"
            "• 50 = 4 мины (средне)\n"
            "• 75 = 2 мины (легко)\n"
            "• 100 = 0 мин (нет мин)",
            parse_mode="HTML"
        )
        return

    parts = args.split()
    
    if message.reply_to_message:
        if len(parts) == 1 and parts[0].isdigit():
            target_id = message.reply_to_message.from_user.id
            target_name = message.reply_to_message.from_user.first_name
            chance = int(parts[0])
        else:
            await message.answer("❌ Используй: /chance <число> (ответом на сообщение)")
            return
    elif len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
        target_id = int(parts[0])
        chance = int(parts[1])
        target_name = f"ID: {target_id}"
    else:
        await message.answer("❌ Неправильный формат команды")
        return

    if chance < 0 or chance > 100:
        await message.answer("❌ Число должно быть от 0 до 100!")
        return

    if chance == 0:
        mines = 8
        level = "ОЧЕНЬ СЛОЖНО 🔥"
    elif chance == 100:
        mines = 0
        level = "ЛЕГКО (нет мин) ⭐"
    elif chance >= 75:
        mines = 2
        level = "ЛЕГКО 👍"
    elif chance >= 50:
        mines = 4
        level = "СРЕДНЕ 👌"
    elif chance >= 25:
        mines = 6
        level = "СЛОЖНО ⚠️"
    else:
        mines = 7
        level = "ОЧЕНЬ СЛОЖНО 🔥"

    user_mini_settings[target_id] = {
        "chance": chance,
        "mines": mines
    }

    await message.answer(
        f"✅ <b>НАСТРОЙКИ МИНИ-ИГРЫ ДЛЯ {target_name}</b>\n\n"
        f"• Сложность: {level}\n"
        f"• Значение: {chance}%\n"
        f"• Мин на поле: {mines}\n"
        f"• Шанс найти мину: {(mines / 25) * 100:.1f}%\n\n"
        f"Теперь в /mini для этого пользователя будет {mines} мин",
        parse_mode="HTML"
    )

    save_data()


# ---------------- МИНИ-ИГРА: КОМАНДА /MINI ----------------
@dp.message(Command("mini"))
@rate_limit(2)
async def cmd_mini(message: Message, command: CommandObject):
    user = message.from_user
    user_id = user.id
    ensure_user(user_id)

    args = command.args
    if not args or not args.isdigit():
        await message.answer(
            "💣 <b>МИНИ-ИГРА: САПЁР</b>\n\n"
            "Правила:\n• Поле 5×5\n• Каждая пустая клетка ×1.3 к выигрышу\n"
            "• Нашел мину - проигрыш\n\n"
            "Используй: <code>/mini сумма</code>\n"
            "Пример: <code>/mini 100</code>",
            parse_mode="HTML",
            reply_markup=games_keyboard()
        )
        return

    bet = int(args)
    if bet <= 0:
        await message.answer("❌ Ставка должна быть больше 0.", reply_markup=games_keyboard())
        return

    if not can_spend(user_id, bet):
        await message.answer("❌ Недостаточно монет для ставки.", reply_markup=games_keyboard())
        return

    infinite_user = has_infinite_balance(user_id)
    if not infinite_user:
        spend_balance(user_id, bet)

    if user_id in user_mini_settings:
        mines_count = user_mini_settings[user_id]['mines']
    else:
        mines_count = MINI_BOMBS

    game_id = f"{user_id}_{datetime.now().timestamp()}"
    bombs = generate_mini_board(mines_count)
    opened = set()

    state = {
        "user_id": user_id,
        "bet": bet,
        "bombs": bombs,
        "opened": opened,
        "started_at": datetime.now().isoformat(),
        "hits": 0,
        "multiplier": 1.0,
        "lost": False,
        "infinite_user": infinite_user,
        "game_id": game_id
    }

    mini_games[game_id] = state

    keyboard = create_mini_keyboard(opened, bombs, game_id)

    try:
        await message.answer(
            f"💣 <b>Мини-игра: Сапёр</b>\n"
            f"Игрок: {user.first_name}\n"
            f"Ставка: {bet:,} монет\n"
            f"Мин на поле: {mines_count}\n"
            f"Открыто клеток: 0 | Множитель: 1.0x\n"
            f"Выигрыш: {bet} монет\n\n"
            f"❌ - закрытая клетка\n💣 - мина\n⬜ - пустая клетка (+1.3x)",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Ошибка при создании мини-игры: {e}")
        if not infinite_user:
            add_balance(user_id, bet)
        await message.answer("❌ Ошибка создания игры. Попробуйте позже.")


@dp.callback_query(F.data.startswith("mini_"))
async def mini_callback_handler(callback: CallbackQuery):
    await callback.answer()

    try:
        data = callback.data
        user_id = callback.from_user.id

        if data.startswith("mini_open_"):
            parts = data.split("_")
            if len(parts) >= 4:
                game_id = "_".join(parts[2:-1])
                cell_idx = int(parts[-1])
                await process_mini_cell_click(callback, game_id, cell_idx, user_id)

        elif data.startswith("mini_cashout_"):
            parts = data.split("_")
            if len(parts) >= 3:
                game_id = "_".join(parts[2:])
                await process_mini_cashout(callback, game_id, user_id)

    except Exception as e:
        logger.error(f"Ошибка в мини-игре: {e}")
        await callback.message.edit_text("❌ Произошла ошибка. Начните игру заново: /mini")


async def process_mini_cell_click(callback: CallbackQuery, game_id: str, cell_idx: int, user_id: int):
    if game_id not in mini_games:
        await callback.message.edit_text("❌ Игра не найдена. Начните новую: /mini")
        return

    state = mini_games[game_id]

    if state.get('lost', False) or state.get('completed', False):
        await callback.message.edit_text("❌ Игра уже завершена. Начните новую: /mini")
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
        state['completed'] = True

        all_opened = state['opened'].copy()
        all_opened.update(state['bombs'])

        keyboard = create_mini_keyboard(all_opened, state['bombs'], game_id)

        try:
            await callback.message.edit_text(
                f"💥 <b>БОМБА! Вы проиграли!</b>\n"
                f"Ставка: {state['bet']:,} монет сгорела.\n"
                f"Открыто клеток: {state['hits']}\n"
                f"Баланс: {format_balance(user_id)}",
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        except TelegramBadRequest:
            pass

        if game_id in mini_games:
            del mini_games[game_id]

        return

    state['hits'] += 1
    state['multiplier'] *= MINI_MULTIPLIER
    win_amount = int(state['bet'] * state['multiplier'])

    keyboard = create_mini_keyboard(state['opened'], state['bombs'], game_id)

    try:
        await callback.message.edit_text(
            f"💣 <b>Мини-игра: Сапёр</b>\n"
            f"Ставка: {state['bet']:,} монет\n"
            f"Открыто клеток: {state['hits']} | Множитель: {state['multiplier']:.2f}x\n"
            f"Выигрыш: {win_amount:,} монет\n\n"
            f"Продолжайте открывать клетки!",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    except TelegramBadRequest:
        pass


async def process_mini_cashout(callback: CallbackQuery, game_id: str, user_id: int):
    if game_id not in mini_games:
        await callback.message.edit_text("❌ Игра не найдена.")
        return

    state = mini_games[game_id]

    if state.get('lost', False) or state.get('completed', False):
        await callback.message.edit_text("❌ Игра уже завершена.")
        return

    if state['user_id'] != user_id:
        await callback.answer("❌ Это не ваша игра!", show_alert=True)
        return

    state['completed'] = True

    win_amount = int(state['bet'] * state['multiplier'])

    if not state['infinite_user']:
        add_balance(user_id, win_amount)
        add_xp(user_id, win_amount // 50)

    all_opened = state['opened'].copy()
    all_opened.update(state['bombs'])

    keyboard = create_mini_keyboard(all_opened, state['bombs'], game_id)

    await callback.message.edit_text(
        f"🏆 <b>ВЫ ЗАБРАЛИ ВЫИГРЫШ!</b>\n\n"
        f"Открыто клеток: {state['hits']}\n"
        f"Множитель: {state['multiplier']:.2f}x\n"
        f"Выигрыш: {win_amount:,} монет\n"
        f"Баланс: {format_balance(user_id)}",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    if game_id in mini_games:
        del mini_games[game_id]

    save_data()


# ---------------- КОМАНДЫ ДЛЯ БАНКА ----------------
@dp.message(Command("bank"))
@rate_limit(1)
async def cmd_bank(message: Message, command: CommandObject):
    user_id = message.from_user.id
    ensure_user(user_id)

    args = command.args
    if not args:
        await message.answer(
            "🏦 <b>КОМАНДЫ БАНКА</b>\n\n"
            f"<code>/bank сумма</code> - положить деньги в банк\n"
            f"<code>/bank w сумма</code> - снять деньги из банка\n\n"
            f"💰 На кармане: {format_balance(user_id)}\n"
            f"🏦 В банке: {format_bank_balance(user_id)}",
            parse_mode="HTML",
            reply_markup=bank_keyboard()
        )
        return

    parts = args.split()
    
    if len(parts) == 1 and parts[0].isdigit():
        amount = int(parts[0])
        if amount <= 0:
            await message.answer("❌ Сумма должна быть больше 0!", reply_markup=bank_keyboard())
            return

        if not can_spend(user_id, amount):
            await message.answer(
                f"❌ Недостаточно монет!\nБаланс: {format_balance(user_id)}",
                reply_markup=bank_keyboard()
            )
            return

        spend_balance(user_id, amount)
        user_bank[user_id] = user_bank.get(user_id, 0) + amount

        await message.answer(
            f"✅ <b>Вы положили {amount:,} монет в банк</b>\n\n"
            f"💰 На кармане: {format_balance(user_id)}\n"
            f"🏦 В банке: {format_bank_balance(user_id)}",
            parse_mode="HTML",
            reply_markup=bank_keyboard()
        )
        save_data()

    elif len(parts) >= 2 and parts[0].lower() in ['w', 'withdraw', 'снять']:
        if not parts[1].isdigit():
            await message.answer("❌ Сумма должна быть числом", reply_markup=bank_keyboard())
            return

        amount = int(parts[1])
        bank_balance = user_bank.get(user_id, 0)

        if amount <= 0:
            await message.answer("❌ Неверная сумма", reply_markup=bank_keyboard())
            return

        if amount > bank_balance:
            await message.answer(
                f"❌ Недостаточно средств в банке!\nДоступно: {bank_balance:,}",
                reply_markup=bank_keyboard()
            )
            return

        user_bank[user_id] -= amount
        add_balance(user_id, amount)

        await message.answer(
            f"✅ <b>Вы сняли {amount:,} монет из банка</b>\n\n"
            f"💰 На кармане: {format_balance(user_id)}\n"
            f"🏦 В банке: {format_bank_balance(user_id)}",
            parse_mode="HTML",
            reply_markup=bank_keyboard()
        )
        save_data()

    else:
        await message.answer(
            "❌ Неправильный формат. Используйте:\n"
            "<code>/bank сумма</code> - положить\n"
            "<code>/bank w сумма</code> - снять",
            parse_mode="HTML",
            reply_markup=bank_keyboard()
        )


# ---------------- КОМАНДЫ ДЛЯ РУЛЕТКИ ----------------
@dp.message(Command("roulette"))
@rate_limit(2)
async def cmd_roulette(message: Message, command: CommandObject, state: FSMContext):
    user_id = message.from_user.id
    ensure_user(user_id)

    args = command.args
    if not args or not args.isdigit():
        await message.answer(
            "🎰 <b>РУЛЕТКА</b>\n\n"
            "Правила:\n• Выберите число от 0 до 36\n• При совпадении выигрыш ×36\n"
            "• При проигрыше ставка сгорает\n\n"
            "Используй: <code>/roulette сумма</code>\n"
            "Пример: <code>/roulette 1000</code>",
            parse_mode="HTML",
            reply_markup=games_keyboard()
        )
        return

    bet = int(args)
    if bet <= 0:
        await message.answer("❌ Ставка должна быть больше 0!", reply_markup=games_keyboard())
        return

    if not can_spend(user_id, bet):
        await message.answer(
            f"❌ Недостаточно монет!\nВаш баланс: {format_balance(user_id)}",
            reply_markup=games_keyboard()
        )
        return

    await state.update_data(bet=bet)

    if not has_infinite_balance(user_id):
        spend_balance(user_id, bet)

    await state.set_state(RouletteStates.waiting_for_number)
    await message.answer(
        f"🎰 <b>РУЛЕТКА</b>\n\nСтавка: {bet:,} монет\nВыберите число от 0 до 36:",
        reply_markup=roulette_keyboard(),
        parse_mode="HTML"
    )


@dp.callback_query(RouletteStates.waiting_for_number, F.data.startswith("roulette_"))
async def roulette_callback_handler(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    user_id = callback.from_user.id
    data = callback.data

    if data == "roulette_cancel":
        data = await state.get_data()
        bet = data.get("bet", 0)
        if bet > 0 and not has_infinite_balance(user_id):
            add_balance(user_id, bet)
        await state.clear()
        await callback.message.edit_text("❌ Игра отменена. Ставка возвращена.")
        return

    if data.startswith("roulette_num_"):
        selected_number = int(data.split("_")[2])
        data = await state.get_data()
        bet = data.get("bet", 0)
        
        winning_number = random.randint(0, 36)

        if selected_number == winning_number:
            win_amount = bet * ROULETTE_MULTIPLIER
            if not has_infinite_balance(user_id):
                add_balance(user_id, win_amount)
            add_xp(user_id, win_amount // 50)

            result_text = (
                f"🎉 <b>ПОБЕДА!</b>\n\n"
                f"Ваше число: {selected_number}\n"
                f"Выигрышное число: {winning_number}\n"
                f"💰 Выигрыш: {win_amount:,} монет\n"
                f"💳 Баланс: {format_balance(user_id)}"
            )
        else:
            result_text = (
                f"💔 <b>ПРОИГРЫШ</b>\n\n"
                f"Ваше число: {selected_number}\n"
                f"Выигрышное число: {winning_number}\n"
                f"❌ Ставка {bet:,} монет сгорела\n"
                f"💳 Баланс: {format_balance(user_id)}"
            )

        await state.clear()
        await callback.message.edit_text(result_text, parse_mode="HTML")
        save_data()


# ---------------- ПРОСТАЯ РУЛЕТКА ----------------
@dp.message(Command("rsimple"))
@rate_limit(2)
async def cmd_roulette_simple(message: Message, command: CommandObject, state: FSMContext):
    user_id = message.from_user.id
    ensure_user(user_id)

    args = command.args
    if not args or not args.isdigit():
        await message.answer(
            "🎰 <b>ПРОСТАЯ РУЛЕТКА</b>\n\n"
            "Правила:\n• Ставишь на красный или черный\n• Выигрыш = ставка × 2\n\n"
            "Используй: <code>/rsimple сумма</code>\n"
            "Пример: <code>/rsimple 100</code>",
            parse_mode="HTML",
            reply_markup=games_keyboard()
        )
        return

    bet = int(args)
    if bet <= 0:
        await message.answer("❌ Ставка должна быть больше 0!", reply_markup=games_keyboard())
        return

    if not can_spend(user_id, bet):
        await message.answer(
            f"❌ Недостаточно монет!\nВаш баланс: {format_balance(user_id)}",
            reply_markup=games_keyboard()
        )
        return

    await state.update_data(bet=bet)

    # Клавиатура с цветами
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔴 Красный", callback_data="simple_red"),
        InlineKeyboardButton(text="⚫ Черный", callback_data="simple_black")
    )
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="simple_cancel"))

    await state.set_state(SimpleRouletteStates.waiting_for_color)
    await message.answer(
        f"🎰 <b>ПРОСТАЯ РУЛЕТКА</b>\n\n"
        f"💰 Ставка: {bet:,} монет\n"
        f"🎯 Выбери цвет:",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )


@dp.callback_query(SimpleRouletteStates.waiting_for_color, F.data.startswith("simple_"))
async def simple_roulette_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    user_id = callback.from_user.id
    data = callback.data

    if data == "simple_cancel":
        await state.clear()
        await callback.message.edit_text("❌ Игра отменена.")
        return

    state_data = await state.get_data()
    bet = state_data.get("bet", 0)
    
    if bet <= 0:
        await state.clear()
        await callback.message.edit_text("❌ Ошибка ставки. Начните заново: /rsimple")
        return

    # Проверяем баланс
    if not can_spend(user_id, bet) and not has_infinite_balance(user_id):
        await callback.message.edit_text("❌ Недостаточно монет!")
        await state.clear()
        return

    # Списываем ставку
    if not has_infinite_balance(user_id):
        spend_balance(user_id, bet)

    # Результат рулетки
    result = random.choice(["red", "black"])
    result_color = "🔴 Красный" if result == "red" else "⚫ Черный"

    # Проверяем выигрыш
    if (data == "simple_red" and result == "red") or (data == "simple_black" and result == "black"):
        win_amount = bet * 2
        if not has_infinite_balance(user_id):
            add_balance(user_id, win_amount)
            add_xp(user_id, win_amount // 50)

        await callback.message.edit_text(
            f"🎉 <b>ПОБЕДА!</b>\n\n"
            f"Выпал: {result_color}\n"
            f"Ты выбрал: {'🔴 Красный' if data == 'simple_red' else '⚫ Черный'}\n"
            f"💰 Выигрыш: {win_amount:,} монет\n"
            f"💳 Баланс: {format_balance(user_id)}",
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text(
            f"💔 <b>ПРОИГРЫШ</b>\n\n"
            f"Выпал: {result_color}\n"
            f"Ты выбрал: {'🔴 Красный' if data == 'simple_red' else '⚫ Черный'}\n"
            f"❌ Ставка {bet:,} монет сгорела\n"
            f"💳 Баланс: {format_balance(user_id)}",
            parse_mode="HTML"
        )

    await state.clear()
    save_data()


# ---------------- ОСНОВНЫЕ КОМАНДЫ ----------------
@dp.message(Command("start"))
@rate_limit(1)
async def cmd_start(message: Message):
    user_id = message.from_user.id
    ensure_user(user_id)

    daily_bonus, daily_acc = get_daily_bonus(user_id)

    await message.answer(
        f"<b>ДОБРО ПОЖАЛОВАТЬ В БОТ-ИГРУ!</b>\n\n"
        f"👤 Статус: {get_user_status(user_id)}\n"
        f"💰 Баланс: {format_balance(user_id)}\n"
        f"⚡ Ускорители: {user_accelerators.get(user_id, 0)}\n\n"
        f"🎁 Ежедневный бонус: /daily (+{daily_bonus:,} монет, +{daily_acc} ускорителей)\n\n"
        f"📌 Короткие команды:\n"
        f"• <code>б</code> или <code>Баланс</code> - показать баланс\n"
        f"• <code>я</code> - показать профиль\n"
        f"• <code>/id</code> - узнать ID пользователя\n\n"
        f"Используйте меню для навигации:",
        parse_mode="HTML",
        reply_markup=main_keyboard()
    )


@dp.message(Command("help"))
@rate_limit(1)
async def cmd_help(message: Message):
    help_text = (
        "📚 <b>ПОЛНАЯ ИНСТРУКЦИЯ</b>\n\n"
        "💰 <b>БАЛАНС И РАБОТА:</b>\n"
        "• Баланс - посмотреть баланс и ускорители\n"
        "• Работа - заработать монеты (тратит ускорители)\n"
        "• /daily - ежедневный бонус\n\n"
        "👤 <b>ПРОФИЛЬ:</b>\n"
        "• Статистика - уровень, опыт, статус\n"
        "• Имущество - рудник, бизнес, банк\n\n"
        "🎮 <b>ИГРЫ:</b>\n"
        "• Казино - /bet сумма (x2)\n"
        "• Монетка - /coin\n"
        "• Мини-игра - /mini сумма (5×5, ×1.3 за клетку)\n"
        "• Рулетка - /roulette сумма (x36)\n"
        "• Простая рулетка - /rsimple сумма (x2)\n\n"
        "⛏️ <b>РУДНИК:</b>\n"
        "• Автоматическая добыча ресурсов\n"
        "• 3 ресурса/сек\n"
        "• Улучшение для более ценных ресурсов\n\n"
        "🏢 <b>БИЗНЕС:</b>\n"
        "• Пассивный доход\n"
        "• Разные уровни бизнеса\n\n"
        "🏦 <b>БАНК:</b>\n"
        "• /bank сумма - положить\n"
        "• /bank w сумма - снять\n\n"
        "⭐ <b>ДОНАТ (Telegram Stars):</b>\n"
        "• /buy_coins <звезды> - купить коины\n"
        "• /buy_elite - купить Элит (50 ⭐)\n"
        "• /buy_deluxe - купить Делюкс (99 ⭐)\n"
        "• /donate_history - история покупок\n"
        "• /refund - возврат звёзд\n\n"
        "🎟️ <b>ПРОМОКОДЫ:</b>\n"
        "• Введите #промокод для активации\n\n"
        "💸 <b>ПЕРЕВОД:</b>\n"
        "• /p @user сумма\n\n"
        "🆔 <b>ID ПОЛЬЗОВАТЕЛЯ:</b>\n"
        "• /id - показать свой ID\n"
        "• Ответ на сообщение + /id - показать ID пользователя\n\n"
        "⚡ <b>КОРОТКИЕ КОМАНДЫ:</b>\n"
        "• б - баланс\n"
        "• я - профиль\n\n"
        "👑 <b>АДМИН КОМАНДЫ:</b>\n"
        "• /chance <ID> <0-100> - установить сложность мини-игры"
    )
    await message.answer(help_text, parse_mode="HTML", reply_markup=main_keyboard())


@dp.message(Command("daily"))
@rate_limit(5)
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
                f"⏳ <b>Ещё рано!</b>\nСледующий бонус через: {hours}ч {minutes}м",
                parse_mode="HTML",
                reply_markup=main_keyboard()
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
        f"💰 Монеты: +{daily_bonus:,}\n"
        f"⚡ Ускорители: +{daily_acc}\n"
        f"💳 Баланс: {format_balance(user_id)}\n"
        f"⚡ Всего ускорителей: {user_accelerators.get(user_id, 0)}",
        parse_mode="HTML",
        reply_markup=main_keyboard()
    )

    save_data()


@dp.message(Command("bet"))
@rate_limit(1)
async def cmd_bet(message: Message, command: CommandObject):
    user_id = message.from_user.id
    ensure_user(user_id)

    args = command.args
    if not args or not args.isdigit():
        await message.answer(
            "Используй: <code>/bet сумма</code>\nПример: <code>/bet 100</code>",
            parse_mode="HTML",
            reply_markup=games_keyboard()
        )
        return

    amount = int(args)
    if amount <= 0:
        await message.answer("❌ Сумма должна быть больше 0!", reply_markup=games_keyboard())
        return

    if not can_spend(user_id, amount):
        await message.answer(
            f"❌ Недостаточно монет!\nБаланс: {format_balance(user_id)}",
            reply_markup=games_keyboard()
        )
        return

    infinite_user = has_infinite_balance(user_id)
    win = random.choice([True, False])

    if win:
        if not infinite_user:
            add_balance(user_id, amount)
            add_xp(user_id, amount // 50)
        result = f"🎉 <b>ПОБЕДА!</b> +{amount:,} монет"
    else:
        if not infinite_user:
            spend_balance(user_id, amount)
        result = f"💔 <b>ПРОИГРЫШ</b> -{amount:,} монет"

    await message.answer(
        f"{result}\nБаланс: {format_balance(user_id)}",
        parse_mode="HTML",
        reply_markup=games_keyboard()
    )

    save_data()


@dp.message(Command("coin"))
@rate_limit(1)
async def cmd_coin(message: Message):
    user_id = message.from_user.id
    ensure_user(user_id)
    result = random.choice(['Орёл', 'Решка'])
    await message.answer(
        f"🪙 <b>{result}</b>\nБаланс: {format_balance(user_id)}",
        parse_mode="HTML",
        reply_markup=games_keyboard()
    )


# ---------------- АДМИН КОМАНДЫ ----------------
@dp.message(Command("money"))
@rate_limit(1)
async def cmd_money(message: Message, command: CommandObject):
    user_id = message.from_user.id

    if not (is_admin(user_id) or has_rank(user_id, "Admin")):
        await message.answer("❌ Только админы могут использовать эту команду")
        return

    args = command.args
    if not args:
        await message.answer(
            "💰 <b>ИСПОЛЬЗОВАНИЕ:</b>\n"
            "<code>/money сумма</code> - выдать себе\n"
            "<code>/money @user сумма</code> - выдать пользователю\n"
            "Ответ на сообщение + <code>/money сумма</code> - выдать ответившему",
            parse_mode="HTML"
        )
        return

    parts = args.split()
    
    try:
        if message.reply_to_message:
            if len(parts) == 1 and parts[0].isdigit():
                target_user = message.reply_to_message.from_user
                target_id = target_user.id
                amount = int(parts[0])
                ensure_user(target_id)
                if not has_infinite_balance(target_id):
                    add_balance(target_id, amount)
                await message.answer(
                    f"✅ Выдано {amount:,} монет пользователю {target_user.first_name}",
                    reply_markup=main_keyboard()
                )
                save_data()
                return

        if len(parts) == 1 and parts[0].isdigit():
            amount = int(parts[0])
            ensure_user(user_id)
            if not has_infinite_balance(user_id):
                add_balance(user_id, amount)
            await message.answer(
                f"✅ Вы получили {amount:,} монет\nБаланс: {format_balance(user_id)}",
                reply_markup=main_keyboard()
            )
            save_data()
            return

        if len(parts) >= 2 and parts[1].isdigit():
            target = parts[0]
            amount = int(parts[1])

            try:
                if target.startswith('@'):
                    # Получаем ID по username
                    chat = await bot.get_chat(target)
                    target_id = chat.id
                else:
                    target_id = int(target)

                ensure_user(target_id)
                if not has_infinite_balance(target_id):
                    add_balance(target_id, amount)

                await message.answer(
                    f"✅ Выдано {amount:,} монет пользователю {target}",
                    reply_markup=main_keyboard()
                )
                save_data()
                return
            except Exception as e:
                logger.error(f"Ошибка в money_cmd: {e}")
                await message.answer("❌ Не удалось найти пользователя", reply_markup=main_keyboard())
                return

    except Exception as e:
        logger.error(f"Ошибка в money_cmd: {e}")
        await message.answer("❌ Ошибка выполнения команды", reply_markup=main_keyboard())


@dp.message(Command("p"))
@rate_limit(1)
async def cmd_givemoney(message: Message, command: CommandObject):
    user_id = message.from_user.id
    ensure_user(user_id)

    args = command.args
    if not args:
        await message.answer(
            "Используй: <code>/p @user сумма</code>\nПример: <code>/p @username 1000</code>",
            parse_mode="HTML"
        )
        return

    parts = args.split()
    try:
        if message.reply_to_message and len(parts) == 1 and parts[0].isdigit():
            target_id = message.reply_to_message.from_user.id
            amount = int(parts[0])
            if amount <= 0:
                await message.answer("❌ Сумма должна быть больше 0")
                return
            if not can_spend(user_id, amount):
                await message.answer("❌ Недостаточно монет")
                return
            spend_balance(user_id, amount)
            add_balance(target_id, amount)
            await message.answer(f"✅ Вы перевели {amount:,} монет")
            save_data()
            return

        if len(parts) >= 2 and parts[1].isdigit():
            target = parts[0]
            amount = int(parts[1])
            if amount <= 0:
                await message.answer("❌ Сумма должна быть больше 0")
                return
            if not can_spend(user_id, amount):
                await message.answer("❌ Недостаточно монет")
                return

            try:
                if target.startswith('@'):
                    chat = await bot.get_chat(target)
                    target_id = chat.id
                else:
                    target_id = int(target)

                spend_balance(user_id, amount)
                add_balance(target_id, amount)
                await message.answer(f"✅ Вы перевели {amount:,} монет пользователю {target}")
                save_data()
                return
            except:
                await message.answer("❌ Не удалось найти пользователя")
                return
    except Exception as e:
        logger.error(f"Ошибка в givemoney_cmd: {e}")
        await message.answer("❌ Ошибка выполнения команды")


# ---------------- ТЕКСТОВЫЙ ОБРАБОТЧИК ----------------
@dp.message(F.text)
@rate_limit(0.5)
async def text_handler(message: Message):
    text = message.text.strip()
    user = message.from_user
    user_id = user.id
    ensure_user(user_id)

    # 1️⃣ "я" - ПОЛНЫЙ ПРОФИЛЬ
    if text.lower() == "я":
        profile = user_profiles.get(user_id, {"level": 1, "xp": 0, "next_level_xp": 100})
        status = get_user_status(user_id)

        profile_text = (
            f"👤 <b>ПРОФИЛЬ: {user.first_name}</b>\n"
            f"🆔 ID: <code>{user_id}</code>\n"
            f"👑 Статус: {status}\n\n"
            f"📊 <b>СТАТИСТИКА:</b>\n"
            f"Уровень: {profile['level']}\n"
            f"Опыт: {profile['xp']:,}/{profile['next_level_xp']:,}\n"
            f"💰 Баланс: {format_balance(user_id)}\n"
            f"🏦 В банке: {format_bank_balance(user_id)}\n"
            f"⚡ Ускорители: {user_accelerators.get(user_id, 0)}\n\n"
            f"🏠 <b>ИМУЩЕСТВО:</b>\n"
        )

        if user_id in mine_data:
            mine = mine_data[user_id]
            level_info = MINE_LEVELS[mine["level"]]
            mine_value = mine["resources"] * level_info["price_per_unit"]
            profile_text += (
                f"⛏️ РУДНИК:\n"
                f"   {level_info['name']}\n"
                f"   Ресурсы: {mine['resources']:,} {level_info['resource']}\n"
                f"   💎 Стоимость: {mine_value:,} монет\n"
            )

        if user_id in business_data and business_data[user_id]["type"]:
            business = business_data[user_id]
            biz_info = BUSINESS_TYPES[business["type"]]
            profile_text += (
                f"🏢 БИЗНЕС:\n"
                f"   {biz_info['name']}\n"
                f"   💰 Прибыль: {business['profit']:,} монет\n"
            )

        await message.answer(profile_text, parse_mode="HTML", reply_markup=main_keyboard())
        return

    # 2️⃣ "б" или "баланс" - БАЛАНС
    if text.lower() in ["б", "баланс"]:
        balance_text = (
            f"💰 <b>ВАШ БАЛАНС</b>\n\n"
            f"Наличные: {format_balance(user_id)}\n"
            f"⚡ Ускорители: {user_accelerators.get(user_id, 0)}\n"
            f"🏦 В банке: {format_bank_balance(user_id)}\n"
        )
        if has_infinite_balance(user_id):
            balance_text += "✨ Бесконечный баланс активирован!"
        await message.answer(balance_text, parse_mode="HTML", reply_markup=main_keyboard())
        return

    # 3️⃣ Промокоды
    if text.startswith('#'):
        promo_code = text[1:].upper()
        await process_promo_code(message, promo_code)
        return

    # 4️⃣ Навигация
    if text == "Назад в меню":
        await message.answer("↩️ Главное меню:", reply_markup=main_keyboard())
        return

    # 5️⃣ Обработка кнопок меню
    if text == "Баланс":
        balance_text = (
            f"💰 <b>ВАШ БАЛАНС</b>\n\n"
            f"Наличные: {format_balance(user_id)}\n"
            f"⚡ Ускорители: {user_accelerators.get(user_id, 0)}\n"
            f"🏦 В банке: {format_bank_balance(user_id)}\n"
        )
        if has_infinite_balance(user_id):
            balance_text += "✨ Бесконечный баланс активирован!"
        await message.answer(balance_text, parse_mode="HTML", reply_markup=main_keyboard())
        return

    if text == "Профиль":
        await message.answer(
            "👤 <b>ВАШ ПРОФИЛЬ</b>\n\nВыберите действие:",
            parse_mode="HTML",
            reply_markup=profile_keyboard()
        )
        return

    if text == "Статистика":
        profile = user_profiles.get(user_id, {"level": 1, "xp": 0, "next_level_xp": 100})
        status = get_user_status(user_id)

        stats_text = (
            f"👤 <b>ПРОФИЛЬ: {user.first_name}</b>\n"
            f"🆔 ID: <code>{user_id}</code>\n"
            f"👑 Статус: {status}\n\n"
            f"📊 <b>СТАТИСТИКА:</b>\n"
            f"Уровень: {profile['level']}\n"
            f"Опыт: {profile['xp']:,}/{profile['next_level_xp']:,}\n"
            f"💰 Баланс: {format_balance(user_id)}\n"
            f"🏦 В банке: {format_bank_balance(user_id)}\n"
            f"⚡ Ускорители: {user_accelerators.get(user_id, 0)}\n"
        )

        await message.answer(stats_text, parse_mode="HTML", reply_markup=profile_keyboard())
        return

    if text == "Имущество":
        assets_text = "🏠 <b>ВАШЕ ИМУЩЕСТВО:</b>\n\n"

        if user_id in mine_data:
            mine = mine_data[user_id]
            level_info = MINE_LEVELS[mine["level"]]
            mine_value = mine["resources"] * level_info["price_per_unit"]
            assets_text += (
                f"⛏️ <b>РУДНИК:</b>\n"
                f"   {level_info['name']} (Уровень {mine['level'] + 1})\n"
                f"   Ресурсы: {mine['resources']:,} {level_info['resource']}\n"
                f"   💎 Стоимость: {mine_value:,} монет\n"
                f"   ⚡ Авто-сбор: {'✅ Вкл' if mine['auto_collect'] else '❌ Выкл'}\n\n"
            )

        if user_id in business_data and business_data[user_id]["type"]:
            business = business_data[user_id]
            biz_info = BUSINESS_TYPES[business["type"]]
            business_value = biz_info["cost"] // 2 + business["profit"]
            assets_text += (
                f"🏢 <b>БИЗНЕС:</b>\n"
                f"   {biz_info['name']}\n"
                f"   💰 Прибыль: {business['profit']:,} монет\n"
                f"   💎 Стоимость: {business_value:,} монет\n\n"
            )

        assets_text += f"🏦 <b>БАНК:</b> {format_bank_balance(user_id)} монет"

        await message.answer(assets_text, parse_mode="HTML", reply_markup=profile_keyboard())
        return

    if text == "Работа":
        if not can_work(user_id):
            await message.answer(
                "❌ У вас закончились ускорители!\nПолучите ускорители через /daily или промокоды.",
                reply_markup=main_keyboard()
            )
            return
        await message.answer("💼 Выберите работу:", reply_markup=jobs_keyboard())
        return

    if text in ["Курьер", "Таксист", "Программист"]:
        if not can_work(user_id):
            await message.answer("❌ Нет ускорителей!", reply_markup=jobs_keyboard())
            return

        earnings = {
            "Курьер": (10, 30),
            "Таксист": (20, 50),
            "Программист": (50, 120)
        }

        earn = random.randint(*earnings[text])
        use_accelerator(user_id, 1)

        if not has_infinite_balance(user_id):
            add_balance(user_id, earn)
            add_xp(user_id, earn // 10)

        await message.answer(
            f"{text}!\n"
            f"+{earn} монет\n"
            f"Использован 1 ускоритель\n"
            f"Баланс: {format_balance(user_id)}\n"
            f"Осталось ускорителей: {user_accelerators.get(user_id, 0)}",
            reply_markup=jobs_keyboard()
        )
        save_data()
        return

    if text == "Игры":
        await message.answer("🎮 ВЫБЕРИТЕ ИГРУ:", reply_markup=games_keyboard())
        return

    if text == "Казино":
        await message.answer(
            "🎰 <b>КАЗИНО</b>\n\nПравила:\n• 50% шанс на выигрыш\n• Выигрыш = ставка × 2\n\nКоманда: <code>/bet сумма</code>",
            parse_mode="HTML",
            reply_markup=games_keyboard()
        )
        return

    if text == "Монетка":
        result = random.choice(['Орёл', 'Решка'])
        await message.answer(
            f"🪙 <b>{result}</b>\nБаланс: {format_balance(user_id)}",
            parse_mode="HTML",
            reply_markup=games_keyboard()
        )
        return

    if text == "Мини-игра":
        await message.answer(
            "💣 <b>МИНИ-ИГРА: САПЁР</b>\n\nПравила:\n• Поле 5×5\n• Каждая пустая клетка ×1.3 к выигрышу\n\nИспользуй: <code>/mini сумма</code>\nПример: <code>/mini 100</code>",
            parse_mode="HTML",
            reply_markup=games_keyboard()
        )
        return

    if text == "Рулетка":
        await message.answer(
            "🎰 <b>РУЛЕТКА</b>\n\nПравила:\n• Выберите число от 0 до 36\n• Выигрыш = ставка × 36\n\nКоманда: <code>/roulette сумма</code>",
            parse_mode="HTML",
            reply_markup=games_keyboard()
        )
        return

    if text == "Донат":
        await message.answer(
            "⭐ <b>ДОНАТ МАГАЗИН</b>\n\n"
            "💰 <b>Коины:</b>\n"
            f"• 1 ⭐ = {STAR_TO_COINS:,} коинов\n"
            "Используй: <code>/buy_coins количество_звезд</code>\n"
            "Пример: <code>/buy_coins 10</code>\n\n"
            "👑 <b>Привилегии:</b>\n"
            f"• Элит - {ELITE_PRICE} ⭐\n"
            "  - Ежедневный бонус: 2500 коинов\n"
            "  - Ускорители: 60 в день\n\n"
            f"• Делюкс - {DELUXE_PRICE} ⭐\n"
            "  - Ежедневный бонус: 5000 коинов\n"
            "  - Ускорители: 100 в день\n\n"
            "📊 История покупок: /donate_history\n"
            "↩️ Возврат звёзд: /refund код_транзакции",
            parse_mode="HTML",
            reply_markup=donate_keyboard()
        )
        return

    if text in ["Купить Элит (50 ⭐)", "Купить Делюкс (99 ⭐)"]:
        # Здесь будет обработка покупки через инвойсы
        await message.answer("Эта функция временно недоступна. Используйте команду /buy_elite или /buy_deluxe")
        return

    if text == "Купить коины":
        await message.answer(
            "💰 <b>ПОКУПКА КОИНОВ</b>\n\n"
            "Используйте: <code>/buy_coins количество_звезд</code>\n"
            f"1 ⭐ = {STAR_TO_COINS:,} коинов\n\n"
            "Пример: <code>/buy_coins 10</code>",
            parse_mode="HTML"
        )
        return

    if text == "Банк":
        await message.answer(
            "🏦 <b>БАНК</b>\n\n"
            f"💰 На кармане: {format_balance(user_id)}\n"
            f"🏦 В банке: {format_bank_balance(user_id)}",
            parse_mode="HTML",
            reply_markup=bank_keyboard()
        )
        return

    if text in ["Внести", "Снять"]:
        action = "положить" if text == "Внести" else "снять"
        cmd = "/bank" if text == "Внести" else "/bank w"
        await message.answer(
            f"🏦 <b>БАНК - {action.upper()}</b>\n\nИспользуйте: <code>{cmd} сумма</code>\nПример: <code>{cmd} 1000</code>",
            parse_mode="HTML"
        )
        return

    if text == "Бизнес":
        if user_id not in business_data:
            ensure_user(user_id)

        business = business_data[user_id]
        if business["type"]:
            biz_info = BUSINESS_TYPES[business["type"]]
            profit_text = (
                f"🏢 <b>ВАШ БИЗНЕС:</b>\n\n"
                f"Название: {biz_info['name']}\n"
                f"💰 Прибыль: {business['profit']:,} монет\n"
                f"⚡ Активен: {'✅ Да' if business['active'] else '❌ Нет'}\n"
                f"💵 Прибыль/период: {biz_info['base_profit']:,} монет\n"
                f"⏱️ Период: {biz_info['profit_period']} сек"
            )
        else:
            profit_text = "🏢 У вас нет бизнеса! Купите в меню."

        await message.answer(profit_text, parse_mode="HTML", reply_markup=business_keyboard())
        return

    if text == "Купить бизнес":
        biz_list = "🏢 <b>ДОСТУПНЫЕ БИЗНЕСЫ:</b>\n\n"
        for biz_id, biz_info in BUSINESS_TYPES.items():
            biz_list += (
                f"• {biz_info['name']}\n"
                f"  💰 Цена: {biz_info['cost']:,} монет\n"
                f"  💵 Прибыль: {biz_info['base_profit']:,}/{biz_info['profit_period']}сек\n"
                f"  🛒 Купить: <code>/buybusiness {biz_id}</code>\n\n"
            )
        await message.answer(biz_list, parse_mode="HTML", reply_markup=business_keyboard())
        return

    if text == "Собрать прибыль":
        if user_id not in business_data or not business_data[user_id]["type"]:
            await message.answer("❌ У вас нет бизнеса!", reply_markup=business_keyboard())
            return

        business = business_data[user_id]
        if not business["active"]:
            await message.answer("❌ Бизнес не активен!", reply_markup=business_keyboard())
            return

        profit = business["profit"]
        if profit > 0:
            add_balance(user_id, profit)
            add_xp(user_id, profit // 100)
            business["profit"] = 0
            business["last_collect"] = datetime.now()
            await message.answer(
                f"💰 <b>Собрано прибыли: {profit:,} монет!</b>\nБаланс: {format_balance(user_id)}",
                parse_mode="HTML",
                reply_markup=business_keyboard()
            )
            save_data()
        else:
            await message.answer("ℹ️ Пока нет прибыли для сбора.", reply_markup=business_keyboard())
        return

    if text == "Продать бизнес":
        if user_id not in business_data or not business_data[user_id]["type"]:
            await message.answer("❌ У вас нет бизнеса!", reply_markup=business_keyboard())
            return

        business = business_data[user_id]
        biz_info = BUSINESS_TYPES[business["type"]]
        sell_price = biz_info["cost"] // 2
        total_received = sell_price + business["profit"]

        add_balance(user_id, total_received)
        add_xp(user_id, total_received // 50)

        await message.answer(
            f"💼 <b>Бизнес продан!</b>\n\n"
            f"{biz_info['name']}\n"
            f"💰 Стоимость: {sell_price:,} монет\n"
            f"💵 Прибыль: {business['profit']:,} монет\n"
            f"💎 Всего: {total_received:,} монет\n"
            f"💳 Баланс: {format_balance(user_id)}",
            parse_mode="HTML",
            reply_markup=business_keyboard()
        )

        business_data[user_id] = {"type": None, "profit": 0, "active": False, "last_collect": None}
        save_data()
        return

    if text == "Рудник":
        mine_info = get_mine_info(user_id)
        await message.answer(mine_info, parse_mode="HTML", reply_markup=mine_keyboard())
        return

    if text == "Собрать ресурсы":
        if user_id not in mine_data:
            ensure_user(user_id)
        mine = mine_data[user_id]
        if mine["resources"] > 0:
            level_info = MINE_LEVELS[mine["level"]]
            total = mine["resources"] * level_info["price_per_unit"]
            add_balance(user_id, total)
            add_xp(user_id, total // 20)
            await message.answer(
                f"💰 <b>Ресурсы собраны!</b>\n"
                f"Добыто: {mine['resources']:,} {level_info['resource']}\n"
                f"Получено: {total:,} монет\n"
                f"Баланс: {format_balance(user_id)}",
                parse_mode="HTML",
                reply_markup=mine_keyboard()
            )
            mine["resources"] = 0
            save_data()
        else:
            await message.answer("ℹ️ Нет ресурсов для сбора.", reply_markup=mine_keyboard())
        return

    if text == "Улучшить рудник":
        if user_id not in mine_data:
            ensure_user(user_id)
        mine = mine_data[user_id]
        if mine["level"] >= 2:
            await message.answer("🎉 Рудник максимального уровня!", reply_markup=mine_keyboard())
            return

        next_level = mine["level"] + 1
        upgrade_cost = MINE_LEVELS[next_level]["upgrade_cost"]

        if not can_spend(user_id, upgrade_cost):
            await message.answer(
                f"❌ Недостаточно монет!\nНужно: {upgrade_cost:,} монет\nУ вас: {format_balance(user_id)}",
                reply_markup=mine_keyboard()
            )
            return

        spend_balance(user_id, upgrade_cost)
        mine["level"] = next_level
        add_xp(user_id, upgrade_cost // 100)

        new_level_info = MINE_LEVELS[next_level]
        await message.answer(
            f"🎉 <b>Рудник улучшен!</b>\n\n"
            f"Новый уровень: {new_level_info['name']}\n"
            f"Ресурс: {new_level_info['resource']}\n"
            f"💎 Цена за единицу: {new_level_info['price_per_unit']} монет\n"
            f"💰 Баланс: {format_balance(user_id)}",
            parse_mode="HTML",
            reply_markup=mine_keyboard()
        )
        save_data()
        return

    if text == "Авто-сбор":
        if user_id not in mine_data:
            ensure_user(user_id)
        mine = mine_data[user_id]
        mine["auto_collect"] = not mine["auto_collect"]
        status = "включен" if mine["auto_collect"] else "выключен"
        await message.answer(f"⚡ Авто-сбор ресурсов {status}!", reply_markup=mine_keyboard())
        save_data()
        return

    if text == "Админ":
        if is_admin(user_id):
            admin_text = (
                "👑 <b>АДМИН ПАНЕЛЬ</b>\n\n"
                "/money - выдать монеты\n"
                "/setmoney - установить баланс\n"
                "/rank - выдать ранг\n"
                "/unrank - снять ранг\n"
                "/inf - бесконечный баланс\n"
                "/removeinf - снять бесконечность\n"
                "/createpromo - создать промокод\n"
                "/chance - установить сложность мини-игры"
            )
        elif has_rank(user_id, "Admin") or has_rank(user_id, "moderator"):
            admin_text = "🛡️ <b>ПАНЕЛЬ МОДЕРАТОРА</b>\n\n/money - выдать монеты (только себе)"
        else:
            admin_text = "❌ У вас нет админ прав"

        await message.answer(admin_text, parse_mode="HTML", reply_markup=main_keyboard())
        return

    if text == "Помощь":
        await cmd_help(message)
        return


async def process_promo_code(message: Message, promo_code: str):
    user_id = message.from_user.id

    if promo_code not in promo_codes:
        await message.answer("❌ Неверный или несуществующий промокод")
        return

    promo = promo_codes[promo_code]

    if isinstance(promo["used_by"], list):
        promo["used_by"] = set(promo["used_by"])

    if len(promo["used_by"]) >= promo["max_activations"]:
        await message.answer("❌ Промокод уже использовал максимальное количество раз")
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
        reward_text = f"{promo['amount']:,} ускорителей"

    remaining = promo["max_activations"] - len(promo["used_by"])

    await message.answer(
        f"✅ <b>Промокод активирован!</b>\n\n"
        f"Вы получили: {reward_text}\n"
        f"Код: {promo_code}\n"
        f"Осталось активаций: {remaining}\n\n"
        f"💰 Баланс: {format_balance(user_id)}\n"
        f"⚡ Ускорителей: {user_accelerators.get(user_id, 0)}",
        parse_mode="HTML"
    )

    save_data()


# ---------------- ФОНОВЫЕ ЗАДАЧИ ----------------
async def background_tasks():
    while True:
        try:
            for user_id, mine in mine_data.items():
                if mine.get("auto_collect", False):
                    mine["resources"] = mine.get("resources", 0) + 3

            now = datetime.now()
            for user_id, business in business_data.items():
                if business.get("type") and business.get("active"):
                    biz_info = BUSINESS_TYPES[business["type"]]

                    if business.get("last_collect"):
                        elapsed = (now - business["last_collect"]).total_seconds()
                        if elapsed >= biz_info["profit_period"]:
                            cycles = int(elapsed // biz_info["profit_period"])
                            profit_to_add = biz_info["base_profit"] * cycles
                            business["profit"] = business.get("profit", 0) + profit_to_add
                            business["last_collect"] = now
                    else:
                        business["last_collect"] = now

            await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Ошибка в фоновых задачах: {e}")
            await asyncio.sleep(1)


# ---------------- ЗАПУСК БОТА ----------------
async def main():
    # Загружаем данные
    load_data()
    
    # Запускаем фоновые задачи
    asyncio.create_task(background_tasks())
    asyncio.create_task(auto_save())
    
    # Запускаем бота
    logger.info("✅ БОТ УСПЕШНО ЗАПУЩЕН! КОМАНДА /id ДОБАВЛЕНА!")
    print("✅ БОТ УСПЕШНО ЗАПУЩЕН! КОМАНДА /id ДОБАВЛЕНА!")
    
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
