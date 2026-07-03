import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import logging
import asyncio
import httpx
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from config import BOT_TOKEN
from utils.db import delete_old_conversations
from handlers import chat_handlers, command_handlers, member_handlers
from handlers.command_handlers import language_callback, change_language_callback

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

NEKO_COMMANDS = {
    "slap": {"emoji": "👋", "text": "slapped"},
    "kiss": {"emoji": "😘", "text": "kissed"},
    "punch": {"emoji": "🥊", "text": "punched"},
    "hug": {"emoji": "🤗", "text": "hugged"},
    "kick": {"emoji": "🦵", "text": "kicked"},
    "pat": {"emoji": "🥰", "text": "patted"},
    "snap": {"emoji": "💥", "text": "snapped"},
}


def escape_md(text: str) -> str:
    escape_chars = r"_*[]()~`>#+-=|{}.!"
    return ''.join(f"\\{c}" if c in escape_chars else c for c in text)


async def get_neko_gif(action: str):
    endpoint_map = {
        "slap": "slap", "kiss": "kiss", "punch": "punch",
        "hug": "hug", "kick": "kick", "pat": "pat", "snap": "poke",
    }
    endpoint = endpoint_map.get(action, action)
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"https://nekos.best/api/v2/{endpoint}")
            data = response.json()
            return data["results"][0]["url"]
    except Exception as e:
        logging.error(f"Nekos.best API error for {action}: {e}")
        return None


async def handle_action(message: types.Message, action: str):
    if action not in NEKO_COMMANDS:
        await message.reply("Unknown command.")
        return

    gif_url = await get_neko_gif(action)
    if not gif_url:
        await message.reply("⚠️ Couldn't fetch animation. Try again later sweetie~ 🥺")
        return

    sender = f"[{escape_md(message.from_user.first_name)}](tg://user?id={message.from_user.id})"
    target = sender
    if message.reply_to_message and message.reply_to_message.from_user:
        target = f"[{escape_md(message.reply_to_message.from_user.first_name)}](tg://user?id={message.reply_to_message.from_user.id})"

    action_text = escape_md(NEKO_COMMANDS[action]["text"])
    emoji = NEKO_COMMANDS[action]["emoji"]
    caption = f"{sender} {action_text} {target}\\! {emoji}"

    try:
        await message.answer_animation(animation=gif_url, caption=caption, parse_mode="MarkdownV2")
    except Exception as e:
        logging.error(f"Error sending GIF for {action}: {e}")
        await message.reply("⚠️ Error sending GIF. Try again later~ 🥺")


async def slap_cmd(message: types.Message): await handle_action(message, "slap")
async def kiss_cmd(message: types.Message): await handle_action(message, "kiss")
async def punch_cmd(message: types.Message): await handle_action(message, "punch")
async def hug_cmd(message: types.Message): await handle_action(message, "hug")
async def kick_cmd(message: types.Message): await handle_action(message, "kick")
async def pet_cmd(message: types.Message): await handle_action(message, "pat")
async def snap_cmd(message: types.Message): await handle_action(message, "snap")


async def roll_dice(message: types.Message):
    dice = await message.answer_dice(emoji="🎲")
    await message.reply(f"🎲 {message.from_user.first_name}, you rolled {dice.dice.value}!")

async def throw_dart(message: types.Message):
    dart = await message.answer_dice(emoji="🎯")
    await message.reply(f"🎯 {message.from_user.first_name}, your score is {dart.dice.value}!")

async def shoot_basket(message: types.Message):
    basket = await message.answer_dice(emoji="🏀")
    await message.reply(f"🏀 {message.from_user.first_name}, your score is {basket.dice.value}!")

async def kick_football(message: types.Message):
    football = await message.answer_dice(emoji="⚽")
    await message.reply(f"⚽ {message.from_user.first_name}, your score is {football.dice.value}!")


async def auto_clear_cache():
    while True:
        await asyncio.sleep(3600)
        try:
            await delete_old_conversations()
            logging.info("🧹 Old conversations cleared.")
        except Exception as e:
            logging.error(f"Error clearing cache: {e}")


def register_handlers(dp: Dispatcher):
    dp.message.register(command_handlers.start_handler, Command("start"))
    dp.callback_query.register(language_callback, F.data.startswith("setlang_"))
    dp.callback_query.register(change_language_callback, F.data == "change_lang")
    dp.message.register(command_handlers.broadcast, Command("broadcast"))
    dp.message.register(command_handlers.stat_handler, Command("stats"))
    dp.message.register(command_handlers.clear_chat_history, Command("clearchat"))
    dp.message.register(chat_handlers.handle_media, F.photo | F.video | F.animation)
    dp.message.register(chat_handlers.handle_sticker, F.sticker)
    dp.message.register(member_handlers.new_chat_members, F.new_chat_members)
    dp.chat_member.register(member_handlers.handle_member_join)
    dp.my_chat_member.register(member_handlers.bot_member_update)
    dp.message.register(member_handlers.left_chat_members, F.left_chat_member)
    dp.message.register(roll_dice, Command("dice"))
    dp.message.register(throw_dart, Command("dart"))
    dp.message.register(shoot_basket, Command("basket"))
    dp.message.register(kick_football, Command("football"))
    dp.message.register(slap_cmd, Command("slap"))
    dp.message.register(kiss_cmd, Command("kiss"))
    dp.message.register(punch_cmd, Command("punch"))
    dp.message.register(hug_cmd, Command("hug"))
    dp.message.register(kick_cmd, Command("kick"))
    dp.message.register(pet_cmd, Command("pet"))
    dp.message.register(snap_cmd, Command("snap"))
    dp.message.register(chat_handlers.handle_message, F.text)


async def main():
    register_handlers(dp)
    asyncio.create_task(auto_clear_cache())
    logging.info("🌸 NYRA Bot is starting up~ 💕 (Powered by Groq)")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot stopped by user.")
    except Exception as e:
        logging.error(f"Fatal error: {e}")
