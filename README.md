# TgBotMemes — Telegram Meme Generator Bot

## Установка

```bash
git clone <repo>
cd meme_bot
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Отредактируй .env
```

## Переменные окружения (.env)

| Переменная | Описание |
|---|---|
| `BOT_TOKEN` | Токен бота от @BotFather |
| `IMAGE_API_BASE_URL` | URL API генерации изображений (OpenAI-совместимый) |
| `IMAGE_API_KEY` | API ключ |
| `IMAGE_MODEL` | Модель (например `dall-e-3`) |
| `TIMEOUT_SECONDS` | Таймаут запроса к API (по умолчанию 90) |
| `RETRIES` | Повторов при ошибке (по умолчанию 2) |
| `ADMIN_IDS` | Telegram user_id администраторов через запятую |
| `DB_PATH` | Путь к SQLite базе (по умолчанию `memes.db`) |
| `FREE_DAILY_LIMIT` | Лимит бесплатных мемов в день (по умолчанию 3) |
| `RATE_LIMIT_SECONDS` | Интервал между запросами (по умолчанию 10) |
| `PAYMENT_PROVIDER_TOKEN` | Токен платёжного провайдера Telegram |

## Запуск

```bash
python bot.py
```

## Деплой (systemd)

```bash
sudo cp meme_bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable meme_bot
sudo systemctl start meme_bot
sudo journalctl -u meme_bot -f    # логи
```

## Замена провайдера изображений

Правим только `providers/image_provider.py` — метод `generate_image()` должен возвращать URL или base64 data URI.

## Структура проекта

```
bot.py                  Точка входа
config.py               Конфигурация из .env
database/
  models.py             SQL схема
  repository.py         Все операции с БД
providers/
  image_provider.py     Генерация изображений (заменяемый провайдер)
handlers/
  start.py              /start, /help
  meme.py               Основная генерация мемов
  favorites.py          Мои мемы / Избранное
  payments.py           Оплата через Telegram Payments
  referral.py           Реферальная система
  admin.py              Команды администратора
  states.py             FSM состояния
middlewares/
  rate_limit.py         Защита от спама
  user_check.py         Авторегистрация пользователей
utils/
  content_filter.py     Модерация запросов
  prompt_builder.py     Построение промптов
  keyboards.py          Все inline-клавиатуры
```
