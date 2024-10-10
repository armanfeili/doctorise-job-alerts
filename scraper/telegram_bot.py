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

# Escape special characters for MarkdownV2
def escape_markdown_v2(text):
    return re.sub(r'([_\*\[\]()~`>#+\-=|{}.!\\])', r'\\\1', text)

# Format the job posting message, including only non-empty and non-"N/A" fields
def format_job_message(job):
    location = job.location if job.job_search_engine != "NHS" else job.employer_address
    fields = [
        (f"*{escape_markdown_v2(job.title)}*", job.title != "N/A"),
        (f"📨 *Published in:* {escape_markdown_v2(job.job_search_engine)}", job.job_search_engine != "N/A"),
        (f"📍 *Location:* {escape_markdown_v2(location)}", location != "N/A"),
        (f"📝 *Type:* {escape_markdown_v2(', '.join(filter(None, [job.contract_type, job.working_pattern])))}", (job.contract_type != "N/A" or job.working_pattern != "N/A")),
        (f"💵 *Salary:* {escape_markdown_v2(job.salary)}", job.salary != "N/A"),
        (f"📅 *Closing Date:* {escape_markdown_v2(job.closing_date)}", job.closing_date != "N/A"),  # Include closing date
        ("🩺 *Channel:* @DoctoRiseJobAlerts", True)  # Always include the channel name
    ]
    return "\n\n".join(text for text, condition in fields if condition)

# Send job alert message to the Telegram channel
async def send_telegram_message(job):
    bot_token, chat_id = Config.TELEGRAM_BOT_TOKEN, Config.TELEGRAM_CHAT_ID
    if not bot_token or not chat_id:
        raise ValueError("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is not set")

    message = format_job_message(job)
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🚀 Click to Apply", url=job.job_link)]])
    
    try:
        bot = Bot(token=bot_token)
        await bot.send_message(chat_id=chat_id, text=message, parse_mode='MarkdownV2', reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Failed to send message to Telegram: {e}")
