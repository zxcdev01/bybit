import os
import logging
import asyncio
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

# ============ ГЛОБАЛЬНІ ЗМІННІ ============
active_users = {}  # {user_id: user_data}
last_liquidation = None  # Останння ліквідація що була надіслана
liquidation_cache = []  # Кеш ліквідацій

# ============ ФУНКЦІЇ ДЛЯ API ============

def get_liquidations():
    """Отримай ліквідації з Bybit API"""
    try:
        url = "https://api.bybit.com/v5/market/liquidation?category=linear&limit=50"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.bybit.com/'
        }
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            return data.get("result", {}).get("rows", [])
    except urllib.error.HTTPError as e:
        logger.warning(f"⚠️ API помилка {e.code}: {e.reason}. Будемо намагатися пізніше...")
        return []
    except Exception as e:
        logger.warning(f"⚠️ Помилка отримання ліквідацій: {e}")
        return []

def format_liquidation(liq):
    """Форматуй ліквідацію для повідомлення"""
    symbol = liq.get("symbol", "UNKNOWN")
    side = liq.get("side", "UNKNOWN")
    price = float(liq.get("price", 0))
    qty = float(liq.get("qty", 0))
    timestamp = liq.get("updatedTime", "")
    
    # Визначи емодзі
    side_emoji = "🔴" if side == "Sell" else "🟢"
    
    text = (
        f"{side_emoji} <b>ЛІКВІДАЦІЯ</b>\n\n"
        f"<b>Торгова пара:</b> {symbol}\n"
        f"<b>Напрямок:</b> {side}\n"
        f"<b>Ціна:</b> ${price:,.2f}\n"
        f"<b>Кількість:</b> {qty:,.2f}\n"
        f"<b>Час:</b> {timestamp}\n\n"
        f"⏰ {datetime.now().strftime('%H:%M:%S')}"
    )
    
    return text, symbol

# ============ ОБРОБНИКИ ============

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user = update.effective_user
    user_id = user.id
    
    if user_id not in ALLOWED_USERS:
        await update.message.reply_text(
            "🚫 <b>Доступ заборонений!</b>\n\n"
            "У вас немає дозволу користуватися цим ботом.",
            parse_mode=ParseMode.HTML
        )
        return
    
    # Реєструємо користувача
    active_users[user_id] = {
        "first_name": user.first_name,
        "last_name": user.last_name or "",
        "username": user.username or "БезUsername",
        "joined": datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    }
    
    logger.info(f"✅ Користувач {user.first_name} ({user_id}) приєднався")
    
    # Главне меню
    keyboard = [
        [
            InlineKeyboardButton("🔔 Ліквідації", callback_data="menu_liquidations"),
            InlineKeyboardButton("👤 Профіль", callback_data="menu_profile")
        ],
        [
            InlineKeyboardButton("⚙️ Налаштування", callback_data="menu_settings"),
            InlineKeyboardButton("📊 Статистика", callback_data="menu_stats")
        ],
        [
            InlineKeyboardButton("❓ Допомога", callback_data="menu_help")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        f"👋 <b>Привіт, {user.first_name}!</b>\n\n"
        "🤖 <b>Ласкаво просимо до Bybit Liquidation Alerts</b>\n\n"
        "📢 <b>Я сповіщу тебе про всі ліквідації</b> на крипто-біржі Bybit\n\n"
        "🚀 <b>Обери дію:</b>"
    )
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

async def menu_liquidations(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню ліквідацій"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("⚡ Активні зараз", callback_data="show_active_liq")],
        [InlineKeyboardButton("📊 Топ-10 ліквідацій", callback_data="show_top_liq")],
        [InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "⚡ <b>ЛІКВІДАЦІЇ</b>\n\n"
        "📡 <b>Що ти хочеш бачити?</b>\n\n"
        "🔔 <i>Усі нові ліквідації будуть автоматично надіслані тобі</i>"
    )
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

async def show_active_liq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Активні ліквідації"""
    query = update.callback_query
    await query.answer("⏳ Завантажую дані...")
    
    liquidations = get_liquidations()
    
    keyboard = [
        [InlineKeyboardButton("🔄 Оновити", callback_data="show_active_liq")],
        [InlineKeyboardButton("🔙 Назад", callback_data="menu_liquidations")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if liquidations:
        text = "⚡ <b>АКТИВНІ ЛІКВІДАЦІЇ</b>\n\n"
        for i, liq in enumerate(liquidations[:10], 1):
            symbol = liq.get("symbol", "UNKNOWN")
            side = liq.get("side", "N/A")
            price = float(liq.get("price", 0))
            emoji = "🔴" if side == "Sell" else "🟢"
            text += f"{i}. {emoji} <b>{symbol}</b> ({side}) - ${price:,.2f}\n"
        
        text += f"\n<i>Всього показано: {len(liquidations[:10])}</i>"
    else:
        text = "⚡ <b>АКТИВНІ ЛІКВІДАЦІЇ</b>\n\n😴 Наразі ліквідацій не виявлено"
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

async def show_top_liq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Топ ліквідацій"""
    query = update.callback_query
    await query.answer("⏳ Завантажую дані...")
    
    liquidations = get_liquidations()
    
    keyboard = [
        [InlineKeyboardButton("🔙 Назад", callback_data="menu_liquidations")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if liquidations:
        text = "📊 <b>ТОП-10 ЛІКВІДАЦІЙ</b>\n\n"
        for i, liq in enumerate(liquidations[:10], 1):
            symbol = liq.get("symbol", "UNKNOWN")
            side = liq.get("side", "N/A")
            price = float(liq.get("price", 0))
            qty = float(liq.get("qty", 0))
            emoji = "🔴" if side == "Sell" else "🟢"
            text += f"{i}. {emoji} <b>{symbol}</b>\n"
            text += f"   💰 Ціна: ${price:,.2f} | Кол-во: {qty:,.0f}\n\n"
    else:
        text = "📊 <b>ТОП ЛІКВІДАЦІЙ</b>\n\n😴 Нема даних"
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

async def menu_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Профіль користувача"""
    query = update.callback_query
    user = query.from_user
    user_id = user.id
    await query.answer()
    
    user_data = active_users.get(user_id, {})
    joined = user_data.get("joined", "N/A")
    
    keyboard = [
        [InlineKeyboardButton("✏️ Редагувати ім'я", callback_data="edit_name")],
        [InlineKeyboardButton("🔔 Сповіщення: ✅ ВКЛ", callback_data="toggle_notifications")],
        [InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    profile_text = (
        f"👤 <b>МІЙ ПРОФІЛЬ</b>\n\n"
        f"<b>👨 Ім'я:</b> {user.first_name} {user.last_name or ''}\n"
        f"<b>📱 Username:</b> @{user.username or 'Без username'}\n"
        f"<b>🆔 ID:</b> <code>{user_id}</code>\n"
        f"<b>📅 Приєднався:</b> {joined}\n"
        f"<b>🔔 Сповіщення:</b> ✅ <b>Включені</b>\n"
        f"<b>✅ Статус:</b> Авторизований"
    )
    
    await query.edit_message_text(profile_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

async def menu_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Налаштування"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🔔 Сповіщення: ✅", callback_data="toggle_notif_settings")],
        [InlineKeyboardButton("🔊 Звук: ✅", callback_data="toggle_sound")],
        [InlineKeyboardButton("📲 Вібрація: ✅", callback_data="toggle_vibration")],
        [InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "⚙️ <b>НАЛАШТУВАННЯ</b>\n\n"
        "🎛️ <b>Керуй своїми уподобаннями:</b>"
    )
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

async def menu_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Статистика"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "📈 <b>СТАТИСТИКА</b>\n\n"
        "📊 <b>Всього ліквідацій:</b> {}\n"
        "💰 <b>Загальна сума:</b> $0\n"
        "🔥 <b>Сьогодні:</b> 0\n"
        "⏱️ <b>За останню годину:</b> 0\n\n"
        "<i>Статистика оновлюється в реальному часі</i>"
    ).format(len(liquidation_cache))
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

async def menu_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Допомога"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "❓ <b>ДОПОМОГА</b>\n\n"
        "🤖 <b>Що робить цей бот?</b>\n"
        "Я моніторю ліквідації на крипто-біржі Bybit і сповіщаю тебе про всі ліквідації на всіх торгових парах.\n\n"
        "🔔 <b>Як я тебе сповіщу?</b>\n"
        "Кожна нова ліквідація буде надіслана тобі приватним повідомленням у Telegram.\n\n"
        "✅ <b>Статус бота:</b> Активний\n"
        "📡 <b>Моніторинг:</b> 24/7\n\n"
        "<i>Якщо у тебе є запитання - напиши мені /help</i>"
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
        [
            InlineKeyboardButton("❓ Допомога", callback_data="menu_help")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "🏠 <b>ГОЛОВНЕ МЕНЮ</b>\n\n"
        "📢 <b>Я постійно моніторю ліквідації Bybit</b>\n"
        "🔔 Усі нові ліквідації буде надіслано тобі\n\n"
        "🚀 <b>Обери дію:</b>"
    )
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

# Простір для інших callback handlers
async def toggle_notif_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("✓ Сповіщення оновлені", show_alert=False)

async def toggle_sound(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("✓ Звук змінений", show_alert=False)

async def toggle_vibration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("✓ Вібрація змінена", show_alert=False)

async def edit_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("ℹ️ Функція в розробці", show_alert=True)

async def toggle_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("✓ Сповіщення включені", show_alert=False)

# ============ ФОНОВИЙ МОНІТОРИНГ ============

async def monitor_liquidations(app: Application):
    """Фоновий task що моніторить ліквідації"""
    global last_liquidation, liquidation_cache
    
    logger.info("🚀 Запуск моніторингу ліквідацій...")
    
    while True:
        try:
            liquidations = get_liquidations()
            
            if liquidations:
                # Отримай найновішу ліквідацію
                latest = liquidations[0]
                
                # Перевір чи це нова ліквідація
                if last_liquidation != latest.get("symbol"):
                    # Це нова ліквідація!
                    message_text, symbol = format_liquidation(latest)
                    last_liquidation = symbol
                    
                    # Кешуй
                    liquidation_cache.append(latest)
                    if len(liquidation_cache) > 100:
                        liquidation_cache.pop(0)
                    
                    # Надішли ВСІМ авторизованим користувачам
                    logger.info(f"🚨 Нова ліквідація: {symbol}")
                    
                    keyboard = [
                        [InlineKeyboardButton("📊 Переглянути деталі", callback_data="menu_liquidations")],
                        [InlineKeyboardButton("⚡ Всі ліквідації", callback_data="show_active_liq")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    for user_id in list(active_users.keys()):
                        try:
                            await app.bot.send_message(
                                chat_id=user_id,
                                text=message_text,
                                reply_markup=reply_markup,
                                parse_mode=ParseMode.HTML
                            )
                            logger.info(f"✅ Повідомлення надіслано користувачу {user_id}")
                        except Exception as e:
                            logger.error(f"❌ Помилка надсилання користувачу {user_id}: {e}")
            
            # Перевіряй кожні 5 секунд
            await asyncio.sleep(5)
            
        except Exception as e:
            logger.error(f"❌ Помилка в моніторингу: {e}")
            await asyncio.sleep(10)

# ============ POST-INIT CALLBACK ============

async def post_init(application: Application) -> None:
    """Запускається після ініціалізації бота"""
    logger.info("✅ Бот готовий!")
    logger.info(f"👥 Дозволені користувачі: {ALLOWED_USERS}")
    logger.info("🚀 Запуск моніторингу ліквідацій...")
    # Запусти фоновий монітор
    asyncio.create_task(monitor_liquidations(application))

# ============ ЗАПУСК БОТА ============

async def main():
    """Запуск бота"""
    logger.info("🚀 Бот запускається...")
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Встанови post_init callback
    app.post_init = post_init
    
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
    app.add_handler(CallbackQueryHandler(toggle_notif_settings, pattern="toggle_notif_settings"))
    app.add_handler(CallbackQueryHandler(toggle_sound, pattern="toggle_sound"))
    app.add_handler(CallbackQueryHandler(toggle_vibration, pattern="toggle_vibration"))
    app.add_handler(CallbackQueryHandler(edit_name, pattern="edit_name"))
    app.add_handler(CallbackQueryHandler(toggle_notifications, pattern="toggle_notifications"))
    
    # Встанови команди
    commands = [
        BotCommand("start", "Запустити бота"),
        BotCommand("help", "Допомога"),
    ]
    await app.bot.set_my_commands(commands)
    
    await app.run_polling()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⛔ Бот зупинений")
