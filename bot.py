import json, asyncio, os
from datetime import datetime, timedelta
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaVideo
from config import *

bot = Client("MovieBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

DB_FILE = "database.json"

# --- DATABASE LOGIC ---
def load_db():
    if not os.path.exists(DB_FILE):
        # ဖိုင်မရှိရင် default အနေနဲ့ ဒါတွေ အရင်ထည့်မယ်
        data = {
            "users": {}, 
            "movies": [], 
            "settings": {
                "is_force_join": False, 
                "force_join_channel": "",
                "welcome_msg": "Welcome to SeaTv-MM Bot!",
                "ad_banner": "Join our channel",
                "ad_link": "https://t.me/seatvmm"
            }
        }
        with open(DB_FILE, "w") as f:
            json.dump(data, f, indent=4)
        return data
    return json.load(open(DB_FILE, "r"))

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

# --- 1. START & MAIN MENU ---
@bot.on_message(filters.command("start") & filters.private)
async def start(client, message):
    user_id = str(message.from_user.id)
    db = load_db()
    
    if user_id not in db["users"]:
        db["users"][user_id] = {
            "name": message.from_user.first_name, "points": 10, "is_vip": False,
            "daily_watch_count": 0, "last_watch_date": str(datetime.now().date()),
            "vip_expiry": None
        }
        save_db(db)

    buttons = [
        [InlineKeyboardButton("🎥 Movies", callback_data="movies_main"), InlineKeyboardButton("🔍 Search", callback_data="search_main")],
        [InlineKeyboardButton("⭐ My Points", callback_data="points_info"), InlineKeyboardButton("💎 VIP Upgrade", callback_data="vip_info")],
        [InlineKeyboardButton("🔗 My Link", callback_data="ref_link"), InlineKeyboardButton("ℹ️ Help", callback_data="help_info")],
        [InlineKeyboardButton(f"📢 {db['settings']['ad_banner']}", url=db['settings']['ad_link'])],
        [InlineKeyboardButton("🎁 Watch Ad (+2 Pts)", callback_data="watch_ad")]
    ]
    await message.reply(db["settings"]["welcome_msg"], reply_markup=InlineKeyboardMarkup(buttons))

# --- 2. MOVIE & WATCH LOGIC ---
@bot.on_callback_query(filters.regex("^movies_main"))
async def movies_list(client, callback_query):
    db = load_db()
    if not db["movies"]:
        return await callback_query.answer("No movies available yet!", show_alert=True)
    # Simple list for example
    await callback_query.message.edit_text("Select a movie to watch:")

@bot.on_callback_query(filters.regex("^watch_ad$"))
async def watch_reward_ad(client, callback_query):
    user_id = str(callback_query.from_user.id)
    db = load_db()
    user = db["users"].get(user_id)
    today = str(datetime.now().date())
    
    if user.get("last_ad_date") != today:
        user["ad_count"] = 0
        user["last_ad_date"] = today

    if user.get("ad_count", 0) >= 3:
        return await callback_query.answer("⚠️ Limit 3 times per day!", show_alert=True)

    await callback_query.answer("Watching ad (5s)...", show_alert=False)
    await asyncio.sleep(5)
    user["points"] += 2
    user["ad_count"] = user.get("ad_count", 0) + 1
    save_db(db)
    await callback_query.message.reply_text("✅ +2 Points Added!")

# --- 3. POINTS & REFERRAL ---
@bot.on_callback_query(filters.regex("points_info"))
async def points_info(client, callback_query):
    db = load_db()
    user = db["users"].get(str(callback_query.from_user.id))
    status = "VIP 💎" if user["is_vip"] else "Free User"
    await callback_query.answer(f"Status: {status}\nPoints: {user['points']}", show_alert=True)

@bot.on_callback_query(filters.regex("ref_link"))
async def get_ref(client, callback_query):
    username = (await client.get_me()).username
    link = f"https://t.me/{username}?start={callback_query.from_user.id}"
    await callback_query.message.reply(f"Invite friends & earn 10 points!\nYour Link: {link}")

# --- 4. VIP SYSTEM ---
@bot.on_callback_query(filters.regex("vip_info"))
async def vip_menu(client, callback_query):
    text = "💎 **VIP Plans**\n1 Month: 250 Pts\n3 Months: 600 Pts"
    btns = [[InlineKeyboardButton("1 Month (250 pts)", callback_data="exchange_vip_1")],
            [InlineKeyboardButton("🔙 Back", callback_data="back_home")]]
    await callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(btns))

@bot.on_callback_query(filters.regex("^exchange_vip_"))
async def exchange_vip(client, callback_query):
    user_id = str(callback_query.from_user.id)
    plan = callback_query.data.split("_")[2]
    db = load_db()
    user = db["users"].get(user_id)
    
    cost = 250 if plan == "1" else 600
    if user["points"] < cost:
        return await callback_query.answer("Need more points!", show_alert=True)
    
    user["points"] -= cost
    user["is_vip"] = True
    expiry = datetime.now() + timedelta(days=30 if plan == "1" else 90)
    user["vip_expiry"] = expiry.strftime("%Y-%m-%d")
    save_db(db)
    await callback_query.message.edit_text(f"🎉 VIP Active until {user['vip_expiry']}")

# --- 5. ADMIN & AD MANAGEMENT ---
@bot.on_message(filters.command("admin") & filters.user(ADMIN_ID))
async def admin_panel(client, message):
    btns = [[InlineKeyboardButton("📊 Stats", callback_data="adm_stats")],
            [InlineKeyboardButton("⚙️ Settings", callback_data="adm_sets")]]
    await message.reply("👑 Admin Panel", reply_markup=InlineKeyboardMarkup(btns))

@bot.on_message(filters.command("setad") & filters.user(ADMIN_ID))
async def set_ad(client, message):
    try:
        data = message.text.split(" ", 1)[1].split("|")
        db = load_db()
        db["settings"]["ad_banner"] = data[0].strip()
        db["settings"]["ad_link"] = data[1].strip()
        save_db(db)
        await message.reply("✅ Ad Updated Successfully!")
    except:
        await message.reply("Format: /setad Text | Link")

# --- 6. HELP & CLOSE ---
@bot.on_callback_query(filters.regex("help_info"))
async def help_info(client, callback_query):
    await callback_query.answer("Contact @Admin for help.", show_alert=True)

@bot.on_callback_query(filters.regex("back_home"))
async def back_home(client, callback_query):
    await start(client, callback_query.message)

# --- 7. START BOT ---
if __name__ == "__main__":
    print("Bot is running...")
    bot.run()
