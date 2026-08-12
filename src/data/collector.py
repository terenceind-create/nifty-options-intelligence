# src/data/collector.py
import threading
import time
from datetime import datetime, timedelta
import pytz
from loguru import logger
import upstox_client
from upstox_client.rest import ApiException

from src.data.upstox_auth import UpstoxAuth
from src.analysis.greeks_calculator import GreeksCalculator
from src.data.models import get_db_session, OptionsTick
from src.utils.market_calendar import market_calendar
from config.settings import settings


class DataCollector:
    """Live Data Collection with Auto Token Check"""
    
    def __init__(self, refresh_interval=None):
        self.auth = UpstoxAuth()
        self.greeks_calc = GreeksCalculator()
        self.ist = pytz.timezone('Asia/Kolkata')
        self.running = False
        self.data_cache = {}
        self.refresh_interval = refresh_interval or settings.DEFAULT_REFRESH
    
    def start_collection(self):
        # Check token FIRST, prompt if expired
        if not self.auth.ensure_valid_token():
            logger.error("❌ Cannot start — invalid token")
            return False
        
        self.running = True
        logger.info(f"Starting collection for {len(settings.TRACKING_SYMBOLS)} stocks")
        logger.info(f"Refresh: {self.refresh_interval}s")
        
        expiry = market_calendar.get_stock_expiry()
        days = (expiry - datetime.now(self.ist).date()).days
        logger.info(f"Expiry: {expiry} ({days} days)")
        
        collect_thread = threading.Thread(target=self._collection_loop, daemon=True)
        collect_thread.start()
        return True
    
    def _get_attr(self, obj, attr, default=0):
        if obj is None:
            return default
        if isinstance(obj, dict):
            return obj.get(attr, default)
        return getattr(obj, attr, default)
    
    def _find_atm_strike(self, spot_price, strikes):
        if not strikes:
            return round(spot_price / 50) * 50
        return min(strikes, key=lambda x: abs(x - spot_price))
    
    def _collection_loop(self):
        while self.running:
            try:
                # Check token validity before each cycle
                if not self.auth.is_token_valid():
                    logger.error("❌ Token expired during collection!")
                    if not self.auth.ensure_valid_token():
                        logger.error("Cannot renew token. Stopping.")
                        break
                
                if self._is_market_open():
                    self._collect_all_stocks()
                else:
                    logger.debug("Market closed")
                
                time.sleep(self.refresh_interval)
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Loop error: {e}")
                time.sleep(60)
    
    def _collect_all_stocks(self):
        logger.info(f"COLLECTING {len(settings.TRACKING_SYMBOLS)} STOCKS")
        
        current_date = datetime.now(self.ist).date()
        expiry_date = market_calendar.get_stock_expiry(current_date)
        days_to_expiry = (expiry_date - current_date).days
        expiry_str = expiry_date.strftime('%Y-%m-%d')
        time_adj = market_calendar.get_time_aware_adjustments(days_to_expiry)
        
        success_count = 0
        
        for symbol in settings.TRACKING_SYMBOLS:
            try:
                instrument_key = settings.INSTRUMENT_KEYS.get(symbol)
                if not instrument_key:
                    continue
                
                spot_price = self._get_spot(instrument_key)
                if not spot_price:
                    continue
                
                chain = self._get_option_chain(instrument_key, expiry_str)
                
                all_strikes = []
                if chain:
                    for item in chain:
                        strike = self._get_attr(item, 'strike_price', 0)
                        if strike > 0:
                            all_strikes.append(strike)
                
                atm_strike = self._find_atm_strike(spot_price, all_strikes)
                
                data = {
                    'spot_price': spot_price, 'atm_strike': atm_strike,
                    'expiry_date': expiry_str, 'days_to_expiry': days_to_expiry,
                    'expiry_phase': time_adj['expiry_context']['expiry_phase'],
                    'market_phase': time_adj['market_phase']['phase'],
                    'theta_multiplier': time_adj['expiry_context']['theta_acceleration'],
                    'vol_multiplier': time_adj['effective_volatility_multiplier'],
                    'ce_ltp': 0, 'ce_bid': 0, 'ce_ask': 0,
                    'ce_oi': 0, 'ce_oi_change': 0, 'ce_volume': 0, 'ce_iv': 0,
                    'ce_delta': 0, 'ce_gamma': 0, 'ce_theta': 0, 'ce_vega': 0,
                    'pe_ltp': 0, 'pe_bid': 0, 'pe_ask': 0,
                    'pe_oi': 0, 'pe_oi_change': 0, 'pe_volume': 0, 'pe_iv': 0,
                    'pe_delta': 0, 'pe_gamma': 0, 'pe_theta': 0, 'pe_vega': 0,
                    'pcr': 0,
                }
                
                if chain:
                    for item in chain:
                        strike = self._get_attr(item, 'strike_price', 0)
                        if strike == atm_strike:
                            data['pcr'] = round(self._get_attr(item, 'pcr', 0), 2)
                            
                            call = self._get_attr(item, 'call_options', None)
                            if call:
                                market = self._get_attr(call, 'market_data', None)
                                greeks = self._get_attr(call, 'option_greeks', None)
                                if market:
                                    data['ce_ltp'] = self._get_attr(market, 'ltp', 0)
                                    data['ce_bid'] = self._get_attr(market, 'bid_price', 0)
                                    data['ce_ask'] = self._get_attr(market, 'ask_price', 0)
                                    data['ce_oi'] = int(self._get_attr(market, 'oi', 0))
                                    data['ce_oi_change'] = data['ce_oi'] - int(self._get_attr(market, 'prev_oi', 0))
                                    data['ce_volume'] = int(self._get_attr(market, 'volume', 0))
                                if greeks:
                                    iv_val = self._get_attr(greeks, 'iv', 0)
                                    if iv_val > 1: iv_val /= 100.0
                                    data['ce_iv'] = iv_val
                                    data['ce_delta'] = self._get_attr(greeks, 'delta', 0)
                                    data['ce_gamma'] = self._get_attr(greeks, 'gamma', 0)
                                    data['ce_theta'] = self._get_attr(greeks, 'theta', 0)
                                    data['ce_vega'] = self._get_attr(greeks, 'vega', 0)
                            
                            put = self._get_attr(item, 'put_options', None)
                            if put:
                                market = self._get_attr(put, 'market_data', None)
                                greeks = self._get_attr(put, 'option_greeks', None)
                                if market:
                                    data['pe_ltp'] = self._get_attr(market, 'ltp', 0)
                                    data['pe_bid'] = self._get_attr(market, 'bid_price', 0)
                                    data['pe_ask'] = self._get_attr(market, 'ask_price', 0)
                                    data['pe_oi'] = int(self._get_attr(market, 'oi', 0))
                                    data['pe_oi_change'] = data['pe_oi'] - int(self._get_attr(market, 'prev_oi', 0))
                                    data['pe_volume'] = int(self._get_attr(market, 'volume', 0))
                                if greeks:
                                    iv_val = self._get_attr(greeks, 'iv', 0)
                                    if iv_val > 1: iv_val /= 100.0
                                    data['pe_iv'] = iv_val
                                    data['pe_delta'] = self._get_attr(greeks, 'delta', 0)
                                    data['pe_gamma'] = self._get_attr(greeks, 'gamma', 0)
                                    data['pe_theta'] = self._get_attr(greeks, 'theta', 0)
                                    data['pe_vega'] = self._get_attr(greeks, 'vega', 0)
                            break
                
                if data['ce_iv'] > 0 or data['pe_iv'] > 0:
                    greeks_calc = self._calculate_greeks_with_iv(data)
                    data.update(greeks_calc)
                
                self._store_to_database(symbol, data)
                self.data_cache[symbol] = data
                success_count += 1
                time.sleep(0.3)
                
            except Exception as e:
                logger.error(f"{symbol}: {e}")
        
        logger.info(f"Collected {success_count}/{len(settings.TRACKING_SYMBOLS)} stocks")
    
    def _get_spot(self, instrument_key):
        try:
            market_api = upstox_client.MarketQuoteApi(self.auth.api_client)
            response = market_api.ltp(symbol=instrument_key, api_version='2.0')
            if hasattr(response, 'data') and response.data:
                for key, data in response.data.items():
                    val = self._get_attr(data, 'last_price', 0)
                    if val > 0:
                        return val
        except:
            pass
        return None
    
    def _get_option_chain(self, instrument_key, expiry_str):
        try:
            options_api = upstox_client.OptionsApi(self.auth.api_client)
            response = options_api.get_put_call_option_chain(
                instrument_key=instrument_key, expiry_date=expiry_str
            )
            if hasattr(response, 'data') and response.data:
                return response.data
        except:
            pass
        return []
    
    def _calculate_greeks_with_iv(self, data):
        try:
            S = data.get('spot_price', 0)
            K = data.get('atm_strike', 0)
            T = max(data.get('days_to_expiry', 1) / 365.0, 0.001)
            r = settings.RISK_FREE_RATE
            theta_mult = data.get('theta_multiplier', 1.0)
            ce_iv = data.get('ce_iv', 0.25) if data.get('ce_iv', 0) > 0 else 0.25
            pe_iv = data.get('pe_iv', 0.25) if data.get('pe_iv', 0) > 0 else 0.25
            
            ce = self.greeks_calc.calculate_all_greeks('call', S, K, T, r, ce_iv)
            pe = self.greeks_calc.calculate_all_greeks('put', S, K, T, r, pe_iv)
            
            return {
                'ce_delta': ce.get('delta', 0), 'ce_gamma': ce.get('gamma', 0),
                'ce_theta': ce.get('theta', 0) * theta_mult, 'ce_vega': ce.get('vega', 0),
                'pe_delta': pe.get('delta', 0), 'pe_gamma': pe.get('gamma', 0),
                'pe_theta': pe.get('theta', 0) * theta_mult, 'pe_vega': pe.get('vega', 0),
            }
        except:
            return {}
    
    def _store_to_database(self, symbol, data):
        try:
            session = get_db_session()
            tick = OptionsTick(
                symbol=symbol, timestamp=datetime.now(self.ist),
                spot_price=data.get('spot_price'), atm_strike=data.get('atm_strike'),
                days_to_expiry=data.get('days_to_expiry'),
                ce_ltp=data.get('ce_ltp'), ce_bid=data.get('ce_bid'), ce_ask=data.get('ce_ask'),
                ce_oi=data.get('ce_oi'), ce_oi_change=data.get('ce_oi_change'), ce_volume=data.get('ce_volume'),
                ce_iv=data.get('ce_iv'), ce_delta=data.get('ce_delta'), ce_gamma=data.get('ce_gamma'),
                ce_theta=data.get('ce_theta'), ce_vega=data.get('ce_vega'),
                pe_ltp=data.get('pe_ltp'), pe_bid=data.get('pe_bid'), pe_ask=data.get('pe_ask'),
                pe_oi=data.get('pe_oi'), pe_oi_change=data.get('pe_oi_change'), pe_volume=data.get('pe_volume'),
                pe_iv=data.get('pe_iv'), pe_delta=data.get('pe_delta'), pe_gamma=data.get('pe_gamma'),
                pe_theta=data.get('pe_theta'), pe_vega=data.get('pe_vega'),
                pcr=data.get('pcr')
            )
            session.add(tick)
            session.commit()
            session.close()
        except:
            pass
    
    def _is_market_open(self):
        now = datetime.now(self.ist)
        if now.weekday() >= 5:
            return False
        return now.replace(hour=9, minute=15, second=0) <= now <= now.replace(hour=15, minute=30, second=0)
    
    def stop_collection(self):
        self.running = False