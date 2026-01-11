import telebot
from telebot import types
import time
import json
import os

# ===== CONFIG =====
BOT_TOKEN = os.getenv("BOT_TOKEN")    # Koyeb Environment Variable
OWNER_ID = 1735522859
MAIN_GROUP = -1002849045181
BACKUP_GROUP = -1003502685671
FORCE_CHANNEL = "osamu1123"

bot = telebot.TeleBot(BOT_TOKEN)

# ===== DATABASE =====
DB_FILE = "database.json"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE,"r",encoding="utf-8") as f:
            return json.load(f)
    return {"users":[],"movies":[],"daily_tasks":[],"custom_ads":[]}

def save_db():
    with open(DB_FILE,"w",encoding="utf-8") as f:
        json.dump(db,f,ensure_ascii=False,indent=2)

db = load_db()

# ===== FORCE JOIN =====
def check_join(user_id):
    try:
        member = bot.get_chat_member(f"@{FORCE_CHANNEL}", user_id)
        return member.status in ["member","administrator","creator"]
    except:
        return False

# ===== MAIN MENU =====
def main_menu(uid):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True,row_width=2)
    kb.add("🎥 Movies","🔍 Search")
    kb.add("⭐ My Points","💎 VIP Upgrade")
    kb.add("🔗 My Link","ℹ️ Help","❌ Exit")
    if str(uid)==str(OWNER_ID):
        kb.add("➕ Add Movie","📢 Broadcast")
    bot.send_message(uid,"🏠 Main Menu",reply_markup=kb)

# ===== START =====
@bot.message_handler(commands=["start"])
def start(message):
    uid = str(message.chat.id)
    if not any(u['user_id']==uid for u in db["users"]):
        db["users"].append({
            "user_id": uid,
            "name": message.from_user.first_name,
            "role": "user",
            "points": 10,
            "is_vip": False,
            "vip_expiry": None,
            "is_approved": False,
            "daily_watch_count":0,
            "last_watch_date": ""
        })
        save_db()
    
    if not check_join(message.chat.id):
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("🔔 Join Channel",url=f"https://t.me/{FORCE_CHANNEL}"))
        kb.add(types.InlineKeyboardButton("✅ Done",callback_data="check_join"))
        bot.send_message(message.chat.id,"🚫 Access Restricted\nJoin our official channel first 👇",reply_markup=kb)
        return

    # Approved
    for u in db["users"]:
        if u["user_id"]==uid:
            u["is_approved"]=True
    save_db()
    main_menu(message.chat.id)

@bot.callback_query_handler(func=lambda c: c.data=="check_join")
def recheck(call):
    if check_join(call.message.chat.id):
        uid=str(call.message.chat.id)
        for u in db["users"]:
            if u["user_id"]==uid:
                u["is_approved"]=True
                
        save_db()
        main_menu(call.message.chat.id)
    else:
        bot.answer_callback_query(call.id,"Join မလုပ်သေးပါ")
        @bot.callback_query_handler(func=lambda call: call.data=="add_movie")
def start_add_movie(call):
    uid = call.message.chat.id
    if not any(u['user_id']==str(uid) for u in db["users"]): return
    db["current_upload"] = {}   # Temp store
    msg = bot.send_message(uid,"🎬 Movie Title ရိုက်ထည့်ပါ")
    bot.register_next_step_handler(msg,get_movie_title)

def get_movie_title(message):
    uid = message.chat.id
    db["current_upload"] = {"title":message.text,"parts":[]}
    msg = bot.send_message(uid,"📝 Movie Description ရိုက်ပါ")
    bot.register_next_step_handler(msg,get_movie_desc)

def get_movie_desc(message):
    uid=message.chat.id
    db["current_upload"]["desc"]=message.text
    msg=bot.send_message(uid,"🖼 Movie Cover Image ပို့ပါ")
    bot.register_next_step_handler(msg,get_movie_cover)

def get_movie_cover(message):
    uid=message.chat.id
    if message.content_type=="photo":
        db["current_upload"]["cover"]=message.photo[-1].file_id
        msg=bot.send_message(uid,"📹 Video(s) ပို့ပါ (/done)")
        bot.register_next_step_handler(msg,get_movie_videos)
    else:
        bot.send_message(uid,"⚠️ Photo ပို့ပါ")
        bot.register_next_step_handler(message,get_movie_cover)
        def get_movie_videos(message):
    uid=message.chat.id
    if message.text=="/done":
        save_movie_to_db(uid)
        return
    if message.content_type in ["video","document"]:
        sent_msg=bot.forward_message(MAIN_GROUP,uid,message.message_id)
        db["current_upload"]["parts"].append({"message_id":sent_msg.message_id,"group_id":"MAIN_GROUP"})
        bot.send_message(uid,f"✅ {len(db['current_upload']['parts'])} parts uploaded")
    bot.register_next_step_handler(message,get_movie_videos)

def save_movie_to_db(uid):
    import time
    data=db["current_upload"]
    movie_id=f"MOV_{int(time.time())}"
    db["movies"].append({
        "movie_id":movie_id,
        "title":data["title"],
        "description":data["desc"],
        "cover_url":data["cover"],
        "status":"Ended",
        "parts":data["parts"],
        "backup_group_id":BACKUP_GROUP,
        "total_parts":len(data["parts"])
    })
    save_db()
    bot.send_message(uid,f"🎊 '{data['title']}' added successfully\nID: {movie_id}")
    @bot.message_handler(func=lambda m: m.text=="🎥 Movies")
def show_movies(message):
    uid=str(message.chat.id)
    user=[u for u in db["users"] if u["user_id"]==uid][0]
    for m in db["movies"]:
        kb=types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("📺 Watch",callback_data=f"watch_{m['movie_id']}"))
        bot.send_photo(message.chat.id,m["cover_url"],caption=f"🎬 {m['title']}\n📝 {m['description']}",reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("watch_"))
def watch(call):
    m_id=call.data.replace("watch_","")
    movie=[m for m in db["movies"] if m["movie_id"]==m_id][0]
    uid=str(call.message.chat.id)
    user=[u for u in db["users"] if u["user_id"]==uid][0]
    if user["is_vip"] or user["daily_watch_count"]<5:
        if not user["is_vip"]: user["daily_watch_count"]+=1
        save_db()
        for part in movie["parts"]:
            try:
                bot.forward_message(call.message.chat.id,MAIN_GROUP,part["message_id"])
            except:
                bot.forward_message(call.message.chat.id,BACKUP_GROUP,part["message_id"])
            time.sleep(2)
        bot.send_message(call.message.chat.id,"✅ Movie sent")
    else:
        bot.send_message(call.message.chat.id,"⚠ Daily free limit reached. Upgrade to VIP")
        @bot.message_handler(func=lambda m: m.text=="⚙️ Owner Dashboard")
def owner_panel(message):
    if message.chat.id != OWNER_ID: return
    kb=types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("👥 Users",callback_data="manage_users"),
        types.InlineKeyboardButton("🎬 Movies",callback_data="manage_movies"),
        types.InlineKeyboardButton("📢 Broadcast",callback_data="broadcast"),
        types.InlineKeyboardButton("🔐 Force Join",callback_data="force_join")
    )
    bot.send_message(OWNER_ID,"Owner Panel",reply_markup=kb)

# ===== RUN BOT =====
bot.infinity_polling()
        
