import logging
import sqlite3
import os
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    PreCheckoutQueryHandler, MessageHandler, filters, ContextTypes
)

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
    return {
        "user_id": row[0],
        "balance": row[1],
        "last_daily": row[2],
        "ref_by": row[3],
        "invited": row[4]
    }

def update_balance(user_id: int, amount: int):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

def set_last_daily(user_id: int):
    now = datetime.now().isoformat()
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("UPDATE users SET last_daily = ? WHERE user_id = ?", (now, user_id))
    conn.commit()
    conn.close()

def main_menu():
    keyboard = [
        [InlineKeyboardButton("💰 Баланс", callback_data="balance")],
        [InlineKeyboardButton("📋 Задания", callback_data="tasks")],
        [InlineKeyboardButton("🛒 Купить монетки", callback_data="buy_coins")],
        [InlineKeyboardButton("🔥 Магазин", callback_data="shop")],
    ]
    return InlineKeyboardMarkup(keyboard)

def tasks_menu():
    keyboard = [
        [InlineKeyboardButton("🎁 Ежедневный бонус", callback_data="daily")],
        [InlineKeyboardButton("👥 Пригласить друга", callback_data="referral")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="main")],
    ]
    return InlineKeyboardMarkup(keyboard)

def shop_menu():
    keyboard = []
    for item in SHOP_ITEMS:
        keyboard.append([InlineKeyboardButton(
            f"{item['name']} — {item['price']} монеток",
            callback_data=f"buy_item_{item['id']}"
        )])
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="main")])
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)

    if context.args and context.args[0].startswith("ref_"):
        try:
            ref_id = int(context.args[0].split("_")[1])
            if ref_id != user_id and user["ref_by"] is None:
                conn = sqlite3.connect("users.db")
                c = conn.cursor()
                c.execute("UPDATE users SET ref_by = ? WHERE user_id = ?", (ref_id, user_id))
                c.execute("UPDATE users SET invited = invited + 1, balance = balance + 30 WHERE user_id = ?", (ref_id,))
                conn.commit()
                conn.close()
                await context.bot.send_message(ref_id, "🎉 По твоей ссылке зашёл новый пользователь! +30 монеток")
        except Exception:
            pass

    await update.message.reply_text(
        "Привет! Это бот модели.\n\nЗдесь можно зарабатывать монетки и покупать фото.",
        reply_markup=main_menu()
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    if data == "main":
        await query.edit_message_text("Главное меню:", reply_markup=main_menu())

    elif data == "balance":
        user = get_user(user_id)
        await query.edit_message_text(
            f"💰 Твой баланс: <b>{user['balance']}</b> монеток\n"
            f"👥 Приглашено друзей: {user['invited']}",
            reply_markup=main_menu(),
            parse_mode="HTML"
        )

    elif data == "tasks":
        await query.edit_message_text("Выбери задание:", reply_markup=tasks_menu())

    elif data == "daily":
        user = get_user(user_id)
        now = datetime.now()
        if user["last_daily"]:
            last = datetime.fromisoformat(user["last_daily"])
            if now - last < timedelta(hours=24):
                await query.answer("Ежедневный бонус уже получен. Приходи завтра.", show_alert=True)
                return
        update_balance(user_id, 15)
        set_last_daily(user_id)
        await query.answer("✅ +15 монеток!", show_alert=True)
        user = get_user(user_id)
        await query.edit_message_text(
            f"💰 Твой баланс: <b>{user['balance']}</b> монеток",
            reply_markup=main_menu(),
            parse_mode="HTML"
        )

    elif data == "referral":
        bot_username = (await context.bot.get_me()).username
        link = f"https://t.me/{bot_username}?start=ref_{user_id}"
        await query.edit_message_text(
            f"👥 Твоя реферальная ссылка:\n<code>{link}</code>\n\nЗа каждого друга — 30 монеток.",
            reply_markup=tasks_menu(),
            parse_mode="HTML"
        )

    elif data == "buy_coins":
        keyboard = []
        for pack in COIN_PACKS:
            keyboard.append([InlineKeyboardButton(
                f"{pack['name']} — {pack['stars']} ⭐",
                callback_data=f"buy_pack_{pack['id']}"
            )])
        keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="main")])
        await query.edit_message_text("Выбери пакет:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("buy_pack_"):
        pack_id = data.replace("buy_pack_", "")
        pack = next((p for p in COIN_PACKS if p["id"] == pack_id), None)
        if pack:
            await context.bot.send_invoice(
                chat_id=user_id,
                title=pack["name"],
                description=f"Пополнение баланса на {pack['coins']} монеток",
                payload=f"pack_{pack_id}_{user_id}",
                provider_token="",
                currency="XTR",
                prices=[LabeledPrice(pack["name"], pack["stars"])]
            )

    elif data == "shop":
        await query.edit_message_text("🔥 Магазин:", reply_markup=shop_menu())

    elif data.startswith("buy_item_"):
        item_id = data.replace("buy_item_", "")
        item = next((i for i in SHOP_ITEMS if i["id"] == item_id), None)
        if not item:
            return
        user = get_user(user_id)
        if user["balance"] < item["price"]:
            await query.answer("Недостаточно монеток", show_alert=True)
            return
        if not item["file_id"]:
            await query.answer("Фото ещё не загружено", show_alert=True)
            return
        update_balance(user_id, -item["price"])
        await context.bot.send_photo(user_id, item["file_id"], caption=f"Твоё фото: {item['name']}")
        await query.answer("✅ Фото отправлено!", show_alert=True)

async def precheckout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.pre_checkout_query.answer(ok=True)

async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    payment = update.message.successful_payment
    payload = payment.invoice_payload
    parts = payload.split("_")
    if len(parts) >= 3 and parts[0] == "pack":
        pack_id = parts[1]
        user_id = int(parts[2])
        pack = next((p for p in COIN_PACKS if p["id"] == pack_id), None)
        if pack:
            update_balance(user_id, pack["coins"])
            await update.message.reply_text(f"✅ Оплата прошла! Начислено {pack['coins']} монеток.")

def main():
    init_db()
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(PreCheckoutQueryHandler(precheckout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))

    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
