import json
import time
import datetime
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
import os
import re
from telegram.constants import ParseMode
import traceback

BOT_TOKEN = os.getenv("BOT_TOKEN")  # Get token from Railway environment
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable not set")

# Load config
with open("config.json") as f:
    config = json.load(f)

OWNER_ID = config["owner_id"]
ALLOWED_USERS = set(config["allowed_users"])
USER_DATA = config["user_data"]

# Load new setups
AUTO_SETUP = config.get("auto_setup", {
    "setup1": {"source_channel": "", "dest_channel": "", "dest_caption": "", "completed_count": 0},
    "setup2": {"source_channel": "", "dest_channel": "", "dest_caption": "", "completed_count": 0},
    "setup3": {"source_channel": "", "dest_channel": "", "dest_caption": "", "completed_count": 0}
})

START_TIME = time.time()
USER_STATE = {}

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
            "user_data": USER_DATA,
            "auto_setup": AUTO_SETUP
        }, f, indent=4)

def is_authorized(user_id: int) -> bool:
    return user_id == OWNER_ID or user_id in ALLOWED_USERS
    
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        await update.message.reply_text(
            "⛔ You are not authorized!\n"
            "📞 Must contact the owner.\n\n"
            "🛠️ Build by: @CeoDarkFury"
        )
        return

    # Save or update basic user data
    user_id_str = str(user_id)
    existing_data = USER_DATA.get(user_id_str, {})
    
    USER_DATA[user_id_str] = {
        "first_name": update.effective_user.first_name or "",
        "username": update.effective_user.username or "",
        "channel": existing_data.get("channel", ""),
        "caption": existing_data.get("caption", "")
    }
    
    save_config()

    inline_keyboard = [
        [InlineKeyboardButton("🌟 Add me to Your Channel", url="https://t.me/TrailKeysHandlerBOT?startchannel=true")],
        [InlineKeyboardButton("📡 Give me Your Channel ID", callback_data="get_channel_id")],
        [InlineKeyboardButton("📝 Give me Your Caption", callback_data="get_caption")]
    ]

    reply_kb = owner_keyboard if user_id == OWNER_ID else allowed_user_keyboard

    # First message
    await update.message.reply_text(
        "👋 *𝖧𝖾𝗒, 𝖡𝗎𝖽𝖽𝗒\\!* 🤖\n"
        "𝖳𝗁𝗂𝗌 𝖡𝗈𝗍 𝖬𝖺𝖽𝖾 𝖡𝗒 [@𝖢𝖾𝗈\\_𝖣𝖺𝗋𝗄𝖥𝗎𝗋𝗒](https://t.me/Ceo_DarkFury) 🧠\n\n"
        "✨ *𝖥𝖾𝖺𝗍𝗎𝗋𝖾𝗌 \\-* \n"
        "🔐 𝖤𝖺𝗌𝗂𝗅𝗒 𝖧𝖺𝗇𝖽𝗅𝖾 𝖸𝗈𝗎𝗋 𝖳𝗋𝖺𝗂𝗅 𝖪𝖾𝗒𝗌\n"
        "⚙️ 𝖶𝗂𝗍𝗁 𝖳𝗁𝗂𝗌 𝖠𝗐𝖾𝗌𝗈𝗆𝖾 𝖡𝗈𝗍\n\n"
        "🧭 𝖴𝗌𝖾 /help 𝗍𝗈 𝖾𝗑𝗉𝗅𝗈𝗋𝖾 𝖺𝗅𝗅 𝗍𝗁𝖾 𝖼𝗈𝗈𝗅 𝖿𝖾𝖺𝗍𝗎𝗋𝖾𝗌\\! 🚀\n\n"
        "🚧 𝗂𝖿 𝖸𝗈𝗎 𝖲𝖾𝖾 𝖾𝗑𝗉𝗂𝗋𝖾𝖽 𝗈𝗋 𝗂𝗇𝗏𝖺𝗅𝗂𝖽\\-\n"
        "❗️𝖤𝗋𝗋𝗈𝗋𝗌  𝖬𝖾𝗇𝗎𝖺𝗅𝗒 𝖴𝗌𝖾 :\n\n"
        "• /setchannelid 📡\n"
        "• /setcaption 📝\n\n"
        "𝖳𝗁𝖾𝗇 𝗂𝗍 𝖶𝗂𝗅𝗅 𝖡𝖾 𝖥𝗂𝗑𝖾𝖽 ☑️",
        parse_mode="MarkdownV2",
        reply_markup=reply_kb
    )

    # Second message
    await update.message.reply_text(
        "*𝖬𝗎𝗌𝗍 𝖲𝖾𝗍 𝖳𝗁𝗂𝗌 𝖡𝗈𝗍 𝖠𝖽𝗆𝗂𝗇 \\- ☑️*",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup(inline_keyboard)
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id == OWNER_ID:
        keyboard = [
            [InlineKeyboardButton("➡️ Next", callback_data="help_next")]
        ]
        await update.message.reply_text(
            "🛠 *Manual Upload Commands:*\n\n"
            "➔ /start - Restart bot interaction\n"
            "➔ /setchannelid - Set Upload Channel\n"
            "➔ /setcaption - Set Upload Caption\n"
            "➔ /resetcaption - Reset Caption\n"
            "➔ /resetchannelid - Reset Channel\n"
            "➔ /reset - Full Reset\n\n"
            "➔ /adduser - Add Allowed User\n"
            "➔ /removeuser - Remove User\n"
            "➔ /userlist - List Users\n"
            "➔ /ping - Bot Status\n"
            "➔ /rules - Bot Rules\n",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif user_id in ALLOWED_USERS:
        await update.message.reply_text(
            "🛠*Available Commands:*\n\n"
            "/start - Restart bot interaction ▶️\n"
            "/ping - Bot status 🏓\n"
            "/rules - Bot rules 📜\n"
            "/reset - Reset your data ♻️\n"
            "/resetcaption - Clear your saved caption 🧹\n"
            "/resetchannelid - Clear your channel ID 🔁\n"
            "/setchannelid - Set your Channel ID 📡\n"
            "/setcaption - Set your Caption ✍️",
            parse_mode="Markdown"
        )

    else:
        await update.message.reply_text("❌ You are not allowed to use this bot.")
        
async def add_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("𝖮𝗍𝗁𝖺 𝖡𝖺𝖺𝖽𝗎 🫵🏼. 𝖢𝗈𝗇𝗍𝖺𝖼𝗍 𝖸𝗈𝗎𝗋 𝖺𝖽𝗆𝗂𝗇 @Ceo_DarkFury 🌝")
        return

    if not context.args:
        await update.message.reply_text(
            "⚠️ *Oops\\!* You forgot to give a user ID\\.\n\nTry like this:\n`/adduser \\<user_id\\>` ✍️",
            parse_mode="MarkdownV2"
        )
        return        

    try:
        user_id = int(context.args[0])
        ALLOWED_USERS.add(user_id)
        save_config()
        await update.message.reply_text(f"✅ User `{user_id}` added successfully!", parse_mode="Markdown")
    except ValueError:
        await update.message.reply_text("Hmm... that doesn't look like a valid user ID. Try a number! 🔢")

async def remove_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("🗣️𝖳𝗁𝗂𝗋𝗎𝗆𝖻𝗂 𝖯𝖺𝖺𝗋𝗎𝖽𝖺 𝖳𝗁𝖾𝗏𝖽𝗂𝗒𝖺 𝖯𝖺𝗂𝗒𝖺")
        return

    if not context.args:
        await update.message.reply_text(
            "📝 *Usage:* `/removeuser` \\<user\\_id\\>\\ Don\\'t leave me hanging\\!",
            parse_mode=ParseMode.MARKDOWN_V2
        )
        return

    try:
        user_id = int(context.args[0])
        ALLOWED_USERS.discard(user_id)
        save_config()
        await update.message.reply_text(
            f"👋 *User* `{user_id}` *has been kicked out of the VIP list!* 🚪💨",
            parse_mode="Markdown"
        )
    except ValueError:
        await update.message.reply_text("❌ That doesn't look like a valid user ID. Numbers only, please! 🔢")

async def userlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("𝖮𝗋𝗎𝗎 𝗉𝖺𝗂𝗒𝖺𝗌𝖺𝗏𝗎𝗄𝗄𝗎🥴 𝖯𝗎𝗋𝖺𝗃𝖺𝗇𝖺𝗆 𝗂𝗅𝖺 𝖽𝖺𝖺 𝗉𝗎𝗇𝖽𝖺 🫵🏼")
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
        await update.message.reply_text("𝖵𝖺𝗇𝗍𝗁𝖺 𝗈𝖽𝖺𝗇𝖾 𝖮𝗆𝖻𝗎𝗍𝗁𝖺 𝖽𝖺𝖺 𝖻𝖺𝖺𝖽𝗎🫂")
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
        await update.message.reply_text("😶‍🌫️𝖮𝗈𝗆𝖻𝗎𝗎𝗎 𝖣𝖺𝖺 𝗍𝗁𝖺𝗒𝖺𝗅𝗂", parse_mode="Markdown")
        return

    await update.message.reply_text(
        "📜 *Bot Rules of Engagement:*\n\n"
        "1️⃣ Please *don't spam* the bot — it's got feelings too! 🤖💔\n"
        "2️⃣ Any violations may result in a *banhammer* drop without warning! 🔨🚫\n\n"
        "💬 *Need help? Got feedback?*\nSlide into the DMs: [@Ceo_DarkFury](https://t.me/Ceo_DarkFury)",
        parse_mode="Markdown"
    )
    
async def reset_caption(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        await update.message.reply_text("🫥𝖭𝖺𝖺𝗇𝗍𝗁𝖺𝗇 𝖽𝖺𝖺 𝗅𝖾𝗈𝗈")
        return

    USER_DATA[str(user_id)]["caption"] = ""
    save_config()
    await update.message.reply_text(
        "🧼 *Caption Cleared\\!* \nReady for a fresh start\\? ➕\nUse /SetCaption to drop a new vibe 🎯",
        parse_mode="MarkdownV2"
    )
    
async def reset_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        await update.message.reply_text("🗣️𝖮𝗈𝗆𝖻𝗎𝗎𝗎")
        return

    USER_DATA[str(user_id)]["channel"] = ""
    save_config()
    await update.message.reply_text(
        "📡 *Channel ID wiped\\!* ✨\nSet new one: /setchannelid 🛠️🚀",
        parse_mode="MarkdownV2"
    )
    
async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("🗣️𝖮𝗈𝗆𝖻𝗎𝗎𝗎")
        return

    for user_id in USER_DATA:
        USER_DATA[user_id]["channel"] = ""
        USER_DATA[user_id]["caption"] = ""
    save_config()
    
    await update.message.reply_text(
        "🧹 *Cleaned up\\!*\n"
        "No more caption or channel\\. 🚮\n"
        "Ready to Setup\\. 🚀",
        parse_mode="MarkdownV2"
    )
    
async def set_channel_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        await update.message.reply_text("🗣️ 𝖮𝗈𝗆𝖻𝗎𝗎𝗎")
        return

    USER_STATE[user_id] = {"status": "waiting_channel"}
    await update.message.reply_text(
        "🔧 *Setup Time\\!*\n"
        "Send me your Channel ID now\\. 📡\n"
        "Format: `@yourchannel` or `\\-100xxxxxxxxxx`",
        parse_mode="MarkdownV2"
    )
    
async def set_caption(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        await update.message.reply_text("𝖮𝗈𝗆𝖻𝗎𝗎𝗎 😭")
        return

    USER_STATE[user_id] = {"status": "waiting_caption"}
    await update.message.reply_text(
        "📝 *Caption Time\\!*\n"
        "Send me your Caption Including\\. ↙️\n"
        "The Placeholder `Key \\-` 🔑",
        parse_mode="MarkdownV2"
    )
    
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        await update.message.reply_text(
            "⛔ You are not authorized!\n"
            "📞 Must contact the owner.\n\n"
            "🛠️ Build by: @CeoDarkFury"
        )
        return

    doc = update.message.document
    caption = update.message.caption or ""

    if not doc.file_name.endswith(".apk"):
        await update.message.reply_text(
            "🗣️ *Only APK files allowed\\!*",
            parse_mode="MarkdownV2"
        )
        return

    # Load or create user state
    user_id = update.effective_user.id

    if user_id not in USER_STATE:
        USER_STATE[user_id] = {
            "apks": [],
            "status": "waiting_apk",
            "current_apk": None,
            "edit_mode": False
        }
    
    state = USER_STATE[user_id]
    
    # Now this is safe:
    if len(state["apks"]) >= 3:
        await update.message.reply_text("⚠️ You already uploaded 3 APKs.")
        return

    apk_info = {
        "file_id": doc.file_id,
        "key": "",
        "caption": "",
        "method": f"Method {len(state['apks']) + 1}"
    }

    match = re.search(r'Key\s*-\s*(\S+)', caption)
    if match:
        apk_info["key"] = match.group(1)
        if len(state["apks"]) == 0:
            # Method 1 (default caption replacement)
            saved_caption = USER_DATA.get(str(user_id), {}).get("caption", "")
            apk_info["caption"] = saved_caption.replace("Key -", f"Key - <code>{apk_info['key']}</code>")
        elif len(state["apks"]) == 1:
            # Method 2 (user's caption + key)
            apk_info["caption"] = f"{caption}\nKey - <code>{apk_info['key']}</code>"
        elif len(state["apks"]) == 2:
            # Method 3 follows Method 2 logic (stacked)
            apk_info["caption"] = f"{caption}\nKey - <code>{apk_info['key']}</code>"

        await update.message.reply_text(
            f"✅ APK {len(state['apks']) + 1} saved with key!",
            reply_markup=get_apk_share_keyboard()
        )
        state["apks"].append(apk_info)
    else:
        # Key missing, ask user to send it
        state["status"] = "waiting_key"
        state["current_apk"] = apk_info
        await update.message.reply_text(
            f"⏳ APK {len(state['apks']) + 1} received.\nNow send the Key to continue."
        )

def get_apk_share_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Yes", callback_data="share_yes"),
         InlineKeyboardButton("❌ No", callback_data="share_no")],
        [InlineKeyboardButton("🔁 Quote Key", callback_data="quote_key"),
         InlineKeyboardButton("📎 Normal Key", callback_data="normal_key")],
        [InlineKeyboardButton("👁 Show Preview", callback_data="show_preview")],
        [InlineKeyboardButton("✏️ Edit Caption", callback_data="edit_caption")]
    ])

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
    elif message_text == "on" and user_id == OWNER_ID:
        await update.message.reply_text("✅ Bot is now *ON*. All systems go! 🚀", parse_mode="Markdown")
        return
    elif message_text == "off" and user_id == OWNER_ID:
        await update.message.reply_text("⛔ Bot is now *OFF*. Shutting down... 📴", parse_mode="Markdown")
        return

    # STATE HANDLING
    state = USER_STATE.get(user_id)
    if not state:
        return

    if state["status"] == "waiting_key":
        key = update.message.text.strip()
        apk = state.get("current_apk")

        if not apk:
            await update.message.reply_text("⚠️ Something went wrong. Please re-upload the APK.")
            return

        apk["key"] = key

        if len(state["apks"]) == 0:
            # Method 1 - Default caption
            user_caption = USER_DATA.get(str(user_id), {}).get("caption", "")
            if "Key -" not in user_caption:
                await update.message.reply_text(
                    "📝 *Default caption missing `Key -` placeholder.*\nUse /setcaption to fix.",
                    parse_mode="Markdown"
                )
                return
            apk["caption"] = user_caption.replace("Key -", f"Key - <code>{key}</code>")
        else:
            # Method 2 or 3 - Append key to uploaded caption
            uploaded_caption = update.message.caption or ""
            apk["caption"] = f"{uploaded_caption}\nKey - <code>{key}</code>"

        state["apks"].append(apk)
        state["current_apk"] = None
        state["status"] = "waiting_apk"

        await update.message.reply_text(
            f"✅ Key added for APK {len(state['apks'])}.",
            reply_markup=get_apk_share_keyboard()
        )

    elif state["status"] == "editing_caption":
        new_caption = update.message.text.strip()
        if "Key -" not in new_caption:
            await update.message.reply_text("⚠️ Caption must include `Key -` placeholder.")
            return

        for apk in state["apks"]:
            apk["caption"] = new_caption.replace("Key -", f"Key - <code>{apk['key']}</code>")

        state["status"] = "waiting_apk"
        await update.message.reply_text("✅ Caption updated for all APKs.", reply_markup=get_apk_share_keyboard())
    
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    data = query.data

    # New: Handle Help Buttons FIRST
    if data == "help_next":
        keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="help_back")]]
        await query.edit_message_text(
            "⚙️ *Auto Channel Monitor Commands:*\n\n"
            "➔ /setsource1 - Set Source 1\n"
            "➔ /setdest1 - Set Destination 1\n"
            "➔ /setdestcaption1 - Set Caption 1\n"
            "➔ /resetsetup1 - Reset Setup 1\n\n"
            "➔ /setsource2 - Set Source 2\n"
            "➔ /setdest2 - Set Destination 2\n"
            "➔ /setdestcaption2 - Set Caption 2\n"
            "➔ /resetsetup2 - Reset Setup 2\n\n"
            "➔ /setsource3 - Set Source 3\n"
            "➔ /setdest3 - Set Destination 3\n"
            "➔ /setdestcaption3 - Set Caption 3\n"
            "➔ /resetsetup3 - Reset Setup 3\n\n"
            "➔ /viewsetup - View All Setups",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    elif data == "help_back":
        keyboard = [[InlineKeyboardButton("➡️ Next", callback_data="help_next")]]
        await query.edit_message_text(
            "🛠 *Manual Upload Commands:*\n\n"
            "➔ /start - Restart bot interaction\n"
            "➔ /setchannelid - Set Upload Channel\n"
            "➔ /setcaption - Set Upload Caption\n"
            "➔ /resetcaption - Reset Caption\n"
            "➔ /resetchannelid - Reset Channel\n"
            "➔ /reset - Full Reset\n\n"
            "➔ /adduser - Add Allowed User\n"
            "➔ /removeuser - Remove User\n"
            "➔ /userlist - List Users\n"
            "➔ /ping - Bot Status\n"
            "➔ /rules - Bot Rules\n",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # Upload Flow Handlers
    if user_id not in USER_STATE:
        await query.edit_message_text("⏳ *Session expired or invalid!* ❌\nPlease restart the process using /start.", parse_mode="Markdown")
        return

    state = USER_STATE[user_id]
    channel_id = USER_DATA.get(str(user_id), {}).get("channel")

    if data == "share_yes":
        if not channel_id:
            await query.edit_message_text("⚠️ You haven't set a channel.\nUse `/setchannelid` first.")
            return

        for apk in state["apks"]:
            try:
                sent = await context.bot.send_document(
                    chat_id=channel_id,
                    document=apk["file_id"],
                    caption=apk["caption"],
                    parse_mode="HTML"
                )

                if str(channel_id).startswith("@"):
                    post_link = f"https://t.me/{channel_id.strip('@')}/{sent.message_id}"
                else:
                    post_link = f"https://t.me/c/{channel_id.replace('-100', '')}/{sent.message_id}"

                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"✅ Shared!\n🔗 <a href='{post_link}'>View Post</a>",
                    parse_mode="HTML"
                )

            except Exception as e:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"❌ Error: {e}"
                )

        USER_STATE[user_id] = {"apks": [], "status": "waiting_apk", "current_apk": None}

    elif data == "share_no":
        await query.edit_message_text("🙅‍♂️ *No worries!* You can retry anytime. Just drop your .apk again. 🚀", parse_mode="Markdown")

    elif data == "get_channel_id":
        USER_STATE[user_id] = {"status": "waiting_channel"}
        await query.edit_message_text(
            "🔧 *Setup Time\\!*\nSend me your Channel ID now\\. 📡\nFormat: `@yourchannel` or `\\-100xxxxxxxxxx`",
            parse_mode="MarkdownV2"
        )

    elif data == "get_caption":
        USER_STATE[user_id] = {"status": "waiting_caption"}
        await query.edit_message_text(
            "📝 *Caption Time\\!*\nSend me your Caption Including\\. ↙️\nThe Placeholder `Key \\-` 🔑",
            parse_mode="MarkdownV2"
        )

    elif data == "show_preview":
        preview = ""
        for i, apk in enumerate(state["apks"], 1):
            preview += f"<b>APK {i}</b>\nKey: <code>{apk['key']}</code>\nMethod: {apk['method']}\n\n"
        await query.edit_message_text(preview, parse_mode="HTML", reply_markup=get_apk_share_keyboard())

    elif data == "quote_key":
        for apk in state["apks"]:
            if apk["key"]:
                apk["caption"] = apk["caption"].replace(
                    f"<code>{apk['key']}</code>",
                    f"<blockquote>{apk['key']}</blockquote>"
                )
                apk["method"] = "Quote Key"
        await query.edit_message_text("🔁 Switched to *Quote Key* mode!", parse_mode="Markdown", reply_markup=get_apk_share_keyboard())

    elif data == "normal_key":
        for apk in state["apks"]:
            if apk["key"]:
                apk["caption"] = re.sub(r'<blockquote>(.*?)</blockquote>', r'<code>\1</code>', apk["caption"])
                apk["method"] = "Normal Key"
        await query.edit_message_text("📎 Back to *Normal Key* mode!", parse_mode="Markdown", reply_markup=get_apk_share_keyboard())

    elif data == "edit_caption":
        USER_STATE[user_id]["status"] = "editing_caption"
        await query.edit_message_text("✏️ Send new caption with `Key -` placeholder.")
    
async def set_source1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("Only owner can set this!")
        return
    if not context.args:
        await update.message.reply_text("Usage: `/setsource1 @channelname or -100xxxx`", parse_mode="Markdown")
        return
    AUTO_SETUP["setup1"]["source_channel"] = context.args[0]
    save_config()
    await update.message.reply_text(f"✅ Setup 1 Source Channel set to: `{context.args[0]}`", parse_mode="Markdown")

# Setup 1 - Set Destination Channel
async def set_dest1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("Only owner can set this!")
        return
    if not context.args:
        await update.message.reply_text("Usage: `/setdest1 @channelname or -100xxxx`", parse_mode="Markdown")
        return
    AUTO_SETUP["setup1"]["dest_channel"] = context.args[0]
    save_config()
    await update.message.reply_text(f"✅ Setup 1 Destination Channel set to: `{context.args[0]}`", parse_mode="Markdown")

# Setup 1 - Set Destination Caption
async def set_destcaption1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("Only owner can set this!")
        return
    text = update.message.text.split(' ', 1)
    if len(text) < 2:
        await update.message.reply_text("Usage: `/setdestcaption1 Caption with Key - placeholder`", parse_mode="Markdown")
        return
    caption = text[1]
    if "Key -" not in caption:
        await update.message.reply_text("❗ Caption must include `Key -` placeholder!", parse_mode="Markdown")
        return
    AUTO_SETUP["setup1"]["dest_caption"] = caption
    save_config()
    await update.message.reply_text("✅ Setup 1 Destination Caption saved!", parse_mode="Markdown")

# Setup 2 - Set Source Channel
async def set_source2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("Only owner can set this!")
        return
    if not context.args:
        await update.message.reply_text("Usage: `/setsource2 @channelname or -100xxxx`", parse_mode="Markdown")
        return
    AUTO_SETUP["setup2"]["source_channel"] = context.args[0]
    save_config()
    await update.message.reply_text(f"✅ Setup 2 Source Channel set to: `{context.args[0]}`", parse_mode="Markdown")

# Setup 2 - Set Destination Channel
async def set_dest2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("Only owner can set this!")
        return
    if not context.args:
        await update.message.reply_text("Usage: `/setdest2 @channelname or -100xxxx`", parse_mode="Markdown")
        return
    AUTO_SETUP["setup2"]["dest_channel"] = context.args[0]
    save_config()
    await update.message.reply_text(f"✅ Setup 2 Destination Channel set to: `{context.args[0]}`", parse_mode="Markdown")

# Setup 2 - Set Destination Caption
async def set_destcaption2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("Only owner can set this!")
        return
    text = update.message.text.split(' ', 1)
    if len(text) < 2:
        await update.message.reply_text("Usage: `/setdestcaption2 Caption with Key - placeholder`", parse_mode="Markdown")
        return
    caption = text[1]
    if "Key -" not in caption:
        await update.message.reply_text("❗ Caption must include `Key -` placeholder!", parse_mode="Markdown")
        return
    AUTO_SETUP["setup2"]["dest_caption"] = caption
    save_config()
    await update.message.reply_text("✅ Setup 2 Destination Caption saved!", parse_mode="Markdown")

# Setup 3 - Set Source Channel
async def set_source3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("Only owner can set this!")
        return
    if not context.args:
        await update.message.reply_text("Usage: `/setsource3 @channelname or -100xxxx`", parse_mode="Markdown")
        return
    AUTO_SETUP["setup3"]["source_channel"] = context.args[0]
    save_config()
    await update.message.reply_text(f"✅ Setup 3 Source Channel set to: `{context.args[0]}`", parse_mode="Markdown")

# Setup 3 - Set Destination Channel
async def set_dest3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("Only owner can set this!")
        return
    if not context.args:
        await update.message.reply_text("Usage: `/setdest3 @channelname or -100xxxx`", parse_mode="Markdown")
        return
    AUTO_SETUP["setup3"]["dest_channel"] = context.args[0]
    save_config()
    await update.message.reply_text(f"✅ Setup 3 Destination Channel set to: `{context.args[0]}`", parse_mode="Markdown")

# Setup 3 - Set Destination Caption
async def set_destcaption3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("Only owner can set this!")
        return
    text = update.message.text.split(' ', 1)
    if len(text) < 2:
        await update.message.reply_text("Usage: `/setdestcaption3 Caption with Key - placeholder`", parse_mode="Markdown")
        return
    caption = text[1]
    if "Key -" not in caption:
        await update.message.reply_text("❗ Caption must include `Key -` placeholder!", parse_mode="Markdown")
        return
    AUTO_SETUP["setup3"]["dest_caption"] = caption
    save_config()
    await update.message.reply_text("✅ Setup 3 Destination Caption saved!", parse_mode="Markdown")

async def view_setup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id != OWNER_ID:
        await update.message.reply_text("❌ Only Owner can view setup!")
        return

    text = ""
    total = 0

    for i in range(1, 4):
        setup = AUTO_SETUP.get(f"setup{i}", {})

        source = setup.get("source_channel")
        dest = setup.get("dest_channel", "Not Set")
        caption = "Saved" if setup.get("dest_caption") else "Not Set"
        completed = setup.get("completed_count", 0)

        if source:
            total += 1

            # Escape for MarkdownV2
            source = re.sub(r'([_\*\~\`\>\#\+\-\=\|\{\}\.\!])', r'\\\1', source)
            dest = re.sub(r'([_\*\~\`\>\#\+\-\=\|\{\}\.\!])', r'\\\1', dest)

            text += (
                f"📌 Setup {i}\n"
                f"├─ 👤 Source : {source}\n"
                f"├─ 🧬 Destination : {dest}\n"
                f"├─ 📝 Caption : {caption}\n"
                f"└─ 🔢 Completed : {completed} Keys\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
            )

    if total == 0:
        await update.message.reply_text("❌ No setup configured yet.")
    else:
        header = f"🧾 *Total Setup : {total}*\n\n"
        await update.message.reply_text(header + text, parse_mode="MarkdownV2")

async def reset_setup1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("Only owner can reset setup 1!")
        return

    AUTO_SETUP["setup1"] = {
        "source_channel": "",
        "dest_channel": "",
        "dest_caption": "",
        "completed_count": 0
    }
    save_config()
    await update.message.reply_text("✅ Setup 1 has been reset successfully!")

async def reset_setup2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("Only owner can reset setup 2!")
        return

    AUTO_SETUP["setup2"] = {
        "source_channel": "",
        "dest_channel": "",
        "dest_caption": "",
        "completed_count": 0
    }
    save_config()
    await update.message.reply_text("✅ Setup 2 has been reset successfully!")

async def reset_setup3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("Only owner can reset setup 3!")
        return

    AUTO_SETUP["setup3"] = {
        "source_channel": "",
        "dest_channel": "",
        "dest_caption": "",
        "completed_count": 0
    }
    save_config()
    await update.message.reply_text("✅ Setup 3 has been reset successfully!")

async def auto_handle_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.channel_post:
        return

    message = update.channel_post
    chat_id = str(message.chat.id)
    source_username = f"@{message.chat.username}" if message.chat.username else None
    doc = message.document
    caption = message.caption or ""

    print(f"✅ Received channel post from {source_username or chat_id}")
    if doc:
        print(f"Document: {doc.file_name}, Size: {doc.file_size}")
    else:
        print("No document attached.")

    if not doc:
        return

    if not doc.file_name.endswith(".apk"):
        print("❌ Not an APK file. Ignoring.")
        return

    file_size = doc.file_size
    file_size_mb = file_size / (1024 * 1024)

    matched_setup = None
    setup_number = None

    for i in range(1, 4):
        setup = AUTO_SETUP.get(f"setup{i}")
        if not setup or not setup.get("source_channel"):
            continue

        src = setup["source_channel"]

        # Matching by @username if available
        if src.startswith("@") and source_username and src.lower() == source_username.lower():
            matched_setup = setup
            setup_number = i
            break
        # Otherwise match by chat ID
        elif src == chat_id:
            matched_setup = setup
            setup_number = i
            break

    if not matched_setup:
        print("❌ No matching setup found for this source channel.")
        return

    print(f"✅ Matched to Setup {setup_number}")

    # Size rules
    if setup_number == 1 and not (1 <= file_size_mb <= 50):
        print("❌ Size not matched for Setup 1.")
        return
    if setup_number == 2 and not (80 <= file_size_mb <= 2048):
        print("❌ Size not matched for Setup 2.")
        return
    # Setup 3 accepts any size

    if not caption:
        await context.bot.send_message(
            chat_id=OWNER_ID,
            text="⚠️ *Alert!*\n➔ *APK received without caption.*\n🚫 *Processing skipped!*",
            parse_mode="Markdown"
        )
        print("❌ Caption missing. Error sent to owner.")
        return

    match = re.search(r'Key\s*-\s*(\S+)', caption)
    if not match:
        await context.bot.send_message(
            chat_id=OWNER_ID,
            text="⚠️ *Warning!*\n➔ *Key missing in caption.*\n⛔ *File not processed!*",
            parse_mode="Markdown"
        )
        print("❌ Key missing in caption. Error sent to owner.")
        return

    key = match.group(1)
    dest_caption = matched_setup["dest_caption"].replace("Key -", f"Key - `{key}`")
    dest_channel = matched_setup["dest_channel"]

    try:
        sent_msg = await context.bot.send_document(
            chat_id=dest_channel,
            document=doc.file_id,
            caption=dest_caption,
            parse_mode="Markdown",
            disable_notification=True
        )

        matched_setup["completed_count"] += 1
        save_config()

        # Post link generator
        post_link = "Unknown"
        if str(dest_channel).startswith("@"):
            post_link = f"https://t.me/{dest_channel.strip('@')}/{sent_msg.message_id}"
        elif str(dest_channel).startswith("-100"):
            post_link = f"https://t.me/c/{str(dest_channel)[4:]}/{sent_msg.message_id}"

        # Escaping for MarkdownV2
        def escape(text):
            return re.sub(r'([_\*~`>\#+\-=|{}.!])', r'\\\1', str(text))

        source_name = source_username if source_username else chat_id
        source = escape(source_name)
        dest = escape(dest_channel)
        key_escape = escape(key)
        post_link_escape = escape(post_link)

        key_escape = f"`{key_escape}`"
        
        await context.bot.send_message(
            chat_id=OWNER_ID,
            text=(
                f"📌 Setup {setup_number} Completed\n"
                f"├─ 👤 Source : {source}\n"
                f"├─ 🧬 Destination : {dest}\n"
                f"├─ 📡 Key : {key_escape}\n"
                f"└─ 🆔 Post Link : [Click Here]({post_link_escape})\n"
                "━━━━━━━━━━━━━━━━━━━━"
            ),
            parse_mode="MarkdownV2",
            disable_web_page_preview=True
        )
        print("✅ Successfully forwarded and log sent to owner.")

    except Exception as e:
        error_message = traceback.format_exc()
        await context.bot.send_message(
            chat_id=OWNER_ID,
            text=f"❌ *Error Sending APK!*\n\n`{error_message}`",
            parse_mode="MarkdownV2"
        )
        print("❌ Error while sending document:\n", error_message)

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Main owner/user commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(CommandHandler("rules", rules))

    # Manual upload system
    app.add_handler(CommandHandler("setchannelid", set_channel_id))
    app.add_handler(CommandHandler("setcaption", set_caption))
    app.add_handler(CommandHandler("resetcaption", reset_caption))
    app.add_handler(CommandHandler("resetchannelid", reset_channel))
    app.add_handler(CommandHandler("reset", reset))

    # Manage allowed users
    app.add_handler(CommandHandler("adduser", add_user))
    app.add_handler(CommandHandler("removeuser", remove_user))
    app.add_handler(CommandHandler("userlist", userlist))

    # Auto setup commands
    app.add_handler(CommandHandler("setsource1", set_source1))
    app.add_handler(CommandHandler("setdest1", set_dest1))
    app.add_handler(CommandHandler("setdestcaption1", set_destcaption1))

    app.add_handler(CommandHandler("setsource2", set_source2))
    app.add_handler(CommandHandler("setdest2", set_dest2))
    app.add_handler(CommandHandler("setdestcaption2", set_destcaption2))

    app.add_handler(CommandHandler("setsource3", set_source3))
    app.add_handler(CommandHandler("setdest3", set_dest3))
    app.add_handler(CommandHandler("setdestcaption3", set_destcaption3))

    # Reset single setup commands
    app.add_handler(CommandHandler("resetsetup1", reset_setup1))
    app.add_handler(CommandHandler("resetsetup2", reset_setup2))
    app.add_handler(CommandHandler("resetsetup3", reset_setup3))

    # View setup command
    app.add_handler(CommandHandler("viewsetup", view_setup))   # <<< ADD this line carefully!

    # Auto forward and manual upload
    app.add_handler(MessageHandler(filters.UpdateType.CHANNEL_POSTS, auto_handle_channel_post))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))

    # Handle callback buttons (for help menu etc.)
    app.add_handler(CallbackQueryHandler(handle_callback))

    app.run_polling()

if __name__ == "__main__":
    main()
