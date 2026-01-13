import os
import json
import time
from telebot import TeleBot, types
from config import *
from buttons import main_menu

bot = TeleBot(BOT_TOKEN)

# Load metadata
if os.path.exists(METADATA_FILE):
    with open(METADATA_FILE, "r") as f:
        metadata = json.load(f)
else:
    metadata = {}

# Load episodes
if os.path.exists(EPISODE_FILE):
    with open(EPISODE_FILE, "r") as f:
        episodes = json.load(f)
else:
    episodes = {}

# Load captions
if os.path.exists(CAPTIONS_FILE):
    with open(CAPTIONS_FILE, "r") as f:
        captions = json.load(f)
else:
    captions = {}

# ----------------------------
# Owner-only decorator
# ----------------------------
def owner_only(func):
    def wrapper(message, *args, **kwargs):
        if message.chat.id != OWNER_ID:
            return
        return func(message, *args, **kwargs)
    return wrapper

# ----------------------------
# Start command
# ----------------------------
@bot.message_handler(commands=['start'])
@owner_only
def start_menu(msg):
    bot.send_message(msg.chat.id, "Welcome Owner!", reply_markup=main_menu())

# ----------------------------
# Reset Titles
# ----------------------------
@bot.message_handler(func=lambda m: m.text == "⚙ Reset Titles")
@owner_only
def reset_titles(msg):
    global metadata, episodes, captions
    metadata = {}
    episodes = {}
    captions = {}
    # Save to files
    with open(METADATA_FILE, "w") as f:
        json.dump(metadata, f)
    with open(EPISODE_FILE, "w") as f:
        json.dump(episodes, f)
    with open(CAPTIONS_FILE, "w") as f:
        json.dump(captions, f)
    bot.send_message(msg.chat.id, "✅ All titles, captions cleared. Episode counters reset to 1.\nNow you can add new titles.")

# ----------------------------
# Edit Caption
# ----------------------------
@bot.message_handler(func=lambda m: m.text == "📝 Edit Caption")
@owner_only
def edit_caption(msg):
    video_files = [f for f in os.listdir(VIDEO_FOLDER) if f.endswith(".mp4")]
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for f in video_files:
        keyboard.add(f)
    bot.send_message(msg.chat.id, "Select a title to edit caption:", reply_markup=keyboard)

@bot.message_handler(func=lambda m: m.text.endswith(".mp4"))
@owner_only
def select_title(msg):
    video = msg.text
    title = os.path.splitext(video)[0]
    current_caption = captions.get(video, metadata.get(title, "No description"))
    episode_num = episodes.get(title, 0) + 1
    bot.send_message(msg.chat.id,
        f"Title: {title}\nCurrent Caption:\n{current_caption}\nEpisode: {episode_num}\n\nSend new caption text or /skip to keep default."
    )
    bot.register_next_step_handler(msg, receive_caption, video)

def receive_caption(msg, video):
    title = os.path.splitext(video)[0]
    if msg.text == "/skip":
        captions[video] = metadata.get(title, "No description")
    else:
        captions[video] = msg.text
    episodes[title] = episodes.get(title, 0) + 1
    # Save files
    with open(CAPTIONS_FILE, "w") as f:
        json.dump(captions, f)
    with open(EPISODE_FILE, "w") as f:
        json.dump(episodes, f)
    bot.send_message(msg.chat.id, f"✅ Caption set for {title} Episode {episodes[title]}")

# ----------------------------
# Post Videos + Forward
# ----------------------------
@bot.message_handler(func=lambda m: m.text == "📺 Post Video")
@owner_only
def post_videos(msg):
    video_files = [f for f in os.listdir(VIDEO_FOLDER) if f.endswith(".mp4")]
    video_files.sort()
    for i in range(0, len(video_files), BATCH_SIZE):
        batch = video_files[i:i+BATCH_SIZE]
        for v in batch:
            title = os.path.splitext(v)[0]
            description = captions.get(v, metadata.get(title, "No description"))
            ep_num = episodes.get(title, 0)
            caption_text = f"{description}\n📺 Episode {ep_num}"

            video_path = os.path.join(VIDEO_FOLDER, v)

            # Post to source channel
            with open(video_path, "rb") as vid:
                msg_obj = bot.send_video(SOURCE_CHANNEL, vid, caption=caption_text)

            # Forward to target channel
            bot.forward_message(TARGET_CHANNEL, SOURCE_CHANNEL, msg_obj.message_id)

            print(f"✅ Posted & Forwarded {title} Episode {ep_num}")
            time.sleep(COOLDOWN)
    bot.send_message(msg.chat.id, "✅ All videos posted and forwarded successfully!")

# ----------------------------
# Run Bot
# ----------------------------
bot.infinity_polling()
