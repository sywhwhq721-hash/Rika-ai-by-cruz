import re
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'NYRA'))

from aiogram import types
from aiogram.enums import ParseMode
from config import NSFW_WORDS
from languages import get_lang
from utils.db import get_user_language
import logging


async def nsfw_filter(message: types.Message) -> bool:
    if message.chat.type in ["group", "supergroup"] and message.text:
        for word in NSFW_WORDS:
            if re.search(rf"\b{re.escape(word)}\b", message.text, re.IGNORECASE):
                try:
                    await message.delete()
                    user_id = message.from_user.id
                    lang_code = get_user_language(user_id)
                    lang = get_lang(lang_code)
                    user_first_name = message.from_user.first_name or "friend"
                    username = f"@{message.from_user.username}" if message.from_user.username else "_No username_"
                    warning_text = (
                        f"{lang['nsfw_warning']}\n\n"
                        f"👤 {user_first_name} | ID: <code>{user_id}</code>\n"
                        f"🔗 {username}"
                    )
                    await message.answer(warning_text, parse_mode=ParseMode.HTML)
                    return True
                except Exception as e:
                    logging.warning(f"Could not handle NSFW message: {e}")
                    return True
    return False


def should_reply(message: types.Message, bot_username: str) -> bool:
    chat_type = message.chat.type
    user_msg = (message.text or "").lower()

    if chat_type == "private":
        return True
    elif chat_type in ["group", "supergroup"]:
        is_mentioned = f"@{bot_username}" in user_msg
        is_name_used = re.search(r'\bnyra\b', user_msg, re.IGNORECASE) is not None
        is_reply_to_bot = (
            message.reply_to_message
            and message.reply_to_message.from_user
            and message.reply_to_message.from_user.username
            and message.reply_to_message.from_user.username.lower() == bot_username
        )
        return is_mentioned or is_name_used or is_reply_to_bot
    return False
