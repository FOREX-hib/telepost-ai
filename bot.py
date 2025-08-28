import os
import sqlite3
import google.generativeai as genai
from telethon import TelegramClient
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("Bot")

class Config:
    GEMINI_API_KEY   = os.environ['GEMINI_API_KEY']
    API_ID           = int(os.environ['API_ID'])
    API_HASH         = os.environ['API_HASH']
    BOT_TOKEN        = os.environ['BOT_TOKEN']
    CHANNEL_USERNAME = os.environ['CHANNEL_USERNAME']

genai.configure(api_key=Config.GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

async def generate_post(topic: str, style: str) -> str:
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
        response = model.generate_content(prompt)
        text = response.text.strip()[:600]
        log.info(f"✅ Пост сгенерирован: {text}")
        return text
    except Exception as e:
        log.error(f"❌ Ошибка генерации: {e}")
        return "Сегодня без поста... 🤖"

async def send_daily_post():
    try:
        with sqlite3.connect('config.db') as conn:
            c = conn.cursor()
            c.execute("SELECT topics, style, enabled FROM settings WHERE id=1")
            row = c.fetchone()
            if not row or not row[2]:
                return
            topics = [t.strip() for t in row[0].split(',') if t.strip()]
            style = row[1]

        if not topics:
            log.warning("Нет тем для поста")
            return

        import random
        topic = random.choice(topics)
        post = await generate_post(topic, style)

        with sqlite3.connect('config.db') as conn:
            conn.execute("UPDATE settings SET last_post = ? WHERE id=1", (post,))
            conn.commit()

        client = TelegramClient('bot_session', Config.API_ID, Config.API_HASH)
        await client.start(bot_token=Config.BOT_TOKEN)
        await client.send_message(Config.CHANNEL_USERNAME, post)
        await client.disconnect()

        log.info(f"📬 Пост отправлен: {post}")

    except Exception as e:
        log.error(f"❌ Ошибка отправки: {e}")
