import os
import random
import asyncio
import time
import sqlite3
from aiohttp import web

from telegram import Update, BotCommand
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ---------------- CONFIG ----------------

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("BOT_TOKEN не задан")

GLOBAL_COOLDOWN = 3
DAILY_COOLDOWN = 24 * 60 * 60

# ---------------- DB ----------------

conn = sqlite3.connect("bot.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    balance INTEGER DEFAULT 0,
    last_daily INTEGER DEFAULT 0,
    last_action INTEGER DEFAULT 0
)
""")
conn.commit()


def ensure_user(user):
    cur.execute("""
        INSERT OR IGNORE INTO users (user_id, username, first_name, balance, last_daily, last_action)
        VALUES (?, ?, ?, 0, 0, 0)
    """, (user.id, user.username or "", user.first_name or "Игрок"))

    cur.execute("""
        UPDATE users
        SET username=?, first_name=?
        WHERE user_id=?
    """, (user.username or "", user.first_name or "Игрок", user.id))

    conn.commit()


def get_user(user_id):
    cur.execute("""
        SELECT username, first_name, balance, last_daily, last_action
        FROM users
        WHERE user_id=?
    """, (user_id,))
    return cur.fetchone()


def update_user(user_id, username, first_name, balance, last_daily, last_action):
    cur.execute("""
        UPDATE users
        SET username=?, first_name=?, balance=?, last_daily=?, last_action=?
        WHERE user_id=?
    """, (username, first_name, balance, last_daily, last_action, user_id))
    conn.commit()


def get_top(limit=10):
    cur.execute("""
        SELECT username, first_name, balance
        FROM users
        ORDER BY balance DESC
        LIMIT ?
    """, (limit,))
    return cur.fetchall()


# ---------------- COOLDOWN ----------------

def check_cd(user_id):
    cur.execute("SELECT last_action FROM users WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    if not row:
        return False

    return (time.time() - row[0]) < GLOBAL_COOLDOWN


def set_cd(user_id):
    cur.execute("""
        UPDATE users
        SET last_action=?
        WHERE user_id=?
    """, (int(time.time()), user_id))
    conn.commit()


# ---------------- BOT ----------------

app = ApplicationBuilder().token(TOKEN).build()


# ---------------- START ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ensure_user(update.effective_user)
    await update.message.reply_text("👋 Привет! /earn /daily /pay /balance /top")


# ---------------- BALANCE ----------------

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ensure_user(user)

    if check_cd(user.id):
        await update.message.reply_text("⏳ Подожди 3 секунды")
        return
    set_cd(user.id)

    _, _, bal, _, _ = get_user(user.id)

    await update.message.reply_text(f"💎 Баланс: {bal} Бебракоинов")


# ---------------- EARN ----------------

async def earn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ensure_user(user)

    if check_cd(user.id):
        await update.message.reply_text("⏳ Подожди 3 секунды")
        return
    set_cd(user.id)

    username = user.username or ""
    name = user.first_name or "Игрок"

    _, _, balance, _, _ = get_user(user.id)

    roll = random.random()

    if roll < 0.69:
        coins = random.randint(10, 35)
    elif roll < 0.89:
        coins = random.randint(36, 70)
    elif roll < 0.96:
        coins = random.randint(71, 120)
    elif roll < 0.993:
        coins = random.randint(121, 155)
    else:
        coins = random.randint(233, 855)

    balance += coins

    update_user(user.id, username, name, balance, 0, int(time.time()))

    await update.message.reply_text(f"💰 {name} получил {coins} Бебракоинов! 🎉")


# ---------------- PAY ----------------

async def pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ensure_user(user)

    if check_cd(user.id):
        await update.message.reply_text("⏳ Подожди 3 секунды")
        return
    set_cd(user.id)

    args = context.args

    if len(args) < 2:
        await update.message.reply_text("Используй: /pay сумма @user")
        return

    try:
        amount = int(args[0])
    except:
        await update.message.reply_text("❌ Неверная сумма")
        return

    if amount < 1 or amount > 1_000_000:
        await update.message.reply_text("❌ 1 - 1 000 000")
        return

    target = args[1].replace("@", "")

    cur.execute("SELECT user_id, balance FROM users WHERE username=?", (target,))
    row = cur.fetchone()

    if not row:
        await update.message.reply_text("❌ Игрок не найден")
        return

    receiver_id, receiver_balance = row

    _, _, sender_balance, _, _ = get_user(user.id)

    if sender_balance < amount:
        await update.message.reply_text("❌ Нет денег")
        return

    sender_balance -= amount
    receiver_balance += amount

    update_user(user.id, user.username or "", user.first_name or "Игрок", sender_balance, 0, int(time.time()))
    update_user(receiver_id, target, "", receiver_balance, 0, 0)

    await update.message.reply_text(
        f"{user.first_name} дал {amount} Бебракоинов @{target} 💸"
    )


# ---------------- DAILY ----------------

async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ensure_user(user)

    if check_cd(user.id):
        await update.message.reply_text("⌛ Подожди 3 секунды")
        return
    set_cd(user.id)

    username = user.username or ""
    name = user.first_name or "Игрок"

    _, _, balance, last_daily, _ = get_user(user.id)

    now = int(time.time())

    if now - last_daily < DAILY_COOLDOWN:
        remaining = DAILY_COOLDOWN - (now - last_daily)
        h = remaining // 3600
        m = (remaining % 3600) // 60

        await update.message.reply_text(
            f"❌ Уже получал!\nПриходи через {h}ч {m}м ☝️"
        )
        return

    roll = random.random()

    if roll < 0.33:
        reward = 100
    elif roll < 0.66:
        reward = 150
    elif roll < 0.99:
        reward = 200
    else:
        reward = 750

    balance += reward

    update_user(user.id, username, name, balance, now, int(time.time()))

    if reward == 750:
        text = f"Похоже найден счастливчик! {name} получил {reward} Бебракоинов! 🍀"
    else:
        text = f"{name} получил ежедневный приз {reward} Бебракоинов! ✨"

    await update.message.reply_text(text)


# ---------------- TOP ----------------

async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if check_cd(update.effective_user.id):
        await update.message.reply_text("⌛ Подожди 3 секунды")
        return
    set_cd(update.effective_user.id)

    data = get_top(10)

    medals = ["🥇", "🥈", "🥉"]
    text = "🏆 Топ игроков:\n\n"

    for i, (username, name, bal) in enumerate(data):
        display = f"@{username}" if username else name
        medal = medals[i] if i < 3 else f"{i+1}."
        text += f"{medal} {display} — {bal} 💰\n"

    await update.message.reply_text(text)


# ---------------- COMMAND MENU ----------------

async def set_commands(app):
    await app.bot.set_my_commands([
        BotCommand("earn", "Заработать"),
        BotCommand("daily", "Ежедневный бонус"),
        BotCommand("pay", "Перевод"),
        BotCommand("balance", "Баланс"),
        BotCommand("top", "Топ"),
        BotCommand("start", "Старт"),
    ])


# ---------------- SERVER ----------------

async def run():
    await app.initialize()
    await app.start()

    await set_commands(app)

    print("Bot started 🤖")

    while True:
        await asyncio.sleep(3600)


# ---------------- HANDLERS ----------------

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("earn", earn))
app.add_handler(CommandHandler("balance", balance))
app.add_handler(CommandHandler("pay", pay))
app.add_handler(CommandHandler("daily", daily))
app.add_handler(CommandHandler("top", top))


if __name__ == "__main__":
    asyncio.run(run())