import logging
import sqlite3
import os
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    PreCheckoutQueryHandler, MessageHandler, filters, ContextTypes
)
from flask import Flask, request, jsonify
import threading

TOKEN = os.getenv("BOT_TOKEN")

COIN_PACKS = [
    {"id": "pack_100", "coins": 100, "stars": 50, "name": "100 монеток"},
    {"id": "pack_300", "coins": 300, "stars": 120, "name": "300 монеток"},
    {"id": "pack_1000", "coins": 1000, "stars": 350, "name": "1000 монеток"},
]

SHOP_ITEMS = [
    {"id": "nude_1", "name": "Нюдс 1", "price": 80, "file_id": None},
    {"id": "nude_2", "name": "Нюдс 2", "price": 150, "file_id": None},
    {"id": "nude_3", "name": "Нюдс 3", "price": 250, "file_id": None},
]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ================== БАЗА ==================
def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance INTEGER DEFAULT 0,
            last_daily TEXT,
            ref_by INTEGER,
            invited INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def get_user(user_id: int):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    if not row:
        c.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()
        conn.close()
        return {"user_id": user_id, "balance": 0, "last_daily": None, "ref_by": None, "invited": 0}
    conn.close()
    return {"user_id": row[0], "balance": row[1], "last_daily": row[2], "ref_by": row[3], "invited": row[4]}

def update_balance(user_id: int, amount: int):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

# ================== FLASK API ==================
app = Flask(__name__)

@app.route("/balance/<int:user_id>", methods=["GET"])
def api_get_balance(user_id):
    user = get_user(user_id)
    return jsonify({"balance": user["balance"]})

@app.route("/tap", methods=["POST"])
def api_tap():
    data = request.json
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error": "no user_id"}), 400
    update_balance(int(user_id), 1)
    user = get_user(int(user_id))
    return jsonify({"balance": user["balance"]})

def run_flask():
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))

# ================== БОТ ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    get_user(user_id)
    await update.message.reply_text("Бот работает. Открой приложение через кнопку меню.")

def main():
    init_db()
    # Запускаем Flask в отдельном потоке
    threading.Thread(target=run_flask, daemon=True).start()

    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    print("Бот запущен...")
    application.run_polling()

if __name__ == "__main__":
    main()
