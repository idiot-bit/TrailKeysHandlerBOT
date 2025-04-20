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
import asyncio

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

    # Initialize or Reset user state
    USER_STATE[user_id] = {
        "current_method": None,
        "status": "selecting_method",
        "session_files": [],
        "saved_key": None,
        "apk_posts": [],
        "waiting_key": False,
        "last_apk_time": None,
        "last_post_link": None,
        "preview_message_id": None
    }

    keyboard = [
        [InlineKeyboardButton("⚡ Method 1", callback_data="method_1")],
        [InlineKeyboardButton("🚀 Method 2", callback_data="method_2")]
    ]

    await update.message.reply_text(
        "👋 Welcome!\n\n"
        "Please select your working method:\n\n"
        "⚡ *Method 1:* Manual Key Capture.\n"
        "🚀 *Method 2:* Upload 2-3 APKs together, then Capture One Key.\n\n"
        "_You can change method anytime later._",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
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

    # --- IMPORTANT: Check if method selected ---
    state = USER_STATE.get(user_id)
    if not state or not state.get("current_method"):
        keyboard = [
            [InlineKeyboardButton("⚡ Choose Method", callback_data="back_to_methods")]
        ]
        await update.message.reply_text(
            "⚠️ *You didn't select any Method yet!*\n\n"
            "Please select Method 1 or Method 2 first.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    method = state.get("current_method")
    
    if method == "method1":
        await process_method1_apk(update, context)
        return

    elif method == "method2":
        await process_method2_apk(update, context)
        return

async def process_method1_apk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    doc = update.message.document
    caption = update.message.caption or ""

    match = re.search(r'Key\s*-\s*(\S+)', caption)
    if match:
        key = match.group(1)

        user_info = USER_DATA.get(str(user_id), {})
        saved_caption = user_info.get("caption", "")
        channel_id = user_info.get("channel", "")

        if not saved_caption or not channel_id:
            await update.message.reply_text(
                "⚠️ *Please setup your Channel and Caption first!*",
                parse_mode="Markdown"
            )
            return

        final_caption = saved_caption.replace("Key -", f"Key - <code>{key}</code>")
        await context.bot.send_document(
            chat_id=channel_id,
            document=doc.file_id,
            caption=final_caption,
            parse_mode="HTML"
        )
        await update.message.reply_text("✅ *APK posted successfully!*", parse_mode="Markdown")

    else:
        # If key missing, ask to send key manually
        USER_STATE[user_id]["waiting_key"] = True
        USER_STATE[user_id]["file_id"] = doc.file_id
        await update.message.reply_text("⏳ *Send the Key now!*", parse_mode="Markdown")

async def process_method2_apk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    doc = update.message.document

    if not doc.file_name.endswith(".apk"):
        await update.message.reply_text(
            "🗣️ *Only APK files allowed!*",
            parse_mode="Markdown"
        )
        return

    state = USER_STATE.setdefault(user_id, {})
    session = state.setdefault("session_files", [])

    if len(session) >= 3:
        await update.message.reply_text(
            "⚠️ *Maximum 3 APKs allowed per session!*\n\n"
            "Please restart by selecting Send APK again.",
            parse_mode="Markdown"
        )
        return

    session.append(doc.file_id)

    # Check if already message_id exists
    message_id = state.get("progress_message_id")
    chat_id = update.message.chat_id

    if message_id:
        try:
            # Edit previous message
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=f"✅ {len(session)} APKs Received! ☑️\nWaiting 5 seconds for next APK..."
            )
        except:
            message_id = None

    if not message_id:
        sent_msg = await update.message.reply_text(
            f"✅ {len(session)} APKs Received! ☑️\nWaiting 5 seconds for next APK...",
            parse_mode="Markdown"
        )
        state["progress_message_id"] = sent_msg.message_id

    # Save last time
    USER_STATE[user_id]["last_apk_time"] = time.time()

    # Start 5 sec countdown
    context.application.create_task(countdown_and_check(user_id, chat_id, context))

async def method2_send_to_channel(user_id, context: ContextTypes.DEFAULT_TYPE):
    user_info = USER_DATA.get(str(user_id), {})
    state = USER_STATE.get(user_id, {})

    channel_id = user_info.get("channel")
    saved_caption = user_info.get("caption")
    session_files = state.get("session_files", [])
    key = state.get("saved_key", "")

    if not channel_id or not saved_caption or not session_files or not key:
        await context.bot.send_message(
            chat_id=user_id,
            text="❌ *Session Data Missing! Please restart.*",
            parse_mode="Markdown"
        )
        return

    posted_ids = []
    last_message = None

    # Send each APK
    for idx, file_id in enumerate(session_files, start=1):
    # Choose caption style
        if state.get("quote_applied"):
            # Quote + Mono format
            caption = f"> Key - `{key}`"
            parse_mode = "Markdown"
        else:
            # Default Normal style (HTML Mono)
            if idx == 1 and len(session_files) == 1:
                caption = saved_caption.replace("Key -", f"Key - <code>{key}</code>")
            elif idx in (1, 2) and len(session_files) >= 2:
                caption = f"Key - <code>{key}</code>"
            elif idx == 3:
                caption = saved_caption.replace("Key -", f"Key - <code>{key}</code>")
            parse_mode = "HTML"
    
        try:
            sent_message = await context.bot.send_document(
                chat_id=channel_id,
                document=file_id,
                caption=caption,
                parse_mode=parse_mode
            )
            posted_ids.append(sent_message.message_id)
            last_message = sent_message
        except Exception as e:
            print(f"Error posting APK {idx}: {e}")

    if not posted_ids:
        await context.bot.send_message(
            chat_id=user_id,
            text="❌ *Failed to post APKs!*",
            parse_mode="Markdown"
        )
        return

    # Save posted info
    USER_STATE[user_id]["session_files"] = []
    USER_STATE[user_id]["saved_key"] = None
    USER_STATE[user_id]["waiting_key"] = False
    USER_STATE[user_id]["last_apk_time"] = None
    USER_STATE[user_id]["apk_posts"] = posted_ids

    # Save Last Post Link
    if last_message:
        if str(channel_id).startswith("@"):
            post_link = f"https://t.me/{channel_id.strip('@')}/{last_message.message_id}"
        elif str(channel_id).startswith("-100"):
            post_link = f"https://t.me/c/{channel_id.replace('-100', '')}/{last_message.message_id}"
        else:
            post_link = "Unknown"
    else:
        post_link = "Unknown"

    USER_STATE[user_id]["last_post_link"] = post_link

    # Manage Menu
    buttons = [
        [InlineKeyboardButton("📄 View Last Post", url=post_link)],
        [InlineKeyboardButton("🗑️ Delete APK Post", callback_data="delete_apk_post")],
        [InlineKeyboardButton("🔙 Back to Methods", callback_data="back_to_methods")]
    ]

    await context.bot.edit_message_text(
        chat_id=user_id,
        message_id=USER_STATE[user_id]["preview_message_id"],
        text="✅ *All APKs Posted Successfully!*\n\nManage your posted APKs below:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def check_session_timeout(user_id, context):
    await asyncio.sleep(5)

    state = USER_STATE.get(user_id)
    if not state:
        return

    last_apk_time = state.get("last_apk_time")
    if not last_apk_time:
        return

    now = time.time()
    if now - last_apk_time >= 5:
        # Timeout reached, move to key capture
        session = state.get("session_files", [])
        if session:
            await ask_key_for_method2(user_id, context)

async def ask_key_for_method2(user_id, context):
    chat_id = user_id
    USER_STATE[user_id]["waiting_key"] = True

    await context.bot.send_message(
        chat_id=chat_id,
        text="🔑 *Send the Key now!* (Only one Key for 2-3 APKs)",
        parse_mode="Markdown"
    )

async def ask_to_share(update: Update):
    keyboard = [
        [InlineKeyboardButton("✅ Yes", callback_data="share_yes"),
         InlineKeyboardButton("❌ No", callback_data="share_no")]
    ]
    await update.message.reply_text(
        "*𝖱𝖾𝖺𝖽𝗒 𝗍𝗈 𝗌𝗁𝖺𝗋𝖾* 🤔\n"
        "_𝗍𝗁𝗂𝗌 𝖯𝗈𝗌𝗍 𝗍𝗈 𝗒𝗈𝗎𝗋 𝖼𝗁𝖺𝗇𝗇𝖾𝗅 \\? ↙️_\n"
        "*𝖢𝗁𝗈𝗈𝗌𝖾 𝗐𝗂𝗌𝖾𝗅𝗒 \\!* 👇",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def countdown_and_check(user_id, chat_id, context):
    try:
        for remaining in range(5, 0, -1):
            await asyncio.sleep(1)

            state = USER_STATE.get(user_id, {})
            progress_id = state.get("progress_message_id")

            # If already waiting for key, stop countdown
            if state.get("waiting_key"):
                return

            if progress_id:
                try:
                    await context.bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=progress_id,
                        text=f"✅ {len(state.get('session_files', []))} APKs Received! ☑️\nWaiting {remaining} sec for next APK...",
                        parse_mode="Markdown"
                    )
                except Exception:
                    pass

        # After 5 sec finished
        state = USER_STATE.get(user_id, {})
        if not state.get("waiting_key") and state.get("session_files"):
            progress_id = state.get("progress_message_id")
            if progress_id:
                try:
                    await context.bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=progress_id,
                        text="🔑 *Send the Key now!* (Only one Key for 2-3 APKs)",
                        parse_mode="Markdown"
                    )
                except Exception:
                    pass
            USER_STATE[user_id]["waiting_key"] = True
            USER_STATE[user_id]["progress_message_id"] = None

    except Exception as e:
        print(f"Countdown Error: {e}")

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

    # Handle Channel Setting
    if state.get("status") == "waiting_channel":
        channel_id = update.message.text.strip()
        USER_DATA[str(user_id)] = USER_DATA.get(str(user_id), {})
        USER_DATA[str(user_id)]["channel"] = channel_id
        save_config()
        await update.message.reply_text(f"✅ *Channel ID saved:* `{channel_id}`", parse_mode="Markdown")
        USER_STATE[user_id]["status"] = "normal"
        await start(update, context)
        return

    # Handle Caption Setting
    if state.get("status") == "waiting_caption":
        caption = update.message.text.strip()
        if "Key -" not in caption:
            await update.message.reply_text(
                "❗ *Invalid caption!*\nYour caption must contain `Key -`.",
                parse_mode="Markdown"
            )
        else:
            USER_DATA[str(user_id)] = USER_DATA.get(str(user_id), {})
            USER_DATA[str(user_id)]["caption"] = caption
            save_config()
            buttons = [
                [InlineKeyboardButton("🔙 Back", callback_data="method2_back_fullmenu")]
            ]
            await context.bot.send_message(
                chat_id=user_id,
                text=f"✅ New Caption Saved!\n\n{caption}",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
            return

    # Handle waiting key for Method 1
    if state.get("waiting_key") and state.get("current_method") == "method1":
        key = update.message.text.strip()
        saved_caption = USER_DATA.get(str(user_id), {}).get("caption", "")
        channel_id = USER_DATA.get(str(user_id), {}).get("channel", "")
        file_id = state.get("file_id")

        if not key or not file_id or not saved_caption or not channel_id:
            await update.message.reply_text(
                "❌ *Missing Data! Please restart.*",
                parse_mode="Markdown"
            )
            return

        final_caption = saved_caption.replace("Key -", f"Key - <code>{key}</code>")
        await context.bot.send_document(
            chat_id=channel_id,
            document=file_id,
            caption=final_caption,
            parse_mode="HTML"
        )
        await update.message.reply_text("✅ *APK posted successfully!*", parse_mode="Markdown")

        USER_STATE[user_id]["waiting_key"] = False
        USER_STATE[user_id]["file_id"] = None
        return

    # Handle waiting key for Method 2
    if state.get("waiting_key") and state.get("current_method") == "method2":
        key = update.message.text.strip()
        session_files = state.get("session_files", [])

        if not key or not session_files:
            await update.message.reply_text(
                "❌ *Session Error! Please restart.*",
                parse_mode="Markdown"
            )
            return

        USER_STATE[user_id]["saved_key"] = key
        USER_STATE[user_id]["waiting_key"] = False
        USER_STATE[user_id]["progress_message_id"] = None  # STOP Countdown

        # Now show confirmation
        buttons = [
            [InlineKeyboardButton("✅ Yes", callback_data="method2_yes"),
             InlineKeyboardButton("❌ No", callback_data="method2_no")],
            [InlineKeyboardButton("✍️ Quote Key", callback_data="method2_quote"),
             InlineKeyboardButton("🔤 Normal Key", callback_data="method2_mono")],
            [InlineKeyboardButton("📝 Edit Caption", callback_data="method2_edit"),
             InlineKeyboardButton("👁️ Show Preview", callback_data="method2_preview")]
        ]

        sent = await update.message.reply_text(
            "🔖 *Key captured!*\n\nChoose what you want to do next:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

        USER_STATE[user_id]["preview_message_id"] = sent.message_id
        return

    # Handle waiting new caption after Edit
    if state.get("status") == "waiting_new_caption":
        await method2_edit_caption(update, context)
        return

async def method2_edit_caption(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    new_caption = update.message.text.strip()

    if "Key -" not in new_caption:
        await update.message.reply_text(
            "❌ *Invalid Caption!*\n\nIt must include `Key -` placeholder.",
            parse_mode="Markdown"
        )
        return

    # Save new Caption
    USER_DATA[str(user_id)] = USER_DATA.get(str(user_id), {})
    USER_DATA[str(user_id)]["caption"] = new_caption
    save_config()

    USER_STATE[user_id]["status"] = "normal"

    # Update Preview
    preview_message_id = USER_STATE.get(user_id, {}).get("preview_message_id")
    key = USER_STATE.get(user_id, {}).get("saved_key", "")
    session_files = USER_STATE.get(user_id, {}).get("session_files", [])

    if not preview_message_id or not key or not session_files:
        await update.message.reply_text(
            "⚠️ *No active session found!*",
            parse_mode="Markdown"
        )
        return

    text = "✅ *New Caption Saved!*\n\n"
    final_caption = new_caption.replace("Key -", f"Key - {key}")

    for idx, _ in enumerate(session_files, start=1):
        text += f"📦 APK {idx}: {final_caption}\n"

    buttons = [
        [InlineKeyboardButton("🔙 Back", callback_data="method2_back_fullmenu")]
    ]

    try:
        await context.bot.edit_message_text(
            chat_id=user_id,
            message_id=preview_message_id,
            text=text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    except Exception as e:
        print(f"Error editing preview after caption: {e}")

async def method2_convert_quote(user_id, context: ContextTypes.DEFAULT_TYPE):
    state = USER_STATE.get(user_id, {})
    preview_message_id = state.get("preview_message_id")
    key = state.get("saved_key", "")
    session_files = state.get("session_files", [])

    if not preview_message_id or not key or not session_files:
        await context.bot.send_message(
            chat_id=user_id,
            text="⚠️ *No session found!*",
            parse_mode="Markdown"
        )
        return

    text = "✅ *Key converted to Quote Style!*\n\n"
    for idx, _ in enumerate(session_files, start=1):
        text += f"📦 APK {idx}: <blockquote>Key - <code>{key}</code></blockquote>\n"

    # Mark quote_applied = True (for button hiding)
    USER_STATE[user_id]["quote_applied"] = True

    buttons = build_method2_buttons(user_id)  # Rebuild dynamic buttons

    try:
        await context.bot.edit_message_text(
            chat_id=user_id,
            message_id=preview_message_id,
            text=text,
            parse_mode="HTML",  # Needed for <code> formatting
            reply_markup=buttons
        )
    except Exception as e:
        print(f"Error converting to quote style: {e}")

async def method2_convert_mono(user_id, context: ContextTypes.DEFAULT_TYPE):
    state = USER_STATE.get(user_id, {})
    preview_message_id = state.get("preview_message_id")
    key = state.get("saved_key", "")
    session_files = state.get("session_files", [])

    if not preview_message_id or not key or not session_files:
        await context.bot.send_message(
            chat_id=user_id,
            text="⚠️ *No session found!*",
            parse_mode="Markdown"
        )
        return

    text = "✅ *Key converted to Normal Style!*\n\n"
    for idx, _ in enumerate(session_files, start=1):
        text += f"`{key}`\n"

    # Mark mono_applied = True (for button hiding)
    USER_STATE[user_id]["mono_applied"] = True

    buttons = build_method2_buttons(user_id)  # Rebuild dynamic buttons

    try:
        await context.bot.edit_message_text(
            chat_id=user_id,
            message_id=preview_message_id,
            text=text,
            parse_mode="Markdown",  # Needed for backtick style
            reply_markup=buttons
        )
    except Exception as e:
        print(f"Error converting to mono style: {e}")

async def method2_edit_caption(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    new_caption = update.message.text.strip()

    if "Key -" not in new_caption:
        await update.message.reply_text(
            "❌ *Invalid Caption!*\n\nMust contain `Key -` placeholder.",
            parse_mode="Markdown"
        )
        return

    # Save caption
    USER_DATA[str(user_id)] = USER_DATA.get(str(user_id), {})
    USER_DATA[str(user_id)]["caption"] = new_caption
    save_config()

    USER_STATE[user_id]["status"] = "normal"
    USER_STATE[user_id]["quote_applied"] = False
    USER_STATE[user_id]["mono_applied"] = False

    preview_message_id = USER_STATE.get(user_id, {}).get("preview_message_id")
    key = USER_STATE.get(user_id, {}).get("saved_key", "")
    session_files = USER_STATE.get(user_id, {}).get("session_files", [])

    if not preview_message_id or not key or not session_files:
        await update.message.reply_text(
            "⚠️ *No active session found!*",
            parse_mode="Markdown"
        )
        return

    text = "✅ *New Caption Saved!*\n\n"
    for idx, _ in enumerate(session_files, start=1):
        text += f"📦 APK {idx}: Key - {key}\n"

    buttons = [
        [InlineKeyboardButton("🔙 Back", callback_data="method2_back_fullmenu")]
    ]

    try:
        await context.bot.edit_message_text(
            chat_id=user_id,
            message_id=preview_message_id,
            text=text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    except Exception as e:
        print(f"Error after Edit Caption: {e}")

async def method2_show_preview(user_id, context: ContextTypes.DEFAULT_TYPE):
    state = USER_STATE.get(user_id, {})
    user_info = USER_DATA.get(str(user_id), {})
    preview_message_id = state.get("preview_message_id")
    saved_caption = user_info.get("caption", "")
    key = state.get("saved_key", "")
    session_files = state.get("session_files", [])

    if not preview_message_id or not key or not session_files:
        await context.bot.send_message(
            chat_id=user_id,
            text="⚠️ *No session or key found!*",
            parse_mode="Markdown"
        )
        return

    text = "👁️ *Preview*\n\n"
    final_caption = saved_caption.replace("Key -", f"Key - {key}")

    for idx, _ in enumerate(session_files, start=1):
        text += f"📦 APK {idx}: {final_caption}\n"

    buttons = [
        [InlineKeyboardButton("🔙 Back", callback_data="method2_back_fullmenu")]
    ]

    try:
        await context.bot.edit_message_text(
            chat_id=user_id,
            message_id=preview_message_id,
            text=text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    except Exception as e:
        print(f"Error showing preview: {e}")

def build_method2_buttons(user_id):
    state = USER_STATE.get(user_id, {})
    
    buttons = [
        [InlineKeyboardButton("✅ Yes", callback_data="method2_yes"),
         InlineKeyboardButton("❌ No", callback_data="method2_no")]
    ]

    quote_applied = state.get("quote_applied", False)
    mono_applied = state.get("mono_applied", False)

    row = []

    if not quote_applied:
        row.append(InlineKeyboardButton("✍️ Quote Key", callback_data="method2_quote"))

    if not mono_applied:
        row.append(InlineKeyboardButton("🔤 Normal Key", callback_data="method2_mono"))

    if row:
        buttons.append(row)

    buttons.append([
        InlineKeyboardButton("📝 Edit Caption", callback_data="method2_edit"),
        InlineKeyboardButton("👁️ Show Preview", callback_data="method2_preview")
    ])

    return InlineKeyboardMarkup(buttons)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    
    state = USER_STATE.get(user_id, {})
    preview_message_id = state.get("preview_message_id")
    
    # --- Cooldown Anti Spam ---
    now = time.time()
    if not hasattr(context, "user_cooldowns"):
        context.user_cooldowns = {}
    if user_id in context.user_cooldowns and now - context.user_cooldowns[user_id] < 1:
        await query.answer("⌛ Wait a second...", show_alert=False)
        return
    context.user_cooldowns[user_id] = now

    # --- Help Buttons Handling ---
    if data == "help_next":
        keyboard = [
            [InlineKeyboardButton("⬅️ Back", callback_data="help_back")]
        ]
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
        keyboard = [
            [InlineKeyboardButton("➡️ Next", callback_data="help_next")]
        ]
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

    # --- Check user session ---
    if user_id not in USER_STATE:
        await query.edit_message_text(
            "⏳ *Session expired or invalid!* ❌\nPlease restart using /start.",
            parse_mode="Markdown"
        )
        return

    state = USER_STATE[user_id]
    channel_id = USER_DATA.get(str(user_id), {}).get("channel")

    # --- Set Channel or Caption ---
    if data == "set_channel":
        USER_STATE[user_id]["status"] = "waiting_channel"
        await query.edit_message_text(
            "📡 *Please send your Channel ID now!* Example: `@yourchannel` or `-100xxxxxxxxxx`",
            parse_mode="Markdown"
        )
        return

    if data == "set_caption":
        USER_STATE[user_id]["status"] = "waiting_caption"
        await query.edit_message_text(
            "📝 *Please send your Caption now!* Must contain: `Key -`",
            parse_mode="Markdown"
        )
        return

    # --- Method 1 Selected ---
    if data == "method_1":
        USER_STATE[user_id]["current_method"] = "method1"
        USER_STATE[user_id]["status"] = "normal"

        buttons = [
            [InlineKeyboardButton("🌟 Bot Admin", url="https://t.me/TrailKeyHandlerBOT?startchannel=true")],
            [InlineKeyboardButton("📡 Set Channel", callback_data="set_channel")],
            [InlineKeyboardButton("📝 Set Caption", callback_data="set_caption")]
        ]

        if channel_id and USER_DATA.get(str(user_id), {}).get("caption"):
            buttons.append([InlineKeyboardButton("📤 Send One APK", callback_data="send_apk_method1")])

        buttons.append([InlineKeyboardButton("🔙 Back to Methods", callback_data="back_to_methods")])

        await query.edit_message_text(
            "✅ *Method 1 Selected!*\n\nManual key capture system activated.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    # --- Method 2 Selected ---
    if data == "method_2":
        USER_STATE[user_id]["current_method"] = "method2"
        USER_STATE[user_id]["status"] = "normal"

        buttons = [
            [InlineKeyboardButton("🌟 Bot Admin", url="https://t.me/TrailKeyHandlerBOT?startchannel=true")],
            [InlineKeyboardButton("📡 Set Channel", callback_data="set_channel")],
            [InlineKeyboardButton("📝 Set Caption", callback_data="set_caption")]
        ]

        if channel_id and USER_DATA.get(str(user_id), {}).get("caption"):
            buttons.append([InlineKeyboardButton("📤 Send 2-3 APKs", callback_data="send_apk_method2")])

        buttons.append([InlineKeyboardButton("🔙 Back to Methods", callback_data="back_to_methods")])

        await query.edit_message_text(
            "✅ *Method 2 Selected!*\n\nMulti APK Upload system activated.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    # --- Method 2 Confirmations ---
    if data == "method2_yes":
        await method2_send_to_channel(user_id, context)
        return

    if data == "method2_no":
        USER_STATE[user_id]["session_files"] = []
        await query.edit_message_text("❌ *Session canceled!*", parse_mode="Markdown")
        return

    if data == "method2_quote":
        await method2_convert_quote(user_id, context)
        return
    
    if data == "method2_mono":
        await method2_convert_mono(user_id, context)
        return

    if data == "method2_edit":
        USER_STATE[user_id]["status"] = "waiting_new_caption"
        await query.edit_message_text(
            "📝 *Send new Caption now!* (Must include `Key -`)",
            parse_mode="Markdown"
        )
        return

    if data == "method2_preview":
        await method2_show_preview(user_id, context)
        return

    # --- Back to Methods ---
    if data == "back_to_methods":
        USER_STATE[user_id]["current_method"] = None
        USER_STATE[user_id]["status"] = "selecting_method"

        keyboard = [
            [InlineKeyboardButton("⚡ Method 1", callback_data="method_1")],
            [InlineKeyboardButton("🚀 Method 2", callback_data="method_2")]
        ]

        await query.edit_message_text(
            "🔄 *Method Selection Reset!*\n\nPlease select again:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
        
    if data == "delete_apk_post":
        apk_posts = USER_STATE.get(user_id, {}).get("apk_posts", [])
    
        keyboard = []
        for idx, _ in enumerate(apk_posts):
            keyboard.append([InlineKeyboardButton(f"🗑️ Delete APK {idx+1}", callback_data=f"delete_apk_{idx+1}")])
    
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back_to_manage_post")])
    
        await context.bot.edit_message_text(
            chat_id=user_id,
            message_id=USER_STATE[user_id]["preview_message_id"],
            text="🗑️ *Select which APK you want to delete:*",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    if data == "back_to_manage_post":
        buttons = [
            [InlineKeyboardButton("📄 View Last Post", url=USER_STATE[user_id]["last_post_link"])],
            [InlineKeyboardButton("🗑️ Delete APK Post", callback_data="delete_apk_post")],
            [InlineKeyboardButton("🔙 Back to Methods", callback_data="back_to_methods")]
        ]
    
        await context.bot.edit_message_text(
            chat_id=user_id,
            message_id=USER_STATE[user_id]["preview_message_id"],
            text="✅ *Manage your posted APKs:*",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return
        
    if data.startswith("delete_apk_"):
        apk_number = int(data.split("_")[-1])
        apk_posts = USER_STATE.get(user_id, {}).get("apk_posts", [])
        channel_id = USER_DATA.get(str(user_id), {}).get("channel")
    
        if apk_number <= len(apk_posts):
            msg_id = apk_posts[apk_number - 1]
    
            try:
                await context.bot.delete_message(chat_id=channel_id, message_id=msg_id)
            except Exception as e:
                print(f"Delete failed: {e}")
    
            # Remove deleted
            apk_posts[apk_number - 1] = None
            apk_posts = [m for m in apk_posts if m]
            USER_STATE[user_id]["apk_posts"] = apk_posts
    
            if not apk_posts:
                # All posts deleted
                USER_STATE[user_id]["session_files"] = []
                USER_STATE[user_id]["saved_key"] = None
                USER_STATE[user_id]["apk_posts"] = []
                USER_STATE[user_id]["last_apk_time"] = None
                USER_STATE[user_id]["waiting_key"] = False
                USER_STATE[user_id]["preview_message_id"] = None
    
                await context.bot.edit_message_text(
                    chat_id=user_id,
                    message_id=query.message.message_id,
                    text="✅ *All APKs deleted!*\nNew season started.",
                    parse_mode="Markdown"
                )
                return
    
            # If posts remaining, show delete menu again
            keyboard = []
            for idx, _ in enumerate(apk_posts):
                keyboard.append([InlineKeyboardButton(f"🗑️ Delete APK {idx+1}", callback_data=f"delete_apk_{idx+1}")])
    
            keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back_to_manage_post")])
    
            await context.bot.edit_message_text(
                chat_id=user_id,
                message_id=query.message.message_id,
                text=f"✅ *Deleted APK {apk_number} Successfully!*\nSelect another to delete:",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return
    
    if data == "method2_back_fullmenu":
        preview_message_id = USER_STATE.get(user_id, {}).get("preview_message_id")
        key = USER_STATE.get(user_id, {}).get("saved_key", "")
        session_files = USER_STATE.get(user_id, {}).get("session_files", [])
    
        if not preview_message_id or not key or not session_files:
            await query.edit_message_text(
                text="⚠️ *Session expired or not found!*",
                parse_mode="Markdown"
            )
            return
    
        text = "🔖 *Key captured!*\n\nChoose what you want to do next:"
    
        try:
            await context.bot.edit_message_text(
                chat_id=user_id,
                message_id=preview_message_id,
                text=text,
                parse_mode="Markdown",
                reply_markup=build_method2_buttons(user_id)
            )
        except Exception as e:
            print(f"Error going back to Full Menu: {e}")
    
# Setup 1 - Set Source Channel
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
