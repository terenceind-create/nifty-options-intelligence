# src/analysis/greeks_calculator.py
import numpy as np
from scipy.stats import norm
from typing import Dict, Optional
from loguru import logger

class GreeksCalculator:
    """Black-Scholes Greeks Calculator"""
    
    def __init__(self):
        self.N = norm.cdf
        self.n = norm.pdf
    
    def calculate_all_greeks(self, 
                             option_type: str,
                             S: float,
                             K: float,
                             T: float,
                             r: float,
                             sigma: float) -> Dict[str, float]:
        """Calculate all Greeks for an option"""
        try:
            if T <= 0 or S <= 0 or K <= 0 or sigma <= 0:
                return self._empty_greeks()
            
            d1 = (np.log(S/K) + (r + sigma**2/2) * T) / (sigma * np.sqrt(T))
            d2 = d1 - sigma * np.sqrt(T)
            
            gamma = self.n(d1) / (S * sigma * np.sqrt(T))
            vega = S * np.sqrt(T) * self.n(d1) * 0.01
            
            if option_type.lower() == 'call':
                delta = self.N(d1)
                theta = (-S * self.n(d1) * sigma / (2 * np.sqrt(T)) - 
                         r * K * np.exp(-r * T) * self.N(d2)) / 365
                rho = K * T * np.exp(-r * T) * self.N(d2) * 0.01
            else:
                delta = self.N(d1) - 1
                theta = (-S * self.n(d1) * sigma / (2 * np.sqrt(T)) + 
                         r * K * np.exp(-r * T) * self.N(-d2)) / 365
                rho = -K * T * np.exp(-r * T) * self.N(-d2) * 0.01
            
            return {
                'delta': round(delta, 4),
                'gamma': round(gamma, 4),
                'theta': round(theta, 4),
                'vega': round(vega, 4),
                'rho': round(rho, 4)
            }
            
        except Exception as e:
            logger.error(f"Error calculating Greeks: {e}")
            return self._empty_greeks()
    
    def _empty_greeks(self) -> Dict[str, float]:
        """Return empty Greeks for error cases"""
        return {
            'delta': 0.0,
            'gamma': 0.0,
            'theta': 0.0,
            'vega': 0.0,
            'rho': 0.0
        }