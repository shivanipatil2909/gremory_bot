# import os
# import requests
# import asyncio
# from flask import Flask, request
# from dotenv import load_dotenv
# from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
# from telegram.ext import (
#     Application,
#     CommandHandler,
#     ContextTypes,
#     CallbackQueryHandler,
#     MessageHandler,
#     filters,
# )

# # Load environment variables
# load_dotenv()
# BOT_TOKEN = os.getenv("BOT_TOKEN")
# WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # e.g., https://your-app-name.onrender.com/webhook

# # Flask app
# app = Flask(__name__)

# # Telegram bot application
# application = Application.builder().token(BOT_TOKEN).build()

# # 🔁 Fetch pool data
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


# # 🔘 Buttons
# def create_buttons():
#     keyboard = [
#         [InlineKeyboardButton("🔍 Explore More Pools", callback_data='more')],
#         [InlineKeyboardButton("🔎 Search for Pool", callback_data='search')],
#         [InlineKeyboardButton("📍 Your Current Position", callback_data='position')],
#         [InlineKeyboardButton("💵 Live Price of Your Token", callback_data='liveprice')],
#     ]
#     return InlineKeyboardMarkup(keyboard)


# # ✅ /start handler
# async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     context.user_data.clear()
#     message = fetch_pools(limit=3)
#     await update.message.reply_text(text=message, reply_markup=create_buttons())


# # 🔘 Button clicks
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


# # 🔍 Search handler
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


# # 🧠 Webhook endpoint
# @app.route('/webhook', methods=['POST'])
# def webhook():
#     if request.method == "POST":
#         update = Update.de_json(request.get_json(force=True), application.bot)
#         asyncio.run(application.process_update(update))  # ✅ important fix
#         return "ok"


# # 🟢 Flask index route
# @app.route('/', methods=['GET'])
# def index():
#     return "🚀 Bot is running via webhook."


# # 🔧 Setup handlers and start webhook
# async def setup():
#     application.add_handler(CommandHandler("start", start))
#     application.add_handler(CallbackQueryHandler(button_handler))
#     application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_handler))

#     await application.initialize()
#     await application.start()  # ✅ start application
#     await application.bot.set_webhook(url=WEBHOOK_URL)


# # Run the Flask app with bot setup
# if __name__ == "__main__":
#     asyncio.run(setup())
#     app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
import os
import asyncio
from flask import Flask, request
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

# Load environment variables from .env file
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # e.g., https://yourappname.onrender.com/webhook

# Create Flask app
app = Flask(__name__)

# Create Telegram application
application = Application.builder().token(BOT_TOKEN).build()


# ✅ Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("✅ /start command received!")
    await update.message.reply_text("Hello Shivani! 🚀 Your bot is working!")


# ✅ Webhook endpoint
@app.route("/webhook", methods=["POST"])
def webhook():
    print("🔥 Telegram sent an update!")
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), application.bot)
        asyncio.run(application.process_update(update))
        return "ok"


# ✅ Simple root check
@app.route("/", methods=["GET"])
def index():
    return "🚀 Bot is running (root check)"


# ✅ Setup bot handlers
async def setup():
    application.add_handler(CommandHandler("start", start))

    await application.initialize()
    await application.start()
    await application.bot.set_webhook(url=WEBHOOK_URL)


# ✅ Main entry point
if __name__ == "__main__":
    asyncio.run(setup())
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

