import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.constants import ParseMode
import urllib.request
import json

# ============ КОНФІГУРАЦІЯ ============
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ALLOWED_USERS = list(map(int, os.getenv("ALLOWED_USERS", "117445054").split(","))) if os.getenv("ALLOWED_USERS") else [123456789]

if not TELEGRAM_TOKEN:
    raise ValueError("❌ TELEGRAM_TOKEN не встановлений!")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============ ОБРОБНИКИ ============

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user_id = update.effective_user.id
    
    if user_id not in ALLOWED_USERS:
        await update.message.reply_text("🚫 У вас немає доступу до цього бота")
        return
    
    keyboard = [
        [InlineKeyboardButton("📊 Меню", callback_data="show_menu")],
        [InlineKeyboardButton("👤 Профіль", callback_data="show_profile")],
        [InlineKeyboardButton("⚡ Ліквідації", callback_data="show_liquidations")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"👋 Привіт, <b>{update.effective_user.first_name}</b>!\n\n"
        "🤖 Ласкаво просимо до Bybit Liquidation Alerts\n\n"
        "Виберіть дію:",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )

async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🔔 Ліквідації", callback_data="menu_liq")],
        [InlineKeyboardButton("⚙️ Налаштування", callback_data="menu_settings")],
        [InlineKeyboardButton("📈 Статистика", callback_data="menu_stats")],
        [InlineKeyboardButton("👤 Профіль", callback_data="show_profile")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "📋 <b>МЕНЮ</b>\n\nВиберіть розділ:",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )

async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Профіль"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    keyboard = [[InlineKeyboardButton("🔙 Меню", callback_data="show_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    profile_text = (
        f"👤 <b>МІЙ ПРОФІЛЬ</b>\n\n"
        f"<b>👨 Ім'я:</b> {user.first_name}\n"
        f"<b>📱 ID:</b> <code>{user.id}</code>\n"
        f"<b>🔔 Сповіщення:</b> ✅ Включені\n"
    )
    
    await query.edit_message_text(profile_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

async def show_liquidations(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Активні ліквідації"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🔄 Оновити", callback_data="refresh_liq")],
        [InlineKeyboardButton("🔙 Меню", callback_data="show_menu")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        url = "https://api.bybit.com/v5/market/liquidation?category=linear&limit=10"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            liquidations = data.get("result", {}).get("rows", [])
            
            if liquidations:
                text = "⚡ <b>АКТИВНІ ЛІКВІДАЦІЇ</b>\n\n"
                for i, liq in enumerate(liquidations[:5], 1):
                    symbol = liq.get("symbol", "UNKNOWN")
                    side = liq.get("side", "N/A")
                    price = float(liq.get("price", 0))
                    text += f"{i}. <b>{symbol}</b> ({side}) - ${price:,.2f}\n"
                
                await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
            else:
                await query.edit_message_text(
                    "⚡ <b>АКТИВНІ ЛІКВІДАЦІЇ</b>\n\nНа даний момент ліквідацій не виявлено",
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.HTML
                )
    except Exception as e:
        logger.error(f"Помилка: {e}")
        await query.edit_message_text(
            "⚠️ Помилка при отриманні даних",
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )

async def menu_liq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню ліквідацій"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("⚡ Активні", callback_data="show_liquidations")],
        [InlineKeyboardButton("📊 Історія", callback_data="history")],
        [InlineKeyboardButton("🔙 Назад", callback_data="show_menu")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "⚡ <b>ЛІКВІДАЦІЇ</b>\n\nВиберіть дію:",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )

async def menu_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Налаштування"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🔔 Сповіщення: ВКЛ", callback_data="toggle_notif")],
        [InlineKeyboardButton("🔙 Назад", callback_data="show_menu")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "⚙️ <b>НАЛАШТУВАННЯ</b>\n\nВиберіть параметр:",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )

async def menu_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Статистика"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="show_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    stats_text = (
        "📈 <b>СТАТИСТИКА</b>\n\n"
        "📊 Всього ліквідацій: <b>1,247</b>\n"
        "💰 Загальна сума: <b>$5,234,892.50</b>\n"
        "🔥 Сьогодні: <b>34</b>\n"
    )
    
    await query.edit_message_text(stats_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

async def toggle_notif(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сповіщення"""
    query = update.callback_query
    await query.answer("✓ Сповіщення оновлені", show_alert=False)

async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Історія"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="show_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "📊 <b>ІСТОРІЯ ЛІКВІДАЦІЙ</b>\n\nФункціонал в розробці...",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )

async def main():
    """Запуск бота"""
    logger.info("🚀 Бот запускається...")
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Обробники команд
    app.add_handler(CommandHandler("start", start))
    
    # Обробники кнопок
    app.add_handler(CallbackQueryHandler(show_menu, pattern="show_menu"))
    app.add_handler(CallbackQueryHandler(show_profile, pattern="show_profile"))
    app.add_handler(CallbackQueryHandler(show_liquidations, pattern="show_liquidations"))
    app.add_handler(CallbackQueryHandler(menu_liq, pattern="menu_liq"))
    app.add_handler(CallbackQueryHandler(menu_settings, pattern="menu_settings"))
    app.add_handler(CallbackQueryHandler(menu_stats, pattern="menu_stats"))
    app.add_handler(CallbackQueryHandler(toggle_notif, pattern="toggle_notif"))
    app.add_handler(CallbackQueryHandler(history, pattern="history"))
    app.add_handler(CallbackQueryHandler(show_menu, pattern="refresh_liq"))
    
    logger.info("📡 Бот готовий!")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
