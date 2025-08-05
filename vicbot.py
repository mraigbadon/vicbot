from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import json
import os

# ==== Configuration ====
TOKEN = "8456296990:AAGNAwQnmBX0yp11NdOSwxtsqqBto1Rhzho"  # Replace with your actual token
PASSWORD = "angela"
DATA_FILE = "data.json"
authorized_users = set()


# ==== Persistent Data ====
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


# ==== Prediction Logic ====
def predict_least_likely(draws, hot_numbers):
    all_numbers = [num for draw in draws for num in draw["current"]]
    count = {str(i): all_numbers.count(i) for i in range(1, 50)}
    sorted_hot = sorted(hot_numbers, key=lambda x: count.get(str(x), 0))
    if sorted_hot:
        selected = sorted_hot[0]
        total = sum(count.get(str(n), 0) for n in hot_numbers)
        confidence = 100 - ((count.get(str(selected), 0) / total) * 100) if total else 100
        return selected, round(confidence, 2)
    return None, 0


# ==== Telegram Handlers ====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔐 Welcome to Victory's Money Bot:")

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip()

    if user_id not in authorized_users:
        if text == PASSWORD:
            authorized_users.add(user_id)
            await update.message.reply_text("✅ Access granted. Send 11 numbers")
        else:
            await update.message.reply_text("❌ Incorrect password. Try again.")
        return

    try:
        parts = [int(x.strip()) for x in text.split(",")]
        if len(parts) != 11:
            raise ValueError

        current = parts[:6]
        hot = parts[6:]

        data = load_data()
        data.append({"current": current, "hot": hot})
        save_data(data)

        prediction, confidence = predict_least_likely(data, hot)
        if prediction:
            await update.message.reply_text(f"❌ Avoid: {prediction} ({confidence}%)")
        else:
            await update.message.reply_text("⚠️ Couldn’t generate prediction. Try again.")
    except:
        await update.message.reply_text("⚠️ Invalid format. Send 11 numbers separated by commas.")

async def logout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id in authorized_users:
        authorized_users.remove(user_id)
        await update.message.reply_text("🔓 Logged out. Type /start to log in again.")
    else:
        await update.message.reply_text("❗You are not logged in.")


# ==== Main Entrypoint ====
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("logout", logout))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    app.run_polling()

main()
