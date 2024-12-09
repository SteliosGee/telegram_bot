import os
import sqlite3
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext
import time
from TOKEN import TOKEN

# Set the token of your bot here

BOT_TOKEN = TOKEN

# Set the path to the database file here
DB_PATH = "db.sqlite3"

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Welcome to the bot!")

# Function to add new subscriber to the database by chat_id and username
async def add_subscriber(update: Update):
    chat_id = update.message.chat_id
    username = update.message.chat.username
    date = time.strftime("%d/%m/%Y")
    print(f"Added subscriber: {username} ({chat_id})")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Insert chat_id and username (if you want to store username in the database as well)
    cursor.execute("INSERT OR IGNORE INTO subscribers (chat_id, username, subscription_date) VALUES (?, ?, ?)", (chat_id, username, date))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"Added subscriber: {username} ({chat_id})")

# Function to remove subscriber from the database by chat_id
async def remove_subscriber(update: Update):
    chat_id = update.message.chat_id
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM subscribers WHERE chat_id = ?", (chat_id,))
    conn.commit()
    conn.close()
    print(f"Removed subscriber: {chat_id}")
    await update.message.reply_text(f"Removed subscriber: {chat_id}")

# Function to get all subscribers from the database
def get_subscribers():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id, username FROM subscribers")
    rows = cursor.fetchall()
    conn.close()
    return rows

# Function to send a message with a list of all subscribers
async def send_subscribers(bot: Bot):
    subscribers = get_subscribers()
    message = "Subscribers:\n"
    for chat_id, username in subscribers:
        message += f"{username} ({chat_id})\n"
    await bot.send_message(chat_id=chat_id, text=message)

# end of the functions

def main():
    # Create the database file if it doesn't exist
    if not os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE subscribers (chat_id INTEGER PRIMARY KEY, username TEXT, subscription_date TEXT)")
        conn.commit()
        conn.close()

    # Create the application
    application = Application.builder().token(TOKEN).build()

    # Add the command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("subscribe", lambda update, context: add_subscriber(update)))
    application.add_handler(CommandHandler("unsubscribe", lambda update, context: remove_subscriber(update)))
    application.add_handler(CommandHandler("subscribers", lambda update, context: send_subscribers(context.bot)))


    application.run_polling()

if __name__ == "__main__":
    main()

    