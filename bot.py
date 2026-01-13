import json, asyncio, os
from datetime import datetime
from pyrogram import Client, filters,
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaVideo
from config import *

bot = Client("MovieBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

DB_FILE = "database.json"

def load_db():
    if not os.path.exists(DB_FILE):
        return {"users": {}, "movies": [], "settings": {"is_force_join": True, "force_join_channel": ""}}
    return json.load(open(DB_FILE, "r"))

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

# Force Join Checker
async def check_fjoin(client, message):
    db = load_db()
    if not db["settings"]["is_force_join"]: return True
    channel = db["settings"]["force_join_channel"].replace("@", "")
    try:
        await client.get_chat_member(channel, message.from_user.id)
        return True
    except:
        btn = [[InlineKeyboardButton("🔔 Join Channel", url=f"https://t.me/{channel}")],
               [InlineKeyboardButton("✅ Done", callback_data="check_start")]]
        await message.reply("🚫 Access Restricted\nJoin our official channel first 👇", reply_markup=InlineKeyboardMarkup(btn))
        return False

@bot.on_message(filters.command("start") & filters.private)
async def start(client, message):
    user_id = str(message.from_user.id)
    db = load_db()
    
    # Register User
    if user_id not in db["users"]:
        db["users"][user_id] = {
            "name": message.from_user.first_name, "points": 10, "is_vip": False,
            "daily_watch_count": 0, "last_watch_date": str(datetime.now().date())
        }
        save_db(db)

    if not await check_fjoin(client, message): return

    buttons = [
        [InlineKeyboardButton("🎥 Movies", callback_data="movies_main"), InlineKeyboardButton("🔍 Search", callback_data="search_main")],
        [InlineKeyboardButton("⭐ My Points", callback_data="points_info"), InlineKeyboardButton("💎 VIP Upgrade", callback_data="vip_info")],
        [InlineKeyboardButton("🔗 My Link", callback_data="ref_link"), InlineKeyboardButton("ℹ️ Help", callback_data="help_info")],
        [InlineKeyboardButton("❌ Exit", callback_data="close_bot")]
    ]
    await message.reply(db["settings"]["welcome_msg"], reply_markup=InlineKeyboardMarkup(buttons))
    @bot.on_callback_query(filters.regex("^watch_"))
async def watch_movie(client, callback_query):
    user_id = str(callback_query.from_user.id)
    movie_id = int(callback_query.data.split("_")[1])
    db = load_db()
    user = db["users"][user_id]

    # Access Control
    today = str(datetime.now().date())
    if user["last_watch_date"] != today:
        user["daily_watch_count"] = 0
        user["last_watch_date"] = today

    if not user["is_vip"] and user["daily_watch_count"] >= 5:
        return await callback_query.message.reply("⚠ Daily free limit reached. Upgrade to VIP!")

    movie = db["movies"][movie_id]
    user["daily_watch_count"] += 1
    save_db(db)

    await callback_query.answer("Processing your movie album...", show_alert=False)
    
    # Album Sequential Delivery
    parts = movie["parts"]
    all_sent = []
    for i in range(0, len(parts), 10):
        batch = parts[i:i+10]
        media = [InputMediaVideo(p["file_id"]) for p in batch]
        sent = await client.send_media_group(callback_query.from_user.id, media)
        all_sent.extend([s.id for s in sent])
    
    # Auto-Delete Logic (1 Min)
    await asyncio.sleep(60)
    await client.delete_messages(callback_query.from_user.id, all_sent)
    await client.send_message(callback_query.from_user.id, "⚠ Video removed due to copyright")
    from datetime import timedelta

@bot.on_callback_query(filters.regex("^exchange_vip_"))
async def exchange_vip(client, callback_query):
    user_id = str(callback_query.from_user.id)
    plan = callback_query.data.split("_")[2] # 1, 3, သို့မဟုတ် 6
    
    db = load_db()
    user = db["users"].get(user_id)
    
    # Point သတ်မှတ်ချက်များ
    plans = {
        "1": {"points": 250, "days": 30},
        "3": {"points": 600, "days": 90},
        "6": {"points": 1000, "days": 180}
    }
    
    required_points = plans[plan]["points"]
    duration_days = plans[plan]["days"]
# --- REWARD ADS LOGIC ---
@bot.on_callback_query(filters.regex("^watch_ad$"))
async def watch_reward_ad(client, callback_query):
    user_id = str(callback_query.from_user.id)
    db = load_db()
    user = db["users"].get(user_id)
    
    # နေ့စဉ် ၃ ကြိမ် ကန့်သတ်ချက် စစ်ဆေးခြင်း
    today = str(datetime.now().date())
    if user.get("last_ad_date") != today:
        user["ad_count"] = 0
        user["last_ad_date"] = today

    if user.get("ad_count", 0) >= 3:
        return await callback_query.answer("⚠️ ဒီနေ့အတွက် အကြိမ်ရေ ပြည့်သွားပါပြီ။", show_alert=True)
# --- ADMIN ADS MANAGEMENT ---
@bot.on_message(filters.command("setad") & filters.user(ADMIN_ID))
async def set_ad(client, message):
    try:
        # ပုံစံ: /setad စာသား | Link
        data = message.text.split(" ", 1)[1].split("|")
        db = load_db()
        db["settings"]["ad_banner"] = data[0].strip()
        db["settings"]["ad_link"] = data[1].strip()
        save_db(db)
        await message.reply("✅ ကြော်ငြာအသစ်ကို အောင်မြင်စွာ ပြောင်းလဲပြီးပါပြီ။")
    except:
        await message.reply("⚠️ ပုံစံမှားနေပါတယ်။ `/setad စာသား | Link` ဟု ရိုက်ပါ။")

    await callback_query.answer("ကြော်ငြာကို ၅ စက္ကန့်ကြည့်ပေးပါ။ Point ရပါလိမ့်မည်...", show_alert=False)
    await asyncio.sleep(5) 
    
    user["points"] += 2 # တစ်ခါကြည့်ရင် 2 points ပေးမယ်
    user["ad_count"] = user.get("ad_count", 0) + 1
    save_db(db)
    
    await callback_query.message.reply_text("✅ ကြော်ငြာကြည့်ပြီးလို့ +2 Points ရရှိပါပြီ။")

    if user["points"] < required_points:
        return await callback_query.answer(f"⚠️ Point မလုံလောက်ပါ။ {required_points} points လိုအပ်ပါတယ်။", show_alert=True)
    
    # VIP Update လုပ်ခြင်း
    user["points"] -= required_points
    user["is_vip"] = True
    
    # ရက်စွဲတွက်ချက်ခြင်း
    current_expiry = user.get("vip_expiry")
    start_date = datetime.now()
    
    # အကယ်၍ VIP ဖြစ်နေဆဲဆိုရင် ရက်ထပ်ပေါင်းပေးမယ်
    if current_expiry and datetime.strptime(current_expiry, "%Y-%m-%d") > start_date:
        start_date = datetime.strptime(current_expiry, "%Y-%m-%d")
        
    expiry_date = start_date + timedelta(days=duration_days)
    user["vip_expiry"] = expiry_date.strftime("%Y-%m-%d")
    
    save_db(db)
    
    await callback_query.message.edit_text(
        f"🎉 VIP အောင်မြင်စွာလဲလှယ်ပြီးပါပြီ!\n\n"
        f"🗓 သက်တမ်းကုန်ရက်: {user['vip_expiry']}\n"
        f"💰 လက်ကျန် Point: {user['points']}",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Home", callback_data="back_home")]])
    )

    @bot.on_message(filters.command("admin") & filters.user(ADMIN_ID))
async def admin_dashboard(client, message):
    btns = [
        [InlineKeyboardButton("👥 Users", callback_data="adm_users"), InlineKeyboardButton("🎬 Manage Movies", callback_data="adm_movies")],
        [InlineKeyboardButton("🔐 Force Join Settings", callback_data="adm_fjoin")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="adm_bc"), InlineKeyboardButton("⚙️ Settings", callback_data="adm_sets")]
    ]
    await message.reply("👑 Owner Dashboard", reply_markup=InlineKeyboardMarkup(btns))

@bot.on_callback_query(filters.regex("^adm_fjoin"))
async def set_fjoin(client, callback_query):
    db = load_db()
    status = "Enabled" if db["settings"]["is_force_join"] else "Disabled"
    btns = [
        [InlineKeyboardButton(f"Status: {status}", callback_data="toggle_fj")],
        [InlineKeyboardButton("✏️ Change Channel", callback_data="change_fj_ch")],
        [InlineKeyboardButton("🔙 Back", callback_data="adm_home")]
    ]
    await callback_query.message.edit_text("Force Join Settings", reply_markup=InlineKeyboardMarkup(btns))
# Points & Referral
@bot.on_callback_query(filters.regex("ref_link"))
async def get_ref(client, callback_query):
    user_id = callback_query.from_user.id
    link = f"https://t.me/{(await client.get_me()).username}?start={user_id}"
    await callback_query.message.reply(f"Invite friends and earn 10 points!\nYour Link: {link}")

# Requirements.txt
# pyrogram
# tgcrypto
/setad
if __name__ == "__main__":
    bot.run()


