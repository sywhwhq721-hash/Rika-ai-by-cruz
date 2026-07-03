import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'NYRA'))

import logging
import random
import asyncio
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandObject
from config import OWNER_ID, LOG_CHAT_ID
from utils.db import chats_collection, load_chats, set_user_language, get_user_language, get_memory_stats
from languages import LANGUAGES, get_lang
from chat_member import log_user_start


def build_language_keyboard() -> InlineKeyboardMarkup:
    buttons = []
    for code, data in LANGUAGES.items():
        buttons.append([InlineKeyboardButton(
            text=data["label"],
            callback_data=f"setlang_{code}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def start_handler(message: types.Message):
    await log_user_start(message)
    user_name = message.from_user.first_name
    await message.answer(
        f"💕 Hey <a href='tg://user?id={message.from_user.id}'>{user_name}</a>!\n\n"
        "🌍 Please choose your language first:\n"
        "மொழி தேர்வு செய்யுங்கள் 🌸",
        parse_mode="HTML",
        reply_markup=build_language_keyboard()
    )


async def language_callback(callback: types.CallbackQuery):
    if not callback.data.startswith("setlang_"):
        return

    lang_code = callback.data.replace("setlang_", "")
    user_id = callback.from_user.id
    set_user_language(user_id, lang_code)

    lang = get_lang(lang_code)
    user_name = callback.from_user.first_name
    me = await callback.bot.get_me()

    video_links = [
        "https://files.catbox.moe/yp8yby.mp4",
        "https://files.catbox.moe/xws2hg.mp4",
        "https://files.catbox.moe/g4b0px.mp4"
    ]
    video_url = random.choice(video_links)

    support_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💬 Support", url="https://t.me/+cCdmZbxyYSw1NGM1"),
            InlineKeyboardButton(text="📢 Updates", url="https://t.me/+7wUfuOsQ1O8wNzI9")
        ],
        [
            InlineKeyboardButton(
                text="🌸 🇦 🇩 🇩  🇲 🇪  🇧 🇦 🇧 🇾 🌸",
                url=f"https://t.me/{me.username}?startgroup=true"
            )
        ],
        [InlineKeyboardButton(text="💞 Change Language", callback_data="change_lang")]
    ])

    try:
        await callback.message.delete()
    except Exception:
        pass

    caption = lang["start_caption"].format(name=user_name)
    await callback.bot.send_video(
        chat_id=callback.message.chat.id,
        video=video_url,
        caption=f"{lang['selected']}\n\n{caption}",
        parse_mode="HTML",
        reply_markup=support_keyboard
    )
    await callback.answer(f"{lang['flag']} Language set!")


async def change_language_callback(callback: types.CallbackQuery):
    user_name = callback.from_user.first_name
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.bot.send_message(
        chat_id=callback.message.chat.id,
        text=f"💕 Hey <a href='tg://user?id={callback.from_user.id}'>{user_name}</a>!\n\n"
             "🌍 Choose your new language:",
        parse_mode="HTML",
        reply_markup=build_language_keyboard()
    )
    await callback.answer()


async def broadcast(message: types.Message, command: CommandObject):
    if message.from_user.id != OWNER_ID:
        await message.reply("❌ You are not authorized to use this command.")
        return

    chats = load_chats()
    success_users, success_groups, success_channels, failed = 0, 0, 0, 0

    args = command.args.split() if command.args else []
    do_pin = "-pin" in args or "-pinloud" in args
    loud_pin = "-pinloud" in args
    user_only = "-user" in args
    group_only = "-group" in args
    do_forward = "-forward" in args

    content = message.reply_to_message if message.reply_to_message else None
    text = " ".join([arg for arg in args if not arg.startswith("-")])

    if not content and not text:
        await message.reply("⚠️ Usage: /broadcast <msg> or reply to a message")
        return

    for chat_id in chats:
        try:
            chat = await message.bot.get_chat(chat_id)
            if (user_only and chat.type != "private") or (group_only and chat.type == "private"):
                continue

            sent_msg = None
            if do_forward and content:
                sent_msg = await message.bot.forward_message(chat_id, content.chat.id, content.message_id)
            elif text:
                sent_msg = await message.bot.send_message(chat_id, text)
            elif content:
                if content.text:
                    sent_msg = await message.bot.send_message(chat_id, content.text)
                elif content.photo:
                    sent_msg = await message.bot.send_photo(chat_id, content.photo[-1].file_id, caption=content.caption or "")
                elif content.video:
                    sent_msg = await message.bot.send_video(chat_id, content.video.file_id, caption=content.caption or "")

            if do_pin and sent_msg and chat.type != "private":
                try:
                    await message.bot.pin_chat_message(chat_id, sent_msg.message_id, disable_notification=not loud_pin)
                except Exception as e:
                    logging.warning(f"Cannot pin in {chat_id}: {e}")

            if chat.type == "private":
                success_users += 1
            elif chat.type in ["group", "supergroup"]:
                success_groups += 1
            elif chat.type == "channel":
                success_channels += 1

            await asyncio.sleep(0.1)
        except Exception as e:
            logging.error(f"Broadcast failed for {chat_id}: {e}")
            failed += 1

    await message.reply(
        f"✅ Broadcast sent!\n\n"
        f"👤 Users: {success_users}\n"
        f"👥 Groups: {success_groups}\n"
        f"📢 Channels: {success_channels}\n"
        f"❌ Failed: {failed}"
        + (" (pinned)" if do_pin else "")
        + (" (forwarded)" if do_forward else "")
    )


async def stat_handler(message: types.Message):
    if message.from_user.id != OWNER_ID:
        await message.reply("❌ You are not authorized to use this command.")
        return
    try:
        total_users = chats_collection.count_documents({"chat_type": "private"})
        total_groups = chats_collection.count_documents({"chat_type": {"$in": ["group", "supergroup"]}})
        total_channels = chats_collection.count_documents({"chat_type": "channel"})

        mem = get_memory_stats()
        lang_breakdown = "\n".join(
            f"  • {lang}: {count} memories"
            for lang, count in mem["languages"].items()
        ) or "  (none yet)"

        await message.reply(
            f"📊 Nyra Bot Stats:\n\n"
            f"👤 Total Users: {total_users}\n"
            f"👥 Total Groups: {total_groups}\n"
            f"📢 Total Channels: {total_channels}\n\n"
            f"💾 Bot Memory (Collection 2):\n"
            f"  Total learned: {mem['total']} entries\n"
            f"{lang_breakdown}"
        )
    except Exception as e:
        logging.error(f"Error fetching stats: {e}")
        await message.reply("⚠️ Something went wrong while fetching stats.")


async def clear_chat_history(message: types.Message):
    await message.reply("🧹 Chat history has been cleared sweetly! 🌸")
