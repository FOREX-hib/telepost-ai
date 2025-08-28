import os
import sqlite3
from flask import Flask, render_template, request, redirect
from flask_httpauth import HTTPBasicAuth

app = Flask(__name__)
auth = HTTPBasicAuth()

@auth.verify_password
def verify(username, password):
    return username == os.environ['ADMIN_USER'] and password == os.environ['ADMIN_PASS']

def init_db():
    with sqlite3.connect('config.db') as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY,
                topics TEXT DEFAULT 'мотивация, заработок, психология',
                post_time TEXT DEFAULT '09:00',
                style TEXT DEFAULT 'дружелюбный и мотивирующий',
                enabled INTEGER DEFAULT 1,
                last_post TEXT
            )
        ''')
        conn.execute('INSERT OR IGNORE INTO settings (id) VALUES (1)')
        conn.commit()

def get_settings():
    with sqlite3.connect('config.db') as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT topics, post_time, style, enabled, last_post FROM settings WHERE id=1")
        row = c.fetchone()
        return dict(row)

def update_setting(field, value):
    with sqlite3.connect('config.db') as conn:
        conn.execute(f"UPDATE settings SET {field} = ? WHERE id=1", (value,))
        conn.commit()

@app.route('/')
@auth.login_required
def index():
    settings = get_settings()
    return render_template('index.html', **settings)

@app.route('/update_topics', methods=['POST'])
@auth.login_required
def update_topics():
    update_setting('topics', request.form['topics'])
    return redirect('/')

@app.route('/update_time', methods=['POST'])
@auth.login_required
def update_time():
    update_setting('post_time', request.form['post_time'])
    return redirect('/')

@app.route('/update_style', methods=['POST'])
@auth.login_required
def update_style():
    update_setting('style', request.form['style'])
    return redirect('/')

@app.route('/toggle', methods=['POST'])
@auth.login_required
def toggle():
    settings = get_settings()
    update_setting('enabled', 0 if settings['enabled'] else 1)
    return redirect('/')

@app.route('/send_test_post', methods=['POST'])
def send_test_post():
    try:
        import asyncio
        from bot import send_daily_post
        asyncio.run(send_daily_post())
        return redirect("/?msg=✅ Тестовый пост отправлен!")
    except Exception as e:
        return redirect(f"/?msg=❌ Ошибка: {str(e)}")
if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
