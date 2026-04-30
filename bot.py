import os
import random
import asyncio
import time
import sqlite3
from aiohttp import web

from telegram import Update
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
    balance INTEGER DEFAULT 0,
    last_earn INTEGER DEFAULT 0
)
""")
conn.commit()


def get_user(user_id):
    cur.execute("SELECT balance, last_earn FROM users WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    if not row:
        cur.execute("INSERT INTO users (user_id, balance, last_earn) VALUES (?, 0, 0)", (user_id,))
        conn.commit()
        return 0, 0
    return row


def update_user(user_id, balance, last_earn):
    cur.execute(
        "REPLACE INTO users (user_id, balance, last_earn) VALUES (?, ?, ?)",
        (user_id, balance, last_earn)
    )
    conn.commit()


# ---------------- BOT ----------------

app = ApplicationBuilder().token(TOKEN).build()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Привет! Используй /earn и /balance")


async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    balance, _ = get_user(user_id)

    await update.message.reply_text(f"💰 Баланс: {balance} Бебракоинов")


async def earn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    name = user.first_name

    balance, last_earn = get_user(user_id)
    now = int(time.time())

    # cooldown check
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
        text = f"💰 {name} получил премию в сумму: {coins} Бебракоинов! 🎉"

    elif roll < 0.89:  # 69 + 20
        coins = random.randint(36, 70)
        text = f"💰 {name} получил премию в сумму: {coins} Бебракоинов! 🎉"

    elif roll < 0.96:  # +7
        coins = random.randint(71, 120)
        text = f"💰 {name} получил премию в сумму: {coins} Бебракоинов! 🎉"

    elif roll < 0.993:  # +3.3
        coins = random.randint(121, 155)
        text = f"💰 {name} получил премию в сумму: {coins} Бебракоинов! 🎉"

    else:  # 0.7%
        coins = random.randint(233, 855)
        text = f"😱 Ничего себе! {name} по дороге на работу нашёл {coins} Бебракоинов! Вот это везение! 💸"

    balance += coins
    update_user(user_id, balance, now)

    await update.message.reply_text(text)
 
    async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top_users = get_top_users(10)

    if not top_users:
        await update.message.reply_text("Пока нет игроков 😢")
        return

    text = "🏆 Топ игроков:\n\n"

    for i, (user_id, balance) in enumerate(top_users, start=1):
        text += f"{i}. ID {user_id} — {balance} 💰\n"

    await update.message.reply_text(text)


# ---------------- handlers ----------------

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("earn", earn))
app.add_handler(CommandHandler("balance", balance))
app.add_handler(CommandHandler("top", top))


# ---------------- webhook ----------------

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