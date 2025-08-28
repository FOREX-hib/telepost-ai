from telethon import TelegramClient, events
import sqlite3
import os

API_ID = int(os.environ['API_ID'])
API_HASH = os.environ['API_HASH']
BOT_TOKEN = os.environ['BOT_TOKEN']
GROUP_ID = os.environ['GROUP_ID']  # ID группы обсуждения

client = TelegramClient('stats_session', API_ID, API_HASH)

@client.on(events.NewMessage(chats=GROUP_ID))
async def handler(event):
    # Сохраняем комментарий
    with sqlite3.connect('stats.db') as conn:
        conn.execute('''
            INSERT INTO comments (post_id, user, text, date)
            VALUES (?, ?, ?, ?)
        ''', (event.reply_to_msg_id, event.sender_id, event.text, event.date.isoformat()))
        conn.commit()

@client.on(events.MessageEdited(chats=GROUP_ID))
async def edit_handler(event):
    # Логируем редактирование
    print(f"Комментарий отредактирован: {event.text}")

print("📊 Сбор статистики запущен...")
client.start(bot_token=BOT_TOKEN)
client.run_until_disconnected()
