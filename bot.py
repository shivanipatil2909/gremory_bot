
# import os
# import logging
# import json
# import requests
# from flask import Flask, request, jsonify
# from dotenv import load_dotenv
# import threading

# # Configure logging
# logging.basicConfig(
#     format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
# )
# logger = logging.getLogger(__name__)

# # Load environment variables
# load_dotenv()
# BOT_TOKEN = os.getenv("BOT_TOKEN")
# WEBHOOK_URL = os.getenv("WEBHOOK_URL")
# API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# app = Flask(__name__)

# # Store user states - simple in-memory storage
# user_states = {}

# # --- Direct Telegram API Functions ---
# def send_message(chat_id, text, reply_markup=None):
#     """Send message using direct API call instead of Bot object"""
#     url = f"{API_URL}/sendMessage"
#     payload = {
#         'chat_id': chat_id,
#         'text': text,
#         'parse_mode': 'HTML'
#     }
    
#     if reply_markup:
#         payload['reply_markup'] = json.dumps(reply_markup)
        
#     try:
#         response = requests.post(url, json=payload)
#         return response.json()
#     except Exception as e:
#         logger.error(f"Error sending message: {e}")
#         return None

# def answer_callback_query(callback_query_id):
#     """Answer callback query using direct API call"""
#     url = f"{API_URL}/answerCallbackQuery"
#     payload = {'callback_query_id': callback_query_id}
    
#     try:
#         response = requests.post(url, json=payload)
#         return response.json()
#     except Exception as e:
#         logger.error(f"Error answering callback: {e}")
#         return None

# def edit_message_text(chat_id, message_id, text, reply_markup=None):
#     """Edit message using direct API call"""
#     url = f"{API_URL}/editMessageText"
#     payload = {
#         'chat_id': chat_id,
#         'message_id': message_id,
#         'text': text,
#         'parse_mode': 'HTML'
#     }
    
#     if reply_markup:
#         payload['reply_markup'] = json.dumps(reply_markup)
        
#     try:
#         response = requests.post(url, json=payload)
#         return response.json()
#     except Exception as e:
#         logger.error(f"Error editing message: {e}")
#         return None

# def set_webhook(webhook_url):
#     """Set webhook using direct API call"""
#     url = f"{API_URL}/setWebhook"
#     payload = {'url': webhook_url}
    
#     try:
#         response = requests.post(url, json=payload)
#         result = response.json()
#         if result.get('ok'):
#             logger.info(f"Webhook set to {webhook_url}")
#         else:
#             logger.error(f"Failed to set webhook: {result}")
#         return result
#     except Exception as e:
#         logger.error(f"Error setting webhook: {e}")
#         return None

# # --- Fetch Pools Function ---
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
#         logger.error(f"Error fetching pools: {e}")
#         return f"❌ Error fetching data: {e}"

# # --- Telegram Button Creation ---
# def create_buttons():
#     keyboard = {
#         "inline_keyboard": [
#             [{"text": "🔍 Explore More Pools", "callback_data": "more"}],
#             [{"text": "🔎 Search for Pool", "callback_data": "search"}],
#             [{"text": "📍 Your Current Position", "callback_data": "position"}],
#             [{"text": "💵 Live Price of Your Token", "callback_data": "liveprice"}]
#         ]
#     }
#     return keyboard

# # --- Command Handlers ---
# def handle_start(chat_id):
#     # Clear user state if any
#     user_states.pop(str(chat_id), None)
    
#     # Send welcome message with pools
#     message = fetch_pools(limit=3)
#     send_message(chat_id, message, create_buttons())

# def handle_message(chat_id, text):
#     # Check if user is in search mode
#     if user_states.get(str(chat_id)) == "awaiting_search":
#         search_term = text.strip()
#         user_states[str(chat_id)] = None  # Clear the search state
        
#         # Simple mock search response - implement actual search here
#         send_message(
#             chat_id,
#             f"🔍 Searching for pool with term: {search_term}\n\nThis functionality is not fully implemented yet.",
#             create_buttons()
#         )
#     else:
#         # Default response for non-command messages
#         send_message(
#             chat_id,
#             "I don't understand that command. Try /start to begin."
#         )

# def handle_callback(callback_query):
#     query_id = callback_query.get("id")
#     data = callback_query.get("data")
#     message = callback_query.get("message", {})
#     chat_id = message.get("chat", {}).get("id")
#     message_id = message.get("message_id")
    
#     # Answer callback query to stop loading indicator
#     answer_callback_query(query_id)
    
#     if data == "more":
#         user_states.pop(str(chat_id), None)  # Clear user state
#         new_text = fetch_pools(limit=10)
#     elif data == "search":
#         user_states[str(chat_id)] = "awaiting_search"
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
#             logger.error(f"Error fetching position: {e}")
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
#             logger.error(f"Error fetching live price: {e}")
#             new_text = f"❌ Error fetching live price: {e}"
#     else:
#         new_text = "⚠️ Unknown option."
    
#     # Edit message text
#     edit_message_text(chat_id, message_id, new_text, create_buttons())

# # --- Flask Routes ---
# @app.route('/')
# def index():
#     return "Bot is running!"

# @app.route('/webhook', methods=['POST'])
# def webhook():
#     """Handle webhook updates from Telegram"""
#     update = request.get_json()
    
#     # Process update in a separate thread to avoid blocking
#     def process_update(update_data):
#         try:
#             # Handle different types of updates
#             if "message" in update_data:
#                 message = update_data["message"]
#                 chat_id = message.get("chat", {}).get("id")
#                 text = message.get("text", "")
                
#                 if text.startswith('/start'):
#                     handle_start(chat_id)
#                 else:
#                     handle_message(chat_id, text)
#             elif "callback_query" in update_data:
#                 callback_query = update_data["callback_query"]
#                 handle_callback(callback_query)
#         except Exception as e:
#             logger.error(f"Error processing update: {e}")
    
#     # Start processing in a new thread
#     threading.Thread(target=process_update, args=(update,)).start()
#     return jsonify(success=True)

# # --- Main Entry Point ---
# if __name__ == '__main__':
#     # Set up the webhook
#     set_webhook(WEBHOOK_URL)
    
#     # Run the Flask app
#     port = int(os.environ.get("PORT", 10000))
#     app.run(host='0.0.0.0', port=port)
import os
import logging
import json
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Configure more verbose logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://gremory-bot.onrender.com/webhook")
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Ensure webhook URL has https:// prefix
if not WEBHOOK_URL.startswith("https://"):
    WEBHOOK_URL = f"https://{WEBHOOK_URL}"
    
logger.info(f"Using webhook URL: {WEBHOOK_URL}")

app = Flask(__name__)

# Store user states - simple in-memory storage
user_states = {}

# --- Direct Telegram API Functions ---
def send_message(chat_id, text, reply_markup=None):
    url = f"{API_URL}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML'
    }
    if reply_markup:
        payload['reply_markup'] = json.dumps(reply_markup)
    try:
        response = requests.post(url, json=payload)
        logger.info(f"Send message response: {response.text}")
        return response.json()
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return None

def delete_webhook():
    url = f"{API_URL}/deleteWebhook"
    try:
        response = requests.get(url)
        logger.info(f"Delete webhook response: {response.text}")
        return response.json()
    except Exception as e:
        logger.error(f"Error deleting webhook: {e}")
        return None

def get_webhook_info():
    url = f"{API_URL}/getWebhookInfo"
    try:
        response = requests.get(url)
        logger.info(f"Webhook info: {response.text}")
        return response.json()
    except Exception as e:
        logger.error(f"Error getting webhook info: {e}")
        return None

def send_test_message():
    # Send a message to yourself (if you know your chat_id)
    # Replace with your actual chat_id
    # You can get your chat_id by talking to @userinfobot on Telegram
    admin_chat_id = os.getenv("ADMIN_CHAT_ID")
    if admin_chat_id:
        send_message(admin_chat_id, "🔄 Bot has been restarted and is now online!")

def answer_callback_query(callback_query_id):
    url = f"{API_URL}/answerCallbackQuery"
    payload = {'callback_query_id': callback_query_id}
    try:
        response = requests.post(url, json=payload)
        logger.info(f"Answer callback response: {response.text}")
        return response.json()
    except Exception as e:
        logger.error(f"Error answering callback: {e}")
        return None

def edit_message_text(chat_id, message_id, text, reply_markup=None):
    url = f"{API_URL}/editMessageText"
    payload = {
        'chat_id': chat_id,
        'message_id': message_id,
        'text': text,
        'parse_mode': 'HTML'
    }
    if reply_markup:
        payload['reply_markup'] = json.dumps(reply_markup)
    try:
        response = requests.post(url, json=payload)
        logger.info(f"Edit message response: {response.text}")
        return response.json()
    except Exception as e:
        logger.error(f"Error editing message: {e}")
        return None

def set_webhook(webhook_url):
    url = f"{API_URL}/setWebhook"
    payload = {'url': webhook_url}
    try:
        response = requests.post(url, json=payload)
        result = response.json()
        logger.info(f"Set webhook response: {response.text}")
        if result.get('ok'):
            logger.info(f"✅ Webhook successfully set to {webhook_url}")
        else:
            logger.error(f"❌ Failed to set webhook: {result}")
        return result
    except Exception as e:
        logger.error(f"Error setting webhook: {e}")
        return None

# --- Telegram Button Creation ---
def create_buttons():
    return {
        "inline_keyboard": [
            [{"text": "Show Agents", "callback_data": "agents"}],
            [{"text": "Balance", "callback_data": "balance"}],
            [{"text": "View/Search Liquidity Pools", "callback_data": "view_search_lp"}]
        ]
    }

def handle_start(chat_id):
    logger.info(f"Handling /start command for chat_id: {chat_id}")
    user_states[chat_id] = "awaiting_login"
    result = send_message(chat_id, "👋 Welcome! Please choose an option:", {
        "inline_keyboard": [
            [{"text": "Login", "callback_data": "login"}],
            [{"text": "Create Account", "callback_data": "register"}]
        ]
    })
    logger.info(f"Result of sending welcome message: {result}")

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

# --- Search Pools Function ---
def search_pool(query):
    url = f"https://dlmm-api.meteora.ag/pair/search?query={query}"
    try:
        response = requests.get(url)
        data = response.json()
        pools = data.get("pairs", [])
        if not pools:
            return "❌ No pools found matching your search."

        msg = f"🔍 Search Results for '{query}':\n"
        for pool in pools:
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
        logger.error(f"Error searching for pools: {e}")
        return f"❌ Error fetching data: {e}"

# --- Flask Routes ---
@app.route('/')
def index():
    # First, delete any existing webhooks
    delete_webhook()
    
    # Then set the new webhook
    webhook_result = set_webhook(WEBHOOK_URL)
    
    # Get webhook info to verify
    info_result = get_webhook_info()
    
    # Send a test message if admin chat ID is set
    send_test_message()
    
    return f"""
    <h1>Telegram Bot Status</h1>
    <p>Bot is running!</p>
    <p>Webhook set to: {WEBHOOK_URL}</p>
    <p>Webhook info: {json.dumps(info_result)}</p>
    """

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        # Log all request information
        logger.info(f"Request headers: {dict(request.headers)}")
        logger.info(f"Request data: {request.data}")
        
        update = request.get_json()
        logger.info(f"Parsed update: {update}")
        
        if update is None:
            logger.error("No JSON data received in webhook")
            return jsonify({"status": "error", "message": "No JSON data received"}), 400

        if "message" in update:
            chat_id = update["message"]["chat"]["id"]
            logger.info(f"Message from chat_id: {chat_id}")
            
            if "text" in update["message"]:
                text = update["message"]["text"]
                logger.info(f"Message text: {text}")
                
                if text.startswith("/start"):
                    handle_start(chat_id)
                elif chat_id in user_states and user_states.get(chat_id) == "awaiting_search":
                    query = text.strip()
                    msg = search_pool(query)
                    send_message(chat_id, msg)
                    user_states[chat_id] = "logged_in"  # Reset state after search
                else:
                    send_message(chat_id, "Unknown command. Try /start")
            else:
                logger.warning(f"Message without text: {update}")
                send_message(chat_id, "I can only process text messages. Please send a text command.")

        elif "callback_query" in update:
            logger.info(f"Callback query received: {update['callback_query']}")
            cb = update["callback_query"]
            data = cb.get("data")
            chat_id = cb["message"]["chat"]["id"]
            message_id = cb["message"]["message_id"]
            answer_callback_query(cb["id"])

            if data == "login" or data == "register":
                user_states[chat_id] = "logged_in"
                send_message(chat_id, "✅ You're now logged in.", create_buttons())

            elif data == "agents":
                send_message(chat_id, "🤖 List of Active Agents (mock)")

            elif data == "balance":
                send_message(chat_id, "📊 Agent Earnings: \nAgent 1: +5.4%\nAgent 2: +3.1%")

            elif data == "view_search_lp":
                send_message(chat_id, "🌐 View or Search for Liquidity Pools", {
                    "inline_keyboard": [
                        [{"text": "Explore Pools", "callback_data": "explore_pools"}],
                        [{"text": "Search Pools", "callback_data": "search_pools"}]
                    ]
                })

            elif data == "explore_pools":
                msg = fetch_pools()
                send_message(chat_id, msg)

            elif data == "search_pools":
                user_states[chat_id] = "awaiting_search"
                send_message(chat_id, "🔍 Type the name/symbol of the pool you want to search:")
        else:
            logger.warning(f"Update with no message or callback_query: {update}")

    except Exception as e:
        logger.error(f"Error processing update: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

    return jsonify({"status": "ok"})

# Additional debug route
@app.route('/debug', methods=['GET'])
def debug():
    # Get webhook info
    webhook_info = get_webhook_info()
    
    # Try to send a test message
    admin_chat_id = os.getenv("ADMIN_CHAT_ID")
    test_message_result = None
    if admin_chat_id:
        test_message_result = send_message(admin_chat_id, "Debug message from bot")
    
    debug_info = {
        "webhook_info": webhook_info,
        "environment": {
            "BOT_TOKEN": BOT_TOKEN[:5] + "..." if BOT_TOKEN else None,
            "WEBHOOK_URL": WEBHOOK_URL,
            "PORT": os.getenv("PORT", "10000"),
            "ADMIN_CHAT_ID": admin_chat_id
        },
        "test_message_result": test_message_result,
        "user_states": user_states
    }
    
    return jsonify(debug_info)

# Manual test endpoint
@app.route('/test_webhook', methods=['GET'])
def test_webhook():
    # Simulate a message update
    test_update = {
        "update_id": 123456789,
        "message": {
            "message_id": 123,
            "from": {
                "id": 12345678,
                "first_name": "Test",
                "username": "test_user"
            },
            "chat": {
                "id": 12345678,
                "first_name": "Test",
                "username": "test_user",
                "type": "private"
            },
            "date": 1618924582,
            "text": "/start"
        }
    }
    
    # Process the simulated update
    admin_chat_id = os.getenv("ADMIN_CHAT_ID")
    if admin_chat_id:
        # Override the chat_id to send to admin
        test_update["message"]["chat"]["id"] = int(admin_chat_id)
        test_update["message"]["from"]["id"] = int(admin_chat_id)
        
        # Log the test update
        logger.info(f"Processing test update: {test_update}")
        
        # Process as if it was received via webhook
        if "message" in test_update:
            chat_id = test_update["message"]["chat"]["id"]
            text = test_update["message"].get("text", "")
            
            if text.startswith("/start"):
                handle_start(chat_id)
            else:
                send_message(chat_id, "Test message received!")
                
        return jsonify({"status": "ok", "message": "Test update processed"})
    else:
        return jsonify({"status": "error", "message": "ADMIN_CHAT_ID not set"})

# Run the application
if __name__ == "__main__":
    # Delete and reset webhook before starting
    delete_webhook()
    set_webhook(WEBHOOK_URL)
    get_webhook_info()
    
    # Send a startup message
    send_test_message()
    
    port = int(os.getenv("PORT", 10000))
    logger.info(f"Starting Flask server on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
