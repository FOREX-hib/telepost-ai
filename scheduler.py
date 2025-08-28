import os
import time
import schedule
import asyncio
from bot import send_daily_post

def start_scheduler():
    def job():
        asyncio.run(send_daily_post())

    try:
        with sqlite3.connect('config.db') as conn:
            c = conn.cursor()
            c.execute("SELECT post_time FROM settings WHERE id=1")
            post_time = c.fetchone()[0]
    except:
        post_time = '09:00'

    schedule.every().day.at(post_time).do(job)
    print(f"⏰ Планировщик запущен. Пост будет в {post_time}")

    while True:
        schedule.run_pending()
        time.sleep(1)
