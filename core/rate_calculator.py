import json
import os

class RateCalculator:
    """محاسبه نرخ‌های نهایی با منطق تبدیل ارز به دلار - تک نرخی"""
    
    def __init__(self, manual_rates):
        self.manual_rates = manual_rates
    
    def _get_special_from_config(self, currency_key):
        """خواندن مستقیم special از config.json (بدون استفاده از Config کلاس)"""
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('currencies', {}).get(currency_key, {}).get('special', '')
        except Exception as e:
            print(f"⚠️ خطا در خواندن special از config: {e}")
            return ''
    
    def calculate(self, api_rates, visible_currencies=None):
        if not api_rates:
            return None
        
        usd_data = self.manual_rates.get('usd', {})
        usd_buy = usd_data.get('buy', 0)
        usd_sell = usd_data.get('sell', 0)
        
        if usd_buy == 0 or usd_sell == 0:
            return None
        
        final_rates = {}
        
        # ارزهای دستی
        final_rates['usd'] = {
            'name': 'دلار آمریکا',
            'flag': '🇺🇸',
            'buy': usd_buy,
            'sell': usd_sell
        }
        
        aed_data = self.manual_rates.get('aed', {})
        final_rates['aed'] = {
            'name': 'درهم امارات',
            'flag': '🇦🇪',
            'buy': aed_data.get('buy', 0),
            'sell': aed_data.get('sell', 0)
        }
        
        usdt_data = self.manual_rates.get('usdt', {})
        final_rates['usdt'] = {
            'name': 'تتر',
            'flag': '🪙',
            'buy': usdt_data.get('buy', 0),
            'sell': usdt_data.get('sell', 0)
        }
        
        def convert_to_usd_rate(api_rate):
            if api_rate <= 0:
                return None
            return 1 / api_rate
        
        # ارزهای از API
        if 'CAD' in api_rates:
            cad_rate = convert_to_usd_rate(api_rates['CAD'])
            if cad_rate:
                final_rates['cad'] = {
                    'name': 'دلار کانادا',
                    'flag': '🇨🇦',
                    'buy': int(usd_buy * cad_rate),
                    'sell': int(usd_sell * cad_rate)
                }
        
        if 'EUR' in api_rates:
            eur_rate = convert_to_usd_rate(api_rates['EUR'])
            if eur_rate:
                final_rates['eur'] = {
                    'name': 'یورو',
                    'flag': '🇪🇺',
                    'buy': int(usd_buy * eur_rate),
                    'sell': int(usd_sell * eur_rate)
                }
        
        if 'GBP' in api_rates:
            gbp_rate = convert_to_usd_rate(api_rates['GBP'])
            if gbp_rate:
                final_rates['gbp'] = {
                    'name': 'پوند انگلیس',
                    'flag': '🇬🇧',
                    'buy': int(usd_buy * gbp_rate),
                    'sell': int(usd_sell * gbp_rate)
                }
        
        if 'TRY' in api_rates:
            try_rate = convert_to_usd_rate(api_rates['TRY'])
            if try_rate:
                final_rates['try'] = {
                    'name': 'لیر ترکیه',
                    'flag': '🇹🇷',
                    'buy': int(usd_buy * try_rate),
                    'sell': int(usd_sell * try_rate)
                }
        
        if 'CNY' in api_rates:
            cny_rate = convert_to_usd_rate(api_rates['CNY'])
            if cny_rate:
                final_rates['cny'] = {
                    'name': 'یوان چین',
                    'flag': '🇨🇳',
                    'buy': int(usd_buy * cny_rate),
                    'sell': int(usd_sell * cny_rate)
                }
        
        # ============================================================
        # فیلتر بر اساس ارزهای قابل نمایش
        # ============================================================
        if visible_currencies:
            filtered_rates = {}
            filtered_rates['usd'] = final_rates['usd']
            for key in visible_currencies:
                if key in final_rates and key != 'usd':
                    filtered_rates[key] = final_rates[key]
            final_rates = filtered_rates
        
        # ============================================================
        # 🔴 اضافه کردن `special` به تمام ارزها (خواندن مستقیم از فایل)
        # ============================================================
        for key in list(final_rates.keys()):
            special = self._get_special_from_config(key)
            final_rates[key]['special'] = special  # حتی اگر خالی باشد، اضافه کن
        
        # ============================================================
        # مرتب‌سازی بر اساس اولویت
        # ============================================================
        order = ['usd', 'cad', 'eur', 'gbp', 'try', 'aed', 'usdt', 'cny']
        sorted_rates = {}
        for key in order:
            if key in final_rates:
                sorted_rates[key] = final_rates[key]
        
        return sorted_rates