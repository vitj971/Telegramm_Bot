print("TOKEN:", os.getenv("BOT_TOKEN"))
print("URL:", os.getenv("RENDER_EXTERNAL_URL"))

import os
import random
import asyncio
from aiohttp import web

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
BASE_URL = os.getenv("RENDER_EXTERNAL_URL")

user_balance = {}

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

# ---------------- telegram app ----------------

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("earn", earn))
app.add_handler(CommandHandler("balance", balance))

# ---------------- webhook server ----------------

async def webhook_handler(request):
    data = await request.json()
    update = Update.de_json(data, app.bot)
    await app.process_update(update)
    return web.Response()

async def run_server():
    if not TOKEN:
        raise ValueError("BOT_TOKEN не задан")
    if not BASE_URL:
        raise ValueError("RENDER_EXTERNAL_URL не задан")

    server = web.Application()
    server.router.add_post(f"/{TOKEN}", webhook_handler)

    runner = web.AppRunner(server)
    await runner.setup()

    site = web.TCPSite(runner, "0.0.0.0", 10000)
    await site.start()

    await app.bot.set_webhook(f"{BASE_URL}/{TOKEN}")

    print("Bot started (webhook mode)")

    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(run_server())