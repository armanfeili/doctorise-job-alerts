import asyncio
import os
import re
import logging
import random
import time
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
import telegram.error

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

# Format job posting message
def format_job_message(job):
    location = job.location if job.job_search_engine != "NHS" else job.employer_address
    fields = [
        (f"*{escape_markdown_v2(job.title)}*", job.title != "N/A"),
        (f"📨 *Published in:* {escape_markdown_v2(job.job_search_engine)}", job.job_search_engine != "N/A"),
        (f"📍 *Location:* {escape_markdown_v2(location)}", location != "N/A"),
        (f"📝 *Type:* {escape_markdown_v2(', '.join(filter(None, [job.contract_type, job.working_pattern])))}", (job.contract_type != "N/A" or job.working_pattern != "N/A")),
        (f"💵 *Salary:* {escape_markdown_v2(job.salary)}", job.salary != "N/A"),
        (f"🗓 *Closing Date:* {escape_markdown_v2(job.closing_date)}", job.closing_date != "N/A"),
        ("🩺 *Channel:* @DoctoRiseJobAlerts", True)
    ]
    return "\n\n".join(text for text, condition in fields if condition)

# Global counter for Telegram messages & reset timer
message_counter = 0
last_reset_time = time.time()  # Tracks the last reset time

# Send Telegram message with adaptive delay
async def send_telegram_message(job, max_retries=5):
    global message_counter, last_reset_time
    bot_token, chat_id = Config.TELEGRAM_BOT_TOKEN, Config.TELEGRAM_CHAT_ID

    if not bot_token or not chat_id:
        raise ValueError("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is not set")

    message = format_job_message(job)
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🚀 Click to Apply", url=job.job_link)]])
    bot = Bot(token=bot_token)

    retries = 0
    while retries < max_retries:
        try:
            # Reset message_counter every 60 seconds to prevent permanent slowdown
            if time.time() - last_reset_time > 60:
                message_counter = 0
                last_reset_time = time.time()

            # Send message
            await bot.send_message(chat_id=chat_id, text=message, parse_mode='MarkdownV2', reply_markup=reply_markup)

            # Increment message counter
            message_counter += 1

            # Dynamically adjust sleep time to prevent flood control
            if message_counter >= 20:  
                sleep_time = 3  # Slow down significantly if nearing limits
            elif message_counter >= 5:  
                sleep_time = 1.5  # Short delay to prevent flooding
            else:
                sleep_time = random.uniform(0.7, 1.2)  # Normal fast operation

            await asyncio.sleep(sleep_time)
            return  # Success, exit retry loop

        except telegram.error.RetryAfter as e:
            wait_time = e.retry_after
            logger.warning(f"Flood limit exceeded. Retrying in {wait_time} seconds...")
            await asyncio.sleep(wait_time)  # Wait and retry

        except telegram.error.TimedOut:
            retry_delay = min(30, 2 ** retries)  # Exponential backoff (max 30 sec)
            logger.warning(f"Telegram API timed out. Retrying in {retry_delay} seconds...")
            await asyncio.sleep(retry_delay)  # Wait before retrying

        except Exception as e:
            logger.error(f"Failed to send message to Telegram: {e}")
            await asyncio.sleep(2)  # Small delay before retrying

        retries += 1

    logger.error(f"Message failed after {max_retries} retries: {message}")
