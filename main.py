import logging
import json
import os
import asyncio
from threading import Thread
from flask import Flask
from telegram import Update, ChatMember
from telegram.ext import (
    Application, 
    MessageHandler, 
    ContextTypes, 
    filters, 
    ChatMemberHandler,
    CommandHandler
)

# ======================================================
# 👇 YOUR SETTINGS 
# ======================================================

BOT_TOKEN = "8467195773:AAG9F7ckbEf_nFQUWgHqTsAuVKUfHciEjzQ"
SOURCE_CHANNEL_ID = -1003058384907
DB_FILE = "connected_chats.json"

# ======================================================

# Logging Setup
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- 0. KEEP ALIVE SERVER (Render Fix) ---
app_web = Flask('')

@app_web.route('/')
def home():
    return "BW Auto-Forwarder & Pinner is Running! 🚀"

def run_http():
    app_web.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_http)
    t.start()

# --- DATABASE SYSTEM ---
def load_chats():
    if not os.path.exists(DB_FILE):
        return []
    try:
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Database Error: {e}")
        return []

def save_chat(chat_id):
    chats = load_chats()
    if chat_id not in chats:
        chats.append(chat_id)
        with open(DB_FILE, 'w') as f:
            json.dump(chats, f)
        print(f"✅ LINKED: New Chat Connected ({chat_id})")

def remove_chat(chat_id):
    chats = load_chats()
    if chat_id in chats:
        chats.remove(chat_id)
        with open(DB_FILE, 'w') as f:
            json.dump(chats, f)
        print(f"❌ REMOVED: Chat Disconnected ({chat_id})")

# --- 1. START COMMAND ---
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 **Hello BW Army!**\n\n"
        "Main **BW Auto-Forwarder Bot** hu.\n"
        "Mera kaam hai messages ko **Forward** karna aur **PIN** karna.\n\n"
        "✅ **System Status:** Online 🟢"
    )

# --- 2. AUTO-DETECT ---
async def track_chats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = update.my_chat_member
    if not result: return

    new_status = result.new_chat_member.status
    chat_id = result.chat.id
    chat_title = result.chat.title or "Unknown Chat"

    if new_status in [ChatMember.MEMBER, ChatMember.ADMINISTRATOR]:
        save_chat(chat_id)
        logger.info(f"🔗 Connected to: {chat_title}")
    
    elif new_status in [ChatMember.LEFT, ChatMember.BANNED]:
        remove_chat(chat_id)
        logger.info(f"💔 Disconnected from: {chat_title}")

# --- 3. FORWARD & PIN LOGIC (Updated) ---
async def forward_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id == SOURCE_CHANNEL_ID:
        msg_id = update.effective_message.id
        target_chats = load_chats()
        
        if not target_chats:
            print("⚠️ Warning: Bot kisi bhi group me nahi hai!")
            return

        print(f"📩 Post Detected! Forwarding & Pinning in {len(target_chats)} chats...")
        
        success = 0
        failed = 0
        
        for chat_id in target_chats:
            if chat_id == SOURCE_CHANNEL_ID: 
                continue
                
            try:
                # Step 1: Forward Message
                sent_msg = await context.bot.forward_message(
                    chat_id=chat_id,
                    from_chat_id=SOURCE_CHANNEL_ID,
                    message_id=msg_id
                )
                
                # Step 2: PIN Message (Ye nayi line hai)
                try:
                    await context.bot.pin_chat_message(
                        chat_id=chat_id,
                        message_id=sent_msg.message_id
                    )
                except Exception as e:
                    print(f"⚠️ Pin Failed in {chat_id}: {e}")

                success += 1
            except Exception as e:
                failed += 1
                logger.warning(f"⚠️ Forward Failed to {chat_id}: {e}")

        print(f"🚀 REPORT: Sent: {success} | Failed: {failed}")

# --- 4. STATUS CHECK ---
async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chats = load_chats()
    await update.message.reply_text(f"📊 **Bot Status:**\n✅ Connected: {len(chats)}\n📌 Auto-Pin: Active")

# --- MAIN EXECUTION ---
def main():
    keep_alive()
    
    print("🤖 ULTRA PRO FORWARDER + PINNER BOT STARTED...")
    print(f"📡 Monitoring Channel: {SOURCE_CHANNEL_ID}")
    
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("stats", stats_cmd))
    app.add_handler(ChatMemberHandler(track_chats, ChatMemberHandler.MY_CHAT_MEMBER))
    app.add_handler(MessageHandler(filters.Chat(chat_id=SOURCE_CHANNEL_ID), forward_post))

    app.run_polling()

if __name__ == '__main__':
    main()
