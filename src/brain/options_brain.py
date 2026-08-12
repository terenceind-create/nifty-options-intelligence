# src/brain/options_brain.py
from typing import Dict, List, Optional
from datetime import datetime
from loguru import logger

class OptionsBrain:
    """
    AI Brain for options analysis
    Analyzes Greeks, IV, OI patterns, and generates directional signals
    """
    
    def __init__(self):
        self.ist_timezone = None
        try:
            import pytz
            self.ist_timezone = pytz.timezone('Asia/Kolkata')
        except:
            pass
    
    def analyze_stock(self, symbol: str, data: Dict) -> Dict:
        """
        Analyze a single stock and generate trading signals
        
        Args:
            symbol: Stock symbol
            data: Dictionary with all metrics
        """
        
        analysis = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'direction': 'neutral',
            'conviction': 0.0,
            'signals': [],
            'risks': [],
            'greek_analysis': {},
            'flow_analysis': {},
            'iv_analysis': {}
        }
        
        try:
            # 1. Analyze Greeks
            greek_signal = self._analyze_greeks(data)
            analysis['greek_analysis'] = greek_signal
            
            # 2. Analyze Flow (OI + Volume)
            flow_signal = self._analyze_flow(data)
            analysis['flow_analysis'] = flow_signal
            
            # 3. Analyze IV
            iv_signal = self._analyze_iv(data)
            analysis['iv_analysis'] = iv_signal
            
            # 4. Combine signals for directional view
            direction, conviction = self._combine_signals(
                greek_signal, flow_signal, iv_signal
            )
            analysis['direction'] = direction
            analysis['conviction'] = conviction
            
            # 5. Generate alerts
            analysis['signals'] = self._generate_signals(analysis)
            analysis['risks'] = self._generate_risks(analysis)
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
        
        return analysis
    
    def _analyze_greeks(self, data: Dict) -> Dict:
        """Analyze Greek dynamics"""
        ce_delta = data.get('ce_delta', 0)
        ce_gamma = data.get('ce_gamma', 0)
        ce_theta = data.get('ce_theta', 0)
        pe_delta = data.get('pe_delta', 0)
        
        signals = []
        bias = 'neutral'
        
        # Delta analysis
        delta_skew = ce_delta / abs(pe_delta) if pe_delta != 0 else 1
        
        if delta_skew > 1.2:
            bias = 'bullish'
            signals.append("Call delta dominant - bullish pressure")
        elif delta_skew < 0.8:
            bias = 'bearish'
            signals.append("Put delta dominant - bearish pressure")
        
        # Gamma analysis
        gamma_risk = False
        if ce_gamma > 0.01:
            gamma_risk = True
            signals.append(f"High gamma ({ce_gamma:.4f}) - potential sharp moves")
        
        return {
            'bias': bias,
            'delta_skew': round(delta_skew, 2),
            'gamma_risk': gamma_risk,
            'signals': signals
        }
    
    def _analyze_flow(self, data: Dict) -> Dict:
        """Analyze OI and volume flow"""
        ce_oi_change = data.get('ce_oi_change', 0)
        pe_oi_change = data.get('pe_oi_change', 0)
        spot_change = data.get('spot_change_pct', 0)
        
        oi_pattern = 'neutral'
        signals = []
        
        # OI Pattern Recognition
        if ce_oi_change > 0 and spot_change > 0:
            oi_pattern = 'long_build_up'
            signals.append("🟢 Call OI building with price up - Long build-up")
        elif ce_oi_change > 0 and spot_change < 0:
            oi_pattern = 'short_build_up'
            signals.append("🔴 Call OI building with price down - Short build-up")
        elif ce_oi_change < 0 and spot_change > 0:
            oi_pattern = 'short_covering'
            signals.append("🟡 Call OI dropping with price up - Short covering")
        elif ce_oi_change < 0 and spot_change < 0:
            oi_pattern = 'long_unwinding'
            signals.append("🟠 Call OI dropping with price down - Long unwinding")
        
        return {
            'oi_pattern': oi_pattern,
            'signals': signals
        }
    
    def _analyze_iv(self, data: Dict) -> Dict:
        """Analyze IV conditions"""
        ce_iv = data.get('ce_iv', 0)
        
        iv_regime = 'normal'
        signals = []
        
        if ce_iv > 0.5:
            iv_regime = 'extreme_high'
            signals.append(f"⚠️ IV extremely high ({ce_iv:.1%}) - premium rich")
        elif ce_iv > 0.35:
            iv_regime = 'elevated'
            signals.append(f"📊 IV elevated ({ce_iv:.1%})")
        elif ce_iv < 0.2:
            iv_regime = 'low'
            signals.append(f"💡 IV low ({ce_iv:.1%}) - options cheap")
        
        return {
            'iv_regime': iv_regime,
            'signals': signals
        }
    
    def _combine_signals(self, greek: Dict, flow: Dict, iv: Dict) -> tuple:
        """Combine all signals to determine direction and conviction"""
        
        direction = 'neutral'
        conviction = 0.0
        
        # Count bullish/bearish signals
        bullish_score = 0
        bearish_score = 0
        
        # Greek contribution
        if greek.get('bias') == 'bullish':
            bullish_score += 2
        elif greek.get('bias') == 'bearish':
            bearish_score += 2
        
        # Flow contribution
        if flow.get('oi_pattern') in ['long_build_up', 'short_covering']:
            bullish_score += 2
        elif flow.get('oi_pattern') in ['short_build_up', 'long_unwinding']:
            bearish_score += 2
        
        # IV contribution
        iv_regime = iv.get('iv_regime', 'normal')
        if iv_regime == 'low':
            bullish_score += 1  # Cheap options favor directional bets
        
        # Determine direction
        if bullish_score > bearish_score:
            direction = 'bullish'
        elif bearish_score > bullish_score:
            direction = 'bearish'
        
        # Calculate conviction (0 to 1)
        total_score = abs(bullish_score - bearish_score)
        conviction = min(total_score / 5.0, 1.0)
        
        return direction, round(conviction, 2)
    
    def _generate_signals(self, analysis: Dict) -> List[str]:
        """Generate trading signals"""
        signals = []
        
        direction = analysis.get('direction', 'neutral')
        conviction = analysis.get('conviction', 0)
        
        if direction == 'bullish' and conviction > 0.5:
            signals.append(f"🟢 BULLISH signal (conviction: {conviction:.0%})")
        elif direction == 'bearish' and conviction > 0.5:
            signals.append(f"🔴 BEARISH signal (conviction: {conviction:.0%})")
        
        # Add Greek signals
        signals.extend(analysis.get('greek_analysis', {}).get('signals', []))
        
        # Add Flow signals
        signals.extend(analysis.get('flow_analysis', {}).get('signals', []))
        
        # Add IV signals
        signals.extend(analysis.get('iv_analysis', {}).get('signals', []))
        
        return signals
    
    def _generate_risks(self, analysis: Dict) -> List[str]:
        """Generate risk warnings"""
        risks = []
        
        greek_analysis = analysis.get('greek_analysis', {})
        
        if greek_analysis.get('gamma_risk'):
            risks.append("⚠️ High gamma - sharp reversals possible")
        
        iv_analysis = analysis.get('iv_analysis', {})
        if iv_analysis.get('iv_regime') == 'extreme_high':
            risks.append("⚠️ IV crush risk - avoid buying premium")
        
        return risks

# Global brain instance
brain = OptionsBrain()