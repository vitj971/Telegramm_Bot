import random
import asyncio
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

user_balance = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Привет! мои команды: /start , /earn , /balance")

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

async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("earn", earn))
    app.add_handler(CommandHandler("balance", balance))

    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())