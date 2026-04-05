import os
import json
import asyncio
import logging
from pathlib import Path
from telethon import TelegramClient, events, Button
from telethon.tl.types import (
    ChannelParticipantAdmin,
    ChannelParticipantCreator,
    ChannelParticipantsAdmins,
)
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.errors import UserNotParticipantError, ChatAdminRequiredError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - [%(levelname)s] - %(message)s",
)
logger = logging.getLogger(__name__)

API_ID = int(os.environ.get("TELEGRAM_API_ID", "0"))
API_HASH = os.environ.get("TELEGRAM_API_HASH", "")
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
BOT_OWNER_ID = int(os.environ.get("BOT_OWNER_ID", "0"))

if not API_ID or not API_HASH or not BOT_TOKEN or not BOT_OWNER_ID:
    logger.error("Missing required environment variables.")
    exit(1)

DATA_DIR = Path("telegram-bot/data")
DATA_DIR.mkdir(parents=True, exist_ok=True)
USERS_FILE = DATA_DIR / "users.json"
SUDO_FILE = DATA_DIR / "sudo_users.json"
GROUPS_FILE = DATA_DIR / "groups.json"


def load_json(path: Path, default):
    if path.exists():
        try:
            with open(path) as f:
                return json.load(f)
        except Exception:
            pass
    return default


def save_json(path: Path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


# users: {user_id: {id, first_name, username}}
users_db: dict = load_json(USERS_FILE, {})
# sudo_users: {chat_id: [user_id, ...]}
sudo_db: dict = load_json(SUDO_FILE, {})
# groups: {chat_id: {id, title}}
groups_db: dict = load_json(GROUPS_FILE, {})

spam_chats = []

client = TelegramClient("telegram-bot/tagall_bot", API_ID, API_HASH)


def save_user(user):
    uid = str(user.id)
    users_db[uid] = {
        "id": user.id,
        "first_name": user.first_name or "",
        "username": user.username or "",
    }
    save_json(USERS_FILE, users_db)


def save_group(chat):
    cid = str(chat.id)
    groups_db[cid] = {
        "id": chat.id,
        "title": getattr(chat, "title", "Unknown Group"),
    }
    save_json(GROUPS_FILE, groups_db)


def is_owner(user_id: int) -> bool:
    return user_id == BOT_OWNER_ID


async def is_group_owner(chat_id, user_id: int) -> bool:
    try:
        result = await client(GetParticipantRequest(chat_id, user_id))
        return isinstance(result.participant, ChannelParticipantCreator)
    except Exception:
        return False


async def is_admin_or_sudo(chat_id, user_id: int) -> bool:
    # Check sudo list for this chat
    chat_sudo = sudo_db.get(str(chat_id), [])
    if user_id in chat_sudo:
        return True
    # Check actual admin
    try:
        result = await client(GetParticipantRequest(chat_id, user_id))
        return isinstance(
            result.participant,
            (ChannelParticipantAdmin, ChannelParticipantCreator),
        )
    except UserNotParticipantError:
        return False
    except Exception:
        return False


async def send_in_batches(chat_id, mentions: list, reply_to: int, extra_text: str = ""):
    BATCH = 5
    for i in range(0, len(mentions), BATCH):
        if chat_id not in spam_chats:
            break
        batch = mentions[i : i + BATCH]
        msg = " ".join(batch)
        if extra_text:
            msg += f"\n\n{extra_text}"
        await client.send_message(chat_id, msg, reply_to=reply_to)
        if i + BATCH < len(mentions):
            await asyncio.sleep(2)


# ─── /start ──────────────────────────────────────────────────────────────────

START_BUTTONS = [
    [Button.url("😈𝙾𝙽𝚆𝙴𝚁😈", "http://t.me/mrdevil12")],
    [Button.url("🔥𝚄𝙿𝙳𝙰𝚃𝙴 𝙲𝙷𝙰𝙽𝙽𝙴𝙻🔥", "https://t.me/devilbots971")],
    [Button.url("🔥𝚂𝚄𝙿𝙿𝙾𝚁𝚃 𝙶𝚁𝙾𝚄𝙿🔥", "https://t.me/devilbotsupport")],
]

@client.on(events.NewMessage(pattern=r"^/start"))
async def cmd_start(event):
    if event.sender:
        save_user(event.sender)

    if not event.is_private:
        return await event.respond("👋 DM me /start to get started.")

    first_name = event.sender.first_name if event.sender else "User"
    caption = (
        f"ĐɆVłⱠ Ӿ ₥Ɇ₦₮łØ₦\n"
        f"             𝐇𝐎𝐖 𝐀𝐑𝐄 𝐘𝐎𝐔 **__`{first_name}`__**,\n\n\n\n"
        f"ʜᴇʏ — ᴛʜɪꜱ ɪꜱ ᴀ ᴍᴇɴᴛɪᴏɴ ʙᴏᴛ\n\n"
        f"ᴛʜɪꜱ ʙᴏᴛ ᴀʟʟᴏᴡꜱ ʏᴏᴜ ᴛᴏ ᴛᴀɢ ᴀʟʟ ᴍᴇᴍʙᴇʀꜱ ᴀɴᴅ ᴍᴇɴᴛɪᴏɴ ᴀᴅᴍɪɴꜱ ꜱᴇᴘᴀʀᴀᴛᴇʟʏ\n\n"
        f"ᴛʏᴘᴇ /help ᴛᴏ ᴠɪᴇᴡ ᴀʟʟ ᴀᴠᴀɪʟᴀʙʟᴇ ᴄᴏᴍᴍᴀɴᴅꜱ\n\n\n"
        f"🖥 𝚃𝙷𝙸𝚂 𝙱𝙾𝚃 𝙸𝚂 𝙲𝚁𝙴𝙰𝚃𝙴𝙳 𝙱𝚈 [𝙈𝙍 𝘿𝙀𝙑𝙄𝙻](http://t.me/mrdevil12)\n"
        f"𝙵𝙾𝚁 𝚄𝙿𝙳𝙰𝚃𝙴 𝙹𝙾𝙸𝙽 𝙾𝚄𝚁 𝙲𝙷𝙰𝙽𝙽𝙴𝙻  [𝘿𝙀𝙑𝙄𝙻 𝘽𝙾𝚃'𝚂](https://t.me/devilbots971)"
    )
    await client.send_file(
        event.chat_id,
        "https://files.catbox.moe/0b934c.jpg",
        caption=caption,
        buttons=START_BUTTONS,
        reply_to=event.id,
        link_preview=False,
    )


# ─── /help ────────────────────────────────────────────────────────────────────

@client.on(events.NewMessage(pattern=r"^/help"))
async def cmd_help(event):
    if event.sender:
        save_user(event.sender)

    if not event.is_private:
        return await event.respond("👋 DM me /help to see all commands.")

    is_own = is_owner(event.sender_id)
    owner_cmds = (
        "\n\n👑 **Owner Commands**\n"
        "`/broadcast <message>` — Send a message to all bot users\n"
        "`/users` — List all users who have interacted with the bot"
        if is_own
        else ""
    )

    await event.reply(
        "👋 **ᴅᴇᴠɪʟ x ᴍᴇɴᴛɪᴏɴ ʙᴏᴛ**\n\n"
        "Add the bot to your group and grant administrator permissions to enable all features.\n\n"
        "👥 **Member Tagging**\n"
        "`/all` or `@all` or `/tagall` — Tag all group members\n"
        "`/admin` or `/tagadmin` — Tag all administrators\n"
        "`/cancel` — Stop an active tagging process\n\n"
        "🔐 **Group Owner Commands**\n"
        "`/addsudo <user_id>` — Grant tagging permission to a user\n"
        "`/desudo <user_id>` — Revoke tagging permission\n"
        "`/sudolist` — View all authorized users"
        + owner_cmds
        + "\n\n💡 **Tip**\nUse `/all Good morning!` to tag all members with a custom message."
    )


# ─── /cancel ─────────────────────────────────────────────────────────────────

@client.on(events.NewMessage(pattern=r"^/cancel$"))
async def cmd_cancel(event):
    if event.is_private:
        return
    chat_id = event.chat_id
    if chat_id not in spam_chats:
        return await event.respond("There is no ongoing process to cancel.")
    spam_chats.remove(chat_id)
    await event.respond("✅ Stopped.")


# ─── /addsudo ────────────────────────────────────────────────────────────────

@client.on(events.NewMessage(pattern=r"^/addsudo ?(.*)"))
async def cmd_addsudo(event):
    if event.is_private:
        return await event.respond("This command works in groups only.")
    if event.sender:
        save_user(event.sender)

    if not await is_group_owner(event.chat_id, event.sender_id):
        return await event.respond("⛔ Only the group owner can add sudo users.")

    arg = event.pattern_match.group(1).strip()
    if not arg or not arg.lstrip("-").isdigit():
        return await event.respond(
            "Usage: `/addsudo <user_id>`\nExample: `/addsudo 123456789`"
        )

    target_id = int(arg)
    chat_key = str(event.chat_id)
    if chat_key not in sudo_db:
        sudo_db[chat_key] = []

    if target_id in sudo_db[chat_key]:
        return await event.respond(f"User `{target_id}` is already a sudo user.")

    sudo_db[chat_key].append(target_id)
    save_json(SUDO_FILE, sudo_db)
    await event.respond(
        f"✅ User `{target_id}` has been granted tagging permission in this group."
    )
    logger.info(f"Added sudo user {target_id} in chat {event.chat_id}")


# ─── /desudo ─────────────────────────────────────────────────────────────────

@client.on(events.NewMessage(pattern=r"^/desudo ?(.*)"))
async def cmd_desudo(event):
    if event.is_private:
        return await event.respond("This command works in groups only.")
    if event.sender:
        save_user(event.sender)

    if not await is_group_owner(event.chat_id, event.sender_id):
        return await event.respond("⛔ Only the group owner can remove sudo users.")

    arg = event.pattern_match.group(1).strip()
    if not arg or not arg.lstrip("-").isdigit():
        return await event.respond(
            "Usage: `/desudo <user_id>`\nExample: `/desudo 123456789`"
        )

    target_id = int(arg)
    chat_key = str(event.chat_id)
    sudo_list = sudo_db.get(chat_key, [])

    if target_id not in sudo_list:
        return await event.respond(f"User `{target_id}` is not a sudo user.")

    sudo_list.remove(target_id)
    sudo_db[chat_key] = sudo_list
    save_json(SUDO_FILE, sudo_db)
    await event.respond(
        f"✅ Tagging permission removed from user `{target_id}`."
    )
    logger.info(f"Removed sudo user {target_id} in chat {event.chat_id}")


# ─── /sudolist ────────────────────────────────────────────────────────────────

@client.on(events.NewMessage(pattern=r"^/sudolist$"))
async def cmd_sudolist(event):
    if event.is_private:
        return await event.respond("This command works in groups only.")

    chat_key = str(event.chat_id)
    sudo_list = sudo_db.get(chat_key, [])

    if not sudo_list:
        return await event.respond("No sudo users in this group.")

    lines = [f"🔐 **Sudo users in this group:**"]
    for uid in sudo_list:
        lines.append(f"• `{uid}`")
    await event.respond("\n".join(lines))


# ─── /users (owner only, private) ────────────────────────────────────────────

@client.on(events.NewMessage(pattern=r"^/users$"))
async def cmd_users(event):
    if not event.is_private:
        return
    if not is_owner(event.sender_id):
        return await event.respond("⛔ This command is for the bot owner only.")

    if not users_db and not groups_db:
        return await event.respond("No users or groups have used this bot yet.")

    lines = [f"👥 **Total users: {len(users_db)}** | 🏘 **Groups: {len(groups_db)}**\n"]

    if groups_db:
        lines.append("**Groups:**")
        for cid, info in groups_db.items():
            lines.append(f"• {info.get('title', 'Unknown')} (`{cid}`)")
        lines.append("")

    if users_db:
        lines.append("**Users:**")
        for uid, info in users_db.items():
            name = info.get("first_name", "Unknown")
            username = f"@{info['username']}" if info.get("username") else "no username"
            lines.append(f"• [{name}](tg://user?id={uid}) — {username} (`{uid}`)")

    # Split if too long
    text = "\n".join(lines)
    if len(text) > 4000:
        chunks = []
        current = lines[0] + "\n"
        for line in lines[1:]:
            if len(current) + len(line) + 1 > 4000:
                chunks.append(current)
                current = line + "\n"
            else:
                current += line + "\n"
        if current:
            chunks.append(current)
        for chunk in chunks:
            await event.respond(chunk)
    else:
        await event.respond(text)


# ─── /broadcast (owner only) ─────────────────────────────────────────────────

@client.on(events.NewMessage(pattern=r"^/broadcast (.+)"))
async def cmd_broadcast(event):
    if not is_owner(event.sender_id):
        return

    message = event.pattern_match.group(1).strip()
    if not message:
        return await event.respond("Usage: `/broadcast <your message>`")

    total = len(users_db) + len(groups_db)
    if total == 0:
        return await event.respond("No users or groups to broadcast to yet.")

    await event.respond(
        f"📢 Broadcasting to {len(users_db)} users and {len(groups_db)} groups..."
    )

    sent = 0
    failed = 0
    broadcast_text = f"📢 **Message from bot owner:**\n\n{message}"

    # Send to private users
    for uid in list(users_db.keys()):
        try:
            await client.send_message(int(uid), broadcast_text)
            sent += 1
            await asyncio.sleep(0.3)
        except Exception as e:
            logger.warning(f"Failed to broadcast to user {uid}: {e}")
            failed += 1

    # Send to groups
    for cid, info in list(groups_db.items()):
        try:
            await client.send_message(int(cid), broadcast_text)
            sent += 1
            await asyncio.sleep(0.3)
        except Exception as e:
            logger.warning(f"Failed to broadcast to group {cid} ({info.get('title')}): {e}")
            failed += 1

    await event.respond(
        f"✅ Broadcast complete!\n"
        f"• Delivered: {sent}\n"
        f"• Failed: {failed}\n"
        f"• Users: {len(users_db)} | Groups: {len(groups_db)}"
    )
    logger.info(f"Broadcast sent: {sent} delivered, {failed} failed")


# ─── /all ────────────────────────────────────────────────────────────────────

@client.on(
    events.NewMessage(
        pattern=r"^(\/(all|tagall)|@all)(\s+[\s\S]*)?$",
        incoming=True,
    )
)
async def cmd_all(event):
    if event.is_private:
        return await event.respond("This command works in groups only.")
    if event.sender:
        save_user(event.sender)

    chat_id = event.chat_id

    if not await is_admin_or_sudo(chat_id, event.sender_id):
        return await event.respond("⛔ Only admins (or sudo users) can use this command.")

    extra_text = (event.pattern_match.group(3) or "").strip()
    reply_to = event.reply_to_msg_id or event.id

    spam_chats.append(chat_id)
    mentions = []

    try:
        async for user in client.iter_participants(chat_id):
            if chat_id not in spam_chats:
                break
            if user.bot:
                continue
            if user.username:
                mentions.append(f"@{user.username}")
            else:
                mentions.append(f"[{user.first_name}](tg://user?id={user.id})")

        if not mentions:
            await event.respond("❌ No members found. Make sure I'm an admin with member access.")
        else:
            await send_in_batches(chat_id, mentions, reply_to, extra_text)

    except ChatAdminRequiredError:
        await event.respond("❌ I need to be an admin with member access to tag everyone.")
    except Exception as e:
        logger.error(f"Error in /all: {e}")
        await event.respond("❌ Something went wrong. Make sure I'm an admin.")

    if chat_id in spam_chats:
        spam_chats.remove(chat_id)
    logger.info(f"Tagged {len(mentions)} members in chat {chat_id}")


# ─── /admin ──────────────────────────────────────────────────────────────────

@client.on(
    events.NewMessage(
        pattern=r"^\/(admin|tagadmin|admins|tagadmins)(\s+[\s\S]*)?$",
        incoming=True,
    )
)
async def cmd_admin(event):
    if event.is_private:
        return await event.respond("This command works in groups only.")
    if event.sender:
        save_user(event.sender)

    chat_id = event.chat_id

    if not await is_admin_or_sudo(chat_id, event.sender_id):
        return await event.respond("⛔ Only admins (or sudo users) can use this command.")

    extra_text = (event.pattern_match.group(2) or "").strip()
    reply_to = event.reply_to_msg_id or event.id

    spam_chats.append(chat_id)
    mentions = []

    try:
        async for user in client.iter_participants(chat_id, filter=ChannelParticipantsAdmins):
            if chat_id not in spam_chats:
                break
            if user.bot:
                continue
            if user.username:
                mentions.append(f"@{user.username}")
            else:
                mentions.append(f"[{user.first_name}](tg://user?id={user.id})")

        if not mentions:
            await event.respond("No admins found to tag.")
        else:
            await send_in_batches(chat_id, mentions, reply_to, extra_text)

    except ChatAdminRequiredError:
        await event.respond("❌ I need to be an admin with member access.")
    except Exception as e:
        logger.error(f"Error in /admin: {e}")
        await event.respond("❌ Something went wrong. Make sure I'm an admin.")

    if chat_id in spam_chats:
        spam_chats.remove(chat_id)
    logger.info(f"Tagged {len(mentions)} admins in chat {chat_id}")


# ─── Track users and groups ───────────────────────────────────────────────────

@client.on(events.NewMessage(incoming=True))
async def track_users_and_groups(event):
    if event.is_private and event.sender:
        save_user(event.sender)
    elif not event.is_private:
        # Track this group
        try:
            chat = await event.get_chat()
            if chat:
                save_group(chat)
        except Exception:
            pass
        # Also track the sender
        if event.sender:
            save_user(event.sender)


@client.on(events.ChatAction())
async def track_group_join(event):
    """Track group when bot is added to it."""
    try:
        me = await client.get_me()
        if event.user_added and me.id in [u.id for u in (event.users or [])]:
            chat = await event.get_chat()
            if chat:
                save_group(chat)
                logger.info(f"Bot added to group: {getattr(chat, 'title', chat.id)}")
    except Exception:
        pass


# ─── Main ─────────────────────────────────────────────────────────────────────

async def main():
    await client.start(bot_token=BOT_TOKEN)
    me = await client.get_me()
    logger.info(f"TagAll bot started as @{me.username}")
    logger.info(f"Owner ID: {BOT_OWNER_ID}")
    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())
