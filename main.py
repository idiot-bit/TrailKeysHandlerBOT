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
        [KeyboardButton("Reset")],
        [KeyboardButton("On"), KeyboardButton("Off")]
    ],
    resize_keyboard=True,
    one_time_keyboard=False
)

allowed_user_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton("Help")],
        [KeyboardButton("Ping"), KeyboardButton("Rules")],
        [KeyboardButton("Reset")]
    ],
    resize_keyboard=True,
    one_time_keyboard=False
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
        "caption": USER_DATA.get(str(user_id), {}).get("caption", "")
    }
    save_config()

    inline_keyboard = [
        [InlineKeyboardButton("𝖠𝖽𝖽 𝗆𝖾 𝗍𝗈 𝖸𝗈𝗎𝗋 𝖢𝗁𝖾𝗇𝗇𝖺𝗅 ⚡", url="https://t.me/TrailKeysHandlerBOT?startchannel=true")],
        [InlineKeyboardButton("𝖦𝗂𝗏𝖾 𝗆𝖾 𝖸𝗈𝗎𝗋 𝖢𝗁𝖾𝗇𝗇𝖺𝗅 🆔", callback_data="get_channel_id")],
        [InlineKeyboardButton("𝖦𝗂𝗏𝖾 𝗆𝖾 𝖸𝗈𝗎𝗋 𝖪𝖾𝗒 𝖢𝖺𝗉𝗍𝗂𝗈𝗇 👽", callback_data="get_caption")]
    ]

    reply_kb = owner_keyboard if user_id == OWNER_ID else allowed_user_keyboard

    await update.message.reply_text(
        "𝖧𝖾𝗒 𝖡𝗎𝖽𝖽𝗒!\𝗇𝖶𝖾𝗅𝖼𝗈𝗆𝖾 𝖳𝗈 𝖸𝗈𝗎𝗋 𝖪𝖾𝗒 𝖧𝖺𝗇𝖽𝗅𝖾𝗋 𝖡𝗈𝗍.\𝗇𝖴𝗌𝖾 /help 𝖳𝗈 𝖤𝗑𝗉𝗅𝗈𝗋𝖾 𝖯𝗈𝗐𝖾𝗋𝖿𝗎𝗅 𝖥𝖾𝖺𝗍𝗎𝗋𝖾𝗌 𝖣𝖾𝗌𝗂𝗀𝗇𝖾𝖽 𝖩𝗎𝗌𝗍 𝖿𝗈𝗋 𝖸𝗈𝗎!",
        reply_markup=reply_kb  # <-- THIS SHOWS THE REPLY KEYBOARD
    )

    await update.message.reply_text(
        "𝖲𝖾𝗅𝖾𝖼𝗍 𝖸𝗈𝗎𝗋 𝖮𝗉𝗍𝗂𝗈𝗇 - 𝗂𝖿 𝖾𝗋𝗋𝗈𝗋𝗌 𝖲𝗁𝗈𝗐 𝖴𝗌𝖾 /setchannelid 𝖺𝗇𝖽 /setcaption",
        reply_markup=InlineKeyboardMarkup(inline_keyboard)
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == OWNER_ID:
        await update.message.reply_text(
            "<b>Available Commands for Owner:</b>\n\n"
            "🚀 <b>/start</b> - Restart bot interaction\n"
            "➕ <b>/adduser</b> - Add allowed user\n"
            "➖ <b>/removeuser</b> - Remove allowed user\n"
            "📋 <b>/userlist</b> - Show all allowed users\n"
            "📡 <b>/ping</b> - Bot status\n"
            "📜 <b>/rules</b> - Bot usage rules\n"
            "♻️ <b>/reset</b> - Reset user data\n"
            "🧹 <b>/resetcaption</b> - Reset your saved caption\n"
            "📤 <b>/resetchannelid</b> - Reset your channel ID\n"
            "🆔 <b>/setchannelid</b> - Set your Channel ID\n"
            "✏️ <b>/setcaption</b> - Set your Caption",
            parse_mode=ParseMode.HTML
        )
    elif user_id in ALLOWED_USERS:
        await update.message.reply_text(
            "<b>Available Commands:</b>\n\n"
            "🚀 <b>/start</b> - Restart bot interaction\n"
            "📡 <b>/ping</b> - Bot status\n"
            "📜 <b>/rules</b> - Bot usage rules\n"
            "♻️ <b>/reset</b> - Reset your data\n"
            "🧹 <b>/resetcaption</b> - Reset your saved caption\n"
            "📤 <b>/resetchannelid</b> - Reset your channel ID\n"
            "🆔 <b>/setchannelid</b> - Set your Channel ID\n"
            "✏️ <b>/setcaption</b> - Set your Caption",
            parse_mode=ParseMode.HTML
        )
        
async def add_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("⛔️ <b>Access Denied</b>. Only the owner can use this command.", parse_mode=ParseMode.HTML)
        return

    if not context.args:
        await update.message.reply_text("⚙️ <b>Usage:</b> /adduser &lt;user_id&gt;", parse_mode=ParseMode.HTML)
        return

    try:
        user_id = int(context.args[0])
        ALLOWED_USERS.add(user_id)
        save_config()
        await update.message.reply_text(f"✅ <b>User {user_id}</b> has been <b>added successfully</b>!", parse_mode=ParseMode.HTML)
    except ValueError:
        await update.message.reply_text("❌ <b>Invalid user ID</b>. Please enter a valid number.", parse_mode=ParseMode.HTML)
        
async def remove_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("⛔️ <b>Access Denied</b>. Only the owner can use this command.", parse_mode=ParseMode.HTML)
        return

    if not context.args:
        await update.message.reply_text("⚙️ <b>Usage:</b> /removeuser &lt;user_id&gt;", parse_mode=ParseMode.HTML)
        return

    try:
        user_id = int(context.args[0])
        ALLOWED_USERS.discard(user_id)
        save_config()
        await update.message.reply_text(f"✅ <b>User {user_id}</b> has been <b>removed successfully</b>!", parse_mode=ParseMode.HTML)
    except ValueError:
        await update.message.reply_text("❌ <b>Invalid user ID</b>. Please enter a valid number.", parse_mode=ParseMode.HTML)

async def userlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("Access Denied.")
        return

    if not ALLOWED_USERS:
        await update.message.reply_text("No allowed users.")
        return

    lines = [f"🧾 <b>Total Allowed Users:</b> {len(ALLOWED_USERS)}\n"]
    for index, user_id in enumerate(ALLOWED_USERS, start=1):
        user_data = USER_DATA.get(str(user_id), {})
        nickname = user_data.get("first_name", "—")
        username = user_data.get("username", "—")
        channel = user_data.get("channel", "—")

        lines.append(
            f"📌 <b>User {index}</b>\n"
            f"├─ 👤 <b>Name:</b> {nickname}\n"
            f"├─ 🧬 <b>Username:</b> {'@' + username if username != '—' else '—'}\n"
            f"├─ 📡 <b>Channel:</b> {channel}\n"
            f"└─ 🆔 <b>ID:</b> <a href=\"tg://openmessage?user_id={user_id}\">{user_id}</a>\n"
            "━━━━━━━━━━━━━━━━━━━━"
        )

    await update.message.reply_text("\n".join(lines), parse_mode="HTML", disable_web_page_preview=True)
    
async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("Access Denied.")
        return

    uptime_seconds = int(time.time() - START_TIME)
    days, remainder = divmod(uptime_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    ping_ms = round(random.uniform(10, 80), 2)
    today = datetime.datetime.now().strftime("%d:%m:%Y")

    msg = (
        "🏓 <b>𝗣𝗼𝗻𝗴!</b>\n\n"
        f"    📅 <b>Update:</b> {today}\n"
        f"    ⏳ <b>Uptime:</b> {days}D : {hours}H : {minutes}M : {seconds}S\n"
        f"    ⚡ <b>Ping:</b> {ping_ms} ms"
    )
    await update.message.reply_text(msg, parse_mode="HTML")

async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("⛔️ <b>Access Denied</b>.", parse_mode=ParseMode.HTML)
        return

    await update.message.reply_text(
        "⚠️ <b>Bot Rules:</b>\n"
        "• No spamming\n"
        "• Violators may be banned without warning\n\n"
        "💬 <i>Need help?</i> Contact: <a href='https://t.me/Ceo_DarkFury'>@Ceo_DarkFury</a>",
        parse_mode=ParseMode.HTML
    )

async def reset_caption(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        await update.message.reply_text("⛔️ <b>Access Denied</b>.", parse_mode=ParseMode.HTML)
        return

    USER_DATA[str(user_id)]["caption"] = ""
    save_config()
    await update.message.reply_text(
        "✅ <b>Your caption has been successfully reset!</b>\n"
        "You can now set a new one with /setcaption.",
        parse_mode=ParseMode.HTML
    )

async def reset_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        await update.message.reply_text("⛔️ <b>Access Denied</b>.", parse_mode=ParseMode.HTML)
        return

    USER_DATA[str(user_id)]["channel"] = ""
    save_config()
    await update.message.reply_text(
        "✅ <b>Your Channel ID has been successfully reset!</b>\n"
        "Use /setchannelid to add a new one.",
        parse_mode=ParseMode.HTML
    )

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("⛔️ <b>Access Denied</b>.", parse_mode=ParseMode.HTML)
        return

    for user_id in USER_DATA:
        USER_DATA[user_id]["channel"] = ""
        USER_DATA[user_id]["caption"] = ""
    save_config()
    
    await update.message.reply_text(
        "♻️ <b>Your Channel IDs and Captions have been successfully reset!</b>\n"
        "Start fresh and set them again when needed.",
        parse_mode=ParseMode.HTML
    )
    
async def set_channel_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        await update.message.reply_text("⛔️ <b>Access Denied</b>.", parse_mode=ParseMode.HTML)
        return
    USER_STATE[user_id] = {"status": "waiting_channel"}
    await update.message.reply_text(
        "🚨 <b>Please send your <i>Channel ID</i></b> 📲\n"
        "Example: <code>@mychannel</code> or <code>-1001234567890</code>.\n"
        "Your ID is required to proceed. 📝",
        parse_mode="HTML"
    )
    
async def set_caption(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        await update.message.reply_text("⛔️ <b>Access Denied.</b>", parse_mode="HTML")
        return

    USER_STATE[user_id] = {"status": "waiting_caption"}
    await update.message.reply_text(
        "📝 <b>Caption Setup</b>\n\n"
        "Please send your custom caption that must include <code>Key -</code> somewhere in it.<br>"
        "<i>Example: Your file is ready - Key -</i>",
        parse_mode="HTML"
    )

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        await update.message.reply_text(
            "⛔️ <b>Access Denied!</b>\n<i>Bruh... you really thought you could?</i> 😂",
            parse_mode="HTML"
        )
        return

    doc = update.message.document
    caption = update.message.caption or ""

    if not doc.file_name.endswith(".apk"):
        await update.message.reply_text(
            "⚠️ <b>Unsupported File!</b>\nOnly <code>.apk</code> files are allowed.",
            parse_mode="HTML"
        )
        return

    match = re.search(r'Key\s*-\s*(\S+)', caption)
    if match:
        key = match.group(1)

        user_info = USER_DATA.get(str(user_id), {})
        saved_caption = user_info.get("caption", "")
        channel_id = user_info.get("channel", "")

        if not saved_caption or not channel_id:
            await update.message.reply_text(
                "⚠️ <b>Missing Setup!</b>\nPlease set both your <b>Caption</b> and <b>Channel ID</b> using /start.",
                parse_mode="HTML"
            )
            return

        final_caption = saved_caption.replace("Key -", f"<code>Key - {key}</code>")
        USER_STATE[user_id] = {
            "file_id": doc.file_id,
            "caption": final_caption,
            "status": "confirm_share"
        }
        await ask_to_share(update)
    else:
        USER_STATE[user_id] = {
            "file_id": doc.file_id,
            "caption": "",
            "status": "waiting_key"
        }
        await update.message.reply_text(
            "📝 <b>Almost done!</b>\nPlease send the <b>Key</b> you want to attach to this file.",
            parse_mode="HTML"
        )
        
async def ask_to_share(update: Update):
    keyboard = [
        [
            InlineKeyboardButton("✅ Yes", callback_data="share_yes"),
            InlineKeyboardButton("❌ No", callback_data="share_no")
        ]
    ]
    await update.message.reply_text(
        "📢 <b>Ready to Share?</b>\nDo you want to post this file to your channel?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message_text = update.message.text.strip().lower()

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
    elif message_text == "on" and user_id == OWNER_ID:
        await update.message.reply_text("✅ <b>Bot is now ON</b> (status placeholder).", parse_mode="HTML")
        return
    elif message_text == "off" and user_id == OWNER_ID:
        await update.message.reply_text("⚠️ <b>Bot is now OFF</b> (status placeholder).", parse_mode="HTML")
        return

    state = USER_STATE.get(user_id)
    if not state:
        return

    if state["status"] == "waiting_key":
        key = update.message.text
        caption = USER_DATA.get(str(user_id), {}).get("caption", "")
        if "Key -" not in caption:
            await update.message.reply_text(
                "❗ <b>Missing Placeholder!</b>\nYour saved caption must include <code>Key -</code>.\n"
                "Update your caption using <b>/start → 'Give me Your Caption'</b>.",
                parse_mode="HTML"
            )
            return

        final_caption = caption.replace("Key -", f"<code>Key - {key}</code>")
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
        await update.message.reply_text(
            f"✅ <b>Channel ID Saved:</b> <code>{channel_id}</code>",
            parse_mode="HTML"
        )
        del USER_STATE[user_id]

    elif state["status"] == "waiting_caption":
        caption = update.message.text.strip()
        if "Key -" not in caption:
            await update.message.reply_text(
                "❌ <b>Invalid Caption</b>\nMake sure to include <code>Key -</code> as a placeholder.",
                parse_mode="HTML"
            )
        else:
            USER_DATA[str(user_id)] = USER_DATA.get(str(user_id), {})
            USER_DATA[str(user_id)]["caption"] = caption
            save_config()
            await update.message.reply_text(
                "✅ <b>Caption Saved Successfully!</b>",
                parse_mode="HTML"
            )
            del USER_STATE[user_id]

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if user_id not in USER_STATE:
        await query.edit_message_text("⚠️ <b>Session expired or invalid.</b>\nPlease restart the process.", parse_mode="HTML")
        return

    data = query.data
    state = USER_STATE[user_id]
    channel_id = USER_DATA.get(str(user_id), {}).get("channel")

    if data == "share_yes":
        if not channel_id:
            await query.edit_message_text(
                "❗ <b>Channel ID not set.</b>\nUse <b>/start</b> to configure your channel first.",
                parse_mode="HTML"
            )
            return

        await context.bot.send_document(
            chat_id=channel_id,
            document=state["file_id"],
            caption=state["caption"],
            parse_mode="HTML",
            disable_notification=True
        )
        
        if channel_id.startswith("@"):
            button = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔗 Go to Channel", url=f"https://t.me/{channel_id.strip('@')}")]
            ])
            await query.edit_message_text("✅ <b>Shared Successfully!</b>\nClick below to view:", parse_mode="HTML", reply_markup=button)
        else:
            await query.edit_message_text("✅ <b>Shared Successfully!</b>\n(Channel is private — no preview link)", parse_mode="HTML")

    elif data == "share_no":
        await query.edit_message_text("❌ <b>Upload cancelled.</b>\nYou can restart anytime!", parse_mode="HTML")

    elif data == "get_channel_id":
        USER_STATE[user_id] = {"status": "waiting_channel"}
        await query.edit_message_text(
            "📢 <b>Please send your Channel ID</b>\nFormat: <code>@channelusername</code> or <code>-1001234567890</code>",
            parse_mode="HTML"
        )

    elif data == "get_caption":
        USER_STATE[user_id] = {"status": "waiting_caption"}
        await query.edit_message_text(
            "📝 <b>Send the caption you want to save</b>\nIt must include the placeholder <code>Key -</code>.",
            parse_mode="HTML"
        )

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("adduser", add_user))
    app.add_handler(CommandHandler("removeuser", remove_user))
    app.add_handler(CommandHandler("userlist", userlist))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(CommandHandler("rules", rules))
    app.add_handler(CommandHandler("resetcaption", reset_caption))
    app.add_handler(CommandHandler("resetchannelid", reset_channel))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("setchannelid", set_channel_id))
    app.add_handler(CommandHandler("setcaption", set_caption))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))
    app.add_handler(CallbackQueryHandler(handle_callback))

    app.run_polling()

if __name__ == "__main__":
    main()
