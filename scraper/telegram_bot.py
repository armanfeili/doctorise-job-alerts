import asyncio
import os
import re
import logging
import time
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
import telegram.error

# ---------------------------------------------------------------------
#                        ENV + LOGGING
# ---------------------------------------------------------------------
class Config:
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------
#                   HELPER FUNCTIONS
# ---------------------------------------------------------------------
def escape_markdown_v2(text: str) -> str:
    """Escape special characters for MarkdownV2."""
    return re.sub(r'([_\*\[\]()~`>#+\-=|{}.!\\])', r'\\\1', text)

def format_job_message(job) -> str:
    """Format a job posting message for Telegram."""
    location = job.location if job.job_search_engine != "NHS" else job.employer_address
    fields = [
        (f"*{escape_markdown_v2(job.title)}*", job.title != "N/A"),
        (f"📨 *Published in:* {escape_markdown_v2(job.job_search_engine)}", job.job_search_engine != "N/A"),
        (f"📍 *Location:* {escape_markdown_v2(location)}", location != "N/A"),
        (
            f"📝 *Type:* {escape_markdown_v2(', '.join(filter(None, [job.contract_type, job.working_pattern])))}",
            (job.contract_type != "N/A" or job.working_pattern != "N/A")
        ),
        (f"💵 *Salary:* {escape_markdown_v2(job.salary)}", job.salary != "N/A"),
        (f"🗓 *Closing Date:* {escape_markdown_v2(job.closing_date)}", job.closing_date != "N/A"),
        ("🩺 *Channel:* @DoctoRiseJobAlerts", True)
    ]
    return "\n\n".join(text for text, condition in fields if condition)

# ---------------------------------------------------------------------
#     SEND TELEGRAM MESSAGE (NO DELAY EXCEPT ON ERROR)
# ---------------------------------------------------------------------
async def send_telegram_message(job, max_retries=5):
    """
    Sends a Telegram message without any normal delay between sends.
    If it fails, wait 5s and retry, up to 5 times total.
    """
    bot_token, chat_id = Config.TELEGRAM_BOT_TOKEN, Config.TELEGRAM_CHAT_ID
    if not bot_token or not chat_id:
        raise ValueError("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is not set")

    message = format_job_message(job)
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🚀 Click to Apply", url=job.job_link)]])
    bot = Bot(token=bot_token)

    retries = 0
    while retries < max_retries:
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode='MarkdownV2',
                reply_markup=reply_markup
            )
            # If successful, exit function immediately
            return

        except (telegram.error.RetryAfter, telegram.error.TimedOut, Exception) as e:
            # Log the error and wait 5 seconds before retry
            logger.warning(f"Error sending Telegram message (attempt {retries+1}): {e}")
            retries += 1
            if retries < max_retries:
                await asyncio.sleep(5)

    logger.error(f"Message failed after {max_retries} retries: {message}")
