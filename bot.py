import os
import random
import asyncio
from aiohttp import web

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ---------------- env ----------------

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("BOT_TOKEN не задан")

# ---------------- memory ----------------

user_balance = {}

# ---------------- telegram app ----------------

app = ApplicationBuilder().token(TOKEN).build()


# ---------------- handlers ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Привет! /earn /balance")


async def earn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    roll = random.random()

    if roll < 0.75:
        coins = random.randint(10, 50)
    elif roll < 0.95:
        coins = random.randint(51, 130)
    elif roll < 0.995:
        coins = random.randint(131, 200)
    else:
        coins = random.randint(300, 855)

    user_balance[user_id] = user_balance.get(user_id, 0) + coins

    await update.message.reply_text(f"+{coins} 💰 Баланс: {user_balance[user_id]}")


async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text(f"Баланс: {user_balance.get(user_id, 0)} 💸")


app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("earn", earn))
app.add_handler(CommandHandler("balance", balance))


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

    # health check (для UptimeRobot)
    server.router.add_get("/", ping)

    # webhook endpoint (стабильный)
    server.router.add_post("/webhook", webhook_handler)

    runner = web.AppRunner(server)
    await runner.setup()

    site = web.TCPSite(runner, "0.0.0.0", 10000)
    await site.start()

    # 🔥 FIX: правильный Replit URL
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