import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram.request import HTTPXRequest

from core.config import Config
from handlers.job_handler import JobHandler
from core.bot_commands import BotCommands

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    logger.info("🚀 شروع ربات نرخ ارز (نسخه نهایی)")
    logger.info("=" * 50)
    
    config = Config()
    job_handler = JobHandler(config)
    
    request = HTTPXRequest(
        connect_timeout=60.0,
        read_timeout=60.0,
        write_timeout=60.0,
        pool_timeout=60.0,
    )
    
    application = Application.builder() \
        .token(config.bot_token) \
        .request(request) \
        .build()
    
    commands = BotCommands(job_handler, config)
    
    application.add_handler(CommandHandler("start", commands.start))
    application.add_handler(CommandHandler("menu", commands.start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, commands.handle_text))
    
    job_queue = application.job_queue
    if job_queue:
        job = job_queue.run_repeating(
            job_handler.send_to_channel,
            interval=config.interval_minutes * 60,
            first=10
        )
        job_handler.set_scheduler(job_queue, job)
        logger.info(f"⏰ زمانبندی {config.interval_minutes} دقیقه‌ای فعال شد")
    
    logger.info(f"📢 کانال مقصد: {config.channel_id}")
    logger.info("✅ ربات آماده است...")
    
    application.run_polling(
        poll_interval=1.0,
        timeout=60,
        drop_pending_updates=True
    )

if __name__ == "__main__":
    main()