import os
import sqlite3
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, CallbackContext
from datetime import datetime, timedelta
import time
import schedule
import threading
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
    date = datetime.now().strftime("%d/%m/%Y")
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

# Function to notify subscribers about subscription expiry
async def notify_subscribers():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Fetch all subscribers
        cursor.execute("SELECT chat_id, username, subscription_date FROM subscribers")
        rows = cursor.fetchall()
    except Exception as e:
        print(f"Database error: {e}")
        return
    finally:
        conn.close()
    
    # Initialize bot once
    bot = Bot(token=BOT_TOKEN)
    today = datetime.now().date()

    for chat_id, username, subscription_date in rows:
        try:
            # Parse subscription date
            subscription_start = datetime.strptime(subscription_date, "%d/%m/%Y").date()
            subscription_end = subscription_start + timedelta(days=30)  # Subscription period: 1 month
            
            # Notify if subscription is about to expire (e.g., 2 days before expiry)
            if (subscription_end - today).days <= 40:
                await bot.send_message(chat_id=chat_id, text="Your subscription is about to expire. Please renew your subscription.")
                print(f"Notification sent to: {username} ({chat_id})")
        except Exception as e:
            print(f"Error processing subscriber {username} ({chat_id}): {e}")

# Background thread to handle daily notifications
import asyncio

# Background thread to handle daily notifications
def start_scheduler():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def run_scheduler():
        while True:
            schedule.run_pending()
            await asyncio.sleep(1)

    #schedule.every().day.at("09:00").do(lambda: asyncio.run_coroutine_threadsafe(notify_subscribers(), loop))
    schedule.every(10).seconds.do(lambda: asyncio.run_coroutine_threadsafe(notify_subscribers(), loop))

    loop.run_until_complete(run_scheduler())
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

    # Start the scheduler in a separate thread
    scheduler_thread = threading.Thread(target=start_scheduler, daemon=True)
    scheduler_thread.start()

    # Run the bot
    application.run_polling()

if __name__ == "__main__":
    main()
