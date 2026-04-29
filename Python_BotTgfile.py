import random
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "8698374492:AAGSLSkT7NKsEi9YpLO_R8V1PpQZeNZGt1A"

user_balance = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Привет! мои команды: /earn ; /start ; /balance 🙂")

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

    if user_id not in user_balance:
        user_balance[user_id] = 0

    user_balance[user_id] += coins

    await update.message.reply_text(
        f"Ты заработал {coins} Бебракоинов! 💰\n"
        f"Баланс: {user_balance[user_id]} 💸"
    )

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in user_balance:
        user_balance[user_id] = 0

    await update.message.reply_text(
        f"Твой баланс: {user_balance[user_id]} 💸"
    )

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("earn", earn))
    app.add_handler(CommandHandler("balance", balance))

    print("Запуск...")
    app.run_polling()

if __name__ == "__main__":
    main()