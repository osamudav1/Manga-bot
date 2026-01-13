🎥 Advanced Movie Search & VIP Telegram Bot
This is a high-performance Telegram bot built using the Pyrogram library. It features an automated movie search system, a point-based VIP membership system, and integrated advertisement management.
✨ Features
• 🔍 Movie Search: Fast and efficient movie retrieval by title.
• 💎 VIP Membership System: Users can exchange earned points for VIP status with automatic expiry tracking.
• 🎁 Reward Ads: Integrated system for users to earn points by "watching" short advertisements.
• 🔗 Referral Program: Unique referral links to invite friends and earn bonus points.
• 🗑️ Auto-Delete Logic: Automatically deletes movie messages after 1 minute to keep the chat clean and protect content.
• 📢 Admin Dashboard: Comprehensive tools for broadcasting, managing users, and setting mandatory channel joins (Force Join).
🚀 Deployment
1. Requirements
Ensure you have the following libraries installed:
• pyrogram
• tgcrypto
• asyncio
2. Configuration
Update your credentials in config.py:
API_ID = 1234567
API_HASH = "your_api_hash"
BOT_TOKEN = "your_bot_token"
ADMIN_ID = 12345678
3. Running on Koyeb
Use the following Run Command in your Koyeb settings:
python3 bot.py
🛠️ Admin Commands
• /admin - Open the Owner Dashboard.
• /setad Text | Link - Change the global advertisement banner and URL.
• /stats - View total user count and bot statistics.
📝 License
This project is open-source. Feel free to fork and modify it for your own use.
💡 How to add this to your GitHub
1. Go to your GitHub Repository.
2. Click Add file > Create new file.
3. Name the file README.md.
4. Paste the English text above and click Commit changes.
