import os
import sqlite3
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, CallbackContext
from datetime import datetime, timedelta
import schedule
import threading
from TOKEN import TOKEN
from config import ADMIN_CHAT_ID, OWNER_CHAT_ID

# Set the token of your bot here
BOT_TOKEN = TOKEN

# Set the path to the database file here
DB_PATH = "db.sqlite3"

# Your admin chat ID (make sure this is your actual admin chat ID)

# Ensure only admin can use specific commands
async def only_admin(update: Update):
    if update.message.from_user.id != ADMIN_CHAT_ID and update.message.from_user.id != OWNER_CHAT_ID and update.message.text != "/pay":
        await update.message.reply_text("Αυτή η εντολή είναι μόνο για τον διαχειριστή.")
        return True
    return False


# Start command
async def start(update: Update, context: CallbackContext):
    if await only_admin(update): return
    await update.message.reply_text("-- ΕΝΤΟΛΕΣ --\n"
                                    "/subscribe <username> - Κάνε εγγραφή του χρήστη στην υπηρεσία\n"
                                    "/unsubscribe <username> - Ακύρωσε την εγγραφή του χρήστη στην υπηρεσία\n"
                                    "/list - Εμφάνισε τους εγγεγραμμένους χρήστες\n"
                                    "/pay - Πληρωμή για την υπηρεσία\n")

# Function to add new subscriber to the database by chat_id and username
async def add_subscriber(update: Update, context: CallbackContext):
    if await only_admin(update): return  # Await the async function here
    if len(context.args) < 1:
        await update.message.reply_text("Παρακαλώ παρέχετε το όνομα χρήστη για την εγγραφή (π.χ. /subscribe username).")
        return

    username = context.args[0]  # Get the username from the arguments
    chat_id = update.message.chat_id
    date = datetime.now().strftime("%d/%m/%Y")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Insert chat_id and username
    cursor.execute("INSERT OR IGNORE INTO subscribers (chat_id, username, subscription_date) VALUES (?, ?, ?)", (chat_id, username, date))
    conn.commit()
    conn.close()
    
    await update.message.reply_text(f"Προστέθηκε ο συνδρομητής: {username} ({chat_id})")

# Function to remove subscriber from the database by chat_id
async def remove_subscriber(update: Update, context: CallbackContext):
    if await only_admin(update): return  # Await the async function here
    if len(context.args) < 1:
        await update.message.reply_text("Παρακαλώ παρέχετε το όνομα χρήστη για την ακύρωση (π.χ. /unsubscribe username).")
        return

    username = context.args[0]  # Get the username from the arguments
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM subscribers WHERE username = ?", (username,))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"Αφαιρέθηκε ο συνδρομητής: {username}")

# Function to get all subscribers from the database and list them
async def list_subscribers(update: Update, context: CallbackContext):
    if await only_admin(update): return  # Await the async function here
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id, username, subscription_date FROM subscribers")
    rows = cursor.fetchall()
    conn.close()
    
    if len(rows) == 0:
        await update.message.reply_text("Δεν βρέθηκαν συνδρομητές.")
    else:
        message = "🧑‍🤝‍🧑 *Λίστα Συνδρομητών*:\n\n"
        for chat_id, username, subscription_date in rows:
            subscription_end = datetime.strptime(subscription_date, '%d/%m/%Y').date() + timedelta(days=30)
            message += (
                f"• *Username*: {username} \n"
                f"  🆔 *Chat ID*: {chat_id} \n"
                f"  📅 *Ημερομηνία Συνδρομής*: {subscription_date} \n"
                f"  ⏳ *Τέλος Συνδρομής*: {subscription_end.strftime('%d/%m/%Y')} \n\n"
            )
        
        message += "⏬ Προβολή όλων των συνδρομητών ολοκληρώθηκε."
        await update.message.reply_text(message, parse_mode='Markdown')


async def pay(update: Update, context: CallbackContext):
    if await only_admin(update): return  # Await the async function here
    # Send revolut link to user
    await update.message.reply_text(f"Ολοκλήρωσε την πληρωμή εδώ: revolut.me/tsouf ή εδώ: https://www.paypal.me/KTsouflidis")

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
            if (subscription_end - today).days <= 2:
                await bot.send_message(chat_id=chat_id, text="Η συνδρομή σας στην υπηρεσία λήγει σε λίγες μέρες. Αν θέλετε να την ανανεώσετε γράψτε /pay.")
                print(f"Notification sent to: {username} ({chat_id})")

            # Notify if subscription has expired
            if subscription_end < today:
                await bot.send_message(chat_id=chat_id, text="Η συνδρομή σας στην υπηρεσία έχει λήξει. Αν θέλετε να την ανανεώσετε γράψτε /pay.")
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

    schedule.every().day.at("09:00").do(lambda: asyncio.run_coroutine_threadsafe(notify_subscribers(), loop))
    #schedule.every(10).seconds.do(lambda: asyncio.run_coroutine_threadsafe(notify_subscribers(), loop))

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
    application.add_handler(CommandHandler("subscribe", add_subscriber))
    application.add_handler(CommandHandler("unsubscribe", remove_subscriber))
    application.add_handler(CommandHandler("list", list_subscribers))
    application.add_handler(CommandHandler("pay", pay))

    # Start the scheduler in a separate thread
    scheduler_thread = threading.Thread(target=start_scheduler, daemon=True)
    scheduler_thread.start()

    # Run the bot
    application.run_polling()

if __name__ == "__main__":
    main()
    print("Bot started")
