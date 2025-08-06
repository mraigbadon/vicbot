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
import re

# ==== Configuration ====
TOKEN = "8456296990:AAGNAwQnmBX0yp11NdOSwxtsqqBto1Rhzho"
PASSWORD = "angela"
DATA_FILE = "data.json"
authorized_users = set()

# ==== Color Logic ====
def get_color(number):
    number = int(number)
    if number == 49:
        return "Yellow"
    colors = ["Red", "Blue", "Green"]
    return colors[(number - 1) % 3]

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

def was_last_prediction_correct(draws, prediction):
    if not prediction or len(draws) < 2:
        return "❓ No previous prediction to check."
    last_draw = draws[-2]["current"]
    return "✅ Win! 🎯" if prediction in last_draw else "❌ Miss."

def get_top_15_most_likely(draws):
    all_numbers = [num for draw in draws for num in draw["current"]]
    count = {i: all_numbers.count(i) for i in range(1, 50)}
    sorted_freq = sorted(count.items(), key=lambda x: x[1], reverse=True)
    return [num for num, _ in sorted_freq[:15]]

def predict_dominant_color(draws):
    all_colors = []
    for draw in draws:
        colors = [get_color(n) for n in draw["current"]]
        all_colors.extend(colors)

    color_count = {"Red": 0, "Blue": 0, "Green": 0}
    for color in all_colors:
        if color in color_count:
            color_count[color] += 1

    total = sum(color_count.values())
    if total == 0:
        return "No color data"

    percentages = {color: round((count / total) * 100, 1) for color, count in color_count.items()}
    dominant = max(percentages, key=percentages.get)
    return f"🎨 Color tip: {dominant} likely to drop 3+ times ({percentages[dominant]}%)"

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
        parts = [int(x) for x in re.split(r"[,\s]+", text) if x.strip().isdigit()]
        
        if len(parts) != 11:
            raise ValueError

        current = parts[:6]
        hot = parts[6:]

        data = load_data()

        # Predict before saving new draw
        prediction, confidence = predict_least_likely(data, hot)

        # Append the new draw
        data.append({"current": current, "hot": hot})
        save_data(data)

        # Check if last prediction hit
        result = was_last_prediction_correct(data, prediction)

        # Get 15 most likely numbers
        top15 = get_top_15_most_likely(data)
        top15_str = ", ".join(str(n) for n in top15)

        # Color prediction
        color_tip = predict_dominant_color(data)

        # Final message
        msg = f"🎯 Prediction: {prediction} ({confidence}%)\n{result}\n\n🔥 Top 15 most likely: {top15_str}\n\n{color_tip}"
        await update.message.reply_text(msg)

    except:
        await update.message.reply_text("⚠️ Invalid format. Send 11 numbers separated by commas or spaces.")

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
