# import asyncio
# import requests
# from flask import Flask, request, jsonify
# from flask_cors import CORS

# from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
# from telegram.ext import (
#     Application, CommandHandler, CallbackQueryHandler, MessageHandler,
#     ContextTypes, filters
# )

# # ---- Flask Setup ----
# app = Flask(__name__)
# CORS(app)

# # ---- Bot Setup ----
# BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # Replace this with your actual bot token
# application = Application.builder().token(BOT_TOKEN).build()


# # ---- Utility Functions ----
# def fetch_pools(limit=3):
#     url = f"https://dlmm-api.meteora.ag/pair/all_with_pagination?limit={limit}"
#     try:
#         response = requests.get(url)
#         data = response.json()
#         pairs = data.get("pairs", [])
#         if not pairs:
#             return "❌ No liquidity pools found."

#         msg = f"🌊 Top {limit} Pools on Meteora:\n"
#         for pool in pairs:
#             name = pool.get("name", "N/A")
#             liquidity = pool.get("liquidity") or 0
#             price = pool.get("current_price") or 0
#             volume = pool.get("trade_volume_24h") or 0
#             tvl = f"${float(liquidity):,.2f}"
#             price_str = f"${float(price):,.2f}"
#             volume_str = f"${float(volume):,.2f}"
#             msg += (
#                 f"\n🔹 Pool: {name}\n"
#                 f"💰 TVL: {tvl}\n"
#                 f"💱 Price: {price_str}\n"
#                 f"📈 Volume (24h): {volume_str}\n"
#             )
#         return msg
#     except Exception as e:
#         return f"❌ Error fetching data: {e}"


# def create_buttons():
#     keyboard = [
#         [InlineKeyboardButton("🔍 Explore More Pools", callback_data='more')],
#         [InlineKeyboardButton("🔎 Search for Pool", callback_data='search')],
#         [InlineKeyboardButton("📍 Your Current Position", callback_data='position')],
#         [InlineKeyboardButton("💵 Live Price of Your Token", callback_data='liveprice')],
#     ]
#     return InlineKeyboardMarkup(keyboard)


# # ---- Telegram Handlers ----
# async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     context.user_data.clear()
#     message = fetch_pools(limit=3)
#     await update.message.reply_text(text=message, reply_markup=create_buttons())


# async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     query = update.callback_query
#     await query.answer()
#     data = query.data
#     current_text = query.message.text

#     if data == "more":
#         context.user_data.clear()
#         new_text = fetch_pools(limit=10)

#     elif data == "search":
#         context.user_data["awaiting_search"] = True
#         new_text = "🔍 Please type the pool name you want to search."

#     elif data == "position":
#         try:
#             response = requests.get("https://gremory-simulationserver.onrender.com/position")
#             position_data = response.json()
#             if position_data.get("error"):
#                 new_text = f"❌ Error fetching position: {position_data['error']}"
#             else:
#                 new_text = (
#                     f"📍 Your Current Position in Pools:\n\n"
#                     f"🔹 Position ID: {position_data.get('position_id', 'N/A')}\n"
#                     f"💰 Funds Deployed: ${position_data.get('funds_deployed', 0):,.2f}\n"
#                     f"💱 Current Price: ${position_data.get('current_price', 0):,.2f}\n"
#                     f"🔲 Current Range: ${position_data.get('current_range', [0,0])[0]:,.2f} - ${position_data.get('current_range', [0,0])[1]:,.2f}\n"
#                     f"💸 Fees Earned: ${position_data.get('fees_earned', 0):,.2f}\n"
#                     f"📊 Last Price Seen: ${position_data.get('last_price_seen', 0):,.2f}\n"
#                     f"🔄 Last Rebalance: {position_data.get('last_rebalance', 'N/A')}\n"
#                     f"🔁 Total Rebalances: {position_data.get('total_rebalances', 0)}"
#                 )
#         except Exception as e:
#             new_text = f"❌ Error fetching position: {e}"

#     elif data == "liveprice":
#         try:
#             response = requests.get("https://gremory-simulationserver.onrender.com/price")
#             price_data = response.json()
#             if price_data.get("error"):
#                 new_text = f"❌ Error fetching live price: {price_data['error']}"
#             else:
#                 new_text = f"💵 Live Price of Your Token: ${price_data.get('price', 0):,.2f}"
#         except Exception as e:
#             new_text = f"❌ Error fetching live price: {e}"
#     else:
#         new_text = "⚠️ Unknown option."

#     if current_text != new_text:
#         await query.edit_message_text(text=new_text, reply_markup=create_buttons())


# async def search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     if not context.user_data.get("awaiting_search"):
#         await update.message.reply_text("ℹ️ Please use /start to begin.", reply_markup=create_buttons())
#         return

#     query = update.message.text.strip().lower()
#     context.user_data["awaiting_search"] = False

#     try:
#         response = requests.get("https://dlmm-api.meteora.ag/pair/all_with_pagination?limit=100")
#         data = response.json()
#         pairs = data.get("pairs", [])
#         for pool in pairs:
#             name = pool.get("name", "").lower()
#             if query in name:
#                 liquidity = pool.get("liquidity") or 0
#                 price = pool.get("current_price") or 0
#                 volume = pool.get("trade_volume_24h") or 0
#                 msg = (
#                     f"🔍 Result for '{query}':\n\n"
#                     f"🔹 Pool: {pool.get('name')}\n"
#                     f"💰 TVL: ${float(liquidity):,.2f}\n"
#                     f"💱 Price: ${float(price):,.2f}\n"
#                     f"📈 Volume (24h): ${float(volume):,.2f}"
#                 )
#                 await update.message.reply_text(msg, reply_markup=create_buttons())
#                 return

#         await update.message.reply_text("❌ No matching pool found.", reply_markup=create_buttons())

#     except Exception as e:
#         await update.message.reply_text(f"⚠️ Error while searching: {e}", reply_markup=create_buttons())


# # ---- Flask Webhook Routes ----
# @app.route('/webhook', methods=['POST'])
# def webhook():
#     update = Update.de_json(request.get_json(force=True), application.bot)
#     asyncio.run(application.process_update(update))
#     return jsonify(success=True)


# @app.route('/', methods=['GET'])
# def index():
#     return "🚀 Telegram bot is live on Render!"


# # ---- Register Telegram Handlers ----
# application.add_handler(CommandHandler("start", start))
# application.add_handler(CallbackQueryHandler(button_handler))
# application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_handler))

# # ---- Start Flask Server ----
# if __name__ == '__main__':
#     print("Starting Flask app with Telegram bot 🚀")
#     app.run(host='0.0.0.0', port=10000)
import os
import logging
import requests
import asyncio
from flask import Flask, request, jsonify
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from dotenv import load_dotenv
import threading

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

app = Flask(__name__)
bot = Bot(token=BOT_TOKEN)

# --- Fetch Pools Function ---
def fetch_pools(limit=3):
    url = f"https://dlmm-api.meteora.ag/pair/all_with_pagination?limit={limit}"
    try:
        response = requests.get(url)
        data = response.json()
        pairs = data.get("pairs", [])
        if not pairs:
            return "❌ No liquidity pools found."

        msg = f"🌊 Top {limit} Pools on Meteora:\n"
        for pool in pairs:
            name = pool.get("name", "N/A")
            liquidity = pool.get("liquidity") or 0
            price = pool.get("current_price") or 0
            volume = pool.get("trade_volume_24h") or 0
            tvl = f"${float(liquidity):,.2f}"
            price_str = f"${float(price):,.2f}"
            volume_str = f"${float(volume):,.2f}"
            msg += (
                f"\n🔹 Pool: {name}\n"
                f"💰 TVL: {tvl}\n"
                f"💱 Price: {price_str}\n"
                f"📈 Volume (24h): {volume_str}\n"
            )
        return msg
    except Exception as e:
        logger.error(f"Error fetching pools: {e}")
        return f"❌ Error fetching data: {e}"

# --- Telegram Button Creation ---
def create_buttons():
    keyboard = [
        [InlineKeyboardButton("🔍 Explore More Pools", callback_data='more')],
        [InlineKeyboardButton("🔎 Search for Pool", callback_data='search')],
        [InlineKeyboardButton("📍 Your Current Position", callback_data='position')],
        [InlineKeyboardButton("💵 Live Price of Your Token", callback_data='liveprice')],
    ]
    return InlineKeyboardMarkup(keyboard)

# Store user states
user_states = {}

# Helper function to run async functions
def run_async(coroutine):
    """Run an async function in a new event loop and return the result"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coroutine)
    finally:
        loop.close()

# --- Command Handlers ---
def handle_start(update):
    chat_id = update.message.chat_id
    user_states.pop(chat_id, None)  # Clear user state if any
    message = fetch_pools(limit=3)
    run_async(bot.send_message(
        chat_id=chat_id,
        text=message,
        reply_markup=create_buttons()
    ))

def handle_message(update):
    chat_id = update.message.chat_id
    message_text = update.message.text
    
    # Check if user is in search mode
    if user_states.get(chat_id) == "awaiting_search":
        search_term = message_text.strip()
        user_states[chat_id] = None  # Clear the search state
        
        # Simple mock search response - implement actual search here
        run_async(bot.send_message(
            chat_id=chat_id,
            text=f"🔍 Searching for pool with term: {search_term}\n\nThis functionality is not fully implemented yet.",
            reply_markup=create_buttons()
        ))
    else:
        # Default response for non-command messages
        run_async(bot.send_message(
            chat_id=chat_id,
            text="I don't understand that command. Try /start to begin.",
        ))

def handle_callback_query(update):
    query = update.callback_query
    chat_id = query.message.chat_id
    message_id = query.message.message_id
    data = query.data
    
    # Answer callback query to stop loading indicator
    run_async(bot.answer_callback_query(callback_query_id=query.id))
    
    if data == "more":
        user_states.pop(chat_id, None)  # Clear user state
        new_text = fetch_pools(limit=10)
    elif data == "search":
        user_states[chat_id] = "awaiting_search"
        new_text = "🔍 Please type the pool name you want to search."
    elif data == "position":
        try:
            response = requests.get("https://gremory-simulationserver.onrender.com/position")
            position_data = response.json()
            if position_data.get("error"):
                new_text = f"❌ Error fetching position: {position_data['error']}"
            else:
                new_text = (
                    f"📍 Your Current Position in Pools:\n\n"
                    f"🔹 Position ID: {position_data.get('position_id', 'N/A')}\n"
                    f"💰 Funds Deployed: ${position_data.get('funds_deployed', 0):,.2f}\n"
                    f"💱 Current Price: ${position_data.get('current_price', 0):,.2f}\n"
                    f"🔲 Current Range: ${position_data.get('current_range', [0,0])[0]:,.2f} - ${position_data.get('current_range', [0,0])[1]:,.2f}\n"
                    f"💸 Fees Earned: ${position_data.get('fees_earned', 0):,.2f}\n"
                    f"📊 Last Price Seen: ${position_data.get('last_price_seen', 0):,.2f}\n"
                    f"🔄 Last Rebalance: {position_data.get('last_rebalance', 'N/A')}\n"
                    f"🔁 Total Rebalances: {position_data.get('total_rebalances', 0)}"
                )
        except Exception as e:
            logger.error(f"Error fetching position: {e}")
            new_text = f"❌ Error fetching position: {e}"
    elif data == "liveprice":
        try:
            response = requests.get("https://gremory-simulationserver.onrender.com/price")
            price_data = response.json()
            if price_data.get("error"):
                new_text = f"❌ Error fetching live price: {price_data['error']}"
            else:
                new_text = f"💵 Live Price of Your Token: ${price_data.get('price', 0):,.2f}"
        except Exception as e:
            logger.error(f"Error fetching live price: {e}")
            new_text = f"❌ Error fetching live price: {e}"
    else:
        new_text = "⚠️ Unknown option."
    
    # Edit message text
    run_async(bot.edit_message_text(
        chat_id=chat_id,
        message_id=message_id,
        text=new_text,
        reply_markup=create_buttons()
    ))

# --- Flask Routes ---
@app.route('/')
def index():
    return "Bot is running!"

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle webhook updates from Telegram"""
    update_json = request.get_json()
    
    # Process update in a separate thread to avoid blocking
    def process_update(update_data):
        try:
            update = Update.de_json(update_data, bot)
            
            # Handle different types of updates
            if update.message and update.message.text:
                if update.message.text.startswith('/start'):
                    handle_start(update)
                else:
                    handle_message(update)
            elif update.callback_query:
                handle_callback_query(update)
        except Exception as e:
            logger.error(f"Error processing update: {e}")
    
    # Start processing in a new thread
    threading.Thread(target=process_update, args=(update_json,)).start()
    return jsonify(success=True)

# Set up webhook (fix for handling coroutines)
def setup_webhook():
    try:
        # Create a separate loop to run the async setup
        async def async_setup():
            # Get current webhook info
            webhook_info = await bot.get_webhook_info()
            current_url = webhook_info.url
            
            # Only set webhook if it's not already set to the right URL
            if current_url != WEBHOOK_URL:
                await bot.delete_webhook()
                await bot.set_webhook(url=WEBHOOK_URL)
                logger.info(f"Webhook set to {WEBHOOK_URL}")
            else:
                logger.info(f"Webhook already set to {WEBHOOK_URL}")
        
        # Run the async setup in a new event loop
        run_async(async_setup())
    except Exception as e:
        logger.error(f"Error setting up webhook: {e}")
        raise

# --- Main Entry Point ---
if __name__ == '__main__':
    # Set up the webhook
    setup_webhook()
    
    # Run the Flask app
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
