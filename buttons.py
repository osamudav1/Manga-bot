from telebot import types

def main_menu():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("📝 Edit Caption", "📺 Post Video")
    keyboard.row("⚙ Reset Titles", "❓ Help")
    return keyboard
