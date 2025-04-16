import os
import logging
import json
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import threading

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

app = Flask(__name__)
user_states = {}

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
        return response.json()
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return None

def answer_callback_query(callback_query_id):
    url = f"{API_URL}/answerCallbackQuery"
    payload = {'callback_query_id': callback_query_id}
    try:
        response = requests.post(url, json=payload)
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
        if result.get('ok'):
            logger.info(f"Webhook set to {webhook_url}")
        else:
            logger.error(f"Failed to set webhook: {result}")
        return result
    except Exception as e:
        logger.error(f"Error setting webhook: {e}")
        return None

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

def create_buttons():
    keyboard = {
        "inline_keyboard": [
            [{"text": "🔍 Explore More Pools", "callback_data": "more"}],
            [{"text": "🔎 Search for Pool", "callback_data": "search"}],
            [{"text": "📍 Your Current Position", "callback_data": "position"}],
            [{"text": "💵 Live Price of Your Token", "callback_data": "liveprice"}]
        ]
    }
    return keyboard

def handle_start(chat_id):
    user_states.pop(str(chat_id), None)
    message = fetch_pools(limit=3)
    send_message(chat_id, message, create_buttons())

def handle_message(chat_id, text):
    if user_states.get(str(chat_id)) == "awaiting_search":
        search_term = text.strip()
        user_states[str(chat_id)] = None
        send_message(
            chat_id,
            f"🔍 Searching for pool with term: {search_term}\n\nThis functionality is not fully implemented yet.",
            create_buttons()
        )
    else:
        send_message(
            chat_id,
            "I don't understand that command. Try /start to begin."
        )

def handle_callback(callback_query):
    query_id = callback_query.get("id")
    data = callback_query.get("data")
    message = callback_query.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    message_id = message.get("message_id")
    answer_callback_query(query_id)

    if data == "more":
        user_states.pop(str(chat_id), None)
        new_text = fetch_pools(limit=10)
    elif data == "search":
        user_states[str(chat_id)] = "awaiting_search"
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

    edit_message_text(chat_id, message_id, new_text, create_buttons())

@app.route('/')
def index():
    return "Bot is running!"

@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.get_json()
    def process_update(update_data):
        try:
            if "message" in update_data:
                message = update_data["message"]
                chat_id = message.get("chat", {}).get("id")
                text = message.get("text", "")
                if text.startswith('/start'):
                    handle_start(chat_id)
                else:
                    handle_message(chat_id, text)
            elif "callback_query" in update_data:
                callback_query = update_data["callback_query"]
                handle_callback(callback_query)
        except Exception as e:
            logger.error(f"Error processing update: {e}")
    threading.Thread(target=process_update, args=(update,)).start()
    return jsonify(success=True)

if __name__ == '__main__':
    set_webhook(WEBHOOK_URL)
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# import os
# import logging
# import json
# import requests
# from flask import Flask, request, jsonify
# from dotenv import load_dotenv
# import threading
# import uuid
# from datetime import datetime

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
# # Simple user database (in a real application, use a proper database)
# users_db = {}
# # Simple agent database (in a real application, use a proper database)
# agents_db = {}

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

# # --- Authentication Functions ---
# def register_user(chat_id, username, password):
#     """Register a new user"""
#     if username in users_db:
#         return False, "Username already exists. Please choose another username."
    
#     users_db[username] = {
#         "password": password,
#         "chat_id": chat_id,
#         "registered_on": datetime.now().isoformat(),
#         "agents": []
#     }
#     return True, f"Registration successful! Welcome {username}!"

# def login_user(chat_id, username, password):
#     """Login an existing user"""
#     if username not in users_db:
#         return False, "Username not found. Please register first."
    
#     if users_db[username]["password"] != password:
#         return False, "Incorrect password. Please try again."
    
#     # Update chat_id in case user is logging in from a different chat
#     users_db[username]["chat_id"] = chat_id
#     return True, f"Login successful! Welcome back {username}!"

# def get_username_by_chat_id(chat_id):
#     """Get username by chat ID"""
#     for username, data in users_db.items():
#         if data["chat_id"] == chat_id:
#             return username
#     return None

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

# def get_pool_details(pool_name):
#     """Get details for a specific pool"""
#     try:
#         # This would be replaced with an actual API call
#         # Mock data for demonstration
#         return {
#             "name": pool_name,
#             "liquidity": 1000000,
#             "current_price": 250.5,
#             "trade_volume_24h": 500000
#         }
#     except Exception as e:
#         logger.error(f"Error fetching pool details: {e}")
#         return None

# # --- Agent Management Functions ---
# def create_agent(username, pool_name, initial_investment, min_price, max_price):
#     """Create a new agent for a user"""
#     agent_id = str(uuid.uuid4())[:8]
    
#     # Get pool details
#     pool = get_pool_details(pool_name)
#     if not pool:
#         return False, "Failed to fetch pool details"
    
#     # Create agent object
#     agent = {
#         "id": agent_id,
#         "pool_name": pool_name,
#         "initial_investment": float(initial_investment),
#         "current_investment": float(initial_investment),
#         "min_price": float(min_price),
#         "max_price": float(max_price),
#         "created_at": datetime.now().isoformat(),
#         "last_rebalance": datetime.now().isoformat(),
#         "total_rebalances": 0,
#         "fees_earned": 0.0,
#         "current_price": pool["current_price"],
#         "status": "active"
#     }
    
#     # Add agent to database and user's agents list
#     agents_db[agent_id] = agent
#     users_db[username]["agents"].append(agent_id)
    
#     return True, agent

# def get_user_agents(username):
#     """Get all agents for a user"""
#     if username not in users_db:
#         return []
    
#     user_agent_ids = users_db[username]["agents"]
#     user_agents = []
    
#     for agent_id in user_agent_ids:
#         if agent_id in agents_db:
#             user_agents.append(agents_db[agent_id])
    
#     return user_agents

# def get_agent_details(agent_id):
#     """Get details for a specific agent"""
#     if agent_id not in agents_db:
#         return None
    
#     return agents_db[agent_id]

# def get_user_balance(username):
#     """Get total balance and stats for a user"""
#     if username not in users_db:
#         return None
    
#     user_agents = get_user_agents(username)
#     total_investment = sum(agent["initial_investment"] for agent in user_agents)
#     current_value = sum(agent["current_investment"] for agent in user_agents)
#     total_fees = sum(agent["fees_earned"] for agent in user_agents)
#     active_agents = sum(1 for agent in user_agents if agent["status"] == "active")
    
#     return {
#         "username": username,
#         "total_investment": total_investment,
#         "current_value": current_value,
#         "profit_loss": current_value - total_investment,
#         "total_fees_earned": total_fees,
#         "active_agents": active_agents,
#         "total_agents": len(user_agents)
#     }

# # --- Telegram Button Creation ---
# def create_auth_buttons():
#     """Create authentication buttons"""
#     keyboard = {
#         "inline_keyboard": [
#             [{"text": "🔐 Register", "callback_data": "register"}],
#             [{"text": "🔑 Login", "callback_data": "login"}]
#         ]
#     }
#     return keyboard

# def create_main_menu_buttons():
#     """Create main menu buttons"""
#     keyboard = {
#         "inline_keyboard": [
#             [{"text": "👥 Show Agents", "callback_data": "show_agents"}],
#             [{"text": "💰 Balance", "callback_data": "balance"}],
#             [{"text": "🔍 Search/Explore Pools", "callback_data": "explore_pools"}],
#             [{"text": "🔒 Logout", "callback_data": "logout"}]
#         ]
#     }
#     return keyboard

# def create_agent_menu_buttons():
#     """Create agent menu buttons"""
#     keyboard = {
#         "inline_keyboard": [
#             [{"text": "➕ Create Agent", "callback_data": "create_agent"}],
#             [{"text": "⬅️ Back to Main Menu", "callback_data": "main_menu"}]
#         ]
#     }
#     return keyboard

# def create_pools_menu_buttons():
#     """Create pools menu buttons"""
#     keyboard = {
#         "inline_keyboard": [
#             [{"text": "🔍 Search Pool", "callback_data": "search_pool"}],
#             [{"text": "📋 Show More Pools", "callback_data": "more_pools"}],
#             [{"text": "⬅️ Back to Main Menu", "callback_data": "main_menu"}]
#         ]
#     }
#     return keyboard

# def create_back_button():
#     """Create a simple back button"""
#     keyboard = {
#         "inline_keyboard": [
#             [{"text": "⬅️ Back", "callback_data": "back"}]
#         ]
#     }
#     return keyboard

# # --- Command Handlers ---
# def handle_start(chat_id):
#     # Clear user state if any
#     user_states.pop(str(chat_id), None)
    
#     # Check if user is already logged in
#     username = get_username_by_chat_id(chat_id)
#     if username:
#         send_message(
#             chat_id,
#             f"Welcome back, {username}! You are already logged in.",
#             create_main_menu_buttons()
#         )
#     else:
#         # Send welcome message with auth options
#         send_message(
#             chat_id,
#             "Welcome to the Meteora Trading Bot! Please register or login to continue.",
#             create_auth_buttons()
#         )

# def handle_message(chat_id, text):
#     username = get_username_by_chat_id(chat_id)
#     user_state = user_states.get(str(chat_id))
    
#     # Handle user states for registration, login and other flows
#     if user_state == "awaiting_register_username":
#         user_states[str(chat_id)] = {
#             "state": "awaiting_register_password",
#             "username": text
#         }
#         send_message(chat_id, "Please enter your password:")
    
#     elif user_state and user_state.get("state") == "awaiting_register_password":
#         username = user_state.get("username")
#         password = text
#         success, message = register_user(chat_id, username, password)
        
#         user_states.pop(str(chat_id), None)  # Clear state
        
#         if success:
#             send_message(chat_id, message, create_main_menu_buttons())
#         else:
#             send_message(chat_id, message, create_auth_buttons())
    
#     elif user_state == "awaiting_login_username":
#         user_states[str(chat_id)] = {
#             "state": "awaiting_login_password",
#             "username": text
#         }
#         send_message(chat_id, "Please enter your password:")
    
#     elif user_state and user_state.get("state") == "awaiting_login_password":
#         username = user_state.get("username")
#         password = text
#         success, message = login_user(chat_id, username, password)
        
#         user_states.pop(str(chat_id), None)  # Clear state
        
#         if success:
#             send_message(chat_id, message, create_main_menu_buttons())
#         else:
#             send_message(chat_id, message, create_auth_buttons())
    
#     elif user_state == "awaiting_search_pool":
#         search_term = text.strip()
#         user_states.pop(str(chat_id), None)  # Clear state
        
#         # Simple mock search response - implement actual search here
#         send_message(
#             chat_id,
#             f"🔍 Results for pool: {search_term}\n\n" +
#             "🔹 Pool: SOL-USDC\n💰 TVL: $2,500,000.00\n💱 Price: $125.75\n📈 Volume (24h): $750,000.00\n",
#             create_pools_menu_buttons()
#         )
    
#     elif user_state and user_state.get("state") == "create_agent_pool":
#         # Store pool name and ask for investment amount
#         user_states[str(chat_id)] = {
#             "state": "create_agent_investment",
#             "pool": text
#         }
#         send_message(chat_id, "Enter initial investment amount (in USD):")
    
#     elif user_state and user_state.get("state") == "create_agent_investment":
#         # Store investment and ask for min price
#         try:
#             investment = float(text)
#             user_states[str(chat_id)] = {
#                 "state": "create_agent_min_price",
#                 "pool": user_state.get("pool"),
#                 "investment": investment
#             }
#             send_message(chat_id, "Enter minimum price for rebalancing range:")
#         except ValueError:
#             send_message(chat_id, "Please enter a valid number for investment.")
    
#     elif user_state and user_state.get("state") == "create_agent_min_price":
#         # Store min price and ask for max price
#         try:
#             min_price = float(text)
#             user_states[str(chat_id)] = {
#                 "state": "create_agent_max_price",
#                 "pool": user_state.get("pool"),
#                 "investment": user_state.get("investment"),
#                 "min_price": min_price
#             }
#             send_message(chat_id, "Enter maximum price for rebalancing range:")
#         except ValueError:
#             send_message(chat_id, "Please enter a valid number for minimum price.")
    
#     elif user_state and user_state.get("state") == "create_agent_max_price":
#         # Create the agent
#         try:
#             max_price = float(text)
#             pool = user_state.get("pool")
#             investment = user_state.get("investment")
#             min_price = user_state.get("min_price")
            
#             username = get_username_by_chat_id(chat_id)
#             if not username:
#                 send_message(chat_id, "You need to be logged in to create an agent.", create_auth_buttons())
#                 user_states.pop(str(chat_id), None)
#                 return
            
#             success, agent = create_agent(username, pool, investment, min_price, max_price)
#             user_states.pop(str(chat_id), None)  # Clear state
            
#             if success:
#                 agent_details = (
#                     f"✅ Agent created successfully!\n\n"
#                     f"🤖 Agent ID: {agent['id']}\n"
#                     f"🔹 Pool: {agent['pool_name']}\n"
#                     f"💰 Investment: ${agent['initial_investment']:,.2f}\n"
#                     f"🔲 Price Range: ${agent['min_price']:,.2f} - ${agent['max_price']:,.2f}\n"
#                     f"📊 Current Price: ${agent['current_price']:,.2f}"
#                 )
#                 send_message(chat_id, agent_details, create_main_menu_buttons())
#             else:
#                 send_message(chat_id, f"❌ Failed to create agent: {agent}", create_main_menu_buttons())
#         except ValueError:
#             send_message(chat_id, "Please enter a valid number for maximum price.")
    
#     else:
#         # Default response for non-command messages
#         if username:
#             send_message(
#                 chat_id,
#                 "I don't understand that command. Use the menu buttons below.",
#                 create_main_menu_buttons()
#             )
#         else:
#             send_message(
#                 chat_id,
#                 "Please register or login first. Type /start to begin.",
#                 create_auth_buttons()
#             )

# def handle_callback(callback_query):
#     query_id = callback_query.get("id")
#     data = callback_query.get("data")
#     message = callback_query.get("message", {})
#     chat_id = message.get("chat", {}).get("id")
#     message_id = message.get("message_id")
    
#     # Answer callback query to stop loading indicator
#     answer_callback_query(query_id)
    
#     # Get username if logged in
#     username = get_username_by_chat_id(chat_id)
    
#     # Handle different callback actions
#     if data == "register":
#         user_states[str(chat_id)] = "awaiting_register_username"
#         edit_message_text(chat_id, message_id, "Please enter your desired username:")
    
#     elif data == "login":
#         user_states[str(chat_id)] = "awaiting_login_username"
#         edit_message_text(chat_id, message_id, "Please enter your username:")
    
#     elif data == "logout":
#         # Remove user's chat_id from database
#         if username:
#             users_db[username]["chat_id"] = None
        
#         user_states.pop(str(chat_id), None)  # Clear state
#         edit_message_text(
#             chat_id, 
#             message_id, 
#             "You have been logged out. Thank you for using Meteora Trading Bot!",
#             create_auth_buttons()
#         )
    
#     elif data == "main_menu":
#         user_states.pop(str(chat_id), None)  # Clear state
#         if username:
#             edit_message_text(
#                 chat_id, 
#                 message_id, 
#                 f"Main Menu - Welcome {username}!",
#                 create_main_menu_buttons()
#             )
#         else:
#             edit_message_text(
#                 chat_id, 
#                 message_id, 
#                 "Please register or login first.",
#                 create_auth_buttons()
#             )
    
#     elif data == "show_agents":
#         if not username:
#             edit_message_text(
#                 chat_id, 
#                 message_id, 
#                 "Please register or login first.",
#                 create_auth_buttons()
#             )
#             return
        
#         user_agents = get_user_agents(username)
        
#         if not user_agents:
#             edit_message_text(
#                 chat_id, 
#                 message_id, 
#                 "You don't have any agents yet. Create one to start trading!",
#                 create_agent_menu_buttons()
#             )
#         else:
#             agents_text = f"🤖 Your Trading Agents ({len(user_agents)}):\n\n"
#             for agent in user_agents:
#                 profit_loss = agent["current_investment"] - agent["initial_investment"]
#                 profit_percent = (profit_loss / agent["initial_investment"]) * 100
                
#                 agents_text += (
#                     f"ID: {agent['id']}\n"
#                     f"Pool: {agent['pool_name']}\n"
#                     f"Investment: ${agent['initial_investment']:,.2f}\n"
#                     f"Current Value: ${agent['current_investment']:,.2f}\n"
#                     f"P/L: ${profit_loss:,.2f} ({profit_percent:.2f}%)\n"
#                     f"Fees Earned: ${agent['fees_earned']:,.2f}\n"
#                     f"Status: {agent['status'].upper()}\n\n"
#                 )
            
#             edit_message_text(
#                 chat_id, 
#                 message_id, 
#                 agents_text,
#                 create_agent_menu_buttons()
#             )
    
#     elif data == "create_agent":
#         if not username:
#             edit_message_text(
#                 chat_id, 
#                 message_id, 
#                 "Please register or login first.",
#                 create_auth_buttons()
#             )
#             return
        
#         user_states[str(chat_id)] = {"state": "create_agent_pool"}
#         edit_message_text(
#             chat_id, 
#             message_id, 
#             "Enter the pool name for your new agent (e.g., SOL-USDC):"
#         )
    
#     elif data == "balance":
#         if not username:
#             edit_message_text(
#                 chat_id, 
#                 message_id, 
#                 "Please register or login first.",
#                 create_auth_buttons()
#             )
#             return
        
#         balance_info = get_user_balance(username)
        
#         if not balance_info:
#             edit_message_text(
#                 chat_id, 
#                 message_id, 
#                 "Failed to retrieve balance information.",
#                 create_main_menu_buttons()
#             )
#             return
        
#         profit_loss = balance_info["profit_loss"]
#         profit_percent = (profit_loss / balance_info["total_investment"]) * 100 if balance_info["total_investment"] > 0 else 0
        
#         balance_text = (
#             f"💰 Balance Summary for {username}\n\n"
#             f"Total Investment: ${balance_info['total_investment']:,.2f}\n"
#             f"Current Value: ${balance_info['current_value']:,.2f}\n"
#             f"Profit/Loss: ${profit_loss:,.2f} ({profit_percent:.2f}%)\n"
#             f"Total Fees Earned: ${balance_info['total_fees_earned']:,.2f}\n\n"
#             f"Active Agents: {balance_info['active_agents']}/{balance_info['total_agents']}"
#         )
        
#         edit_message_text(
#             chat_id, 
#             message_id, 
#             balance_text,
#             create_main_menu_buttons()
#         )
    
#     elif data == "explore_pools":
#         if not username:
#             edit_message_text(
#                 chat_id, 
#                 message_id, 
#                 "Please register or login first.",
#                 create_auth_buttons()
#             )
#             return
        
#         pools_data = fetch_pools(limit=5)
#         edit_message_text(
#             chat_id, 
#             message_id, 
#             pools_data,
#             create_pools_menu_buttons()
#         )
    
#     elif data == "search_pool":
#         if not username:
#             edit_message_text(
#                 chat_id, 
#                 message_id, 
#                 "Please register or login first.",
#                 create_auth_buttons()
#             )
#             return
        
#         user_states[str(chat_id)] = "awaiting_search_pool"
#         edit_message_text(
#             chat_id, 
#             message_id, 
#             "🔍 Please enter the pool name you want to search:"
#         )
    
#     elif data == "more_pools":
#         if not username:
#             edit_message_text(
#                 chat_id, 
#                 message_id, 
#                 "Please register or login first.",
#                 create_auth_buttons()
#             )
#             return
        
#         pools_data = fetch_pools(limit=10)
#         edit_message_text(
#             chat_id, 
#             message_id, 
#             pools_data,
#             create_pools_menu_buttons()
#         )
    
#     elif data == "back":
#         # Generic back button - determine where to go based on state
#         user_state = user_states.get(str(chat_id))
        
#         if user_state and user_state.get("state", "").startswith("create_agent"):
#             # Go back to agent menu
#             user_states.pop(str(chat_id), None)  # Clear state
#             edit_message_text(
#                 chat_id, 
#                 message_id, 
#                 "Agent creation cancelled.",
#                 create_agent_menu_buttons()
#             )
#         else:
#             # Default to main menu
#             user_states.pop(str(chat_id), None)  # Clear state
#             if username:
#                 edit_message_text(
#                     chat_id, 
#                     message_id, 
#                     f"Main Menu - Welcome {username}!",
#                     create_main_menu_buttons()
#                 )
#             else:
#                 edit_message_text(
#                     chat_id, 
#                     message_id, 
#                     "Please register or login first.",
#                     create_auth_buttons()
#                 )
    
#     else:
#         edit_message_text(
#             chat_id, 
#             message_id, 
#             "⚠️ Unknown option."
#         )

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
