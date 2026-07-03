import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'NYRA'))

import logging
import random
import asyncio
from aiogram import types
from aiogram.enums import ChatAction
from groq import Groq, APIStatusError, RateLimitError, APIConnectionError

from prompt import get_prompt, get_language_reminder
from config import GROQ_API_KEYS, GROQ_MODEL
from utils.db import (
    register_chat, add_message, get_history, get_user_language,
    save_to_memory, search_memory
)
from utils.filters import should_reply, nsfw_filter
from utils.chat_logger import log_user_chat
from languages import get_lang

_groq_clients = [Groq(api_key=k) for k in GROQ_API_KEYS]
_key_index = 0
_key_fail_counts = [0] * len(_groq_clients)


def _reset_fail_count(idx):
    _key_fail_counts[idx] = 0

def _increment_fail(idx):
    _key_fail_counts[idx] += 1

async def call_groq_with_fallback(messages, language):
    global _key_index
    tried = set()
    start_idx = _key_index
    for attempt in range(len(_groq_clients)):
        idx = (start_idx + attempt) % len(_groq_clients)
        if idx in tried:
            continue
        tried.add(idx)
        client = _groq_clients[idx]
        try:
            response = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=messages,
                max_tokens=120,
                temperature=0.85,
            )
            _reset_fail_count(idx)
            _key_index = idx
            return response.choices[0].message.content.strip()
        except RateLimitError:
            _increment_fail(idx)
            logging.warning(f"Groq key #{idx + 1} rate limited, trying next...")
            continue
        except APIConnectionError:
            _increment_fail(idx)
            logging.warning(f"Groq key #{idx + 1} connection error, trying next...")
            continue
        except APIStatusError as e:
            _increment_fail(idx)
            logging.warning(f"Groq key #{idx + 1} error {e.status_code}, trying next...")
            continue
        except Exception as e:
            _increment_fail(idx)
            logging.error(f"Groq key #{idx + 1} unexpected error: {e}")
            continue
    logging.error("All Groq API keys failed. Using memory fallback.")
    return None

def _build_groq_messages(nyra_prompt, history, user_text, language):
    reminder = get_language_reminder(language)
    system_content = nyra_prompt + "\n\n" + reminder
    messages = [{"role": "system", "content": system_content}]
    for turn in history:
        role = "user" if turn["role"] == "User" else "assistant"
        messages.append({"role": role, "content": turn["text"]})
    messages.append({"role": "user", "content": user_text})
    return messages

def _memory_fallback_reply(user_text, language, fallback_list):
    memory_results = search_memory(user_text, language=language, limit=5)
    if memory_results:
        _, reply = random.choice(memory_results)
        return reply
    return random.choice(fallback_list)

GROUP_STICKER_PACKS = [
    "gobiez_by_TgEmojis_bot",
    "skr0077_by_fStikBot",
    "cutieeeeeeeeecumtie_by_fStikBot",
    "lovelygoldenhours",
]
DM_STICKER_PACK = "Fragrant_Flower"

TRIGGER_WORDS = [
    "hey", "yoo", "nyra", "anyone", "someone", "here", "hello", "wassup",
    "kaise", "enna", "sollu", "ayyo", "machan", "dai", "dei", "привет", "hola"
]

last_request_time = {}
dm_sticker_count = {}


async def handle_message(message: types.Message):
    if not message.text or message.text.startswith("/"):
        return
    if await nsfw_filter(message):
        return
    bot_username = (await message.bot.get_me()).username.lower()
    chat_id = message.chat.id
    user_id = message.from_user.id
    text_lower = message.text.lower()
    should_trigger = any(word in text_lower for word in TRIGGER_WORDS)
    if not should_reply(message, bot_username) and not should_trigger:
        return
    now = asyncio.get_event_loop().time()
    if user_id in last_request_time and now - last_request_time[user_id] < 1:
        return
    last_request_time[user_id] = now
    if message.chat.type == "private":
        dm_sticker_count[user_id] = 0
    lang_code = get_user_language(user_id)
    lang = get_lang(lang_code)
    nyra_prompt = get_prompt(lang_code)
    try:
        await message.bot.send_chat_action(chat_id, ChatAction.TYPING)
        await register_chat(chat_id, message.chat.type)
        history = get_history(chat_id, user_id)
        groq_messages = _build_groq_messages(nyra_prompt, history, message.text, lang_code)
        nyra_reply = await call_groq_with_fallback(groq_messages, lang_code)
        if nyra_reply is None:
            nyra_reply = _memory_fallback_reply(message.text, lang_code, lang["fallback"])
        await message.reply(nyra_reply, parse_mode="HTML")
        add_message(chat_id, user_id, "User", message.text)
        add_message(chat_id, user_id, "Nyra", nyra_reply)
        save_to_memory(message.text, nyra_reply, language=lang_code)
        await log_user_chat(message, nyra_reply)
    except Exception as e:
        logging.error(f"Error handling message: {e}")
        await message.reply(random.choice(lang["fallback"]))


async def handle_sticker(message: types.Message):
    try:
        bot = await message.bot.get_me()
        user_id = message.from_user.id
        if message.chat.type in ["group", "supergroup"]:
            if message.reply_to_message and message.reply_to_message.from_user.id == bot.id:
                pack_name = random.choice(GROUP_STICKER_PACKS)
                sticker_set = await message.bot.get_sticker_set(pack_name)
                sticker = random.choice(sticker_set.stickers)
                await message.reply_sticker(sticker.file_id)
            return
        elif message.chat.type == "private":
            count = dm_sticker_count.get(user_id, 0)
            if count >= 10:
                return
            dm_sticker_count[user_id] = count + 1
            sticker_set = await message.bot.get_sticker_set(DM_STICKER_PACK)
            sticker = random.choice(sticker_set.stickers)
            await message.reply_sticker(sticker.file_id)
    except Exception as e:
        logging.error(f"Sticker reply error: {e}")


async def handle_media(message: types.Message):
    try:
        if message.chat.type in ["group", "supergroup"]:
            pack_name = random.choice(GROUP_STICKER_PACKS)
        else:
            pack_name = DM_STICKER_PACK
        sticker_set = await message.bot.get_sticker_set(pack_name)
        sticker = random.choice(sticker_set.stickers)
        await message.reply_sticker(sticker.file_id)
    except Exception as e:
        logging.error(f"Media handler error: {e}")
