import json
import os
from collections import Counter
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# ====== CONFIG ======
BOT_TOKEN = "8456296990:AAGNAwQnmBX0yp11NdOSwxtsqqBto1Rhzho"
PASSWORD = "angela"
DATA_FILE = "data.json"

GROUPS = {
    1: range(1, 10),
    2: range(10, 20),
    3: range(20, 30),
    4: range(30, 40),
    5: range(40, 50),
}

COLOURS = {
    1: "red", 2: "blue", 3: "green", 4: "red", 5: "blue", 6: "green",
    7: "red", 8: "blue", 9: "green", 10: "red", 11: "blue", 12: "green",
    13: "red", 14: "blue", 15: "green", 16: "red", 17: "blue", 18: "green",
    19: "red", 20: "blue", 21: "green", 22: "red", 23: "blue", 24: "green",
    25: "red", 26: "blue", 27: "green", 28: "red", 29: "blue", 30: "green",
    31: "red", 32: "blue", 33: "green", 34: "red", 35: "blue", 36: "green",
    37: "red", 38: "blue", 39: "green", 40: "red", 41: "blue", 42: "green",
    43: "red", 44: "blue", 45: "green", 46: "red", 47: "blue", 48: "green",
    49: "yellow"
}

# ====== STATE ======
user_states = {}
# Possible states: WAIT_PASSWORD, WAIT_DRAW, WAIT_HOT

# ====== DATA ======
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"draws": [], "last_result": None}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

# ====== HELPERS ======
def group_of(number):
    for g, rng in GROUPS.items():
        if number in rng:
            return g
    return None

def dominating_colour(draws, last_n=5):
    recent = draws[-last_n:] if len(draws) >= last_n else draws
    colour_counts = Counter()
    for draw in recent:
        for n in draw:
            colour_counts[COLOURS.get(n, "")] += 1
    if not colour_counts:
        return None
    return colour_counts.most_common(1)[0][0]

# ====== PREDICTION ======
def predict(draws, hot_numbers):
    if not draws:
        return "no bet (no history)"

    current_draw = draws[-1]

    # Count how many numbers from each group appear in the current draw
    group_counts = Counter(group_of(n) for n in current_draw)
    if not group_counts:
        return f"no bet (no group data) (previous: {get_last_result()})"

    # Find group with most numbers in current draw
    max_group, max_count = group_counts.most_common(1)[0]

    # Filter hot numbers to only those in max group
    hot_in_max_group = [n for n in hot_numbers if group_of(n) == max_group]

    if not hot_in_max_group:
        return f"no bet (no hot numbers in max group) (previous: {get_last_result()})"

    # Find dominating colour in last 5 draws
    dom_colour = dominating_colour(draws, 5)
    if dom_colour:
        # Exclude hot numbers belonging to dominating colour
        candidates = [n for n in hot_in_max_group if COLOURS.get(n) != dom_colour]
    else:
        candidates = hot_in_max_group

    if not candidates:
        return f"no bet (all hot nums excluded by dominating colour) (previous: {get_last_result()})"

    # Pick candidate with lowest frequency in last 10 draws (tie-break by smallest number)
    freq = {n: sum(n in d for d in draws) for n in candidates}
    pick = min(candidates, key=lambda x: (freq[x], x))

    return f"{pick} (previous: {get_last_result()})"

def get_last_result():
    data = load_data()
    return data.get("last_result", "none")

# ====== HANDLER ======
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    state = user_states.get(user_id, "WAIT_PASSWORD")
    data = load_data()

    if state == "WAIT_PASSWORD":
        if text == PASSWORD:
            user_states[user_id] = "WAIT_DRAW"
            await update.message.reply_text("Password correct. Enter current draw (6 numbers separated by spaces):")
        else:
            await update.message.reply_text("Incorrect password. Try again.")

    elif state == "WAIT_DRAW":
        try:
            draw = list(map(int, text.split()))
            if len(draw) != 6 or any(n < 1 or n > 49 for n in draw):
                raise ValueError
            data["draws"].append(draw)
            data["draws"] = data["draws"][-10:]  # keep last 10
            save_data(data)
            user_states[user_id] = "WAIT_HOT"
            await update.message.reply_text("Enter Hot Numbers (5 numbers separated by spaces):")
        except ValueError:
            await update.message.reply_text("Invalid format. Enter exactly 6 numbers between 1 and 49.")

    elif state == "WAIT_HOT":
        try:
            hot_numbers = list(map(int, text.split()))
            if len(hot_numbers) != 5 or any(n < 1 or n > 49 for n in hot_numbers):
                raise ValueError

            result = predict(load_data()["draws"], hot_numbers)
            await update.message.reply_text(result)

            # Mark last_result "win" if pick in current draw else "loss"
            last_draw = load_data()["draws"][-1]
            picked_num = None
            if "(" in result:
                picked_num = int(result.split()[0]) if result.split()[0].isdigit() else None

            if picked_num and picked_num in last_draw:
                data["last_result"] = "win"
            else:
                data["last_result"] = "loss"
            save_data(data)

            user_states[user_id] = "WAIT_DRAW"
        except ValueError:
            await update.message.reply_text("Invalid format. Enter exactly 5 numbers between 1 and 49.")

# ====== MAIN ======
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot is running...")
    app.run_polling()
