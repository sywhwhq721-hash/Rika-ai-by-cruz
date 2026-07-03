import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'NYRA'))

from pymongo import MongoClient
from config import MONGO_URI, INSTANCE_ID
import logging
from datetime import datetime

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.server_info()
    db = client["telegram_bot"]
    chats_collection = db[f"chats_{INSTANCE_ID}"]
    conversations_collection = db[f"conversations_{INSTANCE_ID}"]
    user_language_collection = db[f"user_languages_{INSTANCE_ID}"]
    bot_memory_collection = db["nyra_bot_memory"]
    logging.info("MongoDB connected.")
except Exception as e:
    logging.error(f"MongoDB connection error: {e}")
    chats_collection = None
    conversations_collection = None
    user_language_collection = None
    bot_memory_collection = None


async def register_chat(chat_id, chat_type):
    if chats_collection is not None and not chats_collection.find_one({"chat_id": chat_id}):
        chats_collection.insert_one({"chat_id": chat_id, "chat_type": chat_type})

async def add_served_chat(chat_id, chat_type):
    await register_chat(chat_id, chat_type)

async def delete_served_chat(chat_id):
    if chats_collection is not None:
        chats_collection.delete_one({"chat_id": chat_id})
    if conversations_collection is not None:
        conversations_collection.delete_many({"chat_id": chat_id})

def load_chats():
    if chats_collection is not None:
        return [chat["chat_id"] for chat in chats_collection.find({}, {"_id": 0, "chat_id": 1})]
    return []

def set_user_language(user_id, language):
    if user_language_collection is not None:
        user_language_collection.update_one(
            {"user_id": user_id}, {"$set": {"language": language}}, upsert=True
        )

def get_user_language(user_id):
    if user_language_collection is not None:
        doc = user_language_collection.find_one({"user_id": user_id})
        if doc:
            return doc.get("language", "tamlish")
    return "tamlish"

def add_message(chat_id, user_id, role, text):
    if conversations_collection is None:
        return
    conversations_collection.insert_one({
        "chat_id": chat_id, "user_id": user_id, "role": role,
        "text": text, "timestamp": datetime.utcnow()
    })
    chat_info = chats_collection.find_one({"chat_id": chat_id}) if chats_collection is not None else None
    is_group_chat = chat_info and chat_info.get("chat_type") in ["group", "supergroup"]
    if is_group_chat:
        total = conversations_collection.count_documents({"chat_id": chat_id})
        if total > 20:
            oldest = conversations_collection.find({"chat_id": chat_id}, {"_id": 1}).sort("timestamp", 1).limit(total - 20)
            ids = [m["_id"] for m in oldest]
            if ids:
                conversations_collection.delete_many({"_id": {"$in": ids}})
    else:
        total = conversations_collection.count_documents({"chat_id": chat_id, "user_id": user_id})
        if total > 50:
            oldest = conversations_collection.find({"chat_id": chat_id, "user_id": user_id}, {"_id": 1}).sort("timestamp", 1).limit(total - 50)
            ids = [m["_id"] for m in oldest]
            if ids:
                conversations_collection.delete_many({"_id": {"$in": ids}})

def get_history(chat_id, user_id):
    if conversations_collection is None:
        return []
    chat_info = chats_collection.find_one({"chat_id": chat_id}) if chats_collection is not None else None
    is_group_chat = chat_info and chat_info.get("chat_type") in ["group", "supergroup"]
    if is_group_chat:
        messages = conversations_collection.find({"chat_id": chat_id}).sort("timestamp", -1).limit(10)
    else:
        messages = conversations_collection.find({"chat_id": chat_id, "user_id": user_id}).sort("timestamp", -1).limit(15)
    return list(reversed(list(messages)))

async def delete_old_conversations():
    if conversations_collection is None:
        return
    from datetime import timedelta
    cutoff = datetime.utcnow() - timedelta(days=7)
    conversations_collection.delete_many({"timestamp": {"$lt": cutoff}})

def save_to_memory(user_text, nyra_reply, language="tamlish"):
    if bot_memory_collection is None:
        return
    try:
        if len(user_text.strip()) < 3 or len(nyra_reply.strip()) < 3:
            return
        bot_memory_collection.insert_one({
            "user_text": user_text.strip().lower(), "nyra_reply": nyra_reply.strip(),
            "language": language, "timestamp": datetime.utcnow(), "use_count": 0,
        })
        total = bot_memory_collection.count_documents({})
        if total > 10000:
            oldest = bot_memory_collection.find({}, {"_id": 1}).sort("timestamp", 1).limit(total - 10000)
            ids = [m["_id"] for m in oldest]
            if ids:
                bot_memory_collection.delete_many({"_id": {"$in": ids}})
    except Exception as e:
        logging.error(f"Error saving to bot memory: {e}")

def search_memory(user_text, language="tamlish", limit=5):
    if bot_memory_collection is None:
        return []
    try:
        import re
        words = [w for w in user_text.lower().split() if len(w) > 2]
        if not words:
            return []
        pattern = "|".join(re.escape(w) for w in words[:8])
        results = list(bot_memory_collection.find(
            {"user_text": {"$regex": pattern, "$options": "i"}, "language": language},
            {"user_text": 1, "nyra_reply": 1, "_id": 1}
        ).limit(limit))
        if not results:
            results = list(bot_memory_collection.find(
                {"user_text": {"$regex": pattern, "$options": "i"}},
                {"user_text": 1, "nyra_reply": 1, "_id": 1}
            ).limit(limit))
        if results:
            ids = [r["_id"] for r in results]
            bot_memory_collection.update_many({"_id": {"$in": ids}}, {"$inc": {"use_count": 1}})
        return [(r["user_text"], r["nyra_reply"]) for r in results]
    except Exception as e:
        logging.error(f"Error searching bot memory: {e}")
        return []

def get_memory_stats():
    if bot_memory_collection is None:
        return {"total": 0, "languages": {}}
    try:
        total = bot_memory_collection.count_documents({})
        pipeline = [{"$group": {"_id": "$language", "count": {"$sum": 1}}}]
        lang_counts = {r["_id"]: r["count"] for r in bot_memory_collection.aggregate(pipeline)}
        return {"total": total, "languages": lang_counts}
    except Exception as e:
        logging.error(f"Error getting memory stats: {e}")
        return {"total": 0, "languages": {}}
