# bot.py
import json
import os
import logging
import random
import asyncio
import string
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Set, List, Tuple, Optional
from functools import wraps

# Отключаем лишние логи
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)

from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    CallbackQueryHandler,
    PreCheckoutQueryHandler,
    JobQueue,
)
from telegram.error import BadRequest

# ---------------- НАСТРОЙКИ ЛОГИРОВАНИЯ ----------------
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# ---------------- НАСТРОЙКИ ----------------
YOUR_BOT_TOKEN = "BOT_TOKEN"
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

# ---------------- НАСТРОЙКИ МИНИ-ИГРЫ (5x5, множитель 1.3) ----------------
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
async def auto_save(context: ContextTypes.DEFAULT_TYPE):
    save_data()


# ---------------- ДЕКОРАТОР ДЛЯ RATE LIMITING ----------------
def rate_limit(seconds: int = 1):
    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            if not update or not update.effective_user:
                return await func(update, context, *args, **kwargs)

            user_id = update.effective_user.id
            now = time.time()
            command = func.__name__

            if user_id not in user_last_command:
                user_last_command[user_id] = {}

            if command in user_last_command[user_id]:
                last_call = user_last_command[user_id][command]
                if now - last_call < seconds:
                    return None

            user_last_command[user_id][command] = now
            return await func(update, context, *args, **kwargs)

        return wrapper

    return decorator


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

    # Защита от несуществующего уровня
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
def main_keyboard():
    kb = [
        ["Баланс", "Работа", "Игры"],
        ["Профиль", "Бизнес", "Рудник"],
        ["Банк", "Рулетка", "Донат"],
        ["Админ", "Помощь"]
    ]
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)


def jobs_keyboard():
    kb = [
        ["Курьер", "Таксист", "Программист"],
        ["Назад в меню"]
    ]
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)


def games_keyboard():
    kb = [
        ["Казино", "Монетка", "Мини-игра"],
        ["Назад в меню"]
    ]
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)


def mine_keyboard():
    kb = [
        ["Собрать ресурсы", "Улучшить рудник"],
        ["Авто-сбор", "Назад в меню"]
    ]
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)


def business_keyboard():
    kb = [
        ["Купить бизнес", "Собрать прибыль"],
        ["Продать бизнес", "Назад в меню"]
    ]
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)


def bank_keyboard():
    kb = [
        ["Внести", "Снять", "Баланс"],
        ["Назад в меню"]
    ]
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)


def donate_keyboard():
    kb = [
        ["Купить Элит (50 ⭐)"],
        ["Купить Делюкс (99 ⭐)"],
        ["Купить коины"],
        ["Назад в меню"]
    ]
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)


def roulette_keyboard():
    keyboard = []
    row = []
    for i in range(0, 37):
        row.append(InlineKeyboardButton(str(i), callback_data=f"roulette_num_{i}"))
        if len(row) == 6:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("Отмена", callback_data="roulette_cancel")])
    return InlineKeyboardMarkup(keyboard)


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


def adjacent_bombs_count(bombs: Set[int], idx: int) -> int:
    return sum(1 for n in neighbors_indices(idx) if n in bombs)


def create_mini_keyboard(opened: Set[int], bombs: Set[int], game_id: str = None) -> InlineKeyboardMarkup:
    keyboard = []

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

        keyboard.append(row_buttons)

    if game_id:
        keyboard.append([InlineKeyboardButton("Забрать выигрыш", callback_data=f"mini_cashout_{game_id}")])

    return InlineKeyboardMarkup(keyboard)


# ---------------- КОМАНДА /CHANCE ----------------
@rate_limit(2)
async def chance_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not (is_admin(user_id) or has_rank(user_id, "Admin")):
        await update.message.reply_text("❌ Только админы могут использовать /chance")
        return

    args = context.args

    if update.message.reply_to_message:
        target_id = update.message.reply_to_message.from_user.id
        target_name = update.message.reply_to_message.from_user.first_name

        if len(args) >= 1 and args[0].isdigit():
            chance = int(args[0])
        else:
            await update.message.reply_text(
                "❌ Используй: /chance <число> (ответом на сообщение)\n"
                "Пример: ответь на сообщение и напиши /chance 30"
            )
            return

    elif len(args) >= 2 and args[0].isdigit() and args[1].isdigit():
        target_id = int(args[0])
        chance = int(args[1])
        target_name = f"ID: {target_id}"

    else:
        await update.message.reply_text(
            "📌 ИСПОЛЬЗОВАНИЕ /chance:\n\n"
            "1. Ответь на сообщение: /chance 30\n"
            "2. По ID: /chance 123456789 30\n\n"
            "Число от 0 до 100:\n"
            "• 0 = 8 мин (очень сложно)\n"
            "• 25 = 6 мин (сложно)\n"
            "• 50 = 4 мины (средне)\n"
            "• 75 = 2 мины (легко)\n"
            "• 100 = 0 мин (нет мин)"
        )
        return

    if chance < 0 or chance > 100:
        await update.message.reply_text("❌ Число должно быть от 0 до 100!")
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

    await update.message.reply_text(
        f"✅ НАСТРОЙКИ МИНИ-ИГРЫ ДЛЯ {target_name}\n\n"
        f"• Сложность: {level}\n"
        f"• Значение: {chance}%\n"
        f"• Мин на поле: {mines}\n"
        f"• Шанс найти мину: {(mines / 25) * 100:.1f}%\n\n"
        f"Теперь в /mini для этого пользователя будет {mines} мин"
    )

    save_data()


# ---------------- МИНИ-ИГРА: КОМАНДА /MINI ----------------
@rate_limit(2)
async def mini_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    ensure_user(user_id)

    args = context.args
    if len(args) != 1 or not args[0].isdigit():
        await update.message.reply_text(
            "МИНИ-ИГРА: САПЁР\n\n"
            "Правила:\n• Поле 5×5\n• Каждая пустая клетка ×1.3 к выигрышу\n"
            "• Нашел мину - проигрыш\n\n"
            "Используй: /mini <сумма>\nПример: /mini 100",
            reply_markup=games_keyboard()
        )
        return

    bet = int(args[0])
    if bet <= 0:
        await update.message.reply_text("❌ Ставка должна быть больше 0.", reply_markup=games_keyboard())
        return

    if not can_spend(user_id, bet):
        await update.message.reply_text("❌ Недостаточно монет для ставки.", reply_markup=games_keyboard())
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
        "game_id": game_id,
        "message_id": None,
        "chat_id": None
    }

    if 'mini_games' not in context.bot_data:
        context.bot_data['mini_games'] = {}
    context.bot_data['mini_games'][game_id] = state

    keyboard = create_mini_keyboard(opened, bombs, game_id)

    try:
        message = await update.message.reply_text(
            f"Мини-игра: Сапёр\nИгрок: {user.first_name}\n"
            f"Ставка: {bet:,} монет\nМин на поле: {mines_count}\n"
            f"Открыто клеток: 0 | Множитель: 1.0x\n"
            f"Выигрыш: {bet} монет\n\n"
            f"❌ - закрытая клетка\n💣 - мина\n⬜ - пустая клетка (+1.3x)",
            reply_markup=keyboard
        )

        state['message_id'] = message.message_id
        state['chat_id'] = message.chat_id

    except Exception as e:
        logger.error(f"Ошибка при создании мини-игры: {e}")
        if not infinite_user:
            add_balance(user_id, bet)
        await update.message.reply_text("❌ Ошибка создания игры. Попробуйте позже.")


async def mini_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        data = query.data
        user_id = query.from_user.id

        if data.startswith("mini_open_"):
            parts = data.split("_")
            if len(parts) >= 4:
                game_id = "_".join(parts[2:-1])
                cell_idx = int(parts[-1])
                await process_mini_cell_click(query, context, game_id, cell_idx, user_id)

        elif data.startswith("mini_cashout_"):
            parts = data.split("_")
            if len(parts) >= 3:
                game_id = "_".join(parts[2:])
                await process_mini_cashout(query, context, game_id, user_id)

    except Exception as e:
        logger.error(f"Ошибка в мини-игре: {e}")
        await query.edit_message_text("❌ Произошла ошибка. Начните игру заново: /mini")


async def process_mini_cell_click(query, context, game_id, cell_idx, user_id):
    if 'mini_games' not in context.bot_data or game_id not in context.bot_data['mini_games']:
        await query.edit_message_text("❌ Игра не найдена. Начните новую: /mini")
        return

    state = context.bot_data['mini_games'][game_id]

    if state.get('lost', False) or state.get('completed', False):
        await query.edit_message_text("❌ Игра уже завершена. Начните новую: /mini")
        return

    if state['user_id'] != user_id:
        await query.answer("❌ Это не ваша игра!", show_alert=True)
        return

    if cell_idx in state['opened']:
        await query.answer("❌ Эта клетка уже открыта!", show_alert=True)
        return

    state['opened'].add(cell_idx)

    if cell_idx in state['bombs']:
        state['lost'] = True
        state['completed'] = True

        all_opened = state['opened'].copy()
        all_opened.update(state['bombs'])

        keyboard = create_mini_keyboard(all_opened, state['bombs'], game_id)

        try:
            await query.edit_message_text(
                f"💥 БОМБА! Вы проиграли!\n"
                f"Ставка: {state['bet']:,} монет сгорела.\n"
                f"Открыто клеток: {state['hits']}\n"
                f"Баланс: {format_balance(user_id)}",
                reply_markup=keyboard
            )
        except BadRequest:
            pass

        if game_id in context.bot_data['mini_games']:
            del context.bot_data['mini_games'][game_id]

        return

    state['hits'] += 1
    state['multiplier'] *= MINI_MULTIPLIER
    win_amount = int(state['bet'] * state['multiplier'])

    keyboard = create_mini_keyboard(state['opened'], state['bombs'], game_id)

    try:
        await query.edit_message_text(
            f"Мини-игра: Сапёр\n"
            f"Ставка: {state['bet']:,} монет\n"
            f"Открыто клеток: {state['hits']} | Множитель: {state['multiplier']:.2f}x\n"
            f"Выигрыш: {win_amount:,} монет\n\n"
            f"Продолжайте открывать клетки!",
            reply_markup=keyboard
        )
    except BadRequest:
        pass


async def process_mini_cashout(query, context, game_id, user_id):
    if 'mini_games' not in context.bot_data or game_id not in context.bot_data['mini_games']:
        await query.edit_message_text("❌ Игра не найдена.")
        return

    state = context.bot_data['mini_games'][game_id]

    if state.get('lost', False) or state.get('completed', False):
        await query.edit_message_text("❌ Игра уже завершена.")
        return

    if state['user_id'] != user_id:
        await query.answer("❌ Это не ваша игра!", show_alert=True)
        return

    state['completed'] = True

    win_amount = int(state['bet'] * state['multiplier'])

    if not state['infinite_user']:
        add_balance(user_id, win_amount)
        add_xp(user_id, win_amount // 50)

    all_opened = state['opened'].copy()
    all_opened.update(state['bombs'])

    keyboard = create_mini_keyboard(all_opened, state['bombs'], game_id)

    message_text = (
        f"🏆 ВЫ ЗАБРАЛИ ВЫИГРЫШ!\n\n"
        f"Открыто клеток: {state['hits']}\n"
        f"Множитель: {state['multiplier']:.2f}x\n"
        f"Выигрыш: {win_amount:,} монет\n"
        f"Баланс: {format_balance(user_id)}"
    )

    try:
        await query.edit_message_text(message_text, reply_markup=keyboard)
    except BadRequest:
        pass

    if game_id in context.bot_data['mini_games']:
        del context.bot_data['mini_games'][game_id]

    save_data()


# ---------------- КОМАНДЫ ДЛЯ БАНКА ----------------
@rate_limit(1)
async def bank_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ensure_user(user_id)

    args = context.args
    if not args:
        await update.message.reply_text(
            "КОМАНДЫ БАНКА:\n\n"
            "/bank <сумма> - положить деньги в банк\n"
            "/bank w <сумма> - снять деньги из банка\n\n"
            f"На кармане: {format_balance(user_id)}\n"
            f"В банке: {format_bank_balance(user_id)}",
            reply_markup=bank_keyboard()
        )
        return

    if len(args) == 1 and args[0].isdigit():
        amount = int(args[0])
        if amount <= 0:
            await update.message.reply_text("❌ Сумма должна быть больше 0!", reply_markup=bank_keyboard())
            return

        if not can_spend(user_id, amount):
            await update.message.reply_text(
                f"❌ Недостаточно монет!\nБаланс: {format_balance(user_id)}",
                reply_markup=bank_keyboard()
            )
            return

        spend_balance(user_id, amount)
        user_bank[user_id] = user_bank.get(user_id, 0) + amount

        await update.message.reply_text(
            f"✅ Вы положили {amount:,} монет в банк\n\n"
            f"На кармане: {format_balance(user_id)}\n"
            f"В банке: {format_bank_balance(user_id)}",
            reply_markup=bank_keyboard()
        )
        save_data()

    elif len(args) >= 2 and args[0].lower() in ['w', 'withdraw', 'снять']:
        if not args[1].isdigit():
            await update.message.reply_text("❌ Сумма должна быть числом", reply_markup=bank_keyboard())
            return

        amount = int(args[1])
        bank_balance = user_bank.get(user_id, 0)

        if amount <= 0:
            await update.message.reply_text("❌ Неверная сумма", reply_markup=bank_keyboard())
            return

        if amount > bank_balance:
            await update.message.reply_text(
                f"❌ Недостаточно средств в банке!\nДоступно: {bank_balance:,}",
                reply_markup=bank_keyboard()
            )
            return

        user_bank[user_id] -= amount
        add_balance(user_id, amount)

        await update.message.reply_text(
            f"✅ Вы сняли {amount:,} монет из банка\n\n"
            f"На кармане: {format_balance(user_id)}\n"
            f"В банке: {format_bank_balance(user_id)}",
            reply_markup=bank_keyboard()
        )
        save_data()

    else:
        await update.message.reply_text(
            "Используйте:\n/bank <сумма> - положить\n/bank w <сумма> - снять",
            reply_markup=bank_keyboard()
        )


# ---------------- КОМАНДЫ ДЛЯ РУЛЕТКИ (КЛАССИЧЕСКАЯ) ----------------
@rate_limit(2)
async def roulette_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ensure_user(user_id)

    args = context.args
    if len(args) != 1 or not args[0].isdigit():
        await update.message.reply_text(
            "РУЛЕТКА\n\n"
            "Правила:\n• Выберите число от 0 до 36\n• При совпадении выигрыш ×36\n• При проигрыше ставка сгорает\n\n"
            "Используй: /roulette <сумма>\nПример: /roulette 1000",
            reply_markup=games_keyboard()
        )
        return

    bet = int(args[0])
    if bet <= 0:
        await update.message.reply_text("❌ Ставка должна быть больше 0!", reply_markup=games_keyboard())
        return

    if not can_spend(user_id, bet):
        await update.message.reply_text(
            f"❌ Недостаточно монет!\nВаш баланс: {format_balance(user_id)}",
            reply_markup=games_keyboard()
        )
        return

    roulette_games[user_id] = {"bet": bet, "step": "waiting_number"}

    if not has_infinite_balance(user_id):
        spend_balance(user_id, bet)

    await update.message.reply_text(
        f"РУЛЕТКА\n\nСтавка: {bet:,} монет\nВыберите число от 0 до 36:",
        reply_markup=roulette_keyboard()
    )


async def roulette_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = query.data

    if data == "roulette_cancel":
        if user_id in roulette_games:
            bet = roulette_games[user_id]["bet"]
            if not has_infinite_balance(user_id):
                add_balance(user_id, bet)
            del roulette_games[user_id]
        await query.edit_message_text("❌ Игра отменена. Ставка возвращена.")
        return

    if data.startswith("roulette_num_"):
        if user_id not in roulette_games:
            await query.edit_message_text("❌ Игра не найдена. Начните заново: /roulette")
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
        await query.edit_message_text(result_text)
        save_data()


# ---------------- НОВАЯ РУЛЕТКА (КРАСНОЕ/ЧЕРНОЕ) ----------------
@rate_limit(2)
async def roulette_simple_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Простая рулетка на красное/черное"""
    user_id = update.effective_user.id
    ensure_user(user_id)

    args = context.args
    if len(args) != 1 or not args[0].isdigit():
        await update.message.reply_text(
            "🎰 ПРОСТАЯ РУЛЕТКА\n\n"
            "Правила:\n• Ставишь на красный или черный\n• Выигрыш = ставка × 2\n\n"
            "Используй: /rsimple <сумма>\nПример: /rsimple 100",
            reply_markup=games_keyboard()
        )
        return

    bet = int(args[0])
    if bet <= 0:
        await update.message.reply_text("❌ Ставка должна быть больше 0!", reply_markup=games_keyboard())
        return

    if not can_spend(user_id, bet):
        await update.message.reply_text(
            f"❌ Недостаточно монет!\nВаш баланс: {format_balance(user_id)}",
            reply_markup=games_keyboard()
        )
        return

    # Сохраняем ставку
    context.user_data["simple_bet"] = bet
    context.user_data["simple_bet_amount"] = bet

    # Клавиатура с цветами
    keyboard = [
        [
            InlineKeyboardButton("🔴 Красный", callback_data="simple_red"),
            InlineKeyboardButton("⚫ Черный", callback_data="simple_black"),
        ],
        [InlineKeyboardButton("❌ Отмена", callback_data="simple_cancel")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"🎰 ПРОСТАЯ РУЛЕТКА\n\n"
        f"💰 Ставка: {bet:,} монет\n"
        f"🎯 Выбери цвет:",
        reply_markup=reply_markup
    )


async def simple_roulette_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик для простой рулетки"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = query.data

    if data == "simple_cancel":
        await query.edit_message_text("❌ Игра отменена.")
        return

    # Получаем ставку
    bet = context.user_data.get("simple_bet", 0)
    if bet <= 0:
        await query.edit_message_text("❌ Ошибка ставки. Начните заново: /rsimple")
        return

    # Проверяем баланс
    if not can_spend(user_id, bet) and not has_infinite_balance(user_id):
        await query.edit_message_text("❌ Недостаточно монет!")
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

        await query.edit_message_text(
            f"🎉 ПОБЕДА!\n\n"
            f"Выпал: {result_color}\n"
            f"Ты выбрал: {'🔴 Красный' if data == 'simple_red' else '⚫ Черный'}\n"
            f"💰 Выигрыш: {win_amount:,} монет\n"
            f"💳 Баланс: {format_balance(user_id)}"
        )
    else:
        await query.edit_message_text(
            f"💔 ПРОИГРЫШ\n\n"
            f"Выпал: {result_color}\n"
            f"Ты выбрал: {'🔴 Красный' if data == 'simple_red' else '⚫ Черный'}\n"
            f"❌ Ставка {bet:,} монет сгорела\n"
            f"💳 Баланс: {format_balance(user_id)}"
        )

    save_data()


# ---------------- КОМАНДЫ ДЛЯ ДОНАТА ----------------
@rate_limit(2)
async def donate_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ensure_user(user_id)

    await update.message.reply_text(
        "ДОНАТ МАГАЗИН\n\n"
        "Коины:\n"
        f"• 1 ⭐ = {STAR_TO_COINS:,} коинов\n"
        "Используй: /buy_coins <количество_звезд>\n"
        "Пример: /buy_coins 10\n\n"
        "Привилегии:\n"
        f"• Элит - {ELITE_PRICE} ⭐\n"
        "  - Ежедневный бонус: 2500 коинов\n"
        "  - Ускорители: 60 в день\n"
        "  - Особый статус\n\n"
        f"• Делюкс - {DELUXE_PRICE} ⭐\n"
        "  - Ежедневный бонус: 5000 коинов\n"
        "  - Ускорители: 100 в день\n"
        "  - Премиум статус\n"
        "  - Все бонусы Элит\n\n"
        "История покупок: /donate_history\n"
        "Возврат звёзд: /refund <код_транзакции>",
        reply_markup=donate_keyboard()
    )


@rate_limit(2)
async def buy_coins_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ensure_user(user_id)

    args = context.args
    if not args or not args[0].isdigit():
        await update.message.reply_text(
            "❌ Используй: /buy_coins <количество_звезд>\n"
            "Пример: /buy_coins 10"
        )
        return

    stars = int(args[0])
    if stars <= 0:
        await update.message.reply_text("❌ Количество звезд должно быть больше 0!")
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

    await context.bot.send_invoice(
        chat_id=user_id,
        title=f"{coins:,} коинов",
        description=f"Покупка {coins:,} игровых коинов за {stars} ⭐",
        payload=invoice_id,
        provider_token="",
        currency="XTR",
        prices=[{"label": f"{stars} ⭐", "amount": stars}],
        start_parameter="donate_coins"
    )


@rate_limit(2)
async def buy_elite_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ensure_user(user_id)

    invoice_id = f"elite_{user_id}_{int(time.time())}"

    pending_invoices[invoice_id] = {
        "user_id": user_id,
        "stars": ELITE_PRICE,
        "type": "elite",
        "timestamp": time.time()
    }

    await context.bot.send_invoice(
        chat_id=user_id,
        title="Статус Элит",
        description="Элит статус НАВСЕГДА!\n"
                    "• Ежедневный бонус: 2500 коинов\n"
                    "• Ускорители: 60 в день\n"
                    "• Особый статус",
        payload=invoice_id,
        provider_token="",
        currency="XTR",
        prices=[{"label": "Элит статус", "amount": ELITE_PRICE}],
        start_parameter="donate_elite"
    )


@rate_limit(2)
async def buy_deluxe_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ensure_user(user_id)

    invoice_id = f"deluxe_{user_id}_{int(time.time())}"

    pending_invoices[invoice_id] = {
        "user_id": user_id,
        "stars": DELUXE_PRICE,
        "type": "deluxe",
        "timestamp": time.time()
    }

    await context.bot.send_invoice(
        chat_id=user_id,
        title="Статус Делюкс",
        description="Делюкс статус НАВСЕГДА!\n"
                    "• Ежедневный бонус: 5000 коинов\n"
                    "• Ускорители: 100 в день\n"
                    "• Премиум статус\n"
                    "• Все бонусы Элит",
        payload=invoice_id,
        provider_token="",
        currency="XTR",
        prices=[{"label": "Делюкс статус", "amount": DELUXE_PRICE}],
        start_parameter="donate_deluxe"
    )


async def pre_checkout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    invoice_id = query.invoice_payload

    if invoice_id in pending_invoices:
        await query.answer(ok=True)
    else:
        await query.answer(ok=False, error_message="❌ Счет не найден. Попробуйте снова.")


async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    user_id = message.from_user.id
    ensure_user(user_id)

    telegram_payment_id = message.successful_payment.telegram_payment_charge_id
    invoice_id = message.successful_payment.invoice_payload
    stars = message.successful_payment.total_amount

    if invoice_id not in pending_invoices:
        await message.reply_text("❌ Ошибка: счет не найден. Обратитесь к администратору.")
        return

    invoice_data = pending_invoices[invoice_id]

    if invoice_data["type"] == "coins":
        coins = invoice_data["coins"]
        add_balance(user_id, coins)
        add_xp(user_id, coins // 100)

        user_donations[user_id]["total_stars"] += stars
        user_donations[user_id]["total_coins"] += coins
        user_donations[user_id]["transactions"].append({
            "id": telegram_payment_id,
            "invoice_id": invoice_id,
            "type": "coins",
            "stars": stars,
            "coins": coins,
            "timestamp": datetime.now().isoformat(),
            "refunded": False
        })

        await message.reply_text(
            f"✅ ОПЛАТА УСПЕШНА!\n\n"
            f"Транзакция: `{telegram_payment_id}`\n"
            f"Звезд: {stars}\n"
            f"Получено коинов: {coins:,}\n"
            f"Баланс: {format_balance(user_id)}\n\n"
            f"Сохраните ID транзакции для возврата звёзд!",
            parse_mode="Markdown",
            reply_markup=main_keyboard()
        )

    elif invoice_data["type"] == "elite":
        user_premium[user_id] = {
            "type": "elite",
            "expires": None,
            "purchased_at": datetime.now().isoformat()
        }

        user_donations[user_id]["total_stars"] += stars
        user_donations[user_id]["transactions"].append({
            "id": telegram_payment_id,
            "invoice_id": invoice_id,
            "type": "elite",
            "stars": stars,
            "timestamp": datetime.now().isoformat(),
            "refunded": False
        })

        await message.reply_text(
            f"✨ ПОЗДРАВЛЯЕМ!\n\n"
            f"Транзакция: `{telegram_payment_id}`\n"
            f"Вам выдан статус ЭЛИТ навсегда!\n\n"
            f"Сохраните ID транзакции для возврата звёзд!",
            parse_mode="Markdown",
            reply_markup=main_keyboard()
        )

    elif invoice_data["type"] == "deluxe":
        user_premium[user_id] = {
            "type": "deluxe",
            "expires": None,
            "purchased_at": datetime.now().isoformat()
        }

        user_donations[user_id]["total_stars"] += stars
        user_donations[user_id]["transactions"].append({
            "id": telegram_payment_id,
            "invoice_id": invoice_id,
            "type": "deluxe",
            "stars": stars,
            "timestamp": datetime.now().isoformat(),
            "refunded": False
        })

        await message.reply_text(
            f"💎 ПОЗДРАВЛЯЕМ!\n\n"
            f"Транзакция: `{telegram_payment_id}`\n"
            f"Вам выдан статус ДЕЛЮКС навсегда!\n\n"
            f"Сохраните ID транзакции для возврата звёзд!",
            parse_mode="Markdown",
            reply_markup=main_keyboard()
        )

    del pending_invoices[invoice_id]
    save_data()


@rate_limit(2)
async def donate_history_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ensure_user(user_id)

    if not user_donations[user_id]["transactions"]:
        await update.message.reply_text("📭 У вас пока нет донат-транзакций.")
        return

    text = "📊 ИСТОРИЯ ПОКУПОК:\n\n"

    for tx in reversed(user_donations[user_id]["transactions"][-10:]):
        status = "✅ ВОЗВРАЩЕН" if tx.get("refunded", False) else "💎 КУПЛЕНО"

        if tx["type"] == "coins":
            text += f"💰 Коины\n"
            text += f"   ⭐ {tx['stars']} → {tx['coins']:,} коинов\n"
        elif tx["type"] == "elite":
            text += f"✨ Статус Элит\n"
            text += f"   ⭐ {tx['stars']}\n"
        elif tx["type"] == "deluxe":
            text += f"💎 Статус Делюкс\n"
            text += f"   ⭐ {tx['stars']}\n"

        text += f"   ID: {tx['id']}\n"
        text += f"   Дата: {tx['timestamp'][:10]} {status}\n\n"

    text += "🔹 ДЛЯ ВОЗВРАТА ЗВЁЗД ИСПОЛЬЗУЙ:\n"
    text += "/refund <код_транзакции>\n"
    text += "⚠️ Звёзды вернутся на ваш счёт в Telegram!"

    await update.message.reply_text(text)


@rate_limit(2)
async def refund_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ensure_user(user_id)

    args = context.args
    if not args:
        await update.message.reply_text(
            "💳 ВОЗВРАТ ЗВЁЗД\n\n"
            "Используй: /refund <код_транзакции>\n"
            "Пример: /refund 12345678901234567890\n\n"
            "Код транзакции можно найти в /donate_history\n\n"
            "⚠️ ВНИМАНИЕ:\n"
            "• Звёзды вернутся НА ВАШ СЧЁТ В TELEGRAM\n"
            "• Коины/статус будут списаны\n"
            "• Возврат возможен в течение 7 дней"
        )
        return

    transaction_id = args[0]

    found = False
    for tx in user_donations[user_id]["transactions"]:
        if tx["id"] == transaction_id and not tx["refunded"]:
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
                        await context.bot.refund_star_payment(
                            user_id=user_id,
                            telegram_payment_charge_id=transaction_id
                        )
                        refund_message = f"✅ Звёзды ({tx['stars']} ⭐) ВОЗВРАЩЕНЫ на ваш счёт в Telegram!"
                    except Exception as e:
                        logger.error(f"Ошибка возврата звёзд: {e}")
                        refund_message = f"⚠️ Ошибка возврата звёзд. Обратитесь к администратору с кодом: {transaction_id}"

                    await update.message.reply_text(
                        f"✅ ВОЗВРАТ ОФОРМЛЕН!\n\n"
                        f"Транзакция: `{transaction_id}`\n"
                        f"Возвращено звёзд: {tx['stars']}\n"
                        f"Списано коинов: {coins_returned:,}\n"
                        f"Новый баланс: {format_balance(user_id)}\n\n"
                        f"{refund_message}",
                        parse_mode="Markdown"
                    )
                    save_data()
                else:
                    await update.message.reply_text(
                        "❌ НЕДОСТАТОЧНО КОИНОВ ДЛЯ ВОЗВРАТА!\n\n"
                        f"Нужно: {coins_returned:,} коинов\n"
                        f"У вас: {format_balance(user_id)}\n\n"
                        "Потратьте меньше коинов и попробуйте снова."
                    )

            elif tx["type"] in ["elite", "deluxe"]:
                if user_premium[user_id]["type"] == tx["type"]:
                    user_premium[user_id]["type"] = None
                    tx["refunded"] = True
                    tx["refunded_at"] = datetime.now().isoformat()
                    user_donations[user_id]["total_stars"] -= tx["stars"]

                    try:
                        await context.bot.refund_star_payment(
                            user_id=user_id,
                            telegram_payment_charge_id=transaction_id
                        )
                        refund_message = f"✅ Звёзды ({tx['stars']} ⭐) ВОЗВРАЩЕНЫ на ваш счёт в Telegram!"
                    except Exception as e:
                        logger.error(f"Ошибка возврата звёзд: {e}")
                        refund_message = f"⚠️ Ошибка возврата звёзд. Обратитесь к администратору с кодом: {transaction_id}"

                    status_name = "Элит" if tx["type"] == "elite" else "Делюкс"
                    await update.message.reply_text(
                        f"✅ ВОЗВРАТ ОФОРМЛЕН!\n\n"
                        f"Транзакция: `{transaction_id}`\n"
                        f"Возвращено звёзд: {tx['stars']}\n"
                        f"Статус '{status_name}' снят\n\n"
                        f"{refund_message}",
                        parse_mode="Markdown"
                    )
                    save_data()
                else:
                    await update.message.reply_text(
                        "❌ НЕВОЗМОЖНО ВЕРНУТЬ СТАТУС!\n\n"
                        "Статус был изменен или уже возвращен."
                    )
            break

    if not found:
        await update.message.reply_text(
            "❌ ТРАНЗАКЦИЯ НЕ НАЙДЕНА ИЛИ УЖЕ ВОЗВРАЩЕНА!\n\n"
            "Проверьте код транзакции в истории покупок:\n"
            "/donate_history"
        )


# ---------------- КОМАНДЫ ДЛЯ ПРОМОКОДОВ ----------------
async def createpromo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not (is_admin(user_id) or has_rank(user_id, "Admin")):
        await update.message.reply_text("❌ Только админы могут создавать промокоды")
        return

    args = context.args
    if len(args) < 3:
        await update.message.reply_text(
            "🎟️ СОЗДАНИЕ ПРОМОКОДА:\n\n"
            "/createpromo <m/u> <сумма> <кол-во активаций> <код (опционально)>\n\n"
            "m - монеты\nu - ускорители\n\n"
            "Примеры:\n/createpromo m 1000 10\n/createpromo u 50 5 GIFT2024"
        )
        return

    promo_type = args[0].lower()
    if promo_type not in ['m', 'u']:
        await update.message.reply_text("❌ Тип должен быть 'm' (монеты) или 'u' (ускорители)")
        return

    if not args[1].isdigit() or not args[2].isdigit():
        await update.message.reply_text("❌ Сумма и количество активаций должны быть числами")
        return

    amount = int(args[1])
    activations = int(args[2])

    if len(args) >= 4:
        promo_code = args[3].upper()
        if promo_code in promo_codes:
            await update.message.reply_text("❌ Такой промокод уже существует")
            return
    else:
        promo_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

    promo_codes[promo_code] = {
        "type": promo_type,
        "amount": amount,
        "activations": activations,
        "max_activations": activations,
        "used_by": set(),
        "created_by": user_id,
        "created_at": datetime.now().isoformat()
    }

    await update.message.reply_text(
        f"✅ Промокод создан!\n\nКод: {promo_code}\n"
        f"Тип: {'Монеты' if promo_type == 'm' else 'Ускорители'}\n"
        f"Сумма: {amount:,}\nАктиваций: {activations}"
    )

    save_data()


async def process_promo_code(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, promo_code: str):
    if promo_code not in promo_codes:
        await update.message.reply_text("❌ Неверный или несуществующий промокод")
        return

    promo = promo_codes[promo_code]

    if isinstance(promo["used_by"], list):
        promo["used_by"] = set(promo["used_by"])

    if len(promo["used_by"]) >= promo["max_activations"]:
        await update.message.reply_text("❌ Промокод уже использовал максимальное количество раз")
        return

    if user_id in promo["used_by"]:
        await update.message.reply_text("❌ Вы уже активировали этот промокод")
        return

    promo["used_by"].add(user_id)

    if promo["type"] == 'm':
        add_balance(user_id, promo["amount"])
        reward_text = f"{promo['amount']:,} монет"
    else:
        add_accelerator(user_id, promo["amount"])
        reward_text = f"{promo['amount']:,} ускорителей"

    remaining = promo["max_activations"] - len(promo["used_by"])

    await update.message.reply_text(
        f"✅ Промокод активирован!\n\nВы получили: {reward_text}\n"
        f"Код: {promo_code}\nОсталось активаций: {remaining}\n\n"
        f"Баланс: {format_balance(user_id)}\nУскорителей: {user_accelerators.get(user_id, 0)}"
    )

    save_data()


# ---------------- ОСНОВНЫЕ КОМАНДЫ ----------------
@rate_limit(1)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ensure_user(user_id)

    daily_bonus, daily_acc = get_daily_bonus(user_id)

    await update.message.reply_text(
        f"ДОБРО ПОЖАЛОВАТЬ В БОТ-ИГРУ!\n\n"
        f"Статус: {get_user_status(user_id)}\n"
        f"Баланс: {format_balance(user_id)}\n"
        f"Ускорители: {user_accelerators.get(user_id, 0)}\n\n"
        f"Ежедневный бонус: /daily (+{daily_bonus:,} монет, +{daily_acc} ускорителей)\n\n"
        f"Короткие команды:\n"
        f"• б или Баланс - показать баланс\n"
        f"• я - показать профиль\n\n"
        f"Используйте меню для навигации:",
        reply_markup=main_keyboard()
    )


@rate_limit(1)
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "ПОЛНАЯ ИНСТРУКЦИЯ\n\n"
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
        "• Мини-игра - /mini <сумма> (5×5, ×1.3 за клетку)\n"
        "• Рулетка - /roulette <сумма> (x36)\n"
        "• Простая рулетка - /rsimple <сумма> (красное/черное, x2)\n\n"
        "РУДНИК:\n"
        "• Автоматическая добыча ресурсов\n• 3 ресурса/сек\n• Улучшение для более ценных ресурсов\n\n"
        "БИЗНЕС:\n"
        "• Пассивный доход\n• Разные уровни бизнеса\n\n"
        "БАНК:\n"
        "• /bank <сумма> - положить\n• /bank w <сумма> - снять\n\n"
        "ДОНАТ (Telegram Stars):\n"
        "• /buy_coins <звезды> - купить коины\n"
        "• /buy_elite - купить Элит (50 ⭐)\n"
        "• /buy_deluxe - купить Делюкс (99 ⭐)\n"
        "• /donate_history - история покупок\n"
        "• /refund - ВОЗВРАТ ЗВЁЗД\n\n"
        "ПРОМОКОДЫ:\n"
        "• Введите #промокод для активации\n• Например: #WELCOME2024\n\n"
        "ПЕРЕВОД:\n"
        "• /givemoney <@user> <сумма>\n\n"
        "КОРОТКИЕ КОМАНДЫ:\n"
        "• б - баланс\n• я - профиль\n\n"
        "АДМИН КОМАНДЫ:\n"
        "• /chance <ID> <0-100> - установить сложность мини-игры"
    )
    await update.message.reply_text(help_text, reply_markup=main_keyboard())


@rate_limit(5)
async def daily_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ensure_user(user_id)

    now = datetime.now()

    if user_id in daily_used and daily_used[user_id]:
        last = daily_used[user_id]
        if now - last < timedelta(hours=DAILY_HOURS):
            remaining = timedelta(hours=DAILY_HOURS) - (now - last)
            hours = remaining.seconds // 3600
            minutes = (remaining.seconds % 3600) // 60
            await update.message.reply_text(
                f"⏳ Ещё рано!\nСледующий бонус через: {hours}ч {minutes}м",
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

    await update.message.reply_text(
        f"🎁 ЕЖЕДНЕВНЫЙ БОНУС!\n\n"
        f"Монеты: +{daily_bonus:,}\n"
        f"Ускорители: +{daily_acc}\n"
        f"Баланс: {format_balance(user_id)}\n"
        f"Всего ускорителей: {user_accelerators.get(user_id, 0)}",
        reply_markup=main_keyboard()
    )

    save_data()


@rate_limit(1)
async def bet_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ensure_user(user_id)

    args = context.args
    if len(args) != 1 or not args[0].isdigit():
        await update.message.reply_text(
            "Используй: /bet <сумма>\nПример: /bet 100",
            reply_markup=games_keyboard()
        )
        return

    amount = int(args[0])
    if amount <= 0:
        await update.message.reply_text("❌ Сумма должна быть больше 0!", reply_markup=games_keyboard())
        return

    if not can_spend(user_id, amount):
        await update.message.reply_text(
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
        result = f"🎉 ПОБЕДА! +{amount:,} монет"
    else:
        if not infinite_user:
            spend_balance(user_id, amount)
        result = f"💔 ПРОИГРЫШ -{amount:,} монет"

    await update.message.reply_text(
        f"{result}\nБаланс: {format_balance(user_id)}",
        reply_markup=games_keyboard()
    )

    save_data()


@rate_limit(1)
async def coin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ensure_user(user_id)
    result = random.choice(['Орёл', 'Решка'])
    await update.message.reply_text(
        f"🪙 {result}\nБаланс: {format_balance(user_id)}",
        reply_markup=games_keyboard()
    )


# ---------------- АДМИН КОМАНДЫ ----------------
@rate_limit(1)
async def money_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not (is_admin(user_id) or has_rank(user_id, "Admin")):
        await update.message.reply_text("❌ Только админы могут использовать эту команду")
        return

    args = context.args

    if not args:
        await update.message.reply_text(
            "💰 ИСПОЛЬЗОВАНИЕ:\n"
            "/money <сумма> - выдать себе\n"
            "/money <user> <сумма> - выдать пользователю\n"
            "Ответ на сообщение + /money <сумма> - выдать ответившему"
        )
        return

    try:
        if update.message.reply_to_message:
            if len(args) == 1 and args[0].isdigit():
                target_user = update.message.reply_to_message.from_user
                target_id = target_user.id
                amount = int(args[0])
                ensure_user(target_id)
                if not has_infinite_balance(target_id):
                    add_balance(target_id, amount)
                await update.message.reply_text(
                    f"✅ Выдано {amount:,} монет пользователю {target_user.first_name}",
                    reply_markup=main_keyboard()
                )
                save_data()
                return

        if len(args) == 1 and args[0].isdigit():
            amount = int(args[0])
            ensure_user(user_id)
            if not has_infinite_balance(user_id):
                add_balance(user_id, amount)
            await update.message.reply_text(
                f"✅ Вы получили {amount:,} монет\nБаланс: {format_balance(user_id)}",
                reply_markup=main_keyboard()
            )
            save_data()
            return

        if len(args) >= 2 and args[1].isdigit():
            target = args[0]
            amount = int(args[1])

            try:
                if target.startswith('@'):
                    chat = await context.bot.get_chat(target)
                    target_id = chat.id
                else:
                    target_id = int(target)

                ensure_user(target_id)
                if not has_infinite_balance(target_id):
                    add_balance(target_id, amount)

                await update.message.reply_text(
                    f"✅ Выдано {amount:,} монет пользователю {target}",
                    reply_markup=main_keyboard()
                )
                save_data()
                return
            except:
                await update.message.reply_text("❌ Не удалось найти пользователя", reply_markup=main_keyboard())
                return

    except Exception as e:
        logger.error(f"Ошибка в money_cmd: {e}")
        await update.message.reply_text("❌ Ошибка выполнения команды", reply_markup=main_keyboard())


@rate_limit(1)
async def setmoney_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not (is_admin(user_id) or has_rank(user_id, "Admin")):
        await update.message.reply_text("❌ Только админы могут использовать эту команду")
        return

    args = context.args
    try:
        if update.message.reply_to_message and len(args) == 1 and args[0].isdigit():
            target_id = update.message.reply_to_message.from_user.id
            amount = int(args[0])
            ensure_user(target_id)
            user_balances[target_id] = amount
            await update.message.reply_text(f"✅ Баланс пользователя установлен на {amount:,}")
            save_data()
            return

        if len(args) >= 2 and args[1].isdigit():
            target = args[0]
            amount = int(args[1])

            try:
                if target.startswith('@'):
                    chat = await context.bot.get_chat(target)
                    target_id = chat.id
                else:
                    target_id = int(target)

                ensure_user(target_id)
                user_balances[target_id] = amount
                await update.message.reply_text(f"✅ Баланс пользователя {target} установлен на {amount:,}")
                save_data()
                return
            except:
                await update.message.reply_text("❌ Не удалось найти пользователя")
                return
    except Exception as e:
        logger.error(f"Ошибка в setmoney_cmd: {e}")
        await update.message.reply_text("❌ Ошибка выполнения команды")


@rate_limit(1)
async def inf_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not (is_admin(user_id) or has_rank(user_id, "Admin")):
        await update.message.reply_text("❌ Только админы могут использовать эту команду")
        return

    try:
        if update.message.reply_to_message:
            target_id = update.message.reply_to_message.from_user.id
            set_infinite_balance(target_id)
            await update.message.reply_text("∞ Пользователю выдан бесконечный баланс")
            save_data()
            return

        args = context.args
        if args:
            target = args[0]
            try:
                if target.startswith('@'):
                    chat = await context.bot.get_chat(target)
                    target_id = chat.id
                else:
                    target_id = int(target)

                set_infinite_balance(target_id)
                await update.message.reply_text(f"∞ Пользователю {target} выдан бесконечный баланс")
                save_data()
                return
            except:
                await update.message.reply_text("❌ Не удалось найти пользователя")
                return
    except Exception as e:
        logger.error(f"Ошибка в inf_cmd: {e}")
        await update.message.reply_text("❌ Ошибка выполнения команды")


@rate_limit(1)
async def removeinf_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not (is_admin(user_id) or has_rank(user_id, "Admin")):
        await update.message.reply_text("❌ Только админы могут использовать эту команду")
        return

    try:
        if update.message.reply_to_message:
            target_id = update.message.reply_to_message.from_user.id
            remove_infinite_balance(target_id)
            await update.message.reply_text("∞ Бесконечный баланс снят")
            save_data()
            return

        args = context.args
        if args:
            target = args[0]
            try:
                if target.startswith('@'):
                    chat = await context.bot.get_chat(target)
                    target_id = chat.id
                else:
                    target_id = int(target)

                remove_infinite_balance(target_id)
                await update.message.reply_text(f"∞ Бесконечный баланс снят у пользователя {target}")
                save_data()
                return
            except:
                await update.message.reply_text("❌ Не удалось найти пользователя")
                return
    except Exception as e:
        logger.error(f"Ошибка в removeinf_cmd: {e}")
        await update.message.reply_text("❌ Ошибка выполнения команды")


@rate_limit(1)
async def rank_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ Только главные админы могут выдавать ранги")
        return

    args = context.args
    try:
        if update.message.reply_to_message and len(args) >= 1:
            rank_type = args[0].lower()
            if rank_type not in ["admin", "moderator", "elite", "deluxe"]:
                await update.message.reply_text("Доступные ранги: Admin, moderator, elite, deluxe")
                return
            target_id = update.message.reply_to_message.from_user.id

            if rank_type in ["elite", "deluxe"]:
                user_premium[target_id] = {"type": rank_type, "expires": None,
                                           "purchased_at": datetime.now().isoformat()}
                await update.message.reply_text(f"👑 Пользователь теперь {rank_type.capitalize()}!")
            else:
                ranks[target_id] = rank_type.capitalize()
                await update.message.reply_text(f"👑 Пользователь теперь {rank_type.capitalize()}!")

            save_data()
            return

        if len(args) >= 2:
            rank_type = args[0].lower()
            if rank_type not in ["admin", "moderator", "elite", "deluxe"]:
                await update.message.reply_text("Доступные ранги: Admin, moderator, elite, deluxe")
                return
            target = args[1]
            try:
                if target.startswith('@'):
                    chat = await context.bot.get_chat(target)
                    target_id = chat.id
                else:
                    target_id = int(target)

                if rank_type in ["elite", "deluxe"]:
                    user_premium[target_id] = {"type": rank_type, "expires": None,
                                               "purchased_at": datetime.now().isoformat()}
                    await update.message.reply_text(f"👑 Пользователь {target} теперь {rank_type.capitalize()}!")
                else:
                    ranks[target_id] = rank_type.capitalize()
                    await update.message.reply_text(f"👑 Пользователь {target} теперь {rank_type.capitalize()}!")

                save_data()
                return
            except:
                await update.message.reply_text("❌ Не удалось найти пользователя")
                return
    except Exception as e:
        logger.error(f"Ошибка в rank_cmd: {e}")
        await update.message.reply_text("❌ Ошибка выполнения команды")


@rate_limit(1)
async def unrank_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ Только главные админы могут снимать ранги")
        return

    try:
        if update.message.reply_to_message:
            target_id = update.message.reply_to_message.from_user.id
            if target_id in ranks:
                old_rank = ranks.pop(target_id)
                await update.message.reply_text(f"👑 Ранг '{old_rank}' снят")
                save_data()
                return
            elif user_premium.get(target_id, {}).get("type"):
                old_type = user_premium[target_id]["type"]
                user_premium[target_id]["type"] = None
                await update.message.reply_text(f"👑 Статус '{old_type}' снят")
                save_data()
                return
            await update.message.reply_text("ℹ️ Пользователь не имеет ранга/статуса")
            return

        args = context.args
        if args:
            target = args[0]
            try:
                if target.startswith('@'):
                    chat = await context.bot.get_chat(target)
                    target_id = chat.id
                else:
                    target_id = int(target)

                if target_id in ranks:
                    old_rank = ranks.pop(target_id)
                    await update.message.reply_text(f"👑 Ранг '{old_rank}' снят у пользователя {target}")
                    save_data()
                    return
                elif user_premium.get(target_id, {}).get("type"):
                    old_type = user_premium[target_id]["type"]
                    user_premium[target_id]["type"] = None
                    await update.message.reply_text(f"👑 Статус '{old_type}' снят у пользователя {target}")
                    save_data()
                    return
                await update.message.reply_text(f"ℹ️ Пользователь {target} не имеет ранга/статуса")
                return
            except:
                await update.message.reply_text("❌ Не удалось найти пользователя")
                return
    except Exception as e:
        logger.error(f"Ошибка в unrank_cmd: {e}")
        await update.message.reply_text("❌ Ошибка выполнения команды")


@rate_limit(1)
async def givemoney_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ensure_user(user_id)

    args = context.args
    try:
        if update.message.reply_to_message and len(args) == 1 and args[0].isdigit():
            target_id = update.message.reply_to_message.from_user.id
            amount = int(args[0])
            if amount <= 0:
                await update.message.reply_text("❌ Сумма должна быть больше 0")
                return
            if not can_spend(user_id, amount):
                await update.message.reply_text("❌ Недостаточно монет")
                return
            spend_balance(user_id, amount)
            add_balance(target_id, amount)
            await update.message.reply_text(f"✅ Вы перевели {amount:,} монет")
            save_data()
            return

        if len(args) >= 2 and args[1].isdigit():
            target = args[0]
            amount = int(args[1])
            if amount <= 0:
                await update.message.reply_text("❌ Сумма должна быть больше 0")
                return
            if not can_spend(user_id, amount):
                await update.message.reply_text("❌ Недостаточно монет")
                return

            try:
                if target.startswith('@'):
                    chat = await context.bot.get_chat(target)
                    target_id = chat.id
                else:
                    target_id = int(target)

                spend_balance(user_id, amount)
                add_balance(target_id, amount)
                await update.message.reply_text(f"✅ Вы перевели {amount:,} монет пользователю {target}")
                save_data()
                return
            except:
                await update.message.reply_text("❌ Не удалось найти пользователя")
                return
    except Exception as e:
        logger.error(f"Ошибка в givemoney_cmd: {e}")
        await update.message.reply_text("❌ Ошибка выполнения команды")


# ---------------- КОМАНДЫ ДЛЯ ПОКУПКИ БИЗНЕСА ----------------
@rate_limit(1)
async def buybusiness_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ensure_user(user_id)

    args = context.args
    if len(args) != 1:
        await update.message.reply_text(
            "🏢 КУПИТЬ БИЗНЕС\n\n"
            "Используй: /buybusiness <тип>\n\n"
            "Типы:\n• shaurma - Шаурма (100 монет)\n• cafe - Кафе (1000 монет)\n• space - Космическое агентство (1,000,000 монет)"
        )
        return

    business_type = args[0].lower()
    if business_type not in BUSINESS_TYPES:
        await update.message.reply_text("❌ Неизвестный тип бизнеса!")
        return

    if business_data[user_id]["type"]:
        await update.message.reply_text("❌ У вас уже есть бизнес! Сначала продайте его.")
        return

    biz_info = BUSINESS_TYPES[business_type]

    if not can_spend(user_id, biz_info["cost"]):
        await update.message.reply_text(
            f"❌ Недостаточно монет!\nНужно: {biz_info['cost']:,} монет\nУ вас: {format_balance(user_id)}"
        )
        return

    spend_balance(user_id, biz_info["cost"])
    add_xp(user_id, biz_info["cost"] // 50)

    business_data[user_id] = {
        "type": business_type,
        "profit": 0,
        "active": True,
        "last_collect": datetime.now()
    }

    await update.message.reply_text(
        f"✅ Бизнес куплен!\n\n{biz_info['name']}\n"
        f"Цена: {biz_info['cost']:,} монет\n"
        f"Прибыль: {biz_info['base_profit']:,} монет/{biz_info['profit_period']}сек\n"
        f"Баланс: {format_balance(user_id)}",
        reply_markup=main_keyboard()
    )

    save_data()


# ---------------- ТЕКСТОВЫЙ ОБРАБОТЧИК ----------------
@rate_limit(0.5)
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user = update.effective_user
    user_id = user.id
    ensure_user(user_id)

    # ⚡⚡⚡ КОРОТКИЕ КОМАНДЫ ⚡⚡⚡

    # 1️⃣ "я" - ПОЛНЫЙ ПРОФИЛЬ
    if text.lower() == "я":
        profile = user_profiles.get(user_id, {"level": 1, "xp": 0, "next_level_xp": 100})
        status = get_user_status(user_id)

        profile_text = (
            f"👤 ПРОФИЛЬ: {user.first_name}\n"
            f"🆔 ID: {user_id}\n"
            f"👑 Статус: {status}\n\n"
            f"📊 СТАТИСТИКА:\n"
            f"Уровень: {profile['level']}\n"
            f"Опыт: {profile['xp']:,}/{profile['next_level_xp']:,}\n"
            f"Баланс: {format_balance(user_id)}\n"
            f"В банке: {format_bank_balance(user_id)}\n"
            f"Ускорители: {user_accelerators.get(user_id, 0)}\n\n"
            f"🏠 ИМУЩЕСТВО:\n"
        )

        if user_id in mine_data:
            mine = mine_data[user_id]
            level_info = MINE_LEVELS[mine["level"]]
            mine_value = mine["resources"] * level_info["price_per_unit"]
            profile_text += (
                f"⛏️ РУДНИК:\n"
                f"   {level_info['name']}\n"
                f"   Ресурсы: {mine['resources']:,} {level_info['resource']}\n"
                f"   Стоимость: {mine_value:,} монет\n"
            )

        if user_id in business_data and business_data[user_id]["type"]:
            business = business_data[user_id]
            biz_info = BUSINESS_TYPES[business["type"]]
            profile_text += (
                f"🏢 БИЗНЕС:\n"
                f"   {biz_info['name']}\n"
                f"   Прибыль: {business['profit']:,} монет\n"
            )

        await update.message.reply_text(profile_text, reply_markup=main_keyboard())
        return

    # 2️⃣ "б" или "баланс" - БАЛАНС
    if text.lower() in ["б", "баланс"]:
        balance_text = (
            f"💰 ВАШ БАЛАНС\n\n"
            f"Наличные: {format_balance(user_id)}\n"
            f"Ускорители: {user_accelerators.get(user_id, 0)}\n"
            f"В банке: {format_bank_balance(user_id)}\n"
        )
        if has_infinite_balance(user_id):
            balance_text += "✨ Бесконечный баланс активирован!"
        await update.message.reply_text(balance_text, reply_markup=main_keyboard())
        return

    # 3️⃣ Промокоды
    if text.startswith('#'):
        promo_code = text[1:].upper()
        await process_promo_code(update, context, user_id, promo_code)
        return

    # 4️⃣ Навигация
    if text == "Назад в меню":
        await update.message.reply_text("↩️ Главное меню:", reply_markup=main_keyboard())
        return

    # 5️⃣ Обработка кнопок меню
    if text == "Баланс":
        balance_text = (
            f"💰 ВАШ БАЛАНС\n\n"
            f"Наличные: {format_balance(user_id)}\n"
            f"Ускорители: {user_accelerators.get(user_id, 0)}\n"
            f"В банке: {format_bank_balance(user_id)}\n"
        )
        if has_infinite_balance(user_id):
            balance_text += "✨ Бесконечный баланс активирован!"
        await update.message.reply_text(balance_text, reply_markup=main_keyboard())
        return

    if text == "Профиль":
        await update.message.reply_text(
            "👤 ВАШ ПРОФИЛЬ\n\nВыберите действие:",
            reply_markup=profile_keyboard()
        )
        return

    if text == "Статистика":
        profile = user_profiles.get(user_id, {"level": 1, "xp": 0, "next_level_xp": 100})
        status = get_user_status(user_id)

        stats_text = (
            f"👤 ПРОФИЛЬ: {user.first_name}\n"
            f"🆔 ID: {user_id}\n"
            f"👑 Статус: {status}\n\n"
            f"📊 СТАТИСТИКА:\n"
            f"Уровень: {profile['level']}\n"
            f"Опыт: {profile['xp']:,}/{profile['next_level_xp']:,}\n"
            f"Баланс: {format_balance(user_id)}\n"
            f"В банке: {format_bank_balance(user_id)}\n"
            f"Ускорители: {user_accelerators.get(user_id, 0)}\n"
        )

        await update.message.reply_text(stats_text, reply_markup=profile_keyboard())
        return

    if text == "Имущество":
        assets_text = "🏠 ВАШЕ ИМУЩЕСТВО:\n\n"

        if user_id in mine_data:
            mine = mine_data[user_id]
            level_info = MINE_LEVELS[mine["level"]]
            mine_value = mine["resources"] * level_info["price_per_unit"]
            assets_text += (
                f"⛏️ РУДНИК:\n"
                f"   {level_info['name']} (Уровень {mine['level'] + 1})\n"
                f"   Ресурсы: {mine['resources']:,} {level_info['resource']}\n"
                f"   Стоимость: {mine_value:,} монет\n"
                f"   Авто-сбор: {'Вкл' if mine['auto_collect'] else 'Выкл'}\n\n"
            )

        if user_id in business_data and business_data[user_id]["type"]:
            business = business_data[user_id]
            biz_info = BUSINESS_TYPES[business["type"]]
            business_value = biz_info["cost"] // 2 + business["profit"]
            assets_text += (
                f"🏢 БИЗНЕС:\n"
                f"   {biz_info['name']}\n"
                f"   Прибыль: {business['profit']:,} монет\n"
                f"   Стоимость: {business_value:,} монет\n\n"
            )

        assets_text += f"🏦 БАНК: {format_bank_balance(user_id)} монет\n"

        await update.message.reply_text(assets_text, reply_markup=profile_keyboard())
        return

    if text == "Работа":
        if not can_work(user_id):
            await update.message.reply_text(
                "❌ У вас закончились ускорители!\nПолучите ускорители через /daily или промокоды.",
                reply_markup=main_keyboard()
            )
            return
        await update.message.reply_text("💼 Выберите работу:", reply_markup=jobs_keyboard())
        return

    if text in ["Курьер", "Таксист", "Программист"]:
        if not can_work(user_id):
            await update.message.reply_text("❌ Нет ускорителей!", reply_markup=jobs_keyboard())
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

        await update.message.reply_text(
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
        await update.message.reply_text("🎮 ВЫБЕРИТЕ ИГРУ:", reply_markup=games_keyboard())
        return

    if text == "Казино":
        await update.message.reply_text(
            "🎰 КАЗИНО\n\nПравила:\n• 50% шанс на выигрыш\n• Выигрыш = ставка × 2\n\nКоманда: /bet <сумма>",
            reply_markup=games_keyboard()
        )
        return

    if text == "Монетка":
        await coin_cmd(update, context)
        return

    if text == "Мини-игра":
        await update.message.reply_text(
            "💣 МИНИ-ИГРА: САПЁР\n\nПравила:\n• Поле 5×5\n• Каждая пустая клетка ×1.3 к выигрышу\n\nИспользуй: /mini <сумма>\nПример: /mini 100",
            reply_markup=games_keyboard()
        )
        return

    if text == "Рулетка":
        await update.message.reply_text(
            "🎰 РУЛЕТКА\n\nПравила:\n• Выберите число от 0 до 36\n• Выигрыш = ставка × 36\n\nКоманда: /roulette <сумма>",
            reply_markup=games_keyboard()
        )
        return

    if text == "Донат":
        await donate_cmd(update, context)
        return

    if text in ["Купить Элит (50 ⭐)", "Купить Делюкс (99 ⭐)"]:
        if text == "Купить Элит (50 ⭐)":
            await buy_elite_cmd(update, context)
        else:
            await buy_deluxe_cmd(update, context)
        return

    if text == "Купить коины":
        await update.message.reply_text(
            "💰 ПОКУПКА КОИНОВ\n\n"
            "Используйте: /buy_coins <количество_звезд>\n"
            f"1 ⭐ = {STAR_TO_COINS:,} коинов\n\n"
            "Пример: /buy_coins 10"
        )
        return

    if text == "Банк":
        await bank_cmd(update, context)
        return

    if text in ["Внести", "Снять"]:
        action = "положить" if text == "Внести" else "снять"
        cmd = "/bank" if text == "Внести" else "/bank w"
        await update.message.reply_text(
            f"🏦 БАНК - {action.upper()}\n\nИспользуйте: {cmd} <сумма>\nПример: {cmd} 1000"
        )
        return

    if text == "Бизнес":
        if user_id not in business_data:
            ensure_user(user_id)

        business = business_data[user_id]
        if business["type"]:
            biz_info = BUSINESS_TYPES[business["type"]]
            profit_text = (
                f"🏢 ВАШ БИЗНЕС:\n\n"
                f"Название: {biz_info['name']}\n"
                f"Прибыль: {business['profit']:,} монет\n"
                f"Активен: {'Да' if business['active'] else 'Нет'}\n"
                f"Прибыль/период: {biz_info['base_profit']:,} монет\n"
                f"Период: {biz_info['profit_period']} сек"
            )
        else:
            profit_text = "🏢 У вас нет бизнеса! Купите в меню."

        await update.message.reply_text(profit_text, reply_markup=business_keyboard())
        return

    if text == "Купить бизнес":
        biz_list = "🏢 ДОСТУПНЫЕ БИЗНЕСЫ:\n\n"
        for biz_id, biz_info in BUSINESS_TYPES.items():
            biz_list += (
                f"• {biz_info['name']}\n"
                f"  Цена: {biz_info['cost']:,} монет\n"
                f"  Прибыль: {biz_info['base_profit']:,}/{biz_info['profit_period']}сек\n"
                f"  Купить: /buybusiness {biz_id}\n\n"
            )
        await update.message.reply_text(biz_list, reply_markup=business_keyboard())
        return

    if text == "Собрать прибыль":
        if user_id not in business_data or not business_data[user_id]["type"]:
            await update.message.reply_text("❌ У вас нет бизнеса!", reply_markup=business_keyboard())
            return

        business = business_data[user_id]
        if not business["active"]:
            await update.message.reply_text("❌ Бизнес не активен!", reply_markup=business_keyboard())
            return

        profit = business["profit"]
        if profit > 0:
            add_balance(user_id, profit)
            add_xp(user_id, profit // 100)
            business["profit"] = 0
            business["last_collect"] = datetime.now()
            await update.message.reply_text(
                f"💰 Собрано прибыли: {profit:,} монет!\nБаланс: {format_balance(user_id)}",
                reply_markup=business_keyboard()
            )
            save_data()
        else:
            await update.message.reply_text("ℹ️ Пока нет прибыли для сбора.", reply_markup=business_keyboard())
        return

    if text == "Продать бизнес":
        if user_id not in business_data or not business_data[user_id]["type"]:
            await update.message.reply_text("❌ У вас нет бизнеса!", reply_markup=business_keyboard())
            return

        business = business_data[user_id]
        biz_info = BUSINESS_TYPES[business["type"]]
        sell_price = biz_info["cost"] // 2
        total_received = sell_price + business["profit"]

        add_balance(user_id, total_received)
        add_xp(user_id, total_received // 50)

        await update.message.reply_text(
            f"💼 Бизнес продан!\n\n"
            f"{biz_info['name']}\n"
            f"Стоимость: {sell_price:,} монет\n"
            f"Прибыль: {business['profit']:,} монет\n"
            f"Всего: {total_received:,} монет\n"
            f"Баланс: {format_balance(user_id)}",
            reply_markup=business_keyboard()
        )

        business_data[user_id] = {"type": None, "profit": 0, "active": False, "last_collect": None}
        save_data()
        return

    if text == "Рудник":
        mine_info = get_mine_info(user_id)
        await update.message.reply_text(mine_info, reply_markup=mine_keyboard())
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
            await update.message.reply_text(
                f"💰 Ресурсы собраны!\n"
                f"Добыто: {mine['resources']:,} {level_info['resource']}\n"
                f"Получено: {total:,} монет\n"
                f"Баланс: {format_balance(user_id)}",
                reply_markup=mine_keyboard()
            )
            mine["resources"] = 0
            save_data()
        else:
            await update.message.reply_text("ℹ️ Нет ресурсов для сбора.", reply_markup=mine_keyboard())
        return

    if text == "Улучшить рудник":
        if user_id not in mine_data:
            ensure_user(user_id)
        mine = mine_data[user_id]
        if mine["level"] >= 2:
            await update.message.reply_text("🎉 Рудник максимального уровня!", reply_markup=mine_keyboard())
            return

        next_level = mine["level"] + 1
        upgrade_cost = MINE_LEVELS[next_level]["upgrade_cost"]

        if not can_spend(user_id, upgrade_cost):
            await update.message.reply_text(
                f"❌ Недостаточно монет!\nНужно: {upgrade_cost:,} монет\nУ вас: {format_balance(user_id)}",
                reply_markup=mine_keyboard()
            )
            return

        spend_balance(user_id, upgrade_cost)
        mine["level"] = next_level
        add_xp(user_id, upgrade_cost // 100)

        new_level_info = MINE_LEVELS[next_level]
        await update.message.reply_text(
            f"🎉 Рудник улучшен!\n\n"
            f"Новый уровень: {new_level_info['name']}\n"
            f"Ресурс: {new_level_info['resource']}\n"
            f"Цена за единицу: {new_level_info['price_per_unit']} монет\n"
            f"Баланс: {format_balance(user_id)}",
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
        await update.message.reply_text(f"⚡ Авто-сбор ресурсов {status}!", reply_markup=mine_keyboard())
        save_data()
        return

    if text == "Админ":
        if is_admin(user_id):
            admin_text = (
                "👑 АДМИН ПАНЕЛЬ\n\n"
                "/money - выдать монеты\n"
                "/setmoney - установить баланс\n"
                "/rank - выдать ранг (admin/moderator/elite/deluxe)\n"
                "/unrank - снять ранг\n"
                "/inf - бесконечный баланс\n"
                "/removeinf - снять бесконечность\n"
                "/createpromo - создать промокод\n"
                "/chance - установить сложность мини-игры"
            )
        elif has_rank(user_id, "Admin") or has_rank(user_id, "moderator"):
            admin_text = "🛡️ ПАНЕЛЬ МОДЕРАТОРА\n\n/money - выдать монеты (только себе)"
        else:
            admin_text = "❌ У вас нет админ прав"

        await update.message.reply_text(admin_text, reply_markup=main_keyboard())
        return

    if text == "Помощь":
        await help_cmd(update, context)
        return


# ---------------- ФОНОВЫЕ ЗАДАЧИ ----------------
async def background_tasks(context: ContextTypes.DEFAULT_TYPE):
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

        if random.random() < 0.0167:
            save_data()

    except Exception as e:
        logger.error(f"Ошибка в фоновых задачах: {e}")


# ---------------- ЗАПУСК БОТА ----------------
def main():
    load_data()

    app = Application.builder().token(YOUR_BOT_TOKEN).build()

    # Основные команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("daily", daily_cmd))
    app.add_handler(CommandHandler("buybusiness", buybusiness_cmd))

    # Игры
    app.add_handler(CommandHandler("bet", bet_cmd))
    app.add_handler(CommandHandler("coin", coin_cmd))
    app.add_handler(CommandHandler("mini", mini_cmd))
    app.add_handler(CommandHandler("roulette", roulette_cmd))
    app.add_handler(CommandHandler("r", roulette_simple_cmd))  # Новая рулетка

    # Банк
    app.add_handler(CommandHandler("bank", bank_cmd))

    # Донат
    app.add_handler(CommandHandler("donate", donate_cmd))
    app.add_handler(CommandHandler("buy_coins", buy_coins_cmd))
    app.add_handler(CommandHandler("buy_elite", buy_elite_cmd))
    app.add_handler(CommandHandler("buy_deluxe", buy_deluxe_cmd))
    app.add_handler(CommandHandler("donate_history", donate_history_cmd))
    app.add_handler(CommandHandler("refund", refund_cmd))

    # Платежи
    app.add_handler(PreCheckoutQueryHandler(pre_checkout_callback))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))

    # Промокоды
    app.add_handler(CommandHandler("createpromo", createpromo_cmd))

    # Админ команды
    app.add_handler(CommandHandler("money", money_cmd))
    app.add_handler(CommandHandler("setmoney", setmoney_cmd))
    app.add_handler(CommandHandler("rank", rank_cmd))
    app.add_handler(CommandHandler("unrank", unrank_cmd))
    app.add_handler(CommandHandler("inf", inf_cmd))
    app.add_handler(CommandHandler("removeinf", removeinf_cmd))
    app.add_handler(CommandHandler("p", givemoney_cmd))
    app.add_handler(CommandHandler("chance", chance_cmd))

    # Callback обработчики
    app.add_handler(CallbackQueryHandler(mini_callback_handler, pattern="^mini_"))
    app.add_handler(CallbackQueryHandler(roulette_callback_handler, pattern="^roulette_"))
    app.add_handler(CallbackQueryHandler(simple_roulette_callback, pattern="^simple_"))  # Новая рулетка

    # Текстовые сообщения
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    # Фоновые задачи
    job_queue = app.job_queue
    if job_queue:
        job_queue.run_repeating(background_tasks, interval=1, first=1)
        job_queue.run_repeating(auto_save, interval=300, first=300)

    logger.info("✅ БОТ УСПЕШНО ЗАПУЩЕН! НОВАЯ РУЛЕТКА ДОБАВЛЕНА!")
    print("✅ БОТ УСПЕШНО ЗАПУЩЕН! НОВАЯ РУЛЕТКА ДОБАВЛЕНА!")

    try:
        app.run_polling()
    except Exception as e:
        logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")


if __name__ == "__main__":
    main()
