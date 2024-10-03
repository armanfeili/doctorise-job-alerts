import os
import re
import logging
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

# Centralized configuration for environment variables
class Config:
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Function to escape MarkdownV2 special characters, including '-'
def escape_markdown_v2(text):
    return re.sub(r'([_\*\[\]()~`>#+\-=|{}.!\\])', r'\\\1', text)

# Helper function to format job posting message
def format_job_message(job):
    title = escape_markdown_v2(job.title)
    category = escape_markdown_v2(job.category)
    job_search_engine = escape_markdown_v2(job.job_search_engine)
    contract_type = escape_markdown_v2(job.contract_type)
    working_pattern = escape_markdown_v2(job.working_pattern)
    salary = escape_markdown_v2(job.salary)
    location = escape_markdown_v2(job.location if job.job_search_engine != "NHS" else job.employer_address)

    return (
        f"*{title}*\n\n"
        f"📨 *Published in:* {job_search_engine}\n\n"
        f"📁 *Category:* \\#{category}\n\n"
        f"📍 *Location:* {location}\n\n"
        f"📝 *Type:* {contract_type}, {working_pattern}\n\n"
        f"💵 *Salary:* {salary}\n\n"
        "🩺 *Channel:* @DoctoRiseJobAlerts"
    )

# Function to send a job alert message to the Telegram channel with an inline button
async def send_telegram_message(job):
    bot_token = Config.TELEGRAM_BOT_TOKEN
    chat_id = Config.TELEGRAM_CHAT_ID

    if not bot_token or not chat_id:
        raise ValueError("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is not set")

    message = format_job_message(job)

    keyboard = [
        [InlineKeyboardButton("🚀 Click to Apply", url=job.job_link)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        bot = Bot(token=bot_token)
        # Send the message with the inline keyboard button
        await bot.send_message(chat_id=chat_id, text=message, parse_mode='MarkdownV2', reply_markup=reply_markup)
        logger.info(f"Message sent to Telegram channel: {chat_id}")
    except Exception as e:
        logger.error(f"Failed to send message to Telegram: {e}")
