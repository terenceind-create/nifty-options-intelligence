# src/dashboard/overview.py
"""Multi-stock overview dashboard"""
import streamlit as st
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings import settings
from src.data.models import get_db_session, OptionsTick

def show_overview():
    """Display overview of all tracked stocks"""
    st.header("📊 All Stocks Overview")
    
    session = get_db_session()
    
    # Get latest data for each stock
    overview_data = []
    
    for symbol in settings.TRACKING_SYMBOLS:
        latest = session.query(OptionsTick)\
            .filter_by(symbol=symbol)\
            .order_by(OptionsTick.timestamp.desc())\
            .first()
        
        if latest:
            overview_data.append({
                'Symbol': symbol,
                'Spot': f"₹{latest.spot_price:,.2f}",
                'ATM': latest.atm_strike,
                'Days to Expiry': latest.days_to_expiry,
                'CE IV': f"{latest.ce_iv:.1%}" if latest.ce_iv else "N/A",
                'PE IV': f"{latest.pe_iv:.1%}" if latest.pe_iv else "N/A",
                'PCR': f"{latest.pcr:.2f}" if latest.pcr else "N/A",
                'CE OI Chg': f"{latest.ce_oi_change:+,}" if latest.ce_oi_change else "N/A",
                'PE OI Chg': f"{latest.pe_oi_change:+,}" if latest.pe_oi_change else "N/A",
                'Nifty Weight': f"{settings.NIFTY_WEIGHTS.get(symbol, 0)}%"
            })
    
    if overview_data:
        df = pd.DataFrame(overview_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.warning("No data available")
    
    session.close()