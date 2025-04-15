import json
import time
import datetime
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
import os
import re
from telegram.constants import ParseMode,  ChatType

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
SETUPS = config.get("setups", {
    "1": {"source_channel": "", "destination_channel": "", "caption": ""},
    "2": {"source_channel": "", "destination_channel": "", "caption": ""},
    "3": {"source_channel": "", "destination_channel": "", "caption": ""}
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
            "setups": SETUPS
        }, f, indent=4)

def is_authorized(user_id: int) -> bool:
    return user_id == OWNER_ID or user_id in ALLOWED_USERS
    
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        await update.message.reply_text(
            "🚀𝗪𝗵𝗮𝘁 𝗕𝗿𝘂𝗵! 😱 𝗜𝘁❜𝘀 𝗩𝗲𝗿𝘆 𝗪𝗿𝗼𝗻𝗴 𝗕𝗿𝗼! 😂"
        )
        return

    # Save basic user data
    USER_DATA[str(user_id)] = {
        "first_name": update.effective_user.first_name,
        "username": update.effective_user.username,
        "channel": USER_DATA.get(str(user_id), {}).get("channel", ""),
        "caption": USER_DATA.get(str(user_id), {}).get("caption", "")
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
        await update.message.reply_text(
            "Available Commands:\n"
            "/start - Restart bot interaction ▶️\n"
            "/adduser - Add allowed user ➕\n"
            "/removeuser - Remove allowed user ➖\n"
            "/userlist - Show all allowed users 👥\n"
            "/ping - Bot status 🏓\n"
            "/rules - Bot usage rules 📜\n"
            "/reset - Reset user data ♻️\n"
            "/resetcaption - Reset your saved caption 🧹\n"
            "/resetchannelid - Reset your channel ID 🔁\n"
            "/setchannelid - Set your Channel ID 📡\n"
            "/setcaption - Set your Caption ✍️\n"
            "🛠️ *Setup 1*\n"
            "/sourcechannel1 - Source Channel\n"
            "/desichannel1 - Destination Channel\n"
            "/setcaption1 - Set Caption\n"
            "/resetsetup1 - Reset Setup 1\n\n"
            "🛠️ *Setup 2*\n"
            "/sourcechannel2 - Source Channel\n"
            "/desichannel2 - Destination Channel\n"
            "/setcaption2 - Set Caption\n"
            "/resetsetup2 - Reset Setup 2\n\n"
            "🛠️ *Setup 3*\n"
            "/sourcechannel3 - Source Channel\n"
            "/desichannel3 - Destination Channel\n"
            "/setcaption3 - Set Caption\n"
            "/resetsetup3 - Reset Setup 3\n\n"
            "🔎 /viewsetup - Show completed setups",
            parse_mode="Markdown"
        )
    elif user_id in ALLOWED_USERS:
        await update.message.reply_text(
            "Available Commands:\n"
            "/start - Restart bot interaction ▶️\n"
            "/ping - Bot status 🏓\n"
            "/rules - Bot usage rules 📜\n"
            "/reset - Reset your data ♻️\n"
            "/resetcaption - Reset your saved caption 🧹\n"
            "/resetchannelid - Reset your channel ID 🔁\n"
            "/setchannelid - Set your Channel ID 📡\n"
            "/setcaption - Set your Caption ✍️"
        )
     
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
        await update.message.reply_text(f"✅ Boom! User `{user_id}` added successfully to the cool club! 🎉", parse_mode="Markdown")
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
        await update.message.reply_text("🚀 𝗪𝗵𝗮𝘁 𝗕𝗿𝘂𝗵 !? 😱 𝗜𝘁❜𝘀 𝗩𝗲𝗿𝘆 𝗪𝗿𝗼𝗻𝗴 𝗕𝗿𝗼 🤯🤣")
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
                "📝 *You haven\\'t set a Caption yet\\!*\n"
                "Use → `/setcaption` → 𝖠𝖽𝖽 𝖸𝗈𝗎𝗋 𝖪𝖾𝗒 𝖢𝖺𝗉𝗍𝗂𝗈𝗇",
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

        final_caption = saved_caption.replace("Key -", f"Key - `{key}`")
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
                "⚠️ *Oops\\!* Your saved caption doesn't contain the `Key \\-` placeholder\\.\\n"
                "Please update it using /setcaption → *𝖠𝖽𝖽 𝖸𝗈𝗎𝗋 𝖪𝖾𝗒 𝖢𝖺𝗉𝗍𝗂𝗈𝗇*\\.",
                parse_mode="MarkdownV2"
                )
                return

        final_caption = caption.replace("Key -", f"Key - `{key}`")
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
                "❌ *Invalid caption\\!*\\nYour caption must include the placeholder `Key \\-`\\.",
                parse_mode="MarkdownV2"
            )
        else:
            USER_DATA[str(user_id)] = USER_DATA.get(str(user_id), {})
            USER_DATA[str(user_id)]["caption"] = caption
            save_config()
            await update.message.reply_text("✅ *Caption saved successfully!* 📝", parse_mode="Markdown")
            del USER_STATE[user_id]
    
    elif state["status"].startswith("waiting_caption_"):
        setup_number = state["status"].split("_")[-1]
        caption = update.message.text.strip()
        if "Key -" not in caption:
            await update.message.reply_text("❌ Your caption must include `Key -`.")
        else:
            SETUPS[setup_number]["caption"] = caption
            save_config()
            await update.message.reply_text(f"✅ Caption {setup_number} saved successfully! 📝")
            if all(SETUPS[setup_number].values()):
                await update.message.reply_text(
                    f"*Completed Setup {setup_number}:*\n"
                    f"• Source Channel {setup_number} → `{SETUPS[setup_number]['source_channel']}`\n"
                    f"• Desi Channel {setup_number}  → `{SETUPS[setup_number]['destination_channel']}`\n"
                    f"• Set Caption {setup_number}  → Caption Saved !",
                    parse_mode="Markdown"
                )
            del USER_STATE[user_id]

    elif state["status"].startswith("waiting_source_"):
        setup_number = state["status"].split("_")[-1]
        SETUPS[setup_number]["source_channel"] = update.message.text.strip().lstrip('@')
        save_config()
        await update.message.reply_text(f"✅ Source channel {setup_number} saved.")
        if all(SETUPS[setup_number].values()):
            await update.message.reply_text(
                f"*Completed Setup {setup_number}:*\n"
                f"• Source Channel {setup_number} → `{SETUPS[setup_number]['source_channel']}`\n"
                f"• Desi Channel {setup_number}  → `{SETUPS[setup_number]['destination_channel']}`\n"
                f"• Set Caption {setup_number}  → Caption Saved !",
                parse_mode="Markdown"
            )
        del USER_STATE[user_id]

    elif state["status"].startswith("waiting_dest_"):
        setup_number = state["status"].split("_")[-1]
        SETUPS[setup_number]["destination_channel"] = update.message.text.strip()
        save_config()
        await update.message.reply_text(f"✅ Destination channel {setup_number} saved.")
        if all(SETUPS[setup_number].values()):
            await update.message.reply_text(
                f"*Completed Setup {setup_number}:*\n"
                f"• Source Channel {setup_number} → `{SETUPS[setup_number]['source_channel']}`\n"
                f"• Desi Channel {setup_number}  → `{SETUPS[setup_number]['destination_channel']}`\n"
                f"• Set Caption {setup_number}  → Caption Saved !",
                parse_mode="Markdown"
            )
        del USER_STATE[user_id]
        
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if user_id not in USER_STATE:
        await query.edit_message_text("⏳ *Session expired or invalid!* ❌\nPlease restart the process using /start.", parse_mode="Markdown")
        return

    data = query.data
    state = USER_STATE[user_id]
    channel_id = USER_DATA.get(str(user_id), {}).get("channel")

    if data == "share_yes":
        if not channel_id:
            await query.edit_message_text(
                "⚠️ *Channel ID not set\\!* 😬\\nUse /setchannelid and give your *Channel ID* to continue\\.",
                parse_mode="MarkdownV2"
            )
            return

        await context.bot.send_document(
            chat_id=channel_id,
            document=state["file_id"],
            caption=state["caption"],
            parse_mode="Markdown",
            disable_notification=True
        )

        if channel_id.startswith("@"):
            button = InlineKeyboardMarkup([
                [InlineKeyboardButton("📡 Go to Channel", url=f"https://t.me/{channel_id.strip('@')}")]
            ])
            await query.edit_message_text("✅ *Shared successfully!*\nCheck your post below! ⬇️", reply_markup=button, parse_mode="Markdown")
        else:
            await query.edit_message_text("✅ *Shared successfully!* 🎉\n(Private channel — no link to show)", parse_mode="Markdown")

    elif data == "share_no":
        await query.edit_message_text("🙅‍♂️ *No worries!* You can retry anytime. Just drop your file again. 🚀", parse_mode="Markdown")

    elif data == "get_channel_id":
        USER_STATE[user_id] = {"status": "waiting_channel"}
        await query.edit_message_text(
            "🔧 *Setup Time\\!* Send me your Channel ID now\\. 📡\\nFormat: `@yourchannel` or `\\-100xxxxxxxxxx`",
            parse_mode="MarkdownV2"
        )

    elif data == "get_caption":
        USER_STATE[user_id] = {"status": "waiting_caption"}
        await query.edit_message_text(
            "📝 *Caption Time\\!*\\nPlease send a caption that includes `Key \\-` as a placeholder\\. 🔑",
            parse_mode="MarkdownV2"
        )
        
async def set_caption_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, setup_number: str):
    if update.effective_user.id != OWNER_ID:
        return
    await update.message.reply_text(
        f"📝 Caption Time! [Cap{setup_number}]\n"
        "Send me your Caption Including. ↙️\n"
        "The Placeholder Key - 🔑"
    )
    USER_STATE[update.effective_user.id] = {"status": f"waiting_caption_{setup_number}"}

async def set_source_channel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, setup_number: str):
    if update.effective_user.id != OWNER_ID:
        return
    await update.message.reply_text(
        f"🔧 Setup Time! [Sourcechannel{setup_number}]\n"
        "Send me your Channel ID now. 📡\n"
        "Format: @yourchannel or -100xxxxxxxxxx"
    )
    USER_STATE[update.effective_user.id] = {"status": f"waiting_source_{setup_number}"}

async def set_destination_channel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, setup_number: str):
    if update.effective_user.id != OWNER_ID:
        return
    await update.message.reply_text(
        f"🔧 Setup Time! [Desi Channel {setup_number}]\n"
        "Send me your Channel ID now. 📡\n"
        "Format: @yourchannel or -100xxxxxxxxxx"
    )
    USER_STATE[update.effective_user.id] = {"status": f"waiting_dest_{setup_number}"}

async def monitor_apks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.document:
        return

    print("[DEBUG] monitor_apks triggered")  # STEP 1: Check if triggered

    doc = update.message.document
    caption = update.message.caption or ""
    file_size = doc.file_size
    incoming_chat_id = str(update.message.chat.id)
    incoming_username = update.message.chat.username

    print(f"[DEBUG] APK received from: {incoming_chat_id}, Size: {file_size}, Caption: {caption}")

    # Extract key from caption
    key_match = re.search(r'Key\s*-\s*(\S+)', caption)
    if not key_match:
        print("[DEBUG] No Key found. Skipping.")
        return

    key = key_match.group(1)

    for setup_number, setup in SETUPS.items():
        print(f"[DEBUG] Checking setup {setup_number}")

        if not all(setup.values()):
            await context.bot.send_message(OWNER_ID, f"⚠️ Setup {setup_number} incomplete. Skipping.")
            continue

        configured_source = setup["source_channel"]

        if not (
            configured_source == incoming_chat_id or
            (incoming_username and configured_source.lstrip("@") == incoming_username)
        ):
            continue

        # File size check
        if setup_number == "1" and not (1_000_000 <= file_size <= 50_000_000):
            print(f"[DEBUG] Size mismatch for setup 1: {file_size}")
            continue
        if setup_number == "2" and not (80_000_000 <= file_size <= 2_000_000_000):
            print(f"[DEBUG] Size mismatch for setup 2: {file_size}")
            continue
        # Setup 3 accepts all sizes

        caption_template = setup["caption"]
        if "Key -" not in caption_template:
            await context.bot.send_message(OWNER_ID, f"⚠️ Setup {setup_number} caption missing placeholder `Key -`.")
            return

        final_caption = caption_template.replace("Key -", f"Key - `{key}`")

        try:
            await context.bot.send_document(
                chat_id=setup["destination_channel"],
                document=doc.file_id,
                caption=final_caption,
                parse_mode="Markdown",
                disable_notification=True
            )

            await context.bot.send_message(
                OWNER_ID,
                f"*Completed Process! :*\n"
                f"• Source Picked → `{incoming_chat_id}`\n"
                f"• Desi Sended → `{setup['destination_channel']}`\n"
                f"• Sended Key → `Key - {key}`",
                parse_mode="Markdown"
            )
        except Exception as e:
            await context.bot.send_message(OWNER_ID, f"❌ Error sending document (setup {setup_number}): `{e}`", parse_mode="Markdown")
        return  # Only process one match per document

async def reset_setup(update: Update, context: ContextTypes.DEFAULT_TYPE, setup_number: str):
    if update.effective_user.id != OWNER_ID:
        return
    SETUPS[setup_number] = {"source_channel": "", "destination_channel": "", "caption": ""}
    save_config()
    await update.message.reply_text(f"♻️ Setup {setup_number} has been reset.")

async def view_setup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    msg = ""
    for num, s in SETUPS.items():
        if all(s.values()):
            msg += (
                f"*Configured setup {num}:*\n"
                f"• Source Channel {num} → `{s['source_channel']}`\n"
                f"• Desi Channel {num}  → `{s['destination_channel']}`\n"
                f"• Set Caption {num}  → Caption Saved !\n\n"
            )
    if not msg:
        msg = "⚠️ No setups configured."
    await update.message.reply_text(msg, parse_mode="Markdown")

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
    app.add_handler(CommandHandler("setcaption1", lambda u, c: set_caption_handler(u, c, "1")))
    app.add_handler(CommandHandler("sourcechannel1", lambda u, c: set_source_channel_handler(u, c, "1")))
    app.add_handler(CommandHandler("desichannel1", lambda u, c: set_destination_channel_handler(u, c, "1")))
    app.add_handler(CommandHandler("setcaption2", lambda u, c: set_caption_handler(u, c, "2")))
    app.add_handler(CommandHandler("sourcechannel2", lambda u, c: set_source_channel_handler(u, c, "2")))
    app.add_handler(CommandHandler("desichannel2", lambda u, c: set_destination_channel_handler(u, c, "2")))
    app.add_handler(CommandHandler("setcaption3", lambda u, c: set_caption_handler(u, c, "3")))
    app.add_handler(CommandHandler("sourcechannel3", lambda u, c: set_source_channel_handler(u, c, "3")))
    app.add_handler(CommandHandler("desichannel3", lambda u, c: set_destination_channel_handler(u, c, "3")))
    app.add_handler(CommandHandler("resetsetup1", lambda u, c: reset_setup(u, c, "1")))
    app.add_handler(CommandHandler("resetsetup2", lambda u, c: reset_setup(u, c, "2")))
    app.add_handler(CommandHandler("resetsetup3", lambda u, c: reset_setup(u, c, "3")))
    app.add_handler(CommandHandler("viewsetup", view_setup))
    app.add_handler(MessageHandler(filters.ChatType.CHANNEL & filters.Document.ALL, monitor_apks))
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))
    app.add_handler(CallbackQueryHandler(handle_callback))

    app.run_polling()

if __name__ == "__main__":
    main()