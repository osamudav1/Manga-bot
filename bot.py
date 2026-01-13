import telebot
import time
import json
import os

from telebot import types
from config import (
    BOT_TOKEN,
    OWNER_ID,
    CHANNEL_ID,
    BATCH_SIZE,
    COOLDOWN
)
from buttons import main_menu

bot = telebot.TeleBot(BOT_TOKEN)

STATE_FILE = "state.json"
CAPTIONS_FILE = "captions.json"
EPISODES_FILE = "episodes.json"
METADATA_FILE = "metadata.json"

# ---------------- UTIL ----------------

def load_json(file, default):
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump(default, f)
    with open(file, "r") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def owner_only(message):
    return message.from_user.id == OWNER_ID

# ---------------- STATE ----------------

def get_state():
    return load_json(STATE_FILE, {"mode": None})

def set_state(mode):
    save_json(STATE_FILE, {"mode": mode})

# ---------------- START ----------------

@bot.message_handler(commands=["start"])
def start(message):
    if not owner_only(message):
        return
    bot.send_message(
        message.chat.id,
        "Welcome Owner!",
        reply_markup=main_menu()
    )

# ---------------- HELP ----------------

@bot.message_handler(func=lambda m: m.text == "❓ Help")
def help_cmd(message):
    if not owner_only(message):
        return
    bot.send_message(
        message.chat.id,
        "🧩 Flow:\n"
        "1️⃣ Edit Caption\n"
        "2️⃣ Post Video\n"
        "3️⃣ Send videos (max 100)\n"
        "4️⃣ Bot auto posts with episode\n"
    )

# ---------------- RESET ----------------

@bot.message_handler(func=lambda m: m.text == "⚙ Reset Titles")
def reset_all(message):
    if not owner_only(message):
        return

    save_json(CAPTIONS_FILE, {})
    save_json(EPISODES_FILE, {})
    save_json(METADATA_FILE, {})

    bot.send_message(
        message.chat.id,
        "✅ All titles, captions cleared.\nEpisode reset to 1."
    )

# ---------------- EDIT CAPTION ----------------

@bot.message_handler(func=lambda m: m.text == "📝 Edit Caption")
def edit_caption(message):
    if not owner_only(message):
        return
    set_state("WAIT_CAPTION")
    bot.send_message(
        message.chat.id,
        "✏️ Send caption text now.\n(Title + Description)"
    )

@bot.message_handler(func=lambda m: get_state()["mode"] == "WAIT_CAPTION")
def save_caption(message):
    if not owner_only(message):
        return

    captions = load_json(CAPTIONS_FILE, {})
    captions["current"] = message.text
    save_json(CAPTIONS_FILE, captions)

    # reset episode
    episodes = load_json(EPISODES_FILE, {})
    episodes["current"] = 1
    save_json(EPISODES_FILE, episodes)

    set_state(None)

    bot.send_message(
        message.chat.id,
        "✅ Caption saved.\nEpisode reset to 1.",
        reply_markup=main_menu()
    )

# ---------------- POST VIDEO ----------------

@bot.message_handler(func=lambda m: m.text == "📺 Post Video")
def post_video(message):
    if not owner_only(message):
        return
    set_state("WAIT_VIDEO")
    bot.send_message(
        message.chat.id,
        "📤 Send videos now (max 100).\nBot will auto post."
    )

# ---------------- VIDEO HANDLER ----------------

@bot.message_handler(content_types=["video"])
def handle_video(message):
    if not owner_only(message):
        return

    state = get_state()
    if state["mode"] != "WAIT_VIDEO":
        return

    captions = load_json(CAPTIONS_FILE, {})
    episodes = load_json(EPISODES_FILE, {})

    caption_text = captions.get("current", "No Caption")
    ep = episodes.get("current", 1)

    final_caption = f"{caption_text}\n\n📺 Episode {ep:02d}"

    bot.send_video(
        CHANNEL_ID,
        message.video.file_id,
        caption=final_caption
    )

    episodes["current"] = ep + 1
    save_json(EPISODES_FILE, episodes)

    # batch control
    if ep % BATCH_SIZE == 0:
        time.sleep(COOLDOWN)

# ---------------- DONE COMMAND ----------------

@bot.message_handler(commands=["done"])
def done_posting(message):
    if not owner_only(message):
        return
    set_state(None)
    bot.send_message(
        message.chat.id,
        "✅ All videos posted successfully!",
        reply_markup=main_menu()
    )

# ---------------- RUN ----------------

print("Bot is running...")
bot.infinity_polling()
