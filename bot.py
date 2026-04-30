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

COOLDOWN = 4 * 60 * 60  # 4 часа

# ---------------- DATABASE ----------------

conn = sqlite3.connect("bot.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    balance INTEGER DEFAULT 0,
    last_earn INTEGER DEFAULT 0
)
""")
conn.commit()


def get_user(user_id):
    cur.execute("""
        SELECT username, first_name, balance, last_earn
        FROM users
        WHERE user_id=?
    """, (user_id,))
    row = cur.fetchone()

    if not row:
        cur.execute("""
            INSERT INTO users (user_id, username, first_name, balance, last_earn)
            VALUES (?, '', '', 0, 0)
        """, (user_id,))
        conn.commit()
        return "", "", 0, 0

    return row


def save_user(user_id, username, first_name, balance, last_earn):
    cur.execute("""
        UPDATE users
        SET username=?, first_name=?, balance=?, last_earn=?
        WHERE user_id=?
    """, (username, first_name, balance, last_earn, user_id))
    conn.commit()


def get_top_users(limit=10):
    cur.execute("""
        SELECT first_name, username, balance
        FROM users
        ORDER BY balance DESC
        LIMIT ?
    """, (limit,))
    return cur.fetchall()


# ---------------- BOT ----------------

app = ApplicationBuilder().token(TOKEN).build()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Привет! Выбери /earn /balance /top")


async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    _, _, balance, _ = get_user(user_id)

    await update.message.reply_text(f"💰 Баланс: {balance} Бебракоинов")


async def earn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id

    username = user.username or ""
    first_name = user.first_name or "Игрок"

    _, _, balance, last_earn = get_user(user_id)
    now = int(time.time())

    # cooldown
    if now - last_earn < COOLDOWN:
        remaining = COOLDOWN - (now - last_earn)
        hours = remaining // 3600
        minutes = (remaining % 3600) // 60

        await update.message.reply_text(
            f"⏳ Подожди {hours}ч {minutes}м перед следующим заработком!"
        )
        return

    roll = random.random()

    if roll < 0.69:
        coins = random.randint(10, 35)
        text = f"💰 {first_name} получил премию: {coins} Бебракоинов! 🎉"

    elif roll < 0.89:
        coins = random.randint(36, 70)
        text = f"💰 {first_name} получил премию: {coins} Бебракоинов! 🎉"

    elif roll < 0.96:
        coins = random.randint(71, 120)
        text = f"💰 {first_name} получил премию: {coins} Бебракоинов! 🎉"

    elif roll < 0.993:
        coins = random.randint(121, 155)
        text = f"💰 {first_name} получил премию: {coins} Бебракоинов! 🎉"

    else:
        coins = random.randint(233, 855)
        text = f"😱 {first_name} нашёл {coins} Бебракоинов! 💸"

    balance += coins

    save_user(user_id, username, first_name, balance, now)

    await update.message.reply_text(text)


async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top_users = get_top_users(10)

    if not top_users:
        await update.message.reply_text("Пока нет игроков 😢")
        return

    medals = ["🥇", "🥈", "🥉"]

    text = "🏆 Топ игроков:\n\n"

    for i, (first_name, username, balance) in enumerate(top_users):

        if username:
            name = f"@{username}"
        else:
            name = first_name or "Игрок"

        medal = medals[i] if i < 3 else f"{i+1}."

        text += f"{medal} {name} — {balance} 💰\n"

    await update.message.reply_text(text)


# ---------------- COMMAND MENU (/ /commands) ----------------

async def set_commands(app):
    await app.bot.set_my_commands([
        BotCommand("earn", "Заработать Бебракоины"),
        BotCommand("balance", "Показать баланс"),
        BotCommand("top", "Топ игроков"),
        BotCommand("start", "Старт"),
    ])


# ---------------- HANDLERS ----------------

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("earn", earn))
app.add_handler(CommandHandler("balance", balance))
app.add_handler(CommandHandler("top", top))


# ---------------- WEB SERVER ----------------

async def ping(request):
    return web.Response(text="ok")


async def webhook_handler(request):
    try:
        data = await request.json()
        update = Update.de_json(data, app.bot)
        await app.process_update(update)
    except Exception as e:
        print("Webhook error:", e)

    return web.Response(text="ok")


async def run_server():
    await app.initialize()
    await app.start()

    # 🔥 SET COMMAND MENU HERE
    await set_commands(app)

    server = web.Application()
    server.router.add_get("/", ping)
    server.router.add_post("/webhook", webhook_handler)

    runner = web.AppRunner(server)
    await runner.setup()

    site = web.TCPSite(runner, "0.0.0.0", 10000)
    await site.start()

    repl_slug = os.getenv("REPL_SLUG")
    repl_owner = os.getenv("REPL_OWNER")

    BASE_URL = f"https://{repl_slug}.{repl_owner}.repl.co"
    webhook_url = f"{BASE_URL}/webhook"

    await app.bot.set_webhook(url=webhook_url)

    print("🤖 Bot started:", webhook_url)

    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(run_server())