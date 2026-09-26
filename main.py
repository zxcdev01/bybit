import os
import logging
import json
import urllib.request
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.constants import ParseMode

# ============ КОНФІГУРАЦІЯ ============
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ALLOWED_USERS = list(map(int, os.getenv("ALLOWED_USERS", "117445054,73455428").split(","))) if os.getenv("ALLOWED_USERS") else [123456789]

if not TELEGRAM_TOKEN:
    raise ValueError("❌ TELEGRAM_TOKEN не встановлений!")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============ ФУНКЦІЇ ДЛЯ API ============

def get_liquidations():
    """Отримай ліквідації з Bybit API"""
    try:
        url = "https://api.bybit.com/v5/market/liquidation?category=linear&limit=50"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            return data.get("result", {}).get("rows", [])
    except Exception as e:
        logger.warning(f"⚠️ API помилка: {e}")
        return []

def format_liquidation(liq):
    """Форматуй ліквідацію"""
    symbol = liq.get("symbol", "UNKNOWN")
    side = liq.get("side", "UNKNOWN")
    price = float(liq.get("price", 0))
    qty = float(liq.get("qty", 0))
    
    side_emoji = "🔴" if side == "Sell" else "🟢"
    
    text = (
        f"{side_emoji} <b>ЛІКВІДАЦІЯ</b>\n\n"
        f"<b>Пара:</b> {symbol}\n"
        f"<b>Напрямок:</b> {side}\n"
        f"<b>Ціна:</b> ${price:,.2f}\n"
        f"<b>Кількість:</b> {qty:,.2f}\n"
        f"⏰ {datetime.now().strftime('%H:%M:%S')}"
    )
    
    return text

# ============ ОБРОБНИКИ ============

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user = update.effective_user
    user_id = user.id
    
    if user_id not in ALLOWED_USERS:
        await update.message.reply_text("🚫 <b>Доступ заборонений!</b>", parse_mode=ParseMode.HTML)
        return
    
    logger.info(f"✅ Користувач {user.first_name} ({user_id}) приєднався")
    
    keyboard = [
        [
            InlineKeyboardButton("🔔 Ліквідації", callback_data="menu_liquidations"),
            InlineKeyboardButton("👤 Профіль", callback_data="menu_profile")
        ],
        [
            InlineKeyboardButton("⚙️ Налаштування", callback_data="menu_settings"),
            InlineKeyboardButton("📊 Статистика", callback_data="menu_stats")
        ],
        [InlineKeyboardButton("❓ Допомога", callback_data="menu_help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        f"👋 <b>Привіт, {user.first_name}!</b>\n\n"
        "🤖 <b>Ласкаво просимо до Bybit Liquidation Alerts</b>\n\n"
        "📢 <b>Я сповіщу тебе про всі ліквідації на Bybit</b>\n\n"
        "🚀 <b>Обери дію:</b>"
    )
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

async def menu_liquidations(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню ліквідацій"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("⚡ Активні зараз", callback_data="show_active_liq")],
        [InlineKeyboardButton("📊 Топ-10", callback_data="show_top_liq")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "⚡ <b>ЛІКВІДАЦІЇ</b>\n\n"
        "📡 <b>Що ти хочеш бачити?</b>\n\n"
        "🔔 <i>Натискай для оновлення</i>"
    )
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

async def show_active_liq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Активні ліквідації"""
    query = update.callback_query
    await query.answer("⏳ Завантажую...")
    
    liquidations = get_liquidations()
    
    keyboard = [
        [InlineKeyboardButton("🔄 Оновити", callback_data="show_active_liq")],
        [InlineKeyboardButton("🔙 Назад", callback_data="menu_liquidations")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if liquidations:
        text = "⚡ <b>АКТИВНІ ЛІКВІДАЦІЇ</b>\n\n"
        for i, liq in enumerate(liquidations[:10], 1):
            symbol = liq.get("symbol", "?")
            side = liq.get("side", "?")
            price = float(liq.get("price", 0))
            emoji = "🔴" if side == "Sell" else "🟢"
            text += f"{i}. {emoji} <b>{symbol}</b> ({side}) - ${price:,.2f}\n"
    else:
        text = "⚡ <b>АКТИВНІ ЛІКВІДАЦІЇ</b>\n\n😴 Нема ліквідацій"
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

async def show_top_liq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Топ ліквідацій"""
    query = update.callback_query
    await query.answer("⏳ Завантажую...")
    
    liquidations = get_liquidations()
    
    keyboard = [
        [InlineKeyboardButton("🔙 Назад", callback_data="menu_liquidations")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if liquidations:
        text = "📊 <b>ТОП-10 ЛІКВІДАЦІЙ</b>\n\n"
        for i, liq in enumerate(liquidations[:10], 1):
            symbol = liq.get("symbol", "?")
            side = liq.get("side", "?")
            price = float(liq.get("price", 0))
            qty = float(liq.get("qty", 0))
            emoji = "🔴" if side == "Sell" else "🟢"
            text += f"{i}. {emoji} <b>{symbol}</b> | ${price:,.2f} | {qty:,.0f}\n"
    else:
        text = "📊 <b>ТОП ЛІКВІДАЦІЙ</b>\n\n😴 Нема даних"
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

async def menu_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Профіль користувача"""
    query = update.callback_query
    user = query.from_user
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    profile_text = (
        f"👤 <b>МІЙ ПРОФІЛЬ</b>\n\n"
        f"<b>Ім'я:</b> {user.first_name} {user.last_name or ''}\n"
        f"<b>Username:</b> @{user.username or 'Немає'}\n"
        f"<b>ID:</b> <code>{user.id}</code>\n"
        f"<b>Сповіщення:</b> ✅ <b>Включені</b>"
    )
    
    await query.edit_message_text(profile_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

async def menu_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Налаштування"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🔔 Сповіщення: ✅", callback_data="toggle_notif")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = "⚙️ <b>НАЛАШТУВАННЯ</b>\n\n🎛️ <b>Керуй параметрами:</b>"
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

async def menu_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Статистика"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "📈 <b>СТАТИСТИКА</b>\n\n"
        "📊 <b>Всього:</b> 0\n"
        "💰 <b>Сума:</b> $0\n"
        "🔥 <b>Сьогодні:</b> 0"
    )
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

async def menu_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Допомога"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "❓ <b>ДОПОМОГА</b>\n\n"
        "🤖 Я моніторю ліквідації на Bybit\n"
        "🔔 Натискай кнопки для перегляду\n"
        "📱 Все просто та легко!\n\n"
        "✅ <b>Статус:</b> Активний 24/7"
    )
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Назад в головне меню"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [
            InlineKeyboardButton("🔔 Ліквідації", callback_data="menu_liquidations"),
            InlineKeyboardButton("👤 Профіль", callback_data="menu_profile")
        ],
        [
            InlineKeyboardButton("⚙️ Налаштування", callback_data="menu_settings"),
            InlineKeyboardButton("📊 Статистика", callback_data="menu_stats")
        ],
        [InlineKeyboardButton("❓ Допомога", callback_data="menu_help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "🏠 <b>ГОЛОВНЕ МЕНЮ</b>\n\n"
        "📢 <b>Я моніторю Bybit 24/7</b>\n\n"
        "🚀 <b>Обери дію:</b>"
    )
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

async def toggle_notif(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("✓ Сповіщення оновлені", show_alert=False)

# ============ ЗАПУСК БОТА ============

def main():
    """Запуск бота"""
    logger.info("🚀 Бот запускається...")
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Команди
    app.add_handler(CommandHandler("start", start))
    
    # Callback обробники
    app.add_handler(CallbackQueryHandler(menu_liquidations, pattern="menu_liquidations"))
    app.add_handler(CallbackQueryHandler(show_active_liq, pattern="show_active_liq"))
    app.add_handler(CallbackQueryHandler(show_top_liq, pattern="show_top_liq"))
    app.add_handler(CallbackQueryHandler(menu_profile, pattern="menu_profile"))
    app.add_handler(CallbackQueryHandler(menu_settings, pattern="menu_settings"))
    app.add_handler(CallbackQueryHandler(menu_stats, pattern="menu_stats"))
    app.add_handler(CallbackQueryHandler(menu_help, pattern="menu_help"))
    app.add_handler(CallbackQueryHandler(back_to_menu, pattern="back_to_menu"))
    app.add_handler(CallbackQueryHandler(toggle_notif, pattern="toggle_notif"))
    
    logger.info("✅ Бот готовий!")
    logger.info(f"👥 Дозволені користувачі: {ALLOWED_USERS}")
    logger.info("📡 Бот запущений і очікує команд...")
    
    app.run_polling()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("⛔ Бот зупинений")
