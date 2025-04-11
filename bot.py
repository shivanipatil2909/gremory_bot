import os
import requests
from dotenv import load_dotenv
from flask import Flask, request
from telegram import Bot, Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
import asyncio

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
bot = Bot(TOKEN)
application = None  # ✅ Define globally here

app = Flask(__name__)

# 🔁 Fetch pool data
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
        return f"❌ Error fetching data: {e}"

# 🔘 Buttons
def create_buttons():
    keyboard = [
        [InlineKeyboardButton("🔍 Explore More Pools", callback_data='more')],
        [InlineKeyboardButton("🔎 Search for Pool", callback_data='search')],
        [InlineKeyboardButton("📍 Your Current Position", callback_data='position')],
        [InlineKeyboardButton("💵 Live Price of Your Token", callback_data='liveprice')],
    ]
    return InlineKeyboardMarkup(keyboard)

# ✅ /start handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    message = "Hey Shivani 👋\n\n" + fetch_pools(limit=3)
    await update.message.reply_text(text=message, reply_markup=create_buttons())

# 🔘 Button click handler
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    current_text = query.message.text

    if data == "more":
        context.user_data.clear()
        new_text = fetch_pools(limit=10)

    elif data == "search":
        context.user_data["awaiting_search"] = True
        new_text = "🔍 Please type the pool name you want to search."

    elif data == "position":
        try:
            response = requests.get("https://gremory-simulationserver.onrender.com/position")
            position_data = response.json()
            if position_data.get("error"):
                new_text = f"❌ Error: {position_data['error']}"
            else:
                new_text = (
                    f"📍 Current Position:\n\n"
                    f"🔹 ID: {position_data.get('position_id', 'N/A')}\n"
                    f"💰 Funds: ${position_data.get('funds_deployed', 0):,.2f}\n"
                    f"💱 Price: ${position_data.get('current_price', 0):,.2f}\n"
                    f"🔲 Range: ${position_data.get('current_range', [0,0])[0]:,.2f} - ${position_data.get('current_range', [0,0])[1]:,.2f}\n"
                    f"💸 Fees: ${position_data.get('fees_earned', 0):,.2f}\n"
                    f"📊 Last Seen: ${position_data.get('last_price_seen', 0):,.2f}\n"
                    f"🔄 Rebalances: {position_data.get('total_rebalances', 0)}"
                )
        except Exception as e:
            new_text = f"❌ Error: {e}"

    elif data == "liveprice":
        try:
            response = requests.get("https://gremory-simulationserver.onrender.com/price")
            price_data = response.json()
            if price_data.get("error"):
                new_text = f"❌ Error: {price_data['error']}"
            else:
                new_text = f"💵 Token Price: ${price_data.get('price', 0):,.2f}"
        except Exception as e:
            new_text = f"❌ Error: {e}"

    else:
        new_text = "⚠️ Unknown option."

    if current_text != new_text:
        await query.edit_message_text(text=new_text, reply_markup=create_buttons())

# 🔍 Search Handler
async def search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("awaiting_search"):
        await update.message.reply_text("ℹ️ Use /start to begin.", reply_markup=create_buttons())
        return

    query = update.message.text.strip().lower()
    context.user_data["awaiting_search"] = False

    try:
        response = requests.get("https://dlmm-api.meteora.ag/pair/all_with_pagination?limit=100")
        data = response.json()
        pairs = data.get("pairs", [])
        for pool in pairs:
            name = pool.get("name", "").lower()
            if query in name:
                liquidity = pool.get("liquidity") or 0
                price = pool.get("current_price") or 0
                volume = pool.get("trade_volume_24h") or 0
                msg = (
                    f"🔍 Result for '{query}':\n\n"
                    f"🔹 Pool: {pool.get('name')}\n"
                    f"💰 TVL: ${float(liquidity):,.2f}\n"
                    f"💱 Price: ${float(price):,.2f}\n"
                    f"📈 Volume (24h): ${float(volume):,.2f}"
                )
                await update.message.reply_text(msg, reply_markup=create_buttons())
                return

        await update.message.reply_text("❌ No matching pool found.", reply_markup=create_buttons())

    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {e}", reply_markup=create_buttons())

# 🌐 Flask Webhook Route
@app.route("/webhook", methods=["POST"])
def webhook():
    global application
    if application:
        update = Update.de_json(request.get_json(force=True), bot)
        application.update_queue.put_nowait(update)
        return "ok"
    return "⚠️ Bot not ready yet.", 503

# 🚀 Main App Runner
async def main():
    global application
    application = (
        Application.builder()
        .token(TOKEN)
        .concurrent_updates(True)
        .build()
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_handler))

    # Set webhook once
    await bot.set_webhook(WEBHOOK_URL)
    print("✅ Webhook set!")

    # No polling because Flask handles updates

if __name__ == "__main__":
    asyncio.run(main())
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
