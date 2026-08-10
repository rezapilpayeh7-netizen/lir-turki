import json
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """مدیریت تنظیمات"""
    
    def __init__(self):
        self.config = {}
        self.previous_rates_file = "data/previous_rates.json"
        self.previous_rates = {}
        self.load_config()
        self.previous_rates = self.load_previous_rates()
    
    def load_config(self):
        """بارگذاری مجدد config از فایل"""
        with open('config.json', 'r', encoding='utf-8') as f:
            self.config = json.load(f)
    
    @property
    def bot_token(self):
        return os.getenv('BOT_TOKEN')
    
    @property
    def admin_id(self):
        try:
            return int(os.getenv('ADMIN_ID', 0))
        except:
            return 0
    
    @property
    def channel_id(self):
        return self.config['telegram']['channel_id']
    
    @property
    def api_url(self):
        return self.config['api']['url']
    
    @property
    def api_key(self):
        return os.getenv('API_KEY') or self.config['api']['access_key']
    
    @property
    def symbols(self):
        return self.config['api']['symbols']
    
    @property
    def currencies(self):
        return self.config['currencies']
    
    @property
    def interval_minutes(self):
        return self.config['schedule']['interval_minutes']
    
    @property
    def manual_rates(self):
        rates = {}
        for key, value in self.config['currencies'].items():
            if value.get('source') == 'manual':
                rates[key] = {
                    'buy': value.get('buy', 0),
                    'sell': value.get('sell', 0)
                }
        return rates
    
    def is_admin(self, user_id):
        return user_id == self.admin_id
    
    # ============================================================
    # متدهای نرخ قبلی
    # ============================================================
    def load_previous_rates(self):
        if os.path.exists(self.previous_rates_file):
            try:
                with open(self.previous_rates_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_previous_rates(self, rates):
        os.makedirs("data", exist_ok=True)
        rates_to_save = {}
        for key, rate in rates.items():
            rates_to_save[key] = rate.get('sell', 0)
        with open(self.previous_rates_file, 'w', encoding='utf-8') as f:
            json.dump(rates_to_save, f, ensure_ascii=False, indent=4)
        self.previous_rates = rates_to_save
    
    def get_previous_rate(self, key):
        return self.previous_rates.get(key, 0)
    
    def update_previous_rates(self, current_rates):
        self.save_previous_rates(current_rates)
    
    # ============================================================
    # سایر متدها
    # ============================================================
    def set_interval_minutes(self, minutes):
        self.config['schedule']['interval_minutes'] = minutes
        self.save_config()
    
    def set_channel_id(self, channel_id):
        self.config['telegram']['channel_id'] = channel_id
        self.save_config()
        os.environ['CHANNEL_ID'] = channel_id
    
    def get_currency_show(self, currency_key):
        return self.config['currencies'].get(currency_key, {}).get('show', True)
    
    def set_currency_show(self, currency_key, show):
        if currency_key in self.config['currencies']:
            self.config['currencies'][currency_key]['show'] = show
            self.save_config()
    
    def get_visible_currencies(self):
        visible = []
        for key, value in self.config['currencies'].items():
            if value.get('show', True):
                visible.append(key)
        return visible
    
    def get_currency_source(self, currency_key):
        return self.config['currencies'].get(currency_key, {}).get('source', 'api')
    
    def set_manual_rate(self, currency_key, buy, sell):
        if currency_key in self.config['currencies']:
            self.config['currencies'][currency_key]['buy'] = buy
            self.config['currencies'][currency_key]['sell'] = sell
            self.save_config()
    
    def save_config(self):
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=4)