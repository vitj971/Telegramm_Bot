import random
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from aiohttp import web

TOKEN = os.getenv("BOT_TOKEN")
URL = os.getenv("RENDER_EXTERNAL_URL")  # Render даст его сам

user_balance = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Привет! /earn /balance")

# ... твои handlers (earn, balance) без изменений ...

def create_app():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("earn", earn))
    app.add_handler(CommandHandler("balance", balance))

    return app

telegram_app = create_app()

async def handle(request):
    data = await request.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return web.Response()

async def main():
    web_app = web.Application()
    web_app.router.add_post(f"/{TOKEN}", handle)

    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 10000)
    await site.start()

    await telegram_app.bot.set_webhook(f"{URL}/{TOKEN}")

    print("Bot started (webhook mode)")

    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

TOKEN = os.getenv("BOT_TOKEN")

user_balance = {}

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

    await update.message.reply_text(
        f"+{coins} 💰 Баланс: {user_balance[user_id]}"
    )

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text(
        f"Баланс: {user_balance.get(user_id, 0)} 💸"
    )

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("earn", earn))
    app.add_handler(CommandHandler("balance", balance))

    print("Bot started")
    app.run_polling()

if __name__ == "__main__":
    main()