import os
import hashlib

BOT_TOKEN = "8628786630:AAENaSvViSaK_WinoYxHaXmsR5lvcFzdLWk"
API_ID = 38081166
API_HASH = "f608a6dcf2b1d4761c53ff29d00c5bbf"

try:
    INSTANCE_ID = hashlib.sha256(BOT_TOKEN.encode()).hexdigest()
except (TypeError, AttributeError):
    INSTANCE_ID = "local_instance"

MONGO_URI = "mongodb+srv://Lucifer:<Lucky1976208>@cluster0.9lfbgac.mongodb.net/?appName=Cluster0"

GROQ_API_KEYS = [
    "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",
    "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",
    "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",
    "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",
  ]

GROQ_MODEL = "llama-3.1-8b-instant"

LOG_CHAT_ID = -1004315457394
OWNER_ID = 8705127026

# Channel configurations
UPDATE_CHANNEL = "https://t.me/rika_updats"
SUPPORT_GROUP = "https://t.me/+U3OxBbEaNrhhZGM9"

# Sudo Users Configuration
SUDO_USERS = [
    8705127026,  # Owner
]

# Ban Users Configuration
BANNED_USERS = []
BANNED_CHATS = []

# Advanced AI Features
ADVANCED_AI_ENABLED = True
MEMORY_LEARNING = True
CONTEXT_AWARENESS = True
EMOTIONAL_INTELLIGENCE = True
MULTI_TURN_CONVERSATION = True
TYPING_INDICATOR = True
REACTION_ENABLED = True

# AI Model Settings
AI_TEMPERATURE = 0.8  # Higher = more creative
AI_TOP_P = 0.9
AI_MAX_TOKENS = 256
AI_RETRY_ATTEMPTS = 3
AI_TIMEOUT = 30

# Response Customization
MIN_RESPONSE_LENGTH = 5
MAX_RESPONSE_LENGTH = 500
RESPONSE_QUALITY = "advanced"  # normal, advanced, expert

def is_sudo(user_id):
    """Check if user has sudo/admin privileges"""
    return user_id in SUDO_USERS or user_id == OWNER_ID

def add_sudo_user(user_id):
    """Add a user to sudo list"""
    if user_id not in SUDO_USERS:
        SUDO_USERS.append(user_id)

def remove_sudo_user(user_id):
    """Remove a user from sudo list"""
    if user_id in SUDO_USERS and user_id != OWNER_ID:
        SUDO_USERS.remove(user_id)

def is_banned_user(user_id):
    """Check if user is banned"""
    return user_id in BANNED_USERS

def is_banned_chat(chat_id):
    """Check if chat is banned"""
    return chat_id in BANNED_CHATS

def ban_user(user_id):
    """Ban a user"""
    if user_id not in BANNED_USERS and user_id != OWNER_ID:
        BANNED_USERS.append(user_id)
        return True
    return False

def ban_chat(chat_id):
    """Ban a chat"""
    if chat_id not in BANNED_CHATS:
        BANNED_CHATS.append(chat_id)
        return True
    return False

def unban_user(user_id):
    """Unban a user"""
    if user_id in BANNED_USERS:
        BANNED_USERS.remove(user_id)
        return True
    return False

def unban_chat(chat_id):
    """Unban a chat"""
    if chat_id in BANNED_CHATS:
        BANNED_CHATS.remove(chat_id)
        return True
    return False

def get_all_banned_users():
    """Get all banned users list"""
    return BANNED_USERS.copy()

def get_all_banned_chats():
    """Get all banned chats list"""
    return BANNED_CHATS.copy()

NSFW_WORDS = [
    "chutiya", "madarchod", "bhosdi", "bhosdiwala", "chutka", "kaminey", "haraamikhor",
    "bhosdike", "bhosdika", "anal", "arse", "ass", "asshole", "bastard", "bitch", "blowjob",
    "bollocks", "boner", "boobs", "bugger", "bullshit", "cock", "cocksucker", "cunt", "dick",
    "dildo", "dyke", "fag", "faggot", "fuck", "fucked", "fucker", "fucking", "goddamn",
    "jackass", "jizz", "kunt", "motherfucker", "nigga", "nigger", "penis", "piss", "prick",
    "pussy", "queer", "rape", "shit", "slut", "twat", "whore", "wank", "wanker", "cum",
    "vagina", "scrotum", "semen", "porn", "pornography", "xxx", "masturbate", "masturbating",
    "fuddi", "fudi", "randwa", "randi", "gandu", "gand", "bhenchod", "lund", "loda",
    "chud", "chodna", "chudai", "gaand",
]
