import telebot
from telebot import types
import sqlite3
import random
import string
import datetime

# Provided Details
BOT_TOKEN = "8741178343:AAGgvHrVqL0dW9lpN5ao5k3okjEjCX6xV1M"
ADMIN_ID = 5883589730

bot = telebot.TeleBot(BOT_TOKEN)

# State management for admin multi-step processing
user_states = {}

# ----------------- DATABASE MANAGEMENT SYSTEM -----------------
def init_db():
    conn = sqlite3.connect("store.db")
    cursor = conn.cursor()
    
    # 1. Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            name TEXT,
            username TEXT,
            join_date TEXT,
            status TEXT DEFAULT 'Active'
        )
    ''')
    
    # 2. Products Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            name TEXT UNIQUE
        )
    ''')
    
    # 3. Plans Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            duration TEXT,
            price INTEGER,
            FOREIGN KEY(product_id) REFERENCES products(id)
        )
    ''')
    
    # 4. Keys Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_id INTEGER,
            license_key TEXT UNIQUE,
            file_link TEXT,
            tutorial_link TEXT,
            status TEXT DEFAULT 'UNUSED',
            used_by INTEGER DEFAULT NULL,
            FOREIGN KEY(plan_id) REFERENCES plans(id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ----------------- MAIN REPLY MARKUP KEYBOARDS -----------------
def get_main_keyboard(user_id):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(types.KeyboardButton("ESP AIMBOT"), types.KeyboardButton("PBC WALLHACK"))
    markup.add(types.KeyboardButton("Send Feedback"), types.KeyboardButton("Help & Support"))
    markup.add(types.KeyboardButton("My ID"), types.KeyboardButton("My Keys"))
    markup.add(types.KeyboardButton("How To Use Bot"))
    if user_id == ADMIN_ID:
        markup.add(types.KeyboardButton("Admin Panel"))
    return markup

# ----------------- INLINE KEYBOARDS FOR ADMIN PANEL -----------------
def get_admin_inline():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("➕ Add Product", callback_data="admin_add_product"),
        types.InlineKeyboardButton("📝 Edit Product", callback_data="admin_edit_product"),
        types.InlineKeyboardButton("❌ Delete Product", callback_data="admin_delete_product"),
        types.InlineKeyboardButton("📅 Add Plan", callback_data="admin_add_plan"),
        types.InlineKeyboardButton("🗑️ Delete Plan", callback_data="admin_delete_plan"),
        types.InlineKeyboardButton("🔑 Add Keys", callback_data="admin_add_keys"),
        types.InlineKeyboardButton("📋 List Keys", callback_data="admin_list_keys"),
        types.InlineKeyboardButton("🗑️ Delete Key", callback_data="admin_delete_key"),
        types.InlineKeyboardButton("💰 Add Balance", callback_data="admin_add_bal"),
        types.InlineKeyboardButton("➖ Remove Balance", callback_data="admin_rem_bal"),
        types.InlineKeyboardButton("🚫 Ban User", callback_data="admin_ban"),
        types.InlineKeyboardButton("🟢 Unban User", callback_data="admin_unban"),
        types.InlineKeyboardButton("📊 Stats", callback_data="admin_stats"),
        types.InlineKeyboardButton("🔙 Back to Main", callback_data="admin_back_main")
    )
    return markup

# ----------------- SYSTEM COMMAND HANDLERS -----------------
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name or "‎ㅤ"
    username = f"@{message.from_user.username}" if message.from_user.username else "@None"
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")

    conn = sqlite3.connect("store.db")
    cursor = conn.cursor()
    cursor.execute("SELECT join_date FROM users WHERE user_id = ?", (user_id,))
    user_exists = cursor.fetchone()
    
    if not user_exists:
        cursor.execute("INSERT INTO users (user_id, name, username, join_date) VALUES (?, ?, ?, ?)", 
                       (user_id, user_name, username, current_date))
        conn.commit()
    conn.close()

    user_states.pop(user_id, None)
    bot.send_message(
        message.chat.id, 
        f"🌟 Hello *{user_name}*! Welcome to KityShopBot. Choose an option from the menu below:", 
        reply_markup=get_main_keyboard(user_id),
        parse_mode="Markdown"
    )

# ----------------- CRITICAL FIX: ADMIN TEXT INPUT HANDLER FIRST -----------------
@bot.message_handler(func=lambda message: message.from_user.id == ADMIN_ID and message.from_user.id in user_states)
def process_admin_inputs(message):
    user_id = message.from_user.id
    state = user_states[user_id]
    
    if state["action"] == "adding_product_name":
        category = state["category"]
        brand_name = message.text.strip()
        
        conn = sqlite3.connect("store.db")
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO products (category, name) VALUES (?, ?)", (category, brand_name))
            conn.commit()
            bot.send_message(
                message.chat.id, 
                f"✅ *Product Added Successfully!*\n\n"
                f"📁 Server: `{category}`\n"
                f"📦 Product Name: *{brand_name}*\n\n"
                f"👉 Now open Admin Panel and click *Add Plan* to set its pricing structure.", 
                parse_mode="Markdown"
            )
        except sqlite3.IntegrityError:
            bot.send_message(message.chat.id, "❌ Error: This product name already exists in database.")
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Database Error: {e}")
        finally:
            conn.close()
        user_states.pop(user_id, None)

    elif state["action"] == "adding_plan_details":
        prod_id = state["product_id"]
        try:
            duration, price = message.text.split(",")
            duration = duration.strip()
            price = int(price.strip())
            
            conn = sqlite3.connect("store.db")
            cursor = conn.cursor()
            cursor.execute("INSERT INTO plans (product_id, duration, price) VALUES (?, ?, ?)", (prod_id, duration, price))
            conn.commit()
            conn.close()
            
            bot.send_message(message.chat.id, f"✅ *Plan Created Successfully!*\n\nDuration: `{duration}`\nPrice: `₹{price}`")
        except Exception:
            bot.send_message(message.chat.id, "❌ Invalid Format! Please enter precisely in `Duration,Price` format.")
        user_states.pop(user_id, None)

    elif state["action"] == "adding_key_data":
        plan_id = state["plan_id"]
        try:
            parts = message.text.split(",")
            lic_key = parts[0].strip()
            file_l = parts[1].strip()
            tuto_l = parts[2].strip()
            
            conn = sqlite3.connect("store.db")
            cursor = conn.cursor()
            cursor.execute("INSERT INTO keys (plan_id, license_key, file_link, tutorial_link) VALUES (?, ?, ?, ?)", (plan_id, lic_key, file_l, tuto_l))
            conn.commit()
            conn.close()
            
            bot.send_message(message.chat.id, "✅ Stock License Key inserted safely into database structure!")
        except Exception:
            bot.send_message(message.chat.id, "❌ Format error! Send details as: `LicenseKey,FileLink,VideoTutorialLink`")
        user_states.pop(user_id, None)

# ----------------- GENERAL BUTTON TEXT HANDLERS SECOND -----------------
@bot.message_handler(func=lambda message: True)
def handle_text_buttons(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    text = message.text

    if text == "Admin Panel":
        if user_id != ADMIN_ID:
            bot.send_message(chat_id, "❌ Unauthorized Access!")
            return
        bot.send_message(chat_id, "🔧 *Admin Panel*", reply_markup=get_admin_inline(), parse_mode="Markdown")

    elif text in ["ESP AIMBOT", "PBC WALLHACK"]:
        category = "Esp Aimbot Server" if text == "ESP AIMBOT" else "Wallhack Server"
        
        conn = sqlite3.connect("store.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM products WHERE category = ?", (category,))
        products = cursor.fetchall()
        conn.close()
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        if products:
            for p in products:
                markup.add(types.InlineKeyboardButton(p[1], callback_data=f"view_product_{p[0]}"))
        markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="user_back_category"))
        
        bot.send_message(chat_id, f"🛒 *Select Product under {text}:*", reply_markup=markup, parse_mode="Markdown")

    elif text == "My ID":
        conn = sqlite3.connect("store.db")
        cursor = conn.cursor()
        cursor.execute("SELECT join_date, status, name, username FROM users WHERE user_id = ?", (user_id,))
        user_data = cursor.fetchone()
        conn.close()
        
        if user_data:
            join_date, status, db_name, db_username = user_data
        else:
            join_date = datetime.datetime.now().strftime("%Y-%m-%d")
            status = "Active"
            db_name = message.from_user.first_name or "‎ㅤ"
            db_username = f"@{message.from_user.username}" if message.from_user.username else "@None"

        profile_text = (
            "🆔 *Your Telegram Details:*\n\n"
            f"👤 Name: {db_name}\n"
            f"🔢 ID: `{user_id}`\n"
            f"☎️ Username: {db_username}\n"
            f"🔥 Joined: {join_date}\n"
            f"🟢 Status: {status}"
        )
        bot.send_message(chat_id, profile_text, parse_mode="Markdown")

    elif text == "My Keys":
        conn = sqlite3.connect("store.db")
        cursor = conn.cursor()
        cursor.execute("SELECT license_key FROM keys WHERE used_by = ?", (user_id,))
        rows = cursor.fetchall()
        conn.close()
        
        if rows:
            keys_list = "\n".join([f"• `{r[0]}`" for r in rows])
            bot.send_message(chat_id, f"🔑 *Your Active Keys:*\n\n{keys_list}", parse_mode="Markdown")
        else:
            bot.send_message(chat_id, "🔑 *Your Active Keys:*\n\nNo active keys found assigned to your ID.", parse_mode="Markdown")

    elif text == "Send Feedback":
        bot.send_message(chat_id, "📝 Please send your suggestions or feedback directly to the owner.")

    elif text == "Help & Support":
        bot.send_message(chat_id, "ℹ️ *Support Panel:*\n\nIf you face any issues, contact support handler or join updates channel.", parse_mode="Markdown")

    elif text == "How To Use Bot":
        instructions = (
            "📖 *How to use this bot:*\n\n"
            "1. Select your preferred game setup.\n"
            "2. Complete payment via the payment template.\n"
            "3. Your keys and setup guides will instantly auto-deliver."
        )
        bot.send_message(chat_id, instructions, parse_mode="Markdown")

# ----------------- SYSTEM INLINE CALLBACK PROCESSOR -----------------
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    
    if call.data.startswith("view_product_"):
        prod_id = call.data.split("_")[2]
        
        conn = sqlite3.connect("store.db")
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM products WHERE id = ?", (prod_id,))
        prod_name = cursor.fetchone()[0]
        
        cursor.execute("SELECT id, duration, price FROM plans WHERE product_id = ?", (prod_id,))
        plans = cursor.fetchall()
        conn.close()
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        for p in plans:
            markup.add(types.InlineKeyboardButton(f"{p[1]} • ₹{p[2]}", callback_data=f"buy_plan_{p[0]}"))
        markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="user_back_category"))
        
        bot.edit_message_text(f"📦 *{prod_name}*\n\nSelect duration:", chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    elif call.data.startswith("buy_plan_"):
        plan_id = call.data.split("_")[2]
        
        conn = sqlite3.connect("store.db")
        cursor = conn.cursor()
        cursor.execute('''
            SELECT products.name, plans.duration, plans.price FROM plans 
            JOIN products ON plans.product_id = products.id WHERE plans.id = ?
        ''', (plan_id,))
        plan_info = cursor.fetchone()
        conn.close()
        
        if plan_info:
            prod_name, duration, price = plan_info
            order_id = f"FAMPAY{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(1000,9999)}"
            
            invoice_text = (
                f"💳 Pay *₹{price}* to get {prod_name} {duration} License\n\n"
                f"Order ID: `{order_id}`\n"
                f"⏳ *Waiting for payment...*\n\n"
                f"_After successful payment, your License Key, Files, and Setup Guide will be delivered automatically._"
            )
            
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("✅ Simulate Payment (Demo)", callback_data=f"pay_success_{plan_id}"))
            
            bot.send_message(chat_id, invoice_text, reply_markup=markup, parse_mode="Markdown")

    elif call.data.startswith("pay_success_"):
        plan_id = call.data.split("_")[2]
        
        conn = sqlite3.connect("store.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, license_key, file_link, tutorial_link FROM keys WHERE plan_id = ? AND status = 'UNUSED' LIMIT 1", (plan_id,))
        key_data = cursor.fetchone()
        
        if key_data:
            key_db_id, license_key, file_link, tutorial_link = key_data
            cursor.execute("UPDATE keys SET status = 'USED', used_by = ? WHERE id = ?", (user_id, key_db_id))
            conn.commit()
            conn.close()
            
            delivery_text = (
                "✅ *Payment Successfully Received!*\n\n"
                f"🔑 *License Key:* `{license_key}`\n\n"
                "⚠️ *Note:* Please copy your license key first, then open the game.\n\n"
                f"📁 *File Link:* {file_link}\n"
                f"🎥 *Setup Tutorial Video:* {tutorial_link}"
            )
            bot.send_message(chat_id, delivery_text, parse_mode="Markdown")
        else:
            conn.close()
            bot.send_message(chat_id, "❌ *Stock Out!* No unused keys left inside this configuration. Contact Admin.")

    elif call.data == "admin_add_product":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("🤖 Esp Aimbot Server", callback_data="set_cat_esp"),
            types.InlineKeyboardButton("🧱 Wallhack Server", callback_data="set_cat_wall")
        )
        bot.edit_message_text("Select the Server/Category where you want to add the product:", chat_id, call.message.message_id, reply_markup=markup)

    elif call.data in ["set_cat_esp", "set_cat_wall"]:
        category = "Esp Aimbot Server" if call.data == "set_cat_esp" else "Wallhack Server"
        user_states[user_id] = {"action": "adding_product_name", "category": category}
        bot.send_message(chat_id, f"📝 Selected Server: *{category}*\n\nNow, type the **Product/Cheat Name** and send it:", parse_mode="Markdown")

    elif call.data == "admin_add_plan":
        conn = sqlite3.connect("store.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, category FROM products")
        prods = cursor.fetchall()
        conn.close()
        
        if not prods:
            bot.send_message(chat_id, "❌ No products available in database. Please add a product first.")
            return
            
        markup = types.InlineKeyboardMarkup(row_width=1)
        for p in prods:
            markup.add(types.InlineKeyboardButton(f"{p[1]} ({p[2]})", callback_data=f"addplan_to_{p[0]}"))
        bot.edit_message_text("Select Product to set or add plans:", chat_id, call.message.message_id, reply_markup=markup)

    elif call.data.startswith("addplan_to_"):
        prod_id = call.data.split("_")[2]
        user_states[user_id] = {"action": "adding_plan_details", "product_id": prod_id}
        bot.send_message(chat_id, "Enter plan details in this format:\n`Duration,Price`\n\nExample: `1 Days,150` or `7 Days,600`")

    elif call.data == "admin_add_keys":
        conn = sqlite3.connect("store.db")
        cursor = conn.cursor()
        cursor.execute('''
            SELECT plans.id, products.name, plans.duration FROM plans 
            JOIN products ON plans.product_id = products.id
        ''')
        plans_list = cursor.fetchall()
        conn.close()
        
        if not plans_list:
            bot.send_message(chat_id, "❌ No plans available. Please create a plan first.")
            return
            
        markup = types.InlineKeyboardMarkup(row_width=1)
        for p in plans_list:
            markup.add(types.InlineKeyboardButton(f"{p[1]} ({p[2]})", callback_data=f"addkey_to_{p[0]}"))
        bot.edit_message_text("Select Plan to insert license stock keys:", chat_id, call.message.message_id, reply_markup=markup)

    elif call.data.startswith("addkey_to_"):
        plan_id = call.data.split("_")[2]
        user_states[user_id] = {"action": "adding_key_data", "plan_id": plan_id}
        bot.send_message(chat_id, "Send key details exactly in this format (comma separated):\n`LicenseKey,FileLink,VideoTutorialLink` \n\nExample:\n`cjknbd37gjv56fhj,https://file.com/setup.zip,https://youtube.com/tutorial`")

    elif call.data in ["admin_back_main", "user_back_category"]:
        user_states.pop(user_id, None)
        try:
            bot.delete_message(chat_id, call.message.message_id)
        except Exception:
            pass

print("KityShopBot fully functional code sequence is live...")
bot.infinity_polling()
