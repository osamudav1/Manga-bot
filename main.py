import telebot
from telebot import types
import time

# --- CONFIGURATION ---
API_ID = 19703932
API_HASH = "2fe31e84e0b537b505f528e62e114664"
BOT_TOKEN = "7292122932:AAG8hCvjbcF-MuM9IUxivPUGyF-MvdW84HQ"
OWNER_ID = 1735522859
MAIN_GROUP = -1002849045181
BACKUP_GROUP = -1003502685671

bot = telebot.TeleBot(BOT_TOKEN)
# DATABASE (ယာယီမှတ်ဉာဏ် - Bot ပိတ်ရင် ပျက်ပါမယ်။ အတည်သိမ်းချင်ရင် Firestore သုံးရပါမယ်)
db = {
    "users": {}, 
    "movies": {}, # Movie ID နဲ့ သိမ်းမယ်
    "current_upload": {} # Admin တစ်ယောက်ချင်းစီရဲ့ Upload process ကို မှတ်ဖို့
}

# --- FUNCTIONS ---
# --- MOVIE ADD FLOW ---

@bot.callback_query_handler(func=lambda call: call.data == "add_movie")
def start_add_movie(call):
    uid = call.message.chat.id
    db["current_upload"][uid] = {} # Process စတင်မယ်
    msg = bot.send_message(uid, "🎬 Movie နာမည်ကို ရိုက်ထည့်ပေးပါ (ဥပမာ - John Wick)")
    bot.register_next_step_handler(msg, get_movie_title)

def get_movie_title(message):
    uid = message.chat.id
    db["current_upload"][uid]['title'] = message.text
    msg = bot.send_message(uid, "📝 Movie ရဲ့ Description ကို ရိုက်ပေးပါ (ဥပမာ - Action / 2024)")
    bot.register_next_step_handler(msg, get_movie_desc)

def get_movie_desc(message):
    uid = message.chat.id
    db["current_upload"][uid]['desc'] = message.text
    msg = bot.send_message(uid, "🖼 Movie Cover Photo (ပုံ) ကို ပို့ပေးပါ")
    bot.register_next_step_handler(msg, get_movie_cover)

def get_movie_cover(message):
    uid = message.chat.id
    if message.content_type == 'photo':
        db["current_upload"][uid]['cover'] = message.photo[-1].file_id
        msg = bot.send_message(uid, "📹 အခု Movie Video ဖိုင်ကို ပို့ပေးပါ။ အပိုင်းလိုက်ဆိုရင် တစ်ခုချင်းစီ ပို့ပေးပါ (ပြီးရင် /done လို့ ရိုက်ပါ)")
        db["current_upload"][uid]['parts'] = []
        bot.register_next_step_handler(msg, get_movie_videos)
    else:
        bot.send_message(uid, "⚠️ ဓာတ်ပုံပဲ ပို့ပေးပါဗျာ။ ပြန်ပို့ကြည့်ပါ။")
        bot.register_next_step_handler(message, get_movie_cover)

def get_movie_videos(message):
    uid = message.chat.id
    if message.text == "/done":
        save_movie_to_db(uid)
        return
    
    if message.content_type in ['video', 'document']:
        # MAIN GROUP ဆီကို Forward (ပို့) လိုက်ခြင်း
        sent_msg = bot.forward_message(MAIN_GROUP, uid, message.message_id)
        # Group ထဲက message_id ကို သိမ်းထားခြင်း
        db["current_upload"][uid]['parts'].append(sent_msg.message_id)
        bot.send_message(uid, f"✅ အပိုင်း {len(db['current_upload'][uid]['parts'])} ရရှိပါပြီ။ နောက်ထပ်အပိုင်း ပို့ပါ (သို့မဟုတ် /done ရိုက်ပါ)")
    
    bot.register_next_step_handler(message, get_movie_videos)

def save_movie_to_db(uid):
    movie_id = f"MOV_{int(time.time())}"
    data = db["current_upload"][uid]
    
    db["movies"][movie_id] = {
        "title": data['title'],
        "desc": data['desc'],
        "cover": data['cover'],
        "parts": data['parts'],
        "status": "Ended"
    }
    bot.send_message(uid, f"🎊 '{data['title']}' ကို အောင်မြင်စွာ တင်ပြီးပါပြီ။\nMovie ID: {movie_id}")
    del db["current_upload"][uid] # Clean up

def check_join(user_id):
    # ဒီနေရာမှာ Force Join စစ်ဆေးဖို့အတွက် ကိုယ့် Channel Username ထည့်ရပါမယ်
    return True 

# --- USER COMMANDS ---
@bot.message_handler(commands=['start'])
def start(message):
    uid = message.chat.id
    if uid not in db["users"]:
        db["users"][uid] = {"approved": False, "points": 10, "is_vip": False, "watch_count": 0}
    
    user = db["users"][uid]
    if not user["approved"] and uid != OWNER_ID:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔔 Join Channel", url="https://t.me/osamu1123"))
        markup.add(types.InlineKeyboardButton("✅ Done", callback_data="check_join"))
        bot.send_message(uid, "🚫 Access Restricted\nJoin our official channel first 👇", reply_markup=markup)
    else:
        main_menu(uid)
        @bot.message_handler(func=lambda m: m.text == "🎥 Movies")
def show_movie_list(message):
    if not db["movies"]:
        bot.send_message(message.chat.id, "လောလောဆယ် Movie မရှိသေးပါဘူးခင်ဗျာ။")
        return
    
    for m_id, m in db["movies"].items():
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📺 Watch Now", callback_data=f"watch_{m_id}"))
        bot.send_photo(message.chat.id, m['cover'], caption=f"🎬 {m['title']}\n📝 {m['desc']}", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("watch_"))
def watch_movie(call):
    m_id = call.data.replace("watch_", "")
    movie = db["movies"].get(m_id)
    
    if movie:
        bot.send_message(call.message.chat.id, f"🎬 {movie['title']} ကို ပို့ပေးနေပါပြီ။ ခဏစောင့်ပါ...")
        for part_id in movie['parts']:
            # Group ထဲက Video ကို User ဆီ Forward ပြန်လုပ်ပေးခြင်း
            bot.forward_message(call.message.chat.id, MAIN_GROUP, part_id)
            time.sleep(2) # Cooldown 2 sec
        
        bot.send_message(call.message.chat.id, "✅ ပို့လို့ပြီးပါပြီ။ ဇာတ်လမ်းဆုံးရင် မူပိုင်ခွင့်အရ ၅ မိနစ်အတွင်း ပြန်ဖျက်ပေးပါမယ်။")


def main_menu(uid):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("🎥 Movies", "🔍 Search", "⭐ My Points", "💎 VIP Upgrade", "🔗 My Link", "ℹ️ Help", "❌ Exit")
    if uid == OWNER_ID:
        markup.add("⚙️ Owner Dashboard")
    bot.send_message(uid, "🏠 Main Menu", reply_markup=markup)

# --- OWNER DASHBOARD ---
@bot.message_handler(func=lambda m: m.text == "⚙️ Owner Dashboard")
def admin_panel(message):
    if message.chat.id != OWNER_ID: return
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("👥 Users", callback_data="manage_users"),
        types.InlineKeyboardButton("🎬 Manage Movies", callback_data="manage_movies"),
        types.InlineKeyboardButton("📢 Broadcast", callback_data="broadcast"),
        types.InlineKeyboardButton("🔐 Force Join", callback_data="force_join")
    )
    bot.send_message(OWNER_ID, "🛠 Owner Control Panel", reply_markup=markup)

# --- CALLBACK HANDLERS ---
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    uid = call.message.chat.id
    if call.data == "check_join":
        bot.answer_callback_query(call.id, "Checking...")
        # စစ်ဆေးပြီးရင် Approved လုပ်ပေးခြင်း (Example)
        db["users"][uid]["approved"] = True
        main_menu(uid)
    elif call.data == "manage_movies":
        bot.send_message(uid, "1. Tap ➕ Add Movie\n2. Enter Title...")

bot.infinity_polling()
