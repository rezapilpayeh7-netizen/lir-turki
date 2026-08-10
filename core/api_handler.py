import requests
import logging

logger = logging.getLogger(__name__)

class APIHandler:
    """مدیریت ارتباط با API"""
    
    def __init__(self, config):
        self.api_url = config.api_url
        self.api_key = config.api_key
        self.symbols = config.symbols
    
    def fetch_rates(self):
        """دریافت نرخ از API"""
        try:
            params = {
                'access_key': self.api_key,
                'symbols': self.symbols
            }
            logger.info("📡 دریافت نرخ از API...")
            response = requests.get(self.api_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if not data.get('success'):
                logger.error(f"❌ خطا در پاسخ API: {data}")
                return None
            
            quotes = data.get('quotes', {})
            rates = {}
            for key, value in quotes.items():
                currency = key.replace('USD', '')
                rates[currency] = value
            
            logger.info(f"✅ نرخ از API دریافت شد: {len(rates)} ارز")
            return rates
            
        except Exception as e:
            logger.error(f"❌ خطا در دریافت نرخ از API: {e}")
            return None