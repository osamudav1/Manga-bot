# config.py
API_ID = 19703932# သင့် API ID
API_HASH = "2fe31e84e0b537b505f528e62e114664" # သင့် API Hash
BOT_TOKEN = "7292122932:AAG8hCvjbcF-MuM9IUxivPUGyF-MvdW84HQ" # သင့် Bot Token
ADMIN_ID = 1735522859 # သင့် User ID (Owner)
MAIN_GROUP =   -1002849045181 # ရုပ်ရှင်ရှိသော Group ID
BACKUP_GROUP = -1003502685671
... # Backup Group ID
import json, asyncio, os
from datetime import datetime, timedelta
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant
from config import *

bot = Client("SeaTvBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
DB_FILE = "database.json"

def load_db():
    if not os.path.exists(DB_FILE):
        return {"users": {}, "movies": [], "settings": {"force_join": True, "force_channel": "@seatvmm"}}
    return json.load(open(DB_FILE, "r"))

def save_db(data):
    json.dump(data, open(DB_FILE, "w"), indent=4)

async def check_force_join(client, user_id):
    db = load_db()
    if not db["settings"]["force_join"]: return True
    try:
        await client.get_chat_member(db["settings"]["force_channel"], user_id)
        return True
    except UserNotParticipant: return False
    except: return True

@bot.on_message(filters.command("start") & filters.private)
async def start(client, message):
    user_id = str(message.from_user.id)
    db = load_db()
    
    # User Registration & Approval Check
    if user_id not in db["users"]:
        db["users"][user_id] = {
            "name": message.from_user.first_name, "points": 10, "is_vip": False,
            "vip_expiry": None, "is_approved": True, "daily_watch_count": 0,
            "last_watch_date": str(datetime.now().date())
        }
        save_db(db)

    if not await check_force_join(client, message.from_user.id):
        btn = [[InlineKeyboardButton("🔔 Join Channel", url=f"https://t.me/seatvmm")],
               [InlineKeyboardButton("✅ Done", callback_data="check_join")]]
        return await message.reply("🚫 Access Restricted\nJoin our official channel first 👇", reply_markup=InlineKeyboardMarkup(btn))

    # Main Menu Buttons
    btns = [
        [InlineKeyboardButton("🎥 Movies", callback_data="movies_list"), InlineKeyboardButton("🔍 Search", callback_data="search_mode")],
        [InlineKeyboardButton("⭐ My Points", callback_data="points_info"), InlineKeyboardButton("💎 VIP Upgrade", callback_data="vip_info")],
        [InlineKeyboardButton("🔗 My Link", callback_data="ref_link"), InlineKeyboardButton("ℹ️ Help", callback_data="help_info")],
        [InlineKeyboardButton("❌ Exit", callback_data="close_bot")]
    ]
    if int(user_id) == ADMIN_ID:
        btns.insert(0, [InlineKeyboardButton("👑 Owner Dashboard", callback_data="owner_main")])
        
    await message.reply("📺 **SeaTv-MM Main Menu**", reply_markup=InlineKeyboardMarkup(btns))
# --- MOVIE ACCESS CONTROL ---
@bot.on_callback_query(filters.regex("^get_movie_"))
async def deliver_movie(client, cb):
    movie_id = cb.data.split("_")[2]
    user_id = str(cb.from_user.id)
    db = load_db()
    user = db["users"][user_id]
    today = str(datetime.now().date())

    # Limit Check
    if user["last_watch_date"] != today:
        user["daily_watch_count"] = 0
        user["last_watch_date"] = today

    if not user["is_vip"] and user["daily_watch_count"] >= 5:
        return await cb.message.reply("⚠ Daily free limit reached. Upgrade to VIP", 
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💎 Upgrade to VIP", callback_data="vip_info")]]))

    # Sequential Forwarding
    movie = next((m for m in db["movies"] if m["movie_id"] == movie_id), None)
    if not movie: return await cb.answer("Movie not found!")

    user["daily_watch_count"] += 1
    save_db(db)
    
    sent_msgs = []
    for part in movie["parts"]:
        try:
            # Try Main Group first, then Backup
            msg = await client.forward_messages(cb.from_user.id, MAIN_GROUP, part["message_id"])
        except:
            msg = await client.forward_messages(cb.from_user.id, BACKUP_GROUP, part["message_id"])
        
        sent_msgs.append(msg.id)
        await asyncio.sleep(2) # Cooldown

    # Auto Delete Logic
    await asyncio.sleep(60) # 1 Minute
    for mid in sent_msgs:
        try: await client.delete_messages(cb.from_user.id, mid)
        except: pass
    await client.send_message(cb.from_user.id, "⚠ Video removed due to copyright")
# --- OWNER DASHBOARD ---
@bot.on_callback_query(filters.regex("owner_main"))
async def owner_dashboard(client, cb):
    btns = [
        [InlineKeyboardButton("👥 Users", callback_data="adm_users"), InlineKeyboardButton("🎬 Manage Movies", callback_data="adm_movies")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="adm_bc"), InlineKeyboardButton("⚙️ Settings", callback_data="adm_sets")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_home")]
    ]
    await cb.message.edit_text("👑 **Owner Dashboard**", reply_markup=InlineKeyboardMarkup(btns))

@bot.on_message(filters.command("addmovie") & filters.user(ADMIN_ID))
async def owner_add_movie(client, message):
    # Format: /addmovie ID | Title | Desc | Parts(msg_ids)
    # Example: /addmovie JW01 | John Wick | Action | 123,124
    try:
        data = message.text.split("|")
        m_id = data[0].split()[1].strip()
        title = data[1].strip()
        desc = data[2].strip()
        parts = [{"message_id": int(i.strip()), "group_id": "MAIN_GROUP"} for i in data[3].split(",")]
        
        db = load_db()
        db["movies"].append({
            "movie_id": m_id, "title": title, "description": desc,
            "parts": parts, "total_parts": len(parts)
        })
        save_db(db)
        await message.reply(f"✅ Movie '{title}' Added Successfully!")
    except:
        await message.reply("❌ Use Format: `/addmovie ID | Title | Desc | PartID1,PartID2`")

# --- POINT & VIP ---
@bot.on_callback_query(filters.regex("points_info"))
async def show_pts(client, cb):
    db = load_db()
    pts = db["users"][str(cb.from_user.id)]["points"]
    await cb.answer(f"⭐ Your Points: {pts}", show_alert=True)

if __name__ == "__main__":
    bot.run()
