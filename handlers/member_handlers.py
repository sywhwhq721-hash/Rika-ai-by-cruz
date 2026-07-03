import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'NYRA'))

import logging
import random
import asyncio
from aiogram import types, enums
from aiogram.enums import ChatAction
from config import LOG_CHAT_ID
from utils.db import chats_collection
from chat_member import log_bot_added, log_bot_removed
from languages import get_lang
from utils.db import get_user_language


WELCOME_MESSAGES = [
    "🌸 Heyy <b>{name}</b>! Welcome to the group da~ 💕",
    "✨ Ayyo <b>{name}</b> aa vandhaanga! Super da welcome 🥰",
    "💖 Hello <b>{name}</b>! Glad to have you here sweetie~ 🌸",
    "🎀 Welcome <b>{name}</b>! Nalla irukkeengala? 😊💕",
    "🌺 Hii <b>{name}</b>! You're going to love it here~ 🤗",
]


async def send_typing_status(bot, chat_id, duration):
    for _ in range(duration // 5):
        await bot.send_chat_action(chat_id, ChatAction.TYPING)
        await asyncio.sleep(4.5)


async def bot_member_update(update: types.ChatMemberUpdated):
    me = await update.bot.get_me()
    chat_id = update.chat.id
    chat_title = update.chat.title or "this group"
    old_status = update.old_chat_member.status
    new_status = update.new_chat_member.status

    if update.new_chat_member.user.id == me.id and old_status == "left" and new_status in ["member", "administrator"]:
        if update.from_user:
            first_name = update.from_user.first_name
            user_id = update.from_user.id
        else:
            first_name = "Someone"
            user_id = update.new_chat_member.user.id
        await update.bot.send_message(
            chat_id,
            f"🌸 Hello everyone! I'm <b>Nyra</b> — your sweet virtual friend~!\n"
            f"💕 Thanks <a href='tg://user?id={user_id}'>{first_name}</a> for adding me to <b>{chat_title}</b>!\n"
            f"✨ Use @{me.username} or say my name to chat with me! 🥰",
            parse_mode=enums.ParseMode.HTML
        )

    if update.new_chat_member.user.id == me.id and new_status in ["left", "kicked"]:
        await log_bot_removed(update)
        if chats_collection is not None:
            chats_collection.delete_one({"chat_id": chat_id})


async def new_chat_members(message: types.Message):
    if message.chat.type in ["group", "supergroup"]:
        for new_member in message.new_chat_members:
            if new_member.id == (await message.bot.get_me()).id:
                await log_bot_added(message)
                continue

            first_name = new_member.first_name or "friend"
            random_message = random.choice(WELCOME_MESSAGES)
            welcome_message = random_message.replace(
                "<b>{name}</b>",
                f"<a href='tg://user?id={new_member.id}'>{first_name}</a>"
            )
            asyncio.create_task(send_typing_status(message.bot, message.chat.id, 5))
            await asyncio.sleep(2)
            await message.answer(text=welcome_message, parse_mode=enums.ParseMode.HTML)


async def left_chat_members(message: types.Message):
    pass


async def handle_member_join(update: types.ChatMemberUpdated):
    if update.old_chat_member.status == enums.ChatMemberStatus.LEFT and \
       update.new_chat_member.status in [enums.ChatMemberStatus.MEMBER, enums.ChatMemberStatus.ADMINISTRATOR]:

        new_member = update.new_chat_member.user
        if new_member.id == (await update.bot.get_me()).id:
            return

        if new_member.username:
            name_to_mention = f"@{new_member.username}"
        else:
            first_name = new_member.first_name or "friend"
            name_to_mention = f"<a href='tg://user?id={new_member.id}'>{first_name}</a>"

        asyncio.create_task(send_typing_status(update.bot, update.chat.id, 5))
        await asyncio.sleep(2)

        random_message = random.choice(WELCOME_MESSAGES)
        welcome_message = random_message.replace("<b>{name}</b>", name_to_mention)

        await update.bot.send_message(
            chat_id=update.chat.id,
            text=welcome_message,
            parse_mode=enums.ParseMode.HTML
        )
