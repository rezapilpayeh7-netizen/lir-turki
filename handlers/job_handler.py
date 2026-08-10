import logging
import json
from core.api_handler import APIHandler
from core.rate_calculator import RateCalculator
from core.message_builder import MessageBuilder
from core.image_generator import ImageGenerator

logger = logging.getLogger(__name__)

class JobHandler:
    """مدیریت وظایف زمانبندی"""
    
    def __init__(self, config, scheduler=None):
        self.config = config
        self.api_handler = APIHandler(config)
        self.rate_calculator = RateCalculator(config.manual_rates)
        self.image_generator = ImageGenerator(config)
        self.bot_enabled = True
        self.manual_rates = config.manual_rates
        self.scheduler = scheduler
        self.job = None
        self.send_image = True
    
    def set_scheduler(self, scheduler, job):
        self.scheduler = scheduler
        self.job = job
    
    def reschedule_job(self, minutes):
        if self.scheduler and self.job:
            self.job.reschedule(trigger='interval', minutes=minutes)
            logger.info(f"⏰ زمانبندی به {minutes} دقیقه تغییر کرد")
    
    def _add_special_to_rates(self, rates):
        """اضافه کردن special به هر ارز با خواندن مستقیم از config.json"""
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                currencies_config = config.get('currencies', {})
                
                for key in rates.keys():
                    if key in currencies_config:
                        special = currencies_config[key].get('special', '')
                        rates[key]['special'] = special
                    else:
                        rates[key]['special'] = ''
                return rates
        except Exception as e:
            logger.error(f"❌ خطا در خواندن special از config: {e}")
            return rates
    
    async def send_to_channel(self, context):
        if not self.bot_enabled:
            logger.info("⏸️ ربات غیرفعال است")
            return
        
        api_rates = self.api_handler.fetch_rates()
        if api_rates:
            visible_currencies = self.config.get_visible_currencies()
            final_rates = self.rate_calculator.calculate(api_rates, visible_currencies)
            if final_rates:
                # ============================================================
                # 🔴 اضافه کردن special به final_rates
                # ============================================================
                final_rates = self._add_special_to_rates(final_rates)
                
                try:
                    channel_id = self.config.channel_id
                    
                    if self.send_image:
                        image_path = self.image_generator.generate(final_rates, "output.png")
                        if image_path:
                            with open(image_path, 'rb') as photo:
                                caption = MessageBuilder.build_image_caption()
                                await context.bot.send_photo(
                                    chat_id=channel_id,
                                    photo=photo,
                                    caption=caption
                                )
                            logger.info(f"✅ تصویر به کانال {channel_id} ارسال شد")
                    else:
                        message = MessageBuilder.build_text_message(final_rates, self.config)
                        if message:
                            await context.bot.send_message(
                                chat_id=channel_id,
                                text=message,
                                parse_mode='Markdown'
                            )
                            logger.info(f"✅ پیام به کانال {channel_id} ارسال شد")
                    
                    self.config.update_previous_rates(final_rates)
                    
                except Exception as e:
                    logger.error(f"❌ خطا در ارسال: {e}")
    
    async def send_update(self, message):
        api_rates = self.api_handler.fetch_rates()
        if not api_rates:
            await message.reply_text("❌ خطا در دریافت نرخ‌ها")
            return False
        
        final_rates = self.rate_calculator.calculate(api_rates, None)
        if not final_rates:
            await message.reply_text("❌ خطا در محاسبه نرخ‌ها")
            return False
        
        # ============================================================
        # 🔴 اضافه کردن special به final_rates
        # ============================================================
        final_rates = self._add_special_to_rates(final_rates)
        
        image_path = self.image_generator.generate(final_rates, "output.png")
        if image_path:
            with open(image_path, 'rb') as photo:
                caption = MessageBuilder.build_image_caption()
                await message.reply_photo(
                    photo=photo,
                    caption=caption
                )
            self.config.update_previous_rates(final_rates)
            return True
        
        text = MessageBuilder.build_text_message(final_rates, self.config)
        if text:
            await message.reply_text(text, parse_mode='Markdown')
            self.config.update_previous_rates(final_rates)
            return True
        
        return False
    
    async def send_status(self, message):
        api_rates = self.api_handler.fetch_rates()
        if not api_rates:
            await message.reply_text("❌ خطا در دریافت وضعیت")
            return
        
        visible_currencies = ['usd', 'aed', 'usdt']
        final_rates = self.rate_calculator.calculate(api_rates, visible_currencies)
        if final_rates:
            text = MessageBuilder.build_status_message(
                final_rates,
                self.bot_enabled,
                self.config.channel_id,
                self.config.interval_minutes
            )
            await message.reply_text(text, parse_mode='Markdown')