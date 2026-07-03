import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'NYRA'))

import logging
from aiogram import types
from logger_config import LOGGING_CHAT_ID


async def log_user_chat(user_message: types.Message, bot_reply: str):
    try:
        if user_message.chat.type == "private":
            return

        user_mention = f"<a href='tg://user?id={user_message.from_user.id}'>{user_message.from_user.full_name}</a>"

        if user_message.chat.username:
            chat_info = f"👥 Group: <b>{user_message.chat.title}</b> (@{user_message.chat.username})"
        else:
            try:
                invite_link = await user_message.bot.export_chat_invite_link(user_message.chat.id)
                chat_info = f"👥 Group: <b>{user_message.chat.title}</b>\n🔗 {invite_link}"
            except Exception:
                chat_info = f"👥 Group: <b>{user_message.chat.title}</b> | ID: <code>{user_message.chat.id}</code>"

        log_text = (
            f"💬 <b>New Message</b>\n\n"
            f"From: {user_mention} (ID: <code>{user_message.from_user.id}</code>)\n"
            f"{chat_info}\n\n"
            f"<b>User:</b> <code>{user_message.text}</code>\n\n"
            f"<b>Nyra:</b> <code>{bot_reply}</code>"
        )
        await user_message.bot.send_message(LOGGING_CHAT_ID, log_text, parse_mode="HTML")
    except Exception as e:
        logging.error(f"Error logging chat: {e}")
