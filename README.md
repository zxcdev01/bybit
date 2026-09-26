# 🤖 Telegram Бот - Bybit Liquidation Alerts

Спрощений Telegram бот для моніторингу ліквідацій на Bybit з меню та профілем.

## 🎯 Можливості

✅ Доступ тільки для авторизованих користувачів (за ID)  
✅ Красиве меню з кнопками  
✅ Профіль користувача  
✅ Отримання даних з Bybit API  
✅ Готово для Render  

## 🚀 Швидкий старт (локально)

### 1. Отримай токен

Напиши `@BotFather` в Telegram → `/newbot` → скопіюй токен

### 2. Дізнайся свій ID

Напиши `@userinfobot` в Telegram → скопіюй ID

### 3. Запусти

```bash
pip install -r requirements.txt
export TELEGRAM_TOKEN="твой_токен"
export ALLOWED_USERS="твой_id,id_другой_персоны"
python main.py
```

## 🌐 Розміщення на Render

### Environment Variables додай на Render:

```
TELEGRAM_TOKEN = твой_токен_від_BotFather
ALLOWED_USERS = 123456789,987654321
```

### Де додати:
1. Dashboard Render → Create → Web Service
2. Вибери GitHub репозиторій
3. Environment → додай змінні
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `python main.py`
6. Deploy!

## 📋 Environment Variables

| Змінна | Опис | Приклад |
|--------|------|---------|
| **TELEGRAM_TOKEN** | Токен від @BotFather | `123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi` |
| **ALLOWED_USERS** | ID користувачів (через кому) | `123456789,987654321` |

## 📁 Файли

```
.
├── main.py              # Основний код (все в одному файлі)
├── requirements.txt     # Залежності
└── README.md           # Документація
```

## 📖 Команди

```
/start  - Запустити бота
/menu   - Меню
```

## 🎨 Меню бота

```
📋 МЕНЮ
├── 🔔 Ліквідації
│   ├─ ⚡ Активні
│   └─ 📊 Історія
├── ⚙️ Налаштування
├── 📈 Статистика
└── 👤 Профіль
```

## 🔐 Безпека

```bash
# Додай у .gitignore (якщо коміться)
.env
.env.local
```

⚠️ **НІКОЛИ** не публікуй TELEGRAM_TOKEN на GitHub!

## 🆘 Помилки

### "TELEGRAM_TOKEN не встановлений"
→ Додай Environment Variable на Render

### "Немає доступу"
→ Додай свій ID в ALLOWED_USERS

### "API помилка"
→ Перевір інтернет або Bybit API статус

## 📚 Залежності

- `aiogram==3.3.0` - Telegram Bot Framework
- `aiohttp==3.9.1` - HTTP запити
- `python-dotenv==1.0.0` - Environment vars

## 🚀 Перший запуск

1. ✅ Отримай токен від @BotFather
2. ✅ Дізнайся свій ID у @userinfobot
3. ✅ Додай Environment Variables на Render
4. ✅ Deploy!
5. ✅ Напиши `/start` боту в Telegram

## 📞 Допомога

Все в `main.py` - код простий та документований!

---

**Готово! Розташуй на Render! 🚀**
