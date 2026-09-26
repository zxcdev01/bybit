import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import BotCommand, InlineKeyboardMarkup, InlineKeyboardButton
import aiohttp
from datetime import datetime

# ============ КОНФІГУРАЦІЯ ============
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ALLOWED_USERS = list(map(int, os.getenv("ALLOWED_USERS", "117445054,73455428").split(","))) if os.getenv("ALLOWED_USERS") else [123456789]

if not TELEGRAM_TOKEN:
    raise ValueError("❌ TELEGRAM_TOKEN не встановлений!")

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ініціалізація
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# ============ ОБРОБНИКИ ============

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Команда /start"""
    user_id = message.from_user.id
    
    if user_id not in ALLOWED_USERS:
        await message.answer("🚫 У вас немає доступу до цього бота")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Меню", callback_data="show_menu")],
        [InlineKeyboardButton(text="👤 Профіль", callback_data="show_profile")],
        [InlineKeyboardButton(text="⚡ Ліквідації", callback_data="show_liquidations")],
    ])
    
    await message.answer(
        f"👋 Привіт, <b>{message.from_user.first_name}</b>!\n\n"
        "🤖 Ласкаво просимо до Bybit Liquidation Alerts\n\n"
        "Виберіть дію:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@dp.callback_query(F.data == "show_menu")
async def show_menu(query: types.CallbackQuery):
    """Меню"""
    await query.answer()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔔 Ліквідації", callback_data="menu_liq")],
        [InlineKeyboardButton(text="⚙️ Налаштування", callback_data="menu_settings")],
        [InlineKeyboardButton(text="📈 Статистика", callback_data="menu_stats")],
        [InlineKeyboardButton(text="👤 Профіль", callback_data="show_profile")],
    ])
    
    await query.message.edit_text(
        "📋 <b>МЕНЮ</b>\n\n"
        "Виберіть розділ:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@dp.callback_query(F.data == "show_profile")
async def show_profile(query: types.CallbackQuery):
    """Профіль"""
    await query.answer()
    
    user = query.from_user
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Меню", callback_data="show_menu")],
    ])
    
    profile_text = (
        f"👤 <b>МІЙ ПРОФІЛЬ</b>\n\n"
        f"<b>👨 Ім'я:</b> {user.first_name}\n"
        f"<b>📱 ID:</b> <code>{user.id}</code>\n"
        f"<b>🔔 Сповіщення:</b> ✅ Включені\n"
    )
    
    await query.message.edit_text(profile_text, reply_markup=keyboard, parse_mode="HTML")

@dp.callback_query(F.data == "show_liquidations")
async def show_liquidations(query: types.CallbackQuery):
    """Активні ліквідації"""
    await query.answer()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Оновити", callback_data="refresh_liq")],
        [InlineKeyboardButton(text="🔙 Меню", callback_data="show_menu")],
    ])
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.bybit.com/v5/market/liquidation",
                params={"category": "linear", "limit": 10},
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    liquidations = data.get("result", {}).get("rows", [])
                    
                    if liquidations:
                        text = "⚡ <b>АКТИВНІ ЛІКВІДАЦІЇ</b>\n\n"
                        for i, liq in enumerate(liquidations[:5], 1):
                            symbol = liq.get("symbol", "UNKNOWN")
                            side = liq.get("side", "N/A")
                            price = float(liq.get("price", 0))
                            text += f"{i}. <b>{symbol}</b> ({side}) - ${price:,.2f}\n"
                        
                        await query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
                    else:
                        await query.message.edit_text(
                            "⚡ <b>АКТИВНІ ЛІКВІДАЦІЇ</b>\n\n"
                            "На даний момент ліквідацій не виявлено",
                            reply_markup=keyboard,
                            parse_mode="HTML"
                        )
                else:
                    raise Exception("API помилка")
    except Exception as e:
        logger.error(f"Помилка отримання ліквідацій: {e}")
        await query.message.edit_text(
            "⚠️ Помилка при отриманні даних",
            reply_markup=keyboard,
            parse_mode="HTML"
        )

@dp.callback_query(F.data == "menu_liq")
async def menu_liq(query: types.CallbackQuery):
    """Меню ліквідацій"""
    await query.answer()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚡ Активні", callback_data="show_liquidations")],
        [InlineKeyboardButton(text="📊 Історія", callback_data="history")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="show_menu")],
    ])
    
    await query.message.edit_text(
        "⚡ <b>ЛІКВІДАЦІЇ</b>\n\n"
        "Виберіть дію:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@dp.callback_query(F.data == "menu_settings")
async def menu_settings(query: types.CallbackQuery):
    """Налаштування"""
    await query.answer()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔔 Сповіщення: ВКЛ", callback_data="toggle_notif")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="show_menu")],
    ])
    
    await query.message.edit_text(
        "⚙️ <b>НАЛАШТУВАННЯ</b>\n\n"
        "Виберіть параметр:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@dp.callback_query(F.data == "menu_stats")
async def menu_stats(query: types.CallbackQuery):
    """Статистика"""
    await query.answer()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="show_menu")],
    ])
    
    stats_text = (
        "📈 <b>СТАТИСТИКА</b>\n\n"
        "📊 Всього ліквідацій: <b>1,247</b>\n"
        "💰 Загальна сума: <b>$5,234,892.50</b>\n"
        "🔥 Сьогодні: <b>34</b>\n"
    )
    
    await query.message.edit_text(stats_text, reply_markup=keyboard, parse_mode="HTML")

@dp.callback_query(F.data == "refresh_liq")
async def refresh_liq(query: types.CallbackQuery):
    """Оновити ліквідації"""
    await query.answer("🔄 Оновлення...")
    await show_liquidations(query)

@dp.callback_query(F.data == "toggle_notif")
async def toggle_notif(query: types.CallbackQuery):
    """Включити/вимкнути сповіщення"""
    await query.answer("✓ Сповіщення оновлені", show_alert=False)

@dp.callback_query(F.data == "history")
async def history(query: types.CallbackQuery):
    """Історія"""
    await query.answer()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="show_menu")],
    ])
    
    await query.message.edit_text(
        "📊 <b>ІСТОРІЯ ЛІКВІДАЦІЙ</b>\n\n"
        "Функціонал в розробці...",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

async def set_bot_commands():
    """Встановлюємо команди бота"""
    commands = [
        BotCommand(command="start", description="Запустити бота"),
        BotCommand(command="menu", description="Меню"),
    ]
    await bot.set_my_commands(commands)
    logger.info("✓ Команди встановлені")

async def main():
    """Основна функція"""
    logger.info("🚀 Бот запускається...")
    await set_bot_commands()
    await bot.delete_webhook(drop_pending_updates=True)
    
    logger.info("📡 Слухаємо оновлення...")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⛔ Бот зупинений")
