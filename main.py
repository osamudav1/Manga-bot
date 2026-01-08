import asyncio
import os
import threading
from flask import Flask
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from motor.motor_asyncio import AsyncIOMotorClient

# --- 1. Render အတွက် Bot ကို နှိုးထားပေးမယ့် Web Server ---
flask_app = Flask('')
@flask_app.route('/')
def home():
    return "Bot is Alive!"

def run_flask():
    flask_app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

# Flask ကို Background မှာ Run ခိုင်းထားမယ်
threading.Thread(target=run_flask).start()

# --- 2. Render Environment Variables မှ Data များယူခြင်း ---
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
MONGO_URL = os.environ.get("MONGO_URL", "")
OWNER_ID = int(os.environ.get("OWNER_ID", 0))

# Database ချိတ်ဆက်ခြင်း
db_client = AsyncIOMotorClient(MONGO_URL)
db = db_client["manga_bot_db"]

# Bot Client
app = Client("manga_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- 3. User Commands & UI ---

@app.on_message(filters.command("start") & filters.private)
async def start_handler(client, message):
    # User Profile & Point စစ်ဆေးခြင်း/သိမ်းခြင်း
    user_id = message.from_user.id
    await db.users.update_one({"user_id": user_id}, {"$set": {"name": message.from_user.first_name}}, upsert=True)
    
    # Main Menu Buttons
    btn = InlineKeyboardMarkup([
        [InlineKeyboardButton("📚 Manga List", callback_data="manga_list"), InlineKeyboardButton("🎁 Daily Task", callback_data="daily_task")],
        [InlineKeyboardButton("💎 VIP Rules", callback_data="vip_rules"), InlineKeyboardButton("👤 My Profile", callback_data="profile")]
    ])
    
    welcome_msg = f"မင်္ဂလာပါ {message.from_user.first_name}!\nManga Bot မှ ကြိုဆိုပါတယ်။ အောက်က ခလုတ်တွေကို သုံးနိုင်ပါတယ်။"
    await message.reply_text(welcome_msg, reply_markup=btn)

# --- 4. Admin Panel (Owner သီးသန့်) ---

@app.on_message(filters.command("admin") & filters.user(OWNER_ID))
async def admin_panel(client, message):
    btn = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add Manga", callback_data="add_manga"), InlineKeyboardButton("📢 Ads Manager", callback_data="manage_ads")],
        [InlineKeyboardButton("🔄 Recovery System", callback_data="recovery_tool")]
    ])
    await message.reply_text("🛠 Owner Control Panel", reply_markup=btn)

# --- 5. Button အလုပ်လုပ်ပုံများ (Callback Query) ---

@app.on_callback_query()
async def callback_handler(client, query):
    user_id = query.from_user.id
    data = query.data

    if data == "manga_list":
        # Manga ရှာရန် (နမူနာ)
        await query.message.edit_text("📚 Manga များ ရှာဖွေနေပါသည်...")
        # ဤနေရာတွင် Database မှ Manga စာရင်း ထုတ်ပြမည့် Logic လာမည်
        
    elif data == "vip_rules":
        await query.message.edit_text("💎 VIP ဝယ်ယူခြင်း\n\n- ၁ လ: ၃၀၀၀ ကျပ်\n- Ads လုံးဝမပါပါ\n- KPay: 09xxxxxxxxx သို့ လွှဲပြီး Admin ကို SS ပို့ပါ။")

    elif data == "daily_task":
        # Ads Timer Logic (၁၅ စက္ကန့် စောင့်ခိုင်းခြင်း)
        await query.message.edit_text("⏳ ဗီဒီယိုကြော်ငြာကို ၁၅ စက္ကန့် ကြည့်ပေးပါ။ Point ရရှိပါမည်။")
        await asyncio.sleep(15)
        await query.message.edit_text("✅ Task ပြီးဆုံးပါပြီ။ Point ၅၀ ရရှိပါတယ်။", 
                                      reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_home")]]))

    elif data == "back_home":
        # Home ပြန်သွားရန်
        btn = InlineKeyboardMarkup([
            [InlineKeyboardButton("📚 Manga List", callback_data="manga_list"), InlineKeyboardButton("🎁 Daily Task", callback_data="daily_task")],
            [InlineKeyboardButton("💎 VIP Rules", callback_data="vip_rules"), InlineKeyboardButton("👤 My Profile", callback_data="profile")]
        ])
        await query.message.edit_text("Main Menu သို့ ပြန်ရောက်ပါပြီ။", reply_markup=btn)

# --- 6. Bot ကို စတင်နှိုးခြင်း ---
print("Bot Is Running Successfully! Check Telegram Admin Panel.")
app.run()
