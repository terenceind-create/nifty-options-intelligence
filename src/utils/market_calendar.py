# src/utils/market_calendar.py
"""
Market Calendar & Time Intelligence Module
Handles expiry dates, market phases, time-aware adjustments
"""
from datetime import datetime, date, timedelta
import calendar
import pytz
from typing import Optional, Tuple
from loguru import logger


class MarketCalendar:
    """
    Complete market calendar with expiry awareness for:
    - Stock options (monthly - last Tuesday)
    - Nifty weekly options (every Thursday)
    - Sensex weekly options (every Thursday)
    - Market phases (opening, mid, closing)
    """
    
    def __init__(self):
        self.ist = pytz.timezone('Asia/Kolkata')
        self.nse_holidays = self._get_nse_holidays_2026()
    
    def _get_nse_holidays_2026(self) -> list:
        """NSE trading holidays for 2026"""
        return [
            date(2026, 1, 26),   # Republic Day
            date(2026, 3, 2),    # Mahashivratri
            date(2026, 3, 20),   # Holi
            date(2026, 4, 14),   # Ambedkar Jayanti
            date(2026, 4, 18),   # Good Friday
            date(2026, 5, 7),    # Maharashtra Day
            date(2026, 8, 15),   # Independence Day
            date(2026, 9, 16),   # Ganesh Chaturthi
            date(2026, 10, 2),   # Gandhi Jayanti
            date(2026, 10, 21),  # Diwali
            date(2026, 11, 15),  # Guru Nanak Jayanti
            date(2026, 12, 25),  # Christmas
        ]
    
    def is_trading_day(self, check_date: Optional[date] = None) -> bool:
        """Check if given date is a trading day"""
        if check_date is None:
            check_date = date.today()
        
        # Weekend check
        if check_date.weekday() >= 5:
            return False
        
        # Holiday check
        if check_date in self.nse_holidays:
            return False
        
        return True
    
    def get_stock_expiry(self, from_date: Optional[date] = None) -> date:
        """
        Get monthly stock option expiry (last Tuesday of month)
        Falls back to previous trading day if holiday
        """
        if from_date is None:
            from_date = date.today()
        
        current_month = from_date.month
        current_year = from_date.year
        
        # Find last Tuesday of current month
        c = calendar.monthcalendar(current_year, current_month)
        last_tuesdays = [week[1] for week in c if week[1] != 0]
        last_tue = max(last_tuesdays)
        expiry = date(current_year, current_month, last_tue)
        
        # If today is after expiry, get next month's expiry
        if from_date > expiry:
            if current_month == 12:
                current_month = 1
                current_year += 1
            else:
                current_month += 1
            
            c = calendar.monthcalendar(current_year, current_month)
            last_tuesdays = [week[1] for week in c if week[1] != 0]
            last_tue = max(last_tuesdays)
            expiry = date(current_year, current_month, last_tue)
        
        # Adjust for holidays
        while not self.is_trading_day(expiry):
            expiry = expiry - timedelta(days=1)
        
        return expiry
    
    def get_nifty_weekly_expiry(self, from_date: Optional[date] = None) -> date:
        """
        Get Nifty weekly expiry (every Thursday, or previous trading day)
        """
        if from_date is None:
            from_date = date.today()
        
        # Find nearest Thursday
        days_until_thursday = (3 - from_date.weekday()) % 7
        
        # If it's Thursday after market close, move to next Thursday
        if days_until_thursday == 0:
            now = datetime.now(self.ist)
            if now.hour >= 15 and now.minute >= 30:
                days_until_thursday = 7
        
        # If Thursday is more than 7 days away, find nearest
        if days_until_thursday == 0 and self.is_trading_day(from_date):
            expiry = from_date
        else:
            expiry = from_date + timedelta(days=days_until_thursday if days_until_thursday > 0 else 7)
        
        # Adjust for holidays
        while not self.is_trading_day(expiry):
            expiry = expiry - timedelta(days=1)
        
        return expiry
    
    def get_market_phase(self) -> dict:
        """
        Determine current market phase with time-based characteristics
        
        Returns detailed information about the current trading session phase
        """
        now = datetime.now(self.ist)
        current_time = now.hour + now.minute / 60.0
        weekday = now.weekday()
        
        # Default: market closed
        phase_info = {
            'is_open': False,
            'phase': 'closed',
            'time_description': 'Market Closed',
            'volatility_multiplier': 1.0,
            'theta_impact': 'normal',
            'gamma_importance': 'normal',
            'minutes_to_close': 0,
            'minutes_from_open': 0,
            'trading_day': self.is_trading_day(),
            'next_expiry_days': 0,
            'day_of_week': calendar.day_name[weekday],
        }
        
        if not self.is_trading_day():
            return phase_info
        
        # Pre-open
        if 9.00 <= current_time < 9.15:
            phase_info.update({
                'is_open': False,
                'phase': 'pre_open',
                'time_description': 'Pre-Open Session',
            })
            return phase_info
        
        # Market open
        if 9.15 <= current_time < 15.30:
            minutes_from_open = int((current_time - 9.25) * 60)  # 9:15 open
            minutes_to_close = int((15.50 - current_time) * 60)  # 15:30 close
            
            phase_info['is_open'] = True
            phase_info['minutes_to_close'] = minutes_to_close
            phase_info['minutes_from_open'] = minutes_from_open
            
            # Opening phase (9:15 - 10:15)
            if current_time < 10.25:
                phase_info.update({
                    'phase': 'opening',
                    'time_description': 'Opening Session - High Volatility',
                    'volatility_multiplier': 1.4,
                    'theta_impact': 'low',  # Theta hasn't kicked in yet
                    'gamma_importance': 'high',  # Gamma drives moves at open
                })
            
            # Mid-session (10:15 - 14:00)
            elif 10.25 <= current_time < 14.00:
                phase_info.update({
                    'phase': 'mid_session',
                    'time_description': 'Mid Session - Normal Trading',
                    'volatility_multiplier': 0.9,
                    'theta_impact': 'normal',
                    'gamma_importance': 'moderate',
                })
            
            # Pre-close (14:00 - 15:00)
            elif 14.00 <= current_time < 15.00:
                phase_info.update({
                    'phase': 'pre_close',
                    'time_description': 'Pre-Close - Position Adjustment',
                    'volatility_multiplier': 1.1,
                    'theta_impact': 'increasing',
                    'gamma_importance': 'increasing',
                })
            
            # Closing rush (15:00 - 15:30)
            elif 15.00 <= current_time < 15.30:
                phase_info.update({
                    'phase': 'closing',
                    'time_description': 'Closing Rush - Gamma/Theta Dominance',
                    'volatility_multiplier': 1.3,
                    'theta_impact': 'maximum',
                    'gamma_importance': 'high',
                })
        
        # Post-market
        elif 15.30 <= current_time < 16.00:
            phase_info.update({
                'phase': 'post_close',
                'time_description': 'Post-Close Processing',
            })
        
        return phase_info
    
    def get_expiry_context(self, days_to_expiry: int) -> dict:
        """
        Get expiry context with appropriate adjustments
        
        This is CRITICAL for accurate Greek interpretation
        """
        context = {
            'days_to_expiry': days_to_expiry,
            'expiry_phase': '',
            'theta_acceleration': 1.0,
            'gamma_explosion_risk': 'none',
            'iv_behavior': 'normal',
            'delivery_risk': 'none',
            'trading_recommendation': '',
        }
        
        # Expiry day
        if days_to_expiry == 0:
            context.update({
                'expiry_phase': 'EXPIRY_DAY',
                'theta_acceleration': 5.0,  # Extreme theta decay
                'gamma_explosion_risk': 'extreme',
                'iv_behavior': 'crush_expected',
                'delivery_risk': 'high_for_itm',
                'trading_recommendation': 'Close ITM positions or prepare for delivery',
            })
        
        # Day before expiry
        elif days_to_expiry == 1:
            context.update({
                'expiry_phase': 'PRE_EXPIRY',
                'theta_acceleration': 2.5,
                'gamma_explosion_risk': 'high',
                'iv_behavior': 'crush_accelerating',
                'delivery_risk': 'moderate',
                'trading_recommendation': 'Roll positions to next expiry',
            })
        
        # 2-3 days to expiry
        elif 2 <= days_to_expiry <= 3:
            context.update({
                'expiry_phase': 'EXPIRY_WEEK',
                'theta_acceleration': 1.5,
                'gamma_explosion_risk': 'moderate',
                'iv_behavior': 'beginning_crush',
                'delivery_risk': 'low',
                'trading_recommendation': 'Monitor ITM positions',
            })
        
        # 4-7 days to expiry
        elif 4 <= days_to_expiry <= 7:
            context.update({
                'expiry_phase': 'NEAR_EXPIRY',
                'theta_acceleration': 1.2,
                'gamma_explosion_risk': 'low',
                'iv_behavior': 'normal',
                'delivery_risk': 'none',
                'trading_recommendation': 'Good for theta strategies',
            })
        
        # More than a week
        else:
            context.update({
                'expiry_phase': 'FAR_EXPIRY',
                'theta_acceleration': 1.0,
                'gamma_explosion_risk': 'none',
                'iv_behavior': 'stable',
                'delivery_risk': 'none',
                'trading_recommendation': 'Directional strategies preferred',
            })
        
        return context
    
    def get_time_aware_adjustments(self, days_to_expiry: int) -> dict:
        """
        Get combined time + expiry adjustments for Greeks
        """
        market_phase = self.get_market_phase()
        expiry_context = self.get_expiry_context(days_to_expiry)
        
        # Combined volatility multiplier
        vol_mult = (market_phase.get('volatility_multiplier', 1.0) * 
                    expiry_context.get('theta_acceleration', 1.0))
        
        return {
            'market_phase': market_phase,
            'expiry_context': expiry_context,
            'effective_volatility_multiplier': round(vol_mult, 2),
            'is_high_risk_period': (
                market_phase.get('phase') in ['opening', 'closing'] and 
                expiry_context.get('days_to_expiry', 30) <= 3
            ),
            'is_theta_critical': (
                expiry_context.get('days_to_expiry', 30) <= 1 or
                market_phase.get('phase') == 'closing'
            ),
            'is_gamma_driven': (
                expiry_context.get('gamma_explosion_risk') in ['extreme', 'high'] or
                market_phase.get('gamma_importance') == 'high'
            ),
            'should_avoid_premium_buying': (
                expiry_context.get('days_to_expiry', 30) <= 1 and
                market_phase.get('phase') == 'closing'
            ),
        }


# Global instance
market_calendar = MarketCalendar()