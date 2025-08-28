import os
import sqlite3
import google.generativeai as genai
from telethon import TelegramClient
import logging

# --- Настройка логирования ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
log = logging.getLogger("Bot")

# --- Конфигурация ---
class Config:
    GEMINI_API_KEY   = os.environ['GEMINI_API_KEY']
    API_ID           = int(os.environ['API_ID'])
    API_HASH         = os.environ['API_HASH']
    BOT_TOKEN        = os.environ['BOT_TOKEN']
    CHANNEL_USERNAME = os.environ['CHANNEL_USERNAME']

# --- Инициализация Gemini ---
try:
    genai.configure(api_key=Config.GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    log.critical(f"❌ Не удалось настроить Gemini API: {e}")
    raise

async def generate_post(topic: str, style: str) -> str:
    """
    Генерирует пост через Google Gemini
    """
    prompt = f"""
    Напиши пост для Telegram-канала:
    - Тема: {topic}
    - Стиль: {style}
    - Длина: 3–5 предложений
    - Язык: русский
    - Добавь 1–2 смайлика
    - Не используй хэштеги
    - Будь дружелюбным, как эксперт
    """
    try:
        response = model.generate_content(prompt, timeout=30)
        text = response.text.strip()[:600]
        log.info(f"✅ Пост сгенерирован: {text}")
        return text
    except AttributeError:
        log.error("❌ Gemini не вернул текст. Возможно, ответ был отфильтрован.")
        return "Сегодня интересный пост — подумай над этим! 💡"
    except Exception as e:
        log.error(f"❌ Ошибка генерации поста: {e}")
        return "Сегодня без поста... 🤖"

async def send_daily_post():
    """
    Основная функция: генерирует и отправляет пост в Telegram
    """
    try:
        # Получаем настройки из базы
        with sqlite3.connect('config.db') as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT topics, style, enabled FROM settings WHERE id=1")
            row = c.fetchone()

        if not row:
            log.warning("❌ Настройки не найдены в базе данных")
            return

        if not row['enabled']:
            log.info("⏸️ Автопостинг отключён. Пост не отправлен.")
            return

        topics = [t.strip() for t in row['topics'].split(',') if t.strip()]
        style = row['style']

        if not topics:
            log.warning("❌ Нет тем для поста")
            return

        import random
        topic = random.choice(topics)
        log.info(f"🎯 Генерация поста по теме: {topic}")

        post = await generate_post(topic, style)

        # Сохраняем пост в базу
        with sqlite3.connect('config.db') as conn:
            conn.execute("UPDATE settings SET last_post = ? WHERE id=1", (post,))
            conn.commit()

        # Отправка в Telegram
        client = TelegramClient('bot_session', Config.API_ID, Config.API_HASH)
        try:
            await client.start(bot_token=Config.BOT_TOKEN)
            await client.send_message(Config.CHANNEL_USERNAME, post)
            log.info(f"📬 Пост успешно отправлен в {Config.CHANNEL_USERNAME}")
        except Exception as e:
            log.error(f"❌ Ошибка отправки в Telegram: {e}")
        finally:
            await client.disconnect()

    except sqlite3.Error as e:
        log.error(f"❌ Ошибка базы данных: {e}")
    except Exception as e:
        log.error(f"❌ Непредвиденная ошибка: {e}")
