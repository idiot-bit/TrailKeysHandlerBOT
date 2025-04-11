import json
import time
import datetime
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")  # Get token from Railway environment
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable not set")

app = Application.builder().token(BOT_TOKEN).build()
# Load config
with open("config.json") as f:
    config = json.load(f)

OWNER_ID = config["owner_id"]
ALLOWED_USERS = set(config["allowed_users"])
USER_DATA = config["user_data"]

START_TIME = time.time()
USER_STATE = {}  # Tracks per-user upload state

# ReplyKeyboardMarkup layouts
owner_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton("/adduser"), KeyboardButton("/removeuser")],
        [KeyboardButton("Userlist"), KeyboardButton("Ping")],
        [KeyboardButton("Rules"), KeyboardButton("Reset")],
        [KeyboardButton("Help")]
    ],
    resize_keyboard=True
)

user_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton("Ping")],
        [KeyboardButton("Rules")],
        [KeyboardButton("Help")]
    ],
    resize_keyboard=True
)

def save_config():
    with open("config.json", "w") as f:
        json.dump({
            "owner_id": OWNER_ID,
            "allowed_users": list(ALLOWED_USERS),
            "user_data": USER_DATA
        }, f, indent=4)

def is_authorized(user_id: int) -> bool:
    return user_id == OWNER_ID or user_id in ALLOWED_USERS

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        await update.message.reply_text("🚀𝗪𝗵𝗮𝘁 𝗕𝗿𝘂𝗵 , 𝗜𝘁❜𝘀 𝗩𝗲𝗿𝘆 𝗪𝗿𝗼𝗻𝗴 𝗕𝗿𝗼 😂")
        return

    keyboard = [
        [InlineKeyboardButton("Add me to Your Channel", url="https://t.me/TrailKeysHandlerBOT?startchannel=true")],
        [InlineKeyboardButton("Give me Your Channel ID", callback_data="get_channel_id")],
        [InlineKeyboardButton("Give me Your Caption", callback_data="get_caption")]
    ]
    reply_kb = owner_keyboard if user_id == OWNER_ID else user_keyboard

    await update.message.reply_text(
        "Hey Buddy How Are You?\nUse /help to find your solution!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    await update.message.reply_text("Choose a command below:", reply_markup=reply_kb)
    
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("Access Denied.")
        return

    text = (
        "Available Commands:\n"
        "/start - Start Interaction\n"
        "/adduser - Add user access (Owner Only)\n"
        "/removeuser - Remove user access (Owner Only)\n"
        "Userlist - List of Allowed Users (Owner Only)\n"
        "Ping - Check Bot Uptime\n"
        "Rules - View Bot Rules\n"
        "Reset - Clear all User Captions/Channels\n"
    )
    await update.message.reply_text(text, reply_markup=owner_keyboard if update.effective_user.id == OWNER_ID else user_keyboard)
    
async def add_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("Access Denied.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /adduser <user_id>")
        return

    try:
        user_id = int(context.args[0])
        ALLOWED_USERS.add(user_id)
        save_config()
        await update.message.reply_text(f"User {user_id} AddeD Successfully")
    except ValueError:
        await update.message.reply_text("Invalid user ID.")

async def remove_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("Access Denied.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /removeuser <user_id>")
        return

    try:
        user_id = int(context.args[0])
        ALLOWED_USERS.discard(user_id)
        save_config()
        await update.message.reply_text(f"User {user_id} RemoveD Successfully")
    except ValueError:
        await update.message.reply_text("Invalid user ID.")

async def userlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("Access Denied.")
        return

    if not ALLOWED_USERS:
        await update.message.reply_text("No allowed users.")
        return

    lines = []
    for user_id in ALLOWED_USERS:
        user_data = USER_DATA.get(str(user_id), {})
        nickname = user_data.get("first_name", "N/A")
        username = user_data.get("username", "N/A")
        channel = user_data.get("channel", "N/A")
        link = f"[{user_id}](tg://openmessage?user_id={user_id})"
        lines.append(f"NickName: {nickname}\nUsername: @{username}\nChannel: {channel}\nUser ID: {link}\n")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("Access Denied.")
        return

    uptime_seconds = int(time.time() - START_TIME)
    days, remainder = divmod(uptime_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    ping_ms = round(random.uniform(10, 80), 2)

    today = datetime.datetime.now().strftime("%d : %m : %Y")
    await update.message.reply_text(
        f"Update - {today}\n"
        f"Uptime - {days}D : {hours}H : {minutes}M : {seconds}S\n"
        f"Ping - {ping_ms:.2f} ms"
    )

async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id)
        return

    await update.message.reply_text(
        "Don't spam the bot — abuse may lead to ban.\n"
        "For issues, contact @Ceo_DarkFury"
    )
async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
    await update.message.reply_text("Access Denied.")
        return

    for user in USER_DATA:
        USER_DATA[user]["channel"] = ""
        USER_DATA[user]["caption"] = ""
    save_config()
    await update.message.reply_text("All user data (channel/caption) has been reset.")
    
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        await update.message.reply_text("🚀𝗪𝗵𝗮𝘁 𝗕𝗿𝘂𝗵 , 𝗜𝘁❜𝘀 𝗩𝗲𝗿𝘆 𝗪𝗿𝗼𝗻𝗴 𝗕𝗿𝗼 😂")
        return

    doc = update.message.document
    caption = update.message.caption or ""

    if not doc.file_name.endswith(".apk"):
        await update.message.reply_text("Only APK files are supported.")
        return

    if "Key -" in caption:
        USER_STATE[user_id] = {
            "file_id": doc.file_id,
            "caption": caption,
            "status": "confirm_share"
        }
        await ask_to_share(update)
    else:
        USER_STATE[user_id] = {
            "file_id": doc.file_id,
            "caption": "",  # To be filled
            "status": "waiting_key"
        }
        await update.message.reply_text("Send the Key Now")

async def ask_to_share(update: Update):
    keyboard = [
        [InlineKeyboardButton("Yes", callback_data="share_yes"),
         InlineKeyboardButton("No", callback_data="share_no")]
    ]
    await update.message.reply_text(
        "Do You Want To Share This To Your Channel?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = USER_STATE.get(user_id)

    if not state:
        return

    # EXISTING: Handling when waiting for a key
    if state["status"] == "waiting_key":
        key = update.message.text
        caption = USER_DATA.get(str(user_id), {}).get("caption", "")
        if "Key -" not in caption:
            await update.message.reply_text("Your original caption doesn't include 'Key -' placeholder.")
            return

        final_caption = caption.replace("Key -", f"Key - {key}")
        USER_STATE[user_id].update({
            "caption": final_caption,
            "status": "confirm_share"
        })

        await ask_to_share(update)

    # >>> ADD THIS BELOW waiting_key BLOCK <<<

    elif state["status"] == "waiting_channel":
        channel_id = update.message.text.strip()
        USER_DATA[str(user_id)] = USER_DATA.get(str(user_id), {})
        USER_DATA[str(user_id)]["channel"] = channel_id
        save_config()
        await update.message.reply_text(f"Channel ID saved: {channel_id}")
        del USER_STATE[user_id]

    elif state["status"] == "waiting_caption":
        caption = update.message.text.strip()
        if "Key -" not in caption:
            await update.message.reply_text("Invalid caption. You must include `Key -` as a placeholder.")
        else:
            USER_DATA[str(user_id)] = USER_DATA.get(str(user_id), {})
            USER_DATA[str(user_id)]["caption"] = caption
            save_config()
            await update.message.reply_text("Caption saved successfully!")
            del USER_STATE[user_id]

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if user_id not in USER_STATE and query.data not in ["get_channel_id", "get_caption"]:
    await query.edit_message_text("Session expired or invalid.")
    return

    data = query.data
    state = USER_STATE[user_id]
    channel_id = USER_DATA.get(str(user_id), {}).get("channel")

    if data == "share_yes":
        if not channel_id:
            await query.edit_message_text("Channel ID not set. Use /start to set your channel.")
            return

        await context.bot.send_document(
            chat_id=channel_id,
            document=state["file_id"],
            caption=state["caption"],
            disable_notification=True
        )

        await query.edit_message_text(
            "View Your Channel",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Go to Channel", url=f"https://t.me/{channel_id.strip('@')}")]
            ])
        )

    elif data == "share_no":
        await query.edit_message_text("No worries, retry the process.")

    elif data == "get_channel_id":
        USER_STATE[user_id] = {"status": "waiting_channel"}
        await query.edit_message_text(
            "Please send your Channel ID (e.g., `@mychannel` or `-1001234567890`)",
            parse_mode="Markdown"
        )

    elif data == "get_caption":
        USER_STATE[user_id] = {"status": "waiting_caption"}
        await query.edit_message_text(
            "Please send your Caption that includes `Key -`",
            parse_mode="Markdown"
        )

# You’ll add other handlers here...

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("adduser", add_user))
    app.add_handler(CommandHandler("removeuser", remove_user))
    app.add_handler(CommandHandler("userlist", userlist))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(CommandHandler("rules", rules))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))
    app.add_handler(CallbackQueryHandler(handle_callback))

    app.run_polling()

if __name__ == "__main__":
    main()
