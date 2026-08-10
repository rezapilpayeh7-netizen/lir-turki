from datetime import datetime
import jdatetime

class MessageBuilder:
    """ساخت پیام - با پشتیبانی از خط تیره و توقف فروش"""
    
    @staticmethod
    def get_persian_date():
        now = jdatetime.datetime.now()
        return now.strftime("%Y/%m/%d - %H:%M:%S")
    
    @staticmethod
    def get_persian_date_short():
        now = jdatetime.datetime.now()
        return now.strftime("%Y/%m/%d - %H:%M")
    
    @staticmethod
    def round_to_tens(value):
        if value <= 0:
            return 0
        return round(value / 10) * 10
    
    @staticmethod
    def format_number(value):
        if value <= 0:
            return "—"
        rounded = MessageBuilder.round_to_tens(value)
        return f"{rounded:,}"
    
    @staticmethod
    def get_change_icon(current, previous, special=''):
        """تعیین آیکون تغییرات - در صورت dash/stop خالی برگردان"""
        if special in ['dash', 'stop']:
            return ""
        
        current_rounded = MessageBuilder.round_to_tens(current)
        previous_rounded = MessageBuilder.round_to_tens(previous)
        
        if previous == 0 or previous_rounded == 0:
            return "🆕"
        if current_rounded > previous_rounded:
            return "📈"
        elif current_rounded < previous_rounded:
            return "📉"
        else:
            return "➖"
    
    @staticmethod
    def get_display_value(rate):
        special = rate.get('special', '')
        price = rate.get('sell', 0)
        
        if special == "dash":
            return "—", "dash"
        elif special == "stop":
            return "⛔", "stop"
        else:
            return MessageBuilder.format_number(price), "number"
    
    @staticmethod
    def build_text_message(rates, config=None):
        if not rates:
            return None
        
        persian_time = MessageBuilder.get_persian_date_short()
        
        message = "📊 **نرخ لحظه‌ای ارزها**\n"
        message += f"🕐 {persian_time}\n\n"
        message += "——————————————\n"
        
        for key, rate in rates.items():
            display_value, display_type = MessageBuilder.get_display_value(rate)
            special = rate.get('special', '')
            
            if config and display_type == "number":
                previous = config.get_previous_rate(key)
                icon = MessageBuilder.get_change_icon(rate.get('sell', 0), previous, special)
            else:
                icon = ""
            
            if display_type == "stop":
                message += f"{rate['flag']} {rate['name']}: **⛔ توقف فروش**\n"
            elif display_type == "dash":
                message += f"{rate['flag']} {rate['name']}: **—** تومان\n"
            else:
                message += f"{rate['flag']} {rate['name']}: **{display_value}** تومان {icon}\n"
        
        message += "——————————————\n"
        return message
    
    @staticmethod
    def build_image_caption():
        persian_time = MessageBuilder.get_persian_date()
        return f"📆 بروزرسانی: {persian_time}"
    
    @staticmethod
    def build_status_message(rates, bot_enabled, channel_id, interval_minutes):
        status_text = "✅ فعال" if bot_enabled else "❌ غیرفعال"
        
        message = f"📊 **وضعیت ربات**\n\n"
        message += f"🔹 وضعیت: {status_text}\n"
        message += f"🔹 کانال: {channel_id}\n"
        message += f"🔹 زمانبندی: هر {interval_minutes} دقیقه\n\n"
        message += "📝 **نرخ‌های فعلی:**\n"
        
        for key in ['usd', 'aed', 'usdt']:
            if key in rates:
                price = rates[key].get('sell', 0)
                formatted_price = MessageBuilder.format_number(price)
                name = rates[key].get('name', key.upper())
                flag = rates[key].get('flag', '')
                message += f"{flag} {name}: {formatted_price} تومان\n"
        
        return message