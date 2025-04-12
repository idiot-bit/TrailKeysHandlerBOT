import json
import time
import datetime
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
import os
import re

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

owner_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton("Userlist"), KeyboardButton("Help")],
        [KeyboardButton("Ping"), KeyboardButton("Rules")],
        [KeyboardButton("Reset")]
    ],
    resize_keyboard=True
)

allowed_user_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton("Help")],
        [KeyboardButton("Ping"), KeyboardButton("Rules")],
        [KeyboardButton("Reset")]
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

# Save basic user data (first name, username)
USER_DATA[str(user_id)] = {
    "first_name": update.effective_user.first_name,
    "username": update.effective_user.username,
    "channel": USER_DATA.get(str(user_id), {}).get("channel", ""),
    "caption": USER_DATA.get(str(user_id), {}).get("caption", "")}
     save_config()

    inline_keyboard = [
        [InlineKeyboardButton("Add me to Your Channel", url="https://t.me/TrailKeysHandlerBOT?startchannel=true")],
        [InlineKeyboardButton("Give me Your Channel ID", callback_data="get_channel_id")],
        [InlineKeyboardButton("Give me Your Caption", callback_data="get_caption")]
    ]

    reply_kb = owner_keyboard if user_id == OWNER_ID else allowed_user_keyboard

    await update.message.reply_text(
        "Hey there, Rockstar!\nWelcome to your APK Sharing Assistant.\nUse /help to explore powerful features designed just for you!",
        USER_STATE[user_id] = {"status": "idle"}
        reply_markup=InlineKeyboardMarkup(inline_keyboard)
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == OWNER_ID:
        await update.message.reply_text(
            "Available Commands:\n"
            "/start - Restart bot interaction\n"
            "/adduser - Add allowed user\n"
            "/removeuser - Remove allowed user\n"
            "/userlist - Show all allowed users\n"
            "/ping - Bot status\n"
            "/rules - Bot usage rules\n"
            "/reset - Reset user data"
            "Available Commands:\n"
        )
    elif user_id in ALLOWED_USERS:
        await update.message.reply_text(
            "Available Commands:\n"
            "/start - Restart bot interaction\n"
            "/ping - Bot status\n"
            "/rules - Bot usage rules\n"
            "/reset - Reset your data"
        )
        
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

    lines = ["**👥 Allowed Users List:**"]
    for user_id in ALLOWED_USERS:
        user_data = USER_DATA.get(str(user_id), {})

        nickname = user_data.get("first_name")
        username = user_data.get("username")
        channel = user_data.get("channel")

        user_line = (
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"**👤NickName** : {nickname if nickname else '—'}\n"
            f"**👽Username** : {'@' + username if username else '—'}\n"
            f"**🌝UserChannel** : {channel if channel else '—'}\n"
            f"**🗣️UserID** : [Click Here](tg://openmessage?user_id={user_id})\n"
            "━━━━━━━━━━━━━━━━━━━━"
        )
        lines.append(user_line)

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
    today = datetime.datetime.now().strftime("%d/%m/%Y")

    msg = (
        "╭━━⪩ Server Status ⪨━━╮\n"
        f"┣⪧ Date : {today}\n"
        f"┣⪧ Uptime : {days}D {hours}H {minutes}M {seconds}S\n"
        f"┣⪧ Ping : {ping_ms} ms\n"
        "╰━━━━━━━━━━━━━━━╯"
    )
    await update.message.reply_text(msg)

async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("Access Denied.")
        return

    await update.message.reply_text(
        "🚫 Please avoid spamming the bot.\nViolations can lead to a ban without notice.\n\nFor support or feedback, contact: @Ceo_DarkFury"
    )

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("Access Denied.")
        return

    for user_id in USER_DATA:
        USER_DATA[user_id]["channel"] = ""
        USER_DATA[user_id]["caption"] = ""
    save_config()
    await update.message.reply_text("Reseted all Caption and Channel ID")

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

    if re.search(r'Key\s*-\s*(\S+)', caption):
    match = re.search(r'Key\s*-\s*(\S+)', caption)
    key = match.group(1)

    saved_caption = USER_DATA.get(str(user_id), {}).get("caption", "")
    if "Key -" in saved_caption:
        final_caption = saved_caption.replace("Key -", f"`Key - {key}`")
    else:
        final_caption = caption

    USER_STATE[user_id] = {
        "file_id": doc.file_id,
        "caption": final_caption,
        "status": "confirm_share"
    }
    await ask_to_share(update)
    else:
        USER_STATE[user_id] = {
            "file_id": doc.file_id,
            "caption": "",  # To be filled
            "status": "waiting_key"
        }
        await update.message.reply_text("Awesome! Now, please send the *Key* you want to attach.", parse_mode="Markdown")

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
    message_text = update.message.text.strip().lower()

    # BUTTON TEXT HANDLING
    if message_text == "ping":
        await ping(update, context)
        return
    elif message_text == "help":
        await help_command(update, context)
        return
    elif message_text == "rules":
        await rules(update, context)
        return
    elif message_text == "reset":
        await reset(update, context)
        return
    elif message_text == "userlist" and user_id == OWNER_ID:
        await userlist(update, context)
        return

    # EXISTING: Continue handling custom states
    state = USER_STATE.get(user_id)

    if not state:
        return

    if state["status"] == "waiting_key":
        key = update.message.text
        caption = USER_DATA.get(str(user_id), {}).get("caption", "")
        if "Key -" not in caption:
            await update.message.reply_text(
    "Oops! Your saved caption doesn't contain the `Key -` placeholder.\n"
    "Please update your caption using /start → 'Give me Your Caption'.",
    parse_mode="Markdown"
       )
            return

        final_caption = caption.replace("Key -", f"`Key - {key}`")
        USER_STATE[user_id].update({
            "caption": final_caption,
            "status": "confirm_share"
        })
        await ask_to_share(update)

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

    if user_id not in USER_STATE:
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
            parse_mode="Markdown",  # <-- ADD THIS
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
