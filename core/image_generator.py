from PIL import Image, ImageDraw, ImageFont
import json
import os
import logging
import jdatetime

logger = logging.getLogger(__name__)

# ============================================================
# توابع کمکی
# ============================================================
def to_persian_numbers(text):
    english_to_persian = {
        '0': '۰', '1': '۱', '2': '۲', '3': '۳', '4': '۴',
        '5': '۵', '6': '۶', '7': '۷', '8': '۸', '9': '۹'
    }
    result = ''
    for char in str(text):
        if char in english_to_persian:
            result += english_to_persian[char]
        else:
            result += char
    return result

def round_to_tens(value):
    if value <= 0:
        return 0
    return round(value / 10) * 10

def format_number(value):
    if value <= 0:
        return "—"
    rounded = round_to_tens(value)
    return f"{rounded:,}"

def get_change_icon(current, previous):
    current_rounded = round_to_tens(current)
    previous_rounded = round_to_tens(previous)
    
    if previous == 0 or previous_rounded == 0:
        return "up"
    if current_rounded > previous_rounded:
        return "up"
    elif current_rounded < previous_rounded:
        return "down"
    else:
        return "stable"

def get_display_value(rate):
    special = rate.get('special', '')
    price = rate.get('sell', 0)
    
    if special == "dash":
        return None, "dash"
    elif special == "stop":
        return None, "stop"
    else:
        return format_number(price), "number"


class ImageGenerator:
    """تولید تصویر با پشتیبانی از آیکون‌های خط تیره و توقف فروش"""
    
    def __init__(self, config=None):
        self.config = config
        self.template_path = "templates/template.png"
        self.font_path = "templates/Vazir.ttf"
        self.positions_path = "templates/positions.json"
        self.toman_icon_path = "templates/icon_toman_ye_fffff.png"
        
        self.icons_path = "templates/icons"
        self.icon_up_path = os.path.join(self.icons_path, "up.png")
        self.icon_down_path = os.path.join(self.icons_path, "down.png")
        self.icon_stable_path = os.path.join(self.icons_path, "stable.png")
        self.icon_stop_path = os.path.join(self.icons_path, "stop.png")
        self.icon_dash_path = os.path.join(self.icons_path, "dash.png")
        
        self.positions = self.load_positions()
        
        if not os.path.exists(self.template_path):
            self.create_default_template()
    
    def load_positions(self):
        default_positions = {
            "currencies": {},
            "footer": {"time_x": 35, "time_y": 1020, "font_size": 20, "color": "#888888"},
            "image": {"width": 1080, "height": 1080},
            "icons": {
                "stop_size": 170,
                "dash_size": 126,
                "toman_size": 56,
                "stable_size": 24
            }
        }
        
        if os.path.exists(self.positions_path):
            try:
                with open(self.positions_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"❌ خطا در بارگذاری positions.json: {e}")
                return default_positions
        else:
            with open(self.positions_path, 'w', encoding='utf-8') as f:
                json.dump(default_positions, f, ensure_ascii=False, indent=4)
            return default_positions
    
    def create_default_template(self):
        os.makedirs("templates", exist_ok=True)
        w = self.positions.get("image", {}).get("width", 1080)
        h = self.positions.get("image", {}).get("height", 1080)
        img = Image.new('RGB', (w, h), color=(20, 25, 45))
        img.save(self.template_path)
    
    def hex_to_rgb(self, hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def get_font(self, size):
        try:
            return ImageFont.truetype(self.font_path, size)
        except:
            logger.warning(f"⚠️ فونت {self.font_path} پیدا نشد!")
            return ImageFont.load_default()
    
    def load_image(self, path, target_size=None):
        if os.path.exists(path):
            try:
                img = Image.open(path)
                if target_size:
                    # ✅ اصلاح: استفاده از thumbnail به جای resize
                    img.thumbnail(target_size, Image.Resampling.LANCZOS)
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                return img
            except Exception as e:
                logger.error(f"❌ خطا در بارگذاری {path}: {e}")
                return None
        return None
    
    def load_toman_icon(self):
        """بارگذاری آیکون تومان با حفظ نسبت ابعاد (بدون کشیدگی)"""
        size = self.positions.get("icons", {}).get("toman_size", 56)
        
        if os.path.exists(self.toman_icon_path):
            try:
                img = Image.open(self.toman_icon_path)
                
                # استفاده از thumbnail برای حفظ نسبت ابعاد
                img.thumbnail((size, size), Image.Resampling.LANCZOS)
                
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                return img
            except Exception as e:
                logger.error(f"❌ خطا در بارگذاری {self.toman_icon_path}: {e}")
                return None
        return None
    
    def load_change_icon(self, icon_type):
        """بارگذاری آیکون تغییرات (up/down/stable) با سایز صحیح از positions.json"""
        size = self.positions.get("icons", {}).get("stable_size", 20)
        if icon_type == "up":
            return self.load_image(self.icon_up_path, target_size=(size, size))
        elif icon_type == "down":
            return self.load_image(self.icon_down_path, target_size=(size, size))
        elif icon_type == "stable":
            return self.load_image(self.icon_stable_path, target_size=(size, size))
        return None
    
    def load_stop_icon(self):
        size = self.positions.get("icons", {}).get("stop_size", 170)
        return self.load_image(self.icon_stop_path, target_size=(size, size))
    
    def load_dash_icon(self):
        size = self.positions.get("icons", {}).get("dash_size", 126)
        return self.load_image(self.icon_dash_path, target_size=(size, size))
    
    def generate(self, rates, output_path="output.png"):
        try:
            # بارگذاری تصویر بدون تغییر سایز (سایز اصلی حفظ می‌شود)
            img = Image.open(self.template_path)
            draw = ImageDraw.Draw(img)
            
            toman_icon = self.load_toman_icon()
            stop_icon = self.load_stop_icon()
            dash_icon = self.load_dash_icon()
            
            currencies_pos = self.positions.get("currencies", {})
            order = ['try', 'usd', 'cad', 'gbp', 'eur', 'aed', 'usdt', 'cny']
            
            for key in order:
                if key not in rates or key not in currencies_pos:
                    continue
                
                rate = rates[key]
                pos = currencies_pos[key]
                font_size = pos.get("font_size", 58)
                font = self.get_font(font_size)
                sell_color = self.hex_to_rgb(pos.get("sell_color", "#FFD700"))
                
                display_value, display_type = get_display_value(rate)
                price = rate.get('sell', 0)
                special = rate.get('special', '')
                
                # ============================================================
                # ۱. آیکون تغییرات (up/down/stable) - فقط در صورت فعال بودن عدد
                # ============================================================
                if self.config and special not in ['dash', 'stop']:
                    previous = self.config.get_previous_rate(key)
                    icon_type = get_change_icon(price, previous)
                    change_icon = self.load_change_icon(icon_type)
                    
                    if change_icon:
                        icon_x = pos.get("x_icon", 0)
                        icon_y = pos.get("y_icon", 0)
                        img.paste(change_icon, (icon_x, icon_y), change_icon)
                
                # ============================================================
                # ۲. نمایش بر اساس نوع
                # ============================================================
                if display_type == "stop" and stop_icon:
                    stop_x = pos.get("x_stop", pos.get("x_num", 0))
                    stop_y = pos.get("y_stop", pos.get("y_num", 0))
                    img.paste(stop_icon, (stop_x, stop_y), stop_icon)
                
                elif display_type == "dash" and dash_icon:
                    dash_x = pos.get("x_dash", pos.get("x_num", 0))
                    dash_y = pos.get("y_dash", pos.get("y_num", 0))
                    img.paste(dash_icon, (dash_x, dash_y), dash_icon)
                
                else:
                    if display_value and display_value != "—":
                        price_persian = to_persian_numbers(display_value)
                        
                        if toman_icon:
                            toman_x = pos.get("x_toman", 0)
                            toman_y = pos.get("y_toman", 0)
                            img.paste(toman_icon, (toman_x, toman_y), toman_icon)
                        
                        num_x = pos.get("x_num", 0)
                        num_y = pos.get("y_num", 0)
                        draw.text((num_x, num_y), price_persian, font=font, fill=sell_color, anchor='lt')
                    else:
                        num_x = pos.get("x_num", 0)
                        num_y = pos.get("y_num", 0)
                        draw.text((num_x, num_y), "—", font=font, fill=sell_color, anchor='lt')
            
            # ============================================================
            # ۴. فوتر
            # ============================================================
            footer = self.positions.get("footer", {})
            font_footer = self.get_font(footer.get("font_size", 20))
            footer_color = self.hex_to_rgb(footer.get("color", "#888888"))
            
            now = jdatetime.datetime.now()
            persian_date = now.strftime("%Y/%m/%d - %H:%M")
            persian_date = to_persian_numbers(persian_date)
            
            draw.text(
                (footer.get("time_x", 35), footer.get("time_y", 1020)), 
                f"🕐 {persian_date}", 
                font=font_footer, 
                fill=footer_color,
                anchor='lt'
            )
            
            img.save(output_path)
            logger.info(f"✅ تصویر در {output_path} ذخیره شد")
            return output_path
            
        except Exception as e:
            logger.error(f"❌ خطا در تولید تصویر: {e}")
            import traceback
            traceback.print_exc()
            return None