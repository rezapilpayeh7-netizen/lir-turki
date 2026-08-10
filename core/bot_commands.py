from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes
import logging
import jdatetime

logger = logging.getLogger(__name__)

class BotCommands:
    """دستورات ربات با دکمه‌های کیبورد - با نمایش وضعیت روی دکمه‌ها"""
    
    def __init__(self, job_handler, config):
        self.job_handler = job_handler
        self.config = config
        self.currency_map = {
            "دلار": "usd",
            "دلار کانادا": "cad",
            "یورو": "eur",
            "پوند": "gbp",
            "لیر": "try",
            "درهم": "aed",
            "تتر": "usdt",
            "یوان": "cny"
        }
        self.special_map = {
            "فعال": "",
            "خط تیره": "dash",
            "توقف فروش": "stop"
        }
    
    # ============================================================
    # منوی اصلی کیبورد
    # ============================================================
    def get_main_keyboard(self):
        keyboard = [
            [KeyboardButton("📊 وضعیت"), KeyboardButton("📈 دریافت نرخ")],
            [KeyboardButton("💰 تنظیم نرخ دلار"), KeyboardButton("💰 تنظیم نرخ درهم")],
            [KeyboardButton("💰 تنظیم نرخ تتر"), KeyboardButton("👁 مدیریت ارزها")],
            [KeyboardButton("⏱ زمان ارسال"), KeyboardButton("⏸ خاموش")],
            [KeyboardButton("▶ روشن"), KeyboardButton("📞 پشتیبانی")],
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    # ============================================================
    # منوی مدیریت ارزها (با نمایش وضعیت فعلی روی دکمه)
    # ============================================================
    def get_show_keyboard(self):
        keyboard = []
        for name, key in self.currency_map.items():
            show = self.config.get_currency_show(key)
            status = "✅" if show else "❌"
            
            special = self.config.currencies.get(key, {}).get('special', '')
            if special == "stop":
                special_icon = "🛑"
            elif special == "dash":
                special_icon = "—"
            else:
                special_icon = "💰"
            
            keyboard.append([KeyboardButton(f"{status} {special_icon} {name}")])
        keyboard.append([KeyboardButton("🔙 بازگشت")])
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    # ============================================================
    # منوی انتخاب وضعیت فروش
    # ============================================================
    def get_special_keyboard(self, currency_name):
        keyboard = [
            [KeyboardButton(f"💰 فعال {currency_name}")],
            [KeyboardButton(f"— خط تیره {currency_name}")],
            [KeyboardButton(f"🛑 توقف فروش {currency_name}")],
            [KeyboardButton("🔙 بازگشت")],
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    # ============================================================
    # استارت با بنر و بررسی ادمین
    # ============================================================
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        
        if not self.config.is_admin(user_id):
            await update.message.reply_text(
                "⛔ **دسترسی غیرمجاز**\n\n"
                "شما اجازه دسترسی به این ربات را ندارید.",
                parse_mode='Markdown'
            )
            return
        
        try:
            with open("templates/welcome_banner.png", 'rb') as photo:
                await update.message.reply_photo(
                    photo=photo,
                    caption=(
                        "🏦 **به ربات لیر ترکی خوش آمدید**\n\n"
                        "این ربات به شما کمک میکند تا نرخ لحظه‌ای ارزها را دریافت کنید.\n\n"
                        f"📢 **کانال:** {self.config.channel_id}\n"
                        f"⏱ **زمانبندی:** هر {self.config.interval_minutes} دقیقه\n\n"
                        "از دکمه‌های زیر استفاده کنید:"
                    ),
                    reply_markup=self.get_main_keyboard(),
                    parse_mode='Markdown'
                )
        except Exception as e:
            logger.error(f"❌ خطا در ارسال بنر: {e}")
            await update.message.reply_text(
                "🏦 **به ربات لیر ترکی خوش آمدید**\n\n"
                f"📢 کانال: {self.config.channel_id}\n"
                f"⏱ زمانبندی: هر {self.config.interval_minutes} دقیقه\n\n"
                "از دکمه‌های زیر استفاده کنید:",
                reply_markup=self.get_main_keyboard()
            )
    
    # ============================================================
    # ارسال مجدد منو
    # ============================================================
    async def send_menu(self, message):
        user_id = message.chat.id
        if not self.config.is_admin(user_id):
            return
        
        await message.reply_text(
            "🏦 **ربات لیر ترکی**\n\n"
            f"📢 کانال: {self.config.channel_id}\n"
            f"⏱ ارسال هر {self.config.interval_minutes} دقیقه",
            reply_markup=self.get_main_keyboard()
        )
    
    # ============================================================
    # مدیریت پیام‌ها
    # ============================================================
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        
        if not self.config.is_admin(user_id):
            await update.message.reply_text("⛔ شما دسترسی به این ربات را ندارید.")
            return
        
        text = update.message.text.strip()
        
        # ============================================================
        # دکمه‌های اصلی
        # ============================================================
        if text == "📊 وضعیت":
            await self.job_handler.send_status(update.message)
            return
        
        elif text == "📈 دریافت نرخ":
            await update.message.reply_text("🔄 در حال دریافت...")
            await self.job_handler.send_update(update.message)
            return
        
        elif text == "💰 تنظیم نرخ دلار":
            await update.message.reply_text("💰 نرخ دلار را وارد کنید:\nمثال: 192000")
            context.user_data['waiting_for_currency'] = 'usd'
            return
        
        elif text == "💰 تنظیم نرخ درهم":
            await update.message.reply_text("💰 نرخ درهم را وارد کنید:\nمثال: 52300")
            context.user_data['waiting_for_currency'] = 'aed'
            return
        
        elif text == "💰 تنظیم نرخ تتر":
            await update.message.reply_text("💰 نرخ تتر را وارد کنید:\nمثال: 192500")
            context.user_data['waiting_for_currency'] = 'usdt'
            return
        
        elif text == "👁 مدیریت ارزها":
            await update.message.reply_text(
                "👁 مدیریت ارزها\n\n"
                "روی هر ارز کلیک کنید تا وضعیت فروش آن را تغییر دهید:\n\n"
                "💰 = فروش فعال\n— = خط تیره\n🛑 = توقف فروش",
                reply_markup=self.get_show_keyboard()
            )
            return
        
        elif text == "⏱ زمان ارسال":
            await update.message.reply_text("⏱ زمان ارسال را به دقیقه وارد کنید:\nمثال: 10")
            context.user_data['waiting_for_interval'] = True
            return
        
        elif text == "⏸ خاموش":
            self.job_handler.bot_enabled = False
            await update.message.reply_text("⏸ ربات خاموش شد.", reply_markup=self.get_main_keyboard())
            return
        
        elif text == "▶ روشن":
            self.job_handler.bot_enabled = True
            await update.message.reply_text("▶ ربات روشن شد.", reply_markup=self.get_main_keyboard())
            return
        
        elif text == "📞 پشتیبانی":
            await update.message.reply_text(
                "📞 پشتیبانی\n\n"
                "🆔 @Reza_Py\n"
                "⏰ ۸ صبح تا ۱۴"
            )
            return
        
        elif text == "🔙 بازگشت":
            await self.send_menu(update.message)
            return
        
        # ============================================================
        # انتخاب ارز از منوی مدیریت ارزها
        # ============================================================
        if text.startswith("✅") or text.startswith("❌"):
            parts = text.split()
            if len(parts) >= 3:
                currency_name = " ".join(parts[2:])
            else:
                currency_name = parts[-1]
            
            if currency_name in self.currency_map:
                key = self.currency_map[currency_name]
                current_special = self.config.currencies.get(key, {}).get('special', '')
                
                if current_special == "":
                    current_status = "فعال"
                elif current_special == "dash":
                    current_status = "خط تیره"
                else:
                    current_status = "توقف فروش"
                
                await update.message.reply_text(
                    f"📌 {currency_name}\n\n"
                    f"وضعیت فعلی: {current_status}\n\n"
                    "لطفاً حالت مورد نظر را انتخاب کنید:",
                    reply_markup=self.get_special_keyboard(currency_name)
                )
                return
        
        # ============================================================
        # انتخاب وضعیت فروش از منوی انتخاب (نسخه اصلاح شده)
        # ============================================================
        # بررسی دکمه فعال
        if "💰 فعال" in text:
            currency_name = text.replace("💰 فعال", "").strip()
            new_special = ""
            status_text = "فعال"
            
        # بررسی دکمه خط تیره
        elif "خط تیره" in text:
            currency_name = text.replace("— خط تیره", "").strip()
            if not currency_name:
                currency_name = text.replace("خط تیره", "").strip()
            new_special = "dash"
            status_text = "خط تیره"
            
        # بررسی دکمه توقف فروش
        elif "توقف فروش" in text:
            currency_name = text.replace("🛑 توقف فروش", "").strip()
            if not currency_name:
                currency_name = text.replace("توقف فروش", "").strip()
            new_special = "stop"
            status_text = "توقف فروش"
            
        else:
            # اگر هیچکدام نبود، به ادامه برو
            pass

        if 'currency_name' in locals() and currency_name in self.currency_map:
            key = self.currency_map[currency_name]
            
            # ============================================================
            # 📝 ثبت لاگ قبل از تغییر
            # ============================================================
            old_special = self.config.currencies.get(key, {}).get('special', '')
            if old_special == "":
                old_status = "فعال"
            elif old_special == "dash":
                old_status = "خط تیره"
            else:
                old_status = "توقف فروش"
            
            logger.info(f"📝 تغییر وضعیت فروش: {currency_name} | {old_status} → {status_text}")
            
            # ============================================================
            # ذخیره در config.json
            # ============================================================
            self.config.currencies[key]['special'] = new_special
            self.config.save_config()
            
            # ============================================================
            # 🔴 ری‌لود کردن config از فایل (برای به‌روزرسانی)
            # ============================================================
            self.config.load_config()
            
            # ============================================================
            # به‌روزرسانی در job_handler
            # ============================================================
            self.job_handler.manual_rates = self.config.manual_rates
            self.job_handler.rate_calculator.manual_rates = self.config.manual_rates
            
            # ============================================================
            # پیام تایید با نمایش آیکون مناسب
            # ============================================================
            if new_special == "":
                icon = "💰"
            elif new_special == "dash":
                icon = "—"
            else:
                icon = "🛑"
            
            await update.message.reply_text(
                f"✅ وضعیت فروش {currency_name} به **{status_text}** تغییر کرد.\n"
                f"آیکون: {icon}"
            )
            
            # ============================================================
            # نمایش مجدد منوی مدیریت ارزها با دکمه‌های به‌روز
            # ============================================================
            await update.message.reply_text(
                "👁 مدیریت ارزها\n\n"
                "روی هر ارز کلیک کنید تا وضعیت فروش آن را تغییر دهید:\n\n"
                "💰 = فروش فعال\n— = خط تیره\n🛑 = توقف فروش",
                reply_markup=self.get_show_keyboard()
            )
            
            # ============================================================
            # 📝 ثبت لاگ بعد از تغییر (با جزئیات کامل)
            # ============================================================
            logger.info(f"✅ وضعیت فروش {currency_name} با موفقیت به {status_text} تغییر کرد.")
            logger.info(f"   کاربر: {update.effective_user.username or update.effective_user.id}")
            logger.info(f"   زمان: {jdatetime.datetime.now().strftime('%Y/%m/%d - %H:%M:%S')}")
            
            return
        
        # ============================================================
        # دریافت ورودی عددی (تنظیم نرخ و زمان ارسال)
        # ============================================================
        
        # تنظیم نرخ دستی
        if 'waiting_for_currency' in context.user_data:
            try:
                rate = int(text.replace(',', '').strip())
                currency = context.user_data['waiting_for_currency']
                
                if currency in self.config.currencies:
                    self.config.currencies[currency]['buy'] = rate
                    self.config.currencies[currency]['sell'] = rate
                    self.config.save_config()
                    
                    # به‌روزرسانی manual_rates
                    self.job_handler.manual_rates = self.config.manual_rates
                    self.job_handler.rate_calculator.manual_rates = self.config.manual_rates
                    
                    name = self.get_currency_name(currency)
                    await update.message.reply_text(f"✅ نرخ {name} با موفقیت تنظیم شد: {rate:,} تومان")
                    
                    del context.user_data['waiting_for_currency']
                    await self.send_menu(update.message)
                    return
                else:
                    await update.message.reply_text("❌ ارز مورد نظر یافت نشد!")
                    return
            except ValueError:
                await update.message.reply_text("❌ لطفاً یک عدد معتبر وارد کنید!")
                return
        
        # تنظیم زمان ارسال
        if 'waiting_for_interval' in context.user_data:
            try:
                minutes = int(text.replace(',', '').strip())
                if minutes < 1:
                    await update.message.reply_text("❌ حداقل زمان ۱ دقیقه است!")
                    return
                
                self.config.set_interval_minutes(minutes)
                self.job_handler.reschedule_job(minutes)
                await update.message.reply_text(f"⏱ زمان ارسال با موفقیت به {minutes} دقیقه تغییر کرد.")
                
                del context.user_data['waiting_for_interval']
                await self.send_menu(update.message)
                return
            except ValueError:
                await update.message.reply_text("❌ لطفاً یک عدد معتبر وارد کنید!")
                return
        
        # اگر هیچکدام نبود، منو را بفرست
        await self.send_menu(update.message)
    
    # ============================================================
    # توابع کمکی
    # ============================================================
    def get_currency_name(self, key):
        names = {
            "usd": "دلار",
            "cad": "دلار کانادا",
            "aed": "درهم",
            "usdt": "تتر",
            "eur": "یورو",
            "gbp": "پوند",
            "try": "لیر",
            "cny": "یوان"
        }
        return names.get(key, key)