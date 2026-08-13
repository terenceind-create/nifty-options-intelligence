# src/dashboard/app.py
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings import settings

# Lot sizes for NSE stock options
LOT_SIZES = {
    'RELIANCE': 500, 'HDFCBANK': 650, 'ICICIBANK': 700, 'INFY': 400,
    'AXISBANK': 625, 'TCS': 225, 'KOTAKBANK': 2000, 'LT': 175,
    'SBIN': 750, 'BAJFINANCE': 750, 'ITC': 1725, 'BHARTIARTL': 475,
    'HINDUNILVR': 300, 'SUNPHARMA': 350, 'MARUTI': 50, 'TITAN': 175,
    'ASIANPAINT': 250, 'HCLTECH': 400, 'WIPRO': 30000, 'NESTLE': 500,
}

MAX_CAPITAL = 14000  # Your maximum capital for 2 lots
from src.data.models import get_db_session, OptionsTick
from src.brain.options_brain import brain
from src.utils.market_calendar import market_calendar
from src.utils.nifty_chart import nifty_chart
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Option Buyer Intelligence", page_icon="🎯", layout="wide")

st_autorefresh(interval=60000, key="dashboard_auto_refresh")

st.markdown("""
<style>
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
        border: 1px solid #3a6fa0; border-radius: 12px; padding: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3); color: #ffffff !important;
    }
    [data-testid="stMetric"] label { color: #a0c4e8 !important; font-size: 0.85rem; white-space: nowrap; }
    [data-testid="stMetricValue"] { color: #ffffff !important; font-size: 1.3rem; font-weight: 700; white-space: nowrap; }
    .section-header {
        background: linear-gradient(90deg, #1a2a4a 0%, #2d4a7a 100%);
        padding: 12px 20px; border-radius: 8px; color: #e0e8f0;
        margin: 15px 0; font-weight: 600; border-left: 4px solid #4fc3f7;
    }
    .buy-call-monthly {
        background: linear-gradient(135deg, #00cc66 0%, #007733 100%);
        padding: 15px; border-radius: 10px; margin: 10px 0; color: white;
        border-left: 5px solid #00ff77;
    }
    .buy-put-monthly {
        background: linear-gradient(135deg, #ff4444 0%, #990000 100%);
        padding: 15px; border-radius: 10px; margin: 10px 0; color: white;
        border-left: 5px solid #ff6666;
    }
    .buy-call-intraday {
        background: linear-gradient(135deg, #33cc99 0%, #008844 100%);
        padding: 15px; border-radius: 10px; margin: 10px 0; color: white;
        border-left: 5px solid #00ffcc; border-style: dashed;
    }
    .buy-put-intraday {
        background: linear-gradient(135deg, #ff7777 0%, #aa2222 100%);
        padding: 15px; border-radius: 10px; margin: 10px 0; color: white;
        border-left: 5px solid #ffaaaa; border-style: dashed;
    }
    .wait-signal {
        background: linear-gradient(135deg, #ffaa00 0%, #cc7700 100%);
        padding: 15px; border-radius: 10px; margin: 10px 0; color: white;
        border-left: 5px solid #ffcc00;
    }
    h1, h2, h3 { color: #d0e0f0 !important; }
    .stButton button {
        background: linear-gradient(135deg, #2d5a87 0%, #1e3a5f 100%);
        color: white !important; border: 1px solid #4a80b0; border-radius: 8px;
        font-weight: 600; padding: 10px 15px;
    }
    .stButton button:hover { border-color: #6ab0e0; }
</style>
""", unsafe_allow_html=True)

# Title
col1, col2 = st.columns([3, 1])
with col1:
    st.title("🎯 Option Buyer Action Plan")
with col2:
    now = datetime.now()
    if 9.25 <= now.hour + now.minute/60 <= 15.5:
        nifty_spot = nifty_chart.get_latest_nifty_price()
        st.success(f"🟢 NIFTY: {nifty_spot:,.0f}" if nifty_spot else "🟢 MARKET LIVE")
    else:
        st.error("🔴 MARKET CLOSED")

st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("📊 Stock Selector")
    selected_symbol = st.selectbox("Choose Stock", settings.TRACKING_SYMBOLS)
    
    st.markdown("---")
    st.header("⏱️ Refresh Speed")
    refresh_speed = st.radio("Auto Refresh", ["1 min", "3 min", "5 min"], index=0)
    
    st.markdown("---")
    if st.button("🔄 Refresh Now", use_container_width=True):
        st.rerun()
    
    st.markdown("---")
    if market_calendar.is_trading_day():
        expiry = market_calendar.get_stock_expiry()
        days = (expiry - datetime.now().date()).days
        st.info(f"Expiry: {expiry.strftime('%d-%b')} ({days}d)")
        if days <= 3:
            st.error("⚠️ Near expiry — prefer intraday!")

# Main Dashboard
try:
    session = get_db_session()
    expiry_date = market_calendar.get_stock_expiry()
    days = (expiry_date - datetime.now().date()).days
    
    # ============================================================
    # FILTER BUTTONS
    # ============================================================
    st.markdown('<div class="section-header">🎯 Quick Filters — Click for Top Picks</div>', unsafe_allow_html=True)
    
    # Build all action plans
    action_plans = []
    
    for symbol in settings.TRACKING_SYMBOLS:
        latest = session.query(OptionsTick)\
            .filter_by(symbol=symbol)\
            .order_by(OptionsTick.timestamp.desc())\
            .first()
        
        if not latest or not latest.spot_price or latest.spot_price <= 0:
            continue
        
        ce_iv = latest.ce_iv or 0
        pe_iv = latest.pe_iv or 0
        avg_iv = (ce_iv + pe_iv) / 2 if (ce_iv + pe_iv) > 0 else 0
        ce_delta = latest.ce_delta or 0
        pe_delta = latest.pe_delta or 0
        pcr = latest.pcr or 1
        ce_oi_chg = latest.ce_oi_change or 0
        pe_oi_chg = latest.pe_oi_change or 0
        ce_ltp = latest.ce_ltp or 0
        pe_ltp = latest.pe_ltp or 0
        ce_volume = latest.ce_volume or 0
        pe_volume = latest.pe_volume or 0
        
        # ==========================================
        # MONTHLY SCORING (positional - buy & hold)
        # ==========================================
        m_bullish = 0
        m_bearish = 0
        
        # Delta alignment (strong trend)
        if ce_delta > 0.60: m_bullish += 3
        elif ce_delta > 0.55: m_bullish += 2
        elif ce_delta > 0.50: m_bullish += 1
        
        if pe_delta < -0.50: m_bearish += 3
        elif pe_delta < -0.55: m_bearish += 2
        elif pe_delta < -0.50: m_bearish += 1
        
        # PCR alignment
        if pcr < 0.7: m_bullish += 2
        elif pcr > 1.3: m_bearish += 2
        
        # OI flow
        if ce_oi_chg > 5000 and pe_oi_chg < 0: m_bullish += 2
        elif pe_oi_chg > 5000 and ce_oi_chg < 0: m_bearish += 2
        
        # IV check (only monthly cares about IV)
        iv_good = avg_iv < 0.30
        
        # Expiry check
        expiry_good = days > 5
        
        # ==========================================
        # INTRADAY SCORING (same day exit)
        # ==========================================
        i_bullish = 0
        i_bearish = 0
        
        # Short-term delta (momentum)
        if ce_delta > 0.55: i_bullish += 2
        if pe_delta < -0.40: i_bearish += 2
        
        # Volume activity (liquidity for quick entry/exit)
        if ce_volume > 100000: i_bullish += 2
        elif ce_volume > 50000: i_bullish += 1
        
        if pe_volume > 100000: i_bearish += 2
        elif pe_volume > 50000: i_bearish += 1
        
        # OI change direction (flow)
        if ce_oi_chg > 0: i_bullish += 2
        if pe_oi_chg > 0: i_bearish += 2
        
        # PCR skew
        if pcr < 0.8: i_bullish += 1
        elif pcr > 1.2: i_bearish += 1
        
        # Premium check (intraday needs cheap enough to move)
        if 5 <= ce_ltp <= 100: i_bullish += 1
        if 5 <= pe_ltp <= 100: i_bearish += 1
        
        # ==========================================
        # CLASSIFY
        # ==========================================
        action_type = ""
        card_class = ""
        
        # Monthly CALL: strong alignment + low IV + far expiry
        if m_bullish >= 5 and m_bearish <= 1 and iv_good and expiry_good:
            action_type = "CALL_MONTHLY"
            card_class = "buy-call-monthly"
        # Monthly PUT
        elif m_bearish >= 5 and m_bullish <= 1 and iv_good and expiry_good:
            action_type = "PUT_MONTHLY"
            card_class = "buy-put-monthly"
        # Intraday CALL: short-term momentum + volume
        elif i_bullish >= 4 and i_bullish > i_bearish:
            action_type = "CALL_INTRADAY"
            card_class = "buy-call-intraday"
        # Intraday PUT
        elif i_bearish >= 3 and i_bearish > i_bullish:
            action_type = "PUT_INTRADAY"
            card_class = "buy-put-intraday"
        else:
            action_type = "WAIT"
            card_class = "wait-signal"
        
        # Check how long this signal has been active
        signal_duration_minutes = 0
        signal_start_time = None
        
        if action_type != 'WAIT':
            # Look back through history (up to 60 minutes = 60 records at 1-min refresh)
            history_ticks = session.query(OptionsTick)\
                .filter(OptionsTick.symbol == symbol)\
                .order_by(OptionsTick.timestamp.desc())\
                .limit(60)\
                .all()
            
            if history_ticks and len(history_ticks) > 1:
                # Go backwards to find when signal first appeared
                for tick in reversed(history_ticks):
                    tick_ce_delta = tick.ce_delta or 0
                    tick_pe_delta = tick.pe_delta or 0
                    tick_pcr = tick.pcr or 1
                    
                    # Simple check: was this action valid at that historical point?
                    was_valid = False
                    if 'CALL' in action_type:
                        was_valid = tick_ce_delta > 0.50 or tick_pcr < 0.8
                    elif 'PUT' in action_type:
                        was_valid = tick_pe_delta < -0.40 or tick_pcr > 1.2
                    
                    if was_valid:
                        signal_start_time = tick.timestamp
                    else:
                        break
                
                if signal_start_time:
                    # Calculate duration
                    signal_duration_minutes = int((datetime.now() - signal_start_time.replace(tzinfo=None)).total_seconds() / 60)
        
        action_plans.append({
            'Symbol': symbol, 'ActionType': action_type, 'Card': card_class,
            'Spot': latest.spot_price, 'Strike': latest.atm_strike,
            'IV': avg_iv, 'CE_Δ': ce_delta, 'PE_Δ': pe_delta, 'PCR': pcr,
            'CE_OIΔ': ce_oi_chg, 'PE_OIΔ': pe_oi_chg,
            'CE_LTP': ce_ltp, 'PE_LTP': pe_ltp,
            'CE_Vol': ce_volume, 'PE_Vol': pe_volume,
            'M_Bull': m_bullish, 'M_Bear': m_bearish,
            'I_Bull': i_bullish, 'I_Bear': i_bearish,
            'SignalDuration': signal_duration_minutes,
            'SignalStart': signal_start_time,
        })
    
    # Filter buttons
    filter_col1, filter_col2, filter_col3, filter_col4, filter_col5 = st.columns(5)
    
    with filter_col1:
        if st.button("📈 CALL (M)", use_container_width=True, key="btn_cm"):
            st.session_state.filter = "CALL_MONTHLY"
    with filter_col2:
        if st.button("📉 PUT (M)", use_container_width=True, key="btn_pm"):
            st.session_state.filter = "PUT_MONTHLY"
    with filter_col3:
        if st.button("⚡ CALL (I)", use_container_width=True, key="btn_ci"):
            st.session_state.filter = "CALL_INTRADAY"
    with filter_col4:
        if st.button("⚡ PUT (I)", use_container_width=True, key="btn_pi"):
            st.session_state.filter = "PUT_INTRADAY"
    with filter_col5:
        if st.button("📊 ALL", use_container_width=True, key="btn_all"):
            st.session_state.filter = "ALL"
    
    if 'filter' not in st.session_state:
        st.session_state.filter = "ALL"
    
    st.markdown("---")
    
    # ============================================================
    # NIFTY CHART + FILTERED SIGNALS
    # ============================================================
    chart_col1, chart_col2 = st.columns([1, 1])
    
    with chart_col1:
        st.subheader(f"📈 Nifty 50 — Auto Refresh: {refresh_speed}")
        df_nifty = nifty_chart.get_today_candles_df()
        
        if not df_nifty.empty:
            fig = go.Figure()
            fig.add_trace(go.Candlestick(
                x=df_nifty.index, open=df_nifty['open'], high=df_nifty['high'],
                low=df_nifty['low'], close=df_nifty['close'],
                increasing_line_color='#00cc66', decreasing_line_color='#ff4444', name='Nifty'
            ))
            if 'EMA_20' in df_nifty.columns:
                fig.add_trace(go.Scatter(x=df_nifty.index, y=df_nifty['EMA_20'],
                    mode='lines', line=dict(color='#ffaa00', width=1.5), name='20 EMA'))
            if 'Pivot' in df_nifty.columns:
                fig.add_trace(go.Scatter(x=df_nifty.index, y=df_nifty['Pivot'],
                    mode='lines', line=dict(color='#ffffff', width=1, dash='dash'), name='Pivot'))
            fig.update_layout(height=400, paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(10,22,40,0.5)', font=dict(color='white', size=10),
                xaxis=dict(rangeslider=dict(visible=False)),
                margin=dict(l=10, r=10, t=30, b=10),
                legend=dict(orientation='h', y=1.02, font=dict(size=9, color='white')))
            st.plotly_chart(fig, use_container_width=True)
    
    with chart_col2:
        current_filter = st.session_state.filter
        
        filter_titles = {
            "ALL": "📊 ALL SIGNALS",
            "CALL_MONTHLY": "📈 TOP CALL (MONTHLY)",
            "PUT_MONTHLY": "📉 TOP PUT (MONTHLY)",
            "CALL_INTRADAY": "⚡ TOP CALL (INTRADAY)",
            "PUT_INTRADAY": "⚡ TOP PUT (INTRADAY)",
        }
        
        st.subheader(filter_titles.get(current_filter, "Signals"))
        
        if current_filter == "ALL":
            filtered = [a for a in action_plans if a['ActionType'] != 'WAIT']
        else:
            filtered = [a for a in action_plans if a['ActionType'] == current_filter]
        
        # Sort by relevance score
        def sort_score(x):
            if 'MONTHLY' in x['ActionType']:
                return x['M_Bull'] + x['M_Bear']
            else:
                return x['I_Bull'] + x['I_Bear']
        
        filtered.sort(key=sort_score, reverse=True)
        
        for plan in filtered[:5]:
            emoji = "📈" if 'CALL' in plan['ActionType'] else "📉"
            label = plan['ActionType'].replace('_', ' ').title()
            premium = plan['CE_LTP'] if 'CALL' in plan['ActionType'] else plan['PE_LTP']
            delta = plan['CE_Δ'] if 'CALL' in plan['ActionType'] else plan['PE_Δ']
            volume = plan['CE_Vol'] if 'CALL' in plan['ActionType'] else plan['PE_Vol']
            
            lot_size = LOT_SIZES.get(plan['Symbol'], 100)
            capital_1_lot = premium * lot_size
            capital_2_lots = premium * lot_size * 2
            
            duration = plan.get('SignalDuration', 0)
            if duration >= 30:
                duration_text = f"⚠️ {duration} min old — may be late"
                duration_color = "#ffaa00"
            elif duration >= 15:
                duration_text = f"📈 {duration} min — confirmed"
                duration_color = "#00ff77"
            elif duration >= 5:
                duration_text = f"🔥 {duration} min — building"
                duration_color = "#ffcc00"
            elif duration > 0:
                duration_text = f"🆕 FRESH — {duration} min"
                duration_color = "#00ffcc"
            else:
                duration_text = "⏳ Building history... (needs 30+ min)"
                duration_color = "#88aacc"
            
            # Check affordability
            if capital_2_lots <= MAX_CAPITAL:
                affordability = f"✅ Fits budget: ₹{capital_2_lots:,.0f} for 2 lots"
                color_budget = "#00ff77"
            elif capital_1_lot <= MAX_CAPITAL:
                affordability = f"⚠️ Only 1 lot fits: ₹{capital_1_lot:,.0f} (2 lots = ₹{capital_2_lots:,.0f})"
                color_budget = "#ffcc00"
            else:
                affordability = f"❌ Over budget: 1 lot = ₹{capital_1_lot:,.0f}"
                color_budget = "#ff4444"
            
            st.markdown(f"""
            <div class="{plan['Card']}">
                <strong>{emoji} {plan['Symbol']} — {label}</strong><br>
                Spot: ₹{plan['Spot']:,.0f} | Strike: ₹{plan['Strike']:,} | Premium: ₹{premium:,.2f}<br>
                IV: {plan['IV']:.1%} | PCR: {plan['PCR']:.2f} | Δ: {delta:.2f} | Vol: {volume:,}<br>
                <small>CE OIΔ: {plan['CE_OIΔ']:+,.0f} | PE OIΔ: {plan['PE_OIΔ']:+,.0f}</small><br>
                <hr style="margin:8px 0; border-color:rgba(255,255,255,0.3)">
                ⏱️ <span style="color:{duration_color}; font-weight:bold;">{duration_text}</span><br>
                📦 Lot Size: <strong>{lot_size}</strong> shares<br>
                💰 1 Lot: <strong>₹{capital_1_lot:,.2f}</strong> | 2 Lots: <strong>₹{capital_2_lots:,.2f}</strong><br>
                <span style="color:{color_budget}; font-weight:bold;">{affordability}</span>
            </div>
            """, unsafe_allow_html=True)
        
        if not filtered:
            st.info(f"No signals for {filter_titles.get(current_filter, '')}")
        
        # Summary
        st.markdown("---")
        cm = sum(1 for a in action_plans if a['ActionType'] == 'CALL_MONTHLY')
        pm = sum(1 for a in action_plans if a['ActionType'] == 'PUT_MONTHLY')
        ci = sum(1 for a in action_plans if a['ActionType'] == 'CALL_INTRADAY')
        pi = sum(1 for a in action_plans if a['ActionType'] == 'PUT_INTRADAY')
        waits = sum(1 for a in action_plans if a['ActionType'] == 'WAIT')
        
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1: st.metric("CALL M", f"{cm}")
        with c2: st.metric("PUT M", f"{pm}")
        with c3: st.metric("CALL I", f"{ci}")
        with c4: st.metric("PUT I", f"{pi}")
        with c5: st.metric("WAIT", f"{waits}")
    
    # ============================================================
    # ROW 2: FULL TABLE
    # ============================================================
    st.markdown("---")
    st.markdown('<div class="section-header">📋 All Stocks — Action Plan</div>', unsafe_allow_html=True)
    
    if action_plans:
        table_data = []
        for a in action_plans:
            table_data.append({
                'Symbol': a['Symbol'],
                'Action': a['ActionType'].replace('_', ' ').title(),
                'Spot': f"₹{a['Spot']:,.0f}",
                'Strike': f"₹{a['Strike']:,}",
                'CE_Prem': f"₹{a['CE_LTP']:,.2f}",
                'PE_Prem': f"₹{a['PE_LTP']:,.2f}",
                'IV': f"{a['IV']:.1%}",
                'CE_Δ': f"{a['CE_Δ']:.2f}",
                'PCR': f"{a['PCR']:.2f}",
                'M_Score': f"{a['M_Bull'] + a['M_Bear']}",
                'I_Score': f"{a['I_Bull'] + a['I_Bear']}",
            })
        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    
    # ============================================================
    # ROW 3: INDIVIDUAL DETAIL
    # ============================================================
    st.markdown("---")
    st.markdown('<div class="section-header">🔍 Individual Stock Detail</div>', unsafe_allow_html=True)
    
    latest = session.query(OptionsTick)\
        .filter_by(symbol=selected_symbol)\
        .order_by(OptionsTick.timestamp.desc())\
        .first()
    
    if latest and latest.spot_price:
        ce_iv = latest.ce_iv or 0
        pe_iv = latest.pe_iv or 0
        avg_iv = (ce_iv + pe_iv) / 2 if (ce_iv + pe_iv) > 0 else 0
        ce_delta = latest.ce_delta or 0
        pcr = latest.pcr or 1
        
        # Find this stock's action
        stock_action = next((a for a in action_plans if a['Symbol'] == selected_symbol), None)
        
        if stock_action:
            action_label = stock_action['ActionType'].replace('_', ' ').title()
            card = stock_action['Card']
            premium = stock_action['CE_LTP'] if 'CALL' in stock_action['ActionType'] else stock_action['PE_LTP']
            
            lot = LOT_SIZES.get(selected_symbol, 100)
            cap_1 = premium * lot
            cap_2 = premium * lot * 2
            
            if cap_2 <= MAX_CAPITAL:
                budget_msg = f"✅ 2 lots = ₹{cap_2:,.2f} (fits in ₹14,000)"
            elif cap_1 <= MAX_CAPITAL:
                budget_msg = f"⚠️ 1 lot = ₹{cap_1:,.2f} | 2 lots = ₹{cap_2:,.2f} (over budget)"
            else:
                budget_msg = f"❌ 1 lot = ₹{cap_1:,.2f} (over budget)"
            
            st.markdown(f"""
            <div class="{card}">
                <strong>🎯 {selected_symbol}: {action_label}</strong><br>
                Strike: ₹{latest.atm_strike:,} | Premium: ₹{premium:,.2f} | Lot: {lot}<br>
                💰 1 Lot: ₹{cap_1:,.2f} | 2 Lots: ₹{cap_2:,.2f}<br>
                {budget_msg}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.warning(f"⚠️ {selected_symbol}: WAIT — No clear edge")
        
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        with col1: st.metric("Spot", f"₹{latest.spot_price:,.2f}")
        with col2: st.metric("ATM", f"₹{latest.atm_strike:,}")
        with col3: st.metric("DTE", f"{days}d")
        with col4: st.metric("PCR", f"{latest.pcr:.2f}" if latest.pcr else "-")
        with col5: st.metric("CE IV", f"{latest.ce_iv:.1%}" if latest.ce_iv else "-")
        with col6: st.metric("PE IV", f"{latest.pe_iv:.1%}" if latest.pe_iv else "-")
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📈 CALL")
            st.metric("LTP", f"₹{latest.ce_ltp:,.2f}" if latest.ce_ltp else "-")
            st.metric("OI Δ", f"{latest.ce_oi_change:+,.0f}" if latest.ce_oi_change else "-")
            st.metric("Vol", f"{latest.ce_volume:,.0f}" if latest.ce_volume else "-")
            st.metric("Δ", f"{latest.ce_delta:.3f}" if latest.ce_delta else "-")
        with col2:
            st.subheader("📉 PUT")
            st.metric("LTP", f"₹{latest.pe_ltp:,.2f}" if latest.pe_ltp else "-")
            st.metric("OI Δ", f"{latest.pe_oi_change:+,.0f}" if latest.pe_oi_change else "-")
            st.metric("Vol", f"{latest.pe_volume:,.0f}" if latest.pe_volume else "-")
            st.metric("Δ", f"{latest.pe_delta:.3f}" if latest.pe_delta else "-")
    
    session.close()

except Exception as e:
    st.error(f"❌ Error: {e}")

st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1: st.caption(f"📊 {len(settings.TRACKING_SYMBOLS)} stocks")
with col2: st.caption("🎯 Monthly + Intraday Signals | 1-min refresh")
with col3: st.caption(f"🕐 {datetime.now().strftime('%d-%b %H:%M:%S')}")