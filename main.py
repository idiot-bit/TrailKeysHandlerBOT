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

    keyboard = [
        [InlineKeyboardButton("Method 1", callback_data="choose_method1"),
         InlineKeyboardButton("Method 2", callback_data="choose_method2")]
    ]
    await update.message.reply_text(
        "Choose your Method!",
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

async def handle_method2_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    doc = update.message.document

    if not doc.file_name.endswith(".apk"):
        await update.message.reply_text("Only APKs allowed for Method 2!")
        return

    if "method2_season" not in USER_STATE[user_id]:
        USER_STATE[user_id]["method2_season"] = {
            "apks": [],
            "last_upload_time": time.time()
        }

    USER_STATE[user_id]["method2_season"]["apks"].append(doc.file_id)
    USER_STATE[user_id]["method2_season"]["last_upload_time"] = time.time()

    if len(USER_STATE[user_id]["method2_season"]["apks"]) >= 3:
        await ask_key_method2(update, context)
    else:
        await update.message.reply_text("✅ APK received. Send another one if you want (max 3 APKs).")

async def ask_key_method2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    keyboard = [
        [InlineKeyboardButton("✅ Yes", callback_data="method2_confirm_yes"),
         InlineKeyboardButton("❌ No", callback_data="method2_confirm_no")],
        [InlineKeyboardButton("📝 Quote Key", callback_data="method2_quote_key"),
         InlineKeyboardButton("📋 Mono Key", callback_data="method2_mono_key")],
        [InlineKeyboardButton("✍️ Edit Caption", callback_data="method2_edit_caption")],
        [InlineKeyboardButton("👀 Show Preview", callback_data="method2_show_preview")]
    ]

    await context.bot.send_message(
        chat_id=user_id,
        text="📦 APK(s) captured!\n\n🔑 Send Key for the season or edit options below:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_method2_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data

    if data == "method2_confirm_yes":
        # Finish upload and send to channel
        await query.edit_message_text("✅ Uploading to Channel... [code coming next step]")
    elif data == "method2_confirm_no":
        # Cancel season
        del USER_STATE[user_id]["method2_season"]
        await query.edit_message_text("❌ Season cancelled!")
    elif data == "method2_quote_key":
        await query.edit_message_text("🔲 Key will be quoted. [update caption logic]")
    elif data == "method2_mono_key":
        await query.edit_message_text("⌨️ Key will be monospace. [update caption logic]")
    elif data == "method2_edit_caption":
        USER_STATE[user_id]["status"] = "waiting_caption_edit_method2"
        await query.edit_message_text("Send new caption including 'Key -' placeholder 📝")
    elif data == "method2_show_preview":
        await query.edit_message_text("👀 Preview coming soon [Preview Logic]")

    if data == "method2_quote_key":
        USER_STATE[user_id]["method2_season"]["key_style"] = "quote"
        await query.edit_message_text("✅ Key will now be formatted as <blockquote>Quoted Key</blockquote>.\nContinue sending APKs or Edit caption if needed.")
        return

    if data == "method2_mono_key":
        USER_STATE[user_id]["method2_season"]["key_style"] = "mono"
        await query.edit_message_text("✅ Key will now be formatted as <code>Monospaced Key</code>.\nContinue sending APKs or Edit caption if needed.")
        return
    
    if data == "method2_show_preview":
        season = USER_STATE[user_id].get("method2_season")
        if not season or not season.get("apks"):
            await query.edit_message_text("❌ No APKs found.")
            return

        total_apks = len(season["apks"])
        preview_text = f"📦 Total APKs Uploaded: {total_apks}\n"

        preview_text += "\nExample Caption Preview:\n"
        preview_text += "🔑 Key - YOUR_KEY_HERE\n"
        preview_text += "📝 Based on current settings (Quote/Mono/Plain)"

        keyboard = [
            [InlineKeyboardButton("✅ Yes", callback_data="method2_confirm_yes"),
             InlineKeyboardButton("❌ No", callback_data="method2_confirm_no")],
            [InlineKeyboardButton("📝 Quote Key", callback_data="method2_quote_key"),
             InlineKeyboardButton("📋 Mono Key", callback_data="method2_mono_key")],
            [InlineKeyboardButton("✍️ Edit Caption", callback_data="method2_edit_caption")]
        ]

        await query.edit_message_text(
            preview_text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Detect user method
    user_mode = USER_STATE.get(user_id, {}).get("mode")

    if user_mode == "method2":
        # Now handle Method 2 season logic
        await handle_method2_upload(update, context)
        return
    
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

    match = re.search(r'Key\s*-\s*(\S+)', caption)
    if match:
        key = match.group(1)

        user_info = USER_DATA.get(str(user_id), {})
        saved_caption = user_info.get("caption", "")
        channel_id = user_info.get("channel", "")

        if not saved_caption and not channel_id:
            await update.message.reply_text(
                "*First Setup Your Bot \\!\\!*\n\n"
                "Clicking 🎯\n"
                "📡 `/setchannelid` → 𝖺𝖽𝖽 𝖸𝗈𝗎𝗋 𝖢𝗁𝖺𝗇𝗇𝖾𝗅\n"
                "📝 `/setcaption` → 𝖠𝖽𝖽 𝖸𝗈𝗎𝗋 𝖪𝖾𝗒 𝖢𝖺𝗉𝗍𝗂𝗈𝗇\n\n"
                "*Setup Complete Then ↙️*\n"
                "🚀 *Share apk \\!\\!*",
                parse_mode="MarkdownV2"
            )
            return

        if not saved_caption:
            await update.message.reply_text(
                "📝 *Caption not found\\!*\\n"
                "Use → /setcaption → 𝖺𝖽𝖽 𝖸𝗈𝗎𝗋 𝖢𝖺𝗉𝗍𝗂𝗈𝗇",
                parse_mode="MarkdownV2"
            )
            return

        if not channel_id:
            await update.message.reply_text(
                "📡 *Channel ID not found\\!*\n"
                "Use → `/setchannelid` → 𝖺𝖽𝖽 𝖸𝗈𝗎𝗋 𝖢𝗁𝖺𝗇𝗇𝖾𝗅",
                parse_mode="MarkdownV2"
            )
            return

        final_caption = saved_caption.replace("Key -", f"Key - <code>{key}</code>")
        USER_STATE[user_id] = {
            "file_id": doc.file_id,
            "caption": final_caption,
            "status": "confirm_share"
        }
        await ask_to_share(update)

    else:
        # If key is not present in caption
        USER_STATE[user_id] = {
            "file_id": doc.file_id,
            "caption": "",
            "status": "waiting_key"
        }
        await update.message.reply_text("⏳ Send the key now !")

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
        caption = USER_DATA.get(str(user_id), {}).get("caption", "")
        
        if "Key -" not in caption:
            await update.message.reply_text(
                "📝 *Caption not found\\!*\\n"
                "Use → /setcaption → 𝖺𝖽𝖽 𝖸𝗈𝗎𝗋 𝖢𝖺𝗉𝗍𝗂𝗈𝗇",
                parse_mode="MarkdownV2"
            )
            return

        final_caption = caption.replace("Key -", f"Key - <code>{key}</code>")
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
        await update.message.reply_text(f"📡 *Channel ID saved:* `{channel_id}`", parse_mode="Markdown")
        del USER_STATE[user_id]

    elif state["status"] == "waiting_caption":
        caption = update.message.text.strip()
        if "Key -" not in caption:
            await update.message.reply_text(
                "❌ *Invalid caption*\n"
                "Your caption must include\n"
                "the placeholder `Key \\-`\\.",
                parse_mode="MarkdownV2"
            )
        else:
            USER_DATA[str(user_id)] = USER_DATA.get(str(user_id), {})
            USER_DATA[str(user_id)]["caption"] = caption
            save_config()
            await update.message.reply_text("✅ *Caption saved successfully!* 📝", parse_mode="Markdown")
            del USER_STATE[user_id]
    
    if state["status"] == "waiting_channel_method2":
        channel_id = update.message.text.strip()
        USER_DATA[str(user_id)] = USER_DATA.get(str(user_id), {})
        USER_DATA[str(user_id)]["method2_channel"] = channel_id
        save_config()
        await update.message.reply_text(f"✅ Method 2 Channel Saved: {channel_id}")
        del USER_STATE[user_id]
        return

    if state["status"] == "waiting_caption_method2":
        caption = update.message.text.strip()
        if "Key -" not in caption:
            await update.message.reply_text("❌ Caption must include `Key -` placeholder!")
        else:
            USER_DATA[str(user_id)] = USER_DATA.get(str(user_id), {})
            USER_DATA[str(user_id)]["method2_caption"] = caption
            save_config()
            await update.message.reply_text(f"✅ Method 2 Caption Saved!")
            del USER_STATE[user_id]
        return
    
    if state["status"] == "waiting_key_method2":
        key = update.message.text.strip()
        apks = USER_STATE[user_id]["method2_season"]["apks"]
        channel_id = USER_DATA.get(str(user_id), {}).get("method2_channel")
        caption_template = USER_DATA.get(str(user_id), {}).get("method2_caption")
    
        key_style = USER_STATE[user_id]["method2_season"].get("key_style", "default")
    
        if key_style == "quote":
            formatted_key = f"<blockquote>{key}</blockquote>"
        elif key_style == "mono":
            formatted_key = f"<code>{key}</code>"
        else:
            formatted_key = f"<code>{key}</code>"
    
        messages = []
        for idx, apk_file_id in enumerate(apks):
            if len(apks) == 1:
                caption = caption_template.replace("Key -", f"Key - {formatted_key}")
            elif len(apks) == 2 and idx == 0:
                caption = f"Key - {formatted_key}"
            elif len(apks) == 2 and idx == 1:
                caption = caption_template.replace("Key -", f"Key - {formatted_key}")
            elif len(apks) == 3 and idx < 2:
                caption = f"Key - {formatted_key}"
            else:
                caption = caption_template.replace("Key -", f"Key - {formatted_key}")
    
            sent = await context.bot.send_document(
                chat_id=channel_id,
                document=apk_file_id,
                caption=caption,
                parse_mode="HTML",
                disable_notification=True
            )
            messages.append(sent)
    
        # Send View Last Post button
        last_msg = messages[-1]
        if str(channel_id).startswith("@"):
            post_link = f"https://t.me/{channel_id.strip('@')}/{last_msg.message_id}"
        else:
            post_link = f"https://t.me/c/{str(channel_id)[4:]}/{last_msg.message_id}"
    
        keyboard = [
            [InlineKeyboardButton("🔗 View Last Post", url=post_link)],
            [InlineKeyboardButton("⬅️ Back to Methods", callback_data="back_to_methods")]
        ]
    
        await update.message.reply_text(
            "✅ All APKs sent successfully!",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # Clear season
    del USER_STATE[user_id]["method2_season"]
    del USER_STATE[user_id]["status"]
    return

# Another part, correct position
    if state["status"] == "waiting_caption_edit_method2":
        caption = update.message.text.strip()
        if "Key -" not in caption:
            await update.message.reply_text("❌ Caption must have 'Key -' placeholder! Try again.")
        else:
            USER_DATA[str(user_id)]["method2_caption"] = caption
            save_config()
            await update.message.reply_text("✅ New Caption saved for Method 2!")
            # Reset back to method2 menu
            USER_STATE[user_id]["status"] = None
            await ask_key_method2(update, context)
        return
    
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if data.startswith("method2_"):
        await handle_method2_buttons(update, context)
        return
    
    data = query.data

    # New: Handle Help Buttons FIRST
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

    # Now continue your old manual upload logic normally
    if user_id not in USER_STATE:
        await query.edit_message_text("⏳ *Session expired or invalid!* ❌\nPlease restart the process using /start.", parse_mode="Markdown")
        return

    data = query.data
    state = USER_STATE[user_id]
    channel_id = USER_DATA.get(str(user_id), {}).get("channel")

    if data == "share_yes":
        if not channel_id:
            await query.edit_message_text(
                "⚠️ <b>Channel ID not set!</b>\nUse <code>/setchannelid</code> to continue.",
                parse_mode="HTML"
            )
            return
    
        try:
            # Send document and store the message
            sent_msg = await context.bot.send_document(
                chat_id=channel_id,
                document=state["file_id"],
                caption=state["caption"],
                parse_mode="HTML",
                disable_notification=True
            )
    
            # Generate post link
            if channel_id.startswith("@"):
                post_link = f"https://t.me/{channel_id.strip('@')}/{sent_msg.message_id}"
            else:
                post_link = f"https://t.me/c/{channel_id.replace('-100', '')}/{sent_msg.message_id}"
    
            # Create button and send confirmation
            button = InlineKeyboardMarkup([
                [InlineKeyboardButton("📡 Go to Post", url=post_link)]
            ])
    
            await query.edit_message_text(
                "✅ <b>Shared successfully!</b>\nClick below to view the post ⬇️",
                reply_markup=button,
                parse_mode="HTML"
            )
    
        except Exception as e:
            await query.edit_message_text(
                f"❌ <b>Failed to send document:</b>\n<pre>{e}</pre>",
                parse_mode="HTML"
            )

    elif data == "share_no":
        await query.edit_message_text("🙅‍♂️ *No worries!* You can retry anytime. Just drop your .apk again. 🚀", parse_mode="Markdown")

    elif data == "get_channel_id":
        USER_STATE[user_id] = {"status": "waiting_channel"}
        await query.edit_message_text(
            "🔧 *Setup Time\\!*\n"
            "Send me your Channel ID now\\. 📡\n"
            "Format: `@yourchannel` or `\\-100xxxxxxxxxx`",
            parse_mode="MarkdownV2"
        )

    elif data == "get_caption":
        USER_STATE[user_id] = {"status": "waiting_caption"}
        await query.edit_message_text(
            "📝 *Caption Time\\!*\n"
            "Send me your Caption Including\\. ↙️\n"
            "The Placeholder `Key \\-` 🔑",
            parse_mode="MarkdownV2"
        )
        
    if data == "choose_method1":
        # Save user mode
        USER_STATE[user_id] = {"mode": "method1"}
        # Show Method 1 menu
        keyboard = [
            [InlineKeyboardButton("Bot Admin", url="https://t.me/TrailKeyHandlerBOT?startchannel=true")],
            [InlineKeyboardButton("Set Channel", callback_data="set_channel_method1")],
            [InlineKeyboardButton("Set Caption", callback_data="set_caption_method1")],
            [InlineKeyboardButton("Back to Methods", callback_data="back_to_methods")]
        ]
        await query.edit_message_text(
            "✨ Welcome to Method 1\nChoose an option:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    if data == "choose_method2":
        USER_STATE[user_id] = {"mode": "method2"}
        keyboard = [
            [InlineKeyboardButton("Bot Admin", url="https://t.me/TrailKeyHandlerBOT?startchannel=true")],
            [InlineKeyboardButton("Set Channel", callback_data="set_channel_method2")],
            [InlineKeyboardButton("Set Caption", callback_data="set_caption_method2")],
            [InlineKeyboardButton("Back to Methods", callback_data="back_to_methods")]
        ]
        await query.edit_message_text(
            "✨ Welcome to Method 2\nChoose an option:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    if data == "back_to_methods":
        keyboard = [
            [InlineKeyboardButton("Method 1", callback_data="choose_method1"),
             InlineKeyboardButton("Method 2", callback_data="choose_method2")]
        ]
        await query.edit_message_text(
            "Choose your Method!",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    if data == "set_channel_method2":
        USER_STATE[user_id] = {"status": "waiting_channel_method2"}
        await query.edit_message_text("Send your Channel ID for Method 2 📡")
        return

    if data == "set_caption_method2":
        USER_STATE[user_id] = {"status": "waiting_caption_method2"}
        await query.edit_message_text("Send your Caption with 'Key -' placeholder for Method 2 📝")
        return
    
    
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
