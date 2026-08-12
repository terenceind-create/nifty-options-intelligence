# src/dashboard/app.py
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings import settings
from src.data.models import get_db_session, OptionsTick
from src.brain.options_brain import brain
from src.utils.market_calendar import market_calendar
from src.utils.nifty_chart import nifty_chart

st.set_page_config(page_title="Option Buyer Intelligence", page_icon="🎯", layout="wide")

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
    .buy-signal { background: #00cc66; padding: 10px; border-radius: 8px; color: white; font-weight: bold; }
    .avoid-signal { background: #cc0000; padding: 10px; border-radius: 8px; color: white; font-weight: bold; }
    .neutral-signal { background: #666666; padding: 10px; border-radius: 8px; color: white; font-weight: bold; }
    h1, h2, h3 { color: #d0e0f0 !important; }
    .stButton button {
        background: linear-gradient(135deg, #2d5a87 0%, #1e3a5f 100%);
        color: white !important; border: 1px solid #4a80b0; border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Title
col1, col2 = st.columns([3, 1])
with col1:
    st.title("🎯 Option Buyer Intelligence")
with col2:
    now = datetime.now()
    market_hour = now.hour + now.minute/60
    if 9.25 <= market_hour <= 15.5:
        nifty_spot = nifty_chart.get_latest_nifty_price()
        if nifty_spot:
            st.success(f"🟢 NIFTY: {nifty_spot:,.0f}")
        else:
            st.success("🟢 MARKET LIVE")
    else:
        st.error("🔴 MARKET CLOSED")

st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("📊 Stock Selector")
    selected_symbol = st.selectbox("Choose Stock", settings.TRACKING_SYMBOLS)
    
    st.markdown("---")
    st.header("🎯 Buyer's Checklist")
    st.caption("Green = Good to buy | Red = Avoid buying")
    
    st.markdown("---")
    if st.button("🔄 Refresh Now", use_container_width=True):
        st.rerun()
    
    st.markdown("---")
    st.header("📅 Market Info")
    if market_calendar.is_trading_day():
        expiry = market_calendar.get_stock_expiry()
        days = (expiry - datetime.now().date()).days
        st.info(f"Expiry: {expiry.strftime('%d-%b')} ({days}d)")
        phase = market_calendar.get_market_phase()
        st.caption(f"Session: {phase['time_description']}")
        if days <= 3:
            st.error("⚠️ Near expiry — Theta decay is HIGH. Option buying is RISKY!")

# Main Dashboard
try:
    session = get_db_session()
    
    expiry_date = market_calendar.get_stock_expiry()
    days = (expiry_date - datetime.now().date()).days
    
    # ============================================================
    # ROW 1: NIFTY CHART + BEST BUYING OPPORTUNITIES
    # ============================================================
    st.markdown('<div class="section-header">📊 Nifty Chart & Top Option Buying Opportunities</div>', unsafe_allow_html=True)
    
    chart_col1, chart_col2 = st.columns([1, 1])
    
    with chart_col1:
        st.subheader("📈 Nifty 50 (5-Min) — 20 EMA + Fib Pivots")
        
        df_nifty = nifty_chart.get_today_candles_df()
        
        if not df_nifty.empty:
            fig = go.Figure()
            
            fig.add_trace(go.Candlestick(
                x=df_nifty.index, open=df_nifty['open'], high=df_nifty['high'],
                low=df_nifty['low'], close=df_nifty['close'],
                increasing_line_color='#00cc66', decreasing_line_color='#ff4444',
                name='Nifty 50', showlegend=True
            ))
            
            if 'EMA_20' in df_nifty.columns:
                fig.add_trace(go.Scatter(
                    x=df_nifty.index, y=df_nifty['EMA_20'], mode='lines',
                    line=dict(color='#ffaa00', width=1.5), name='20 EMA'
                ))
            
            if 'Pivot' in df_nifty.columns:
                fig.add_trace(go.Scatter(
                    x=df_nifty.index, y=df_nifty['Pivot'], mode='lines',
                    line=dict(color='#ffffff', width=1.2, dash='dash'), name='Pivot'
                ))
            
            for level, color in [('Fib_R1', '#ff6666'), ('Fib_R2', '#ff4444'), ('Fib_S1', '#66ff66'), ('Fib_S2', '#44ff44')]:
                if level in df_nifty.columns:
                    fig.add_trace(go.Scatter(x=df_nifty.index, y=df_nifty[level], mode='lines',
                        line=dict(color=color, width=0.8, dash='dot'), name=level.replace('Fib_', 'Fib ')))
            
            fig.update_layout(
                height=450, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(10,22,40,0.5)',
                font=dict(color='white', size=10),
                xaxis=dict(gridcolor='rgba(255,255,255,0.08)', rangeslider=dict(visible=False)),
                yaxis=dict(title='Nifty', gridcolor='rgba(255,255,255,0.08)'),
                margin=dict(l=10, r=10, t=30, b=10),
                legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1,
                          font=dict(size=9, color='white'), bgcolor='rgba(0,0,0,0.3)'),
                hovermode='x unified'
            )
            
            current = df_nifty['close'].iloc[-1]
            fig.add_hline(y=current, line_dash="solid", line_color="#4fc3f7", opacity=0.5, line_width=1)
            st.plotly_chart(fig, use_container_width=True)
            
            if len(df_nifty) >= 2:
                change = df_nifty['close'].iloc[-1] - df_nifty['close'].iloc[0]
                change_pct = (change / df_nifty['close'].iloc[0]) * 100
                ema_val = df_nifty['EMA_20'].iloc[-1] if 'EMA_20' in df_nifty.columns else 0
                
                sc1, sc2, sc3, sc4 = st.columns(4)
                with sc1: st.metric("Open", f"{df_nifty['open'].iloc[0]:,.0f}")
                with sc2: st.metric("Day Range", f"{df_nifty['low'].min():,.0f} - {df_nifty['high'].max():,.0f}")
                with sc3: st.metric("Change", f"{change:+,.0f} ({change_pct:+.2f}%)")
                with sc4:
                    if ema_val > 0:
                        ema_diff = current - ema_val
                        trend = "🟢 Above EMA" if ema_diff > 0 else "🔴 Below EMA"
                        st.metric("Trend", trend)
        else:
            st.warning("Chart loads during market hours")
    
    with chart_col2:
        st.subheader("🎯 Top Option Buying Opportunities")
        st.caption("Stocks ranked by: Low IV + Strong Direction + Favorable PCR")
        
        # Score each stock for option buying suitability
        buying_opportunities = []
        
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
            ce_oi_change = latest.ce_oi_change or 0
            
            # Option Buyer Score (0-100)
            score = 0
            
            # 1. IV Check (Low IV = cheaper premiums = better for buyers) — max 30 points
            if avg_iv > 0 and avg_iv < 0.20:
                score += 30  # Very cheap
            elif avg_iv > 0 and avg_iv < 0.30:
                score += 20  # Reasonable
            elif avg_iv > 0 and avg_iv < 0.40:
                score += 10  # Slightly expensive
            else:
                score += 0   # Too expensive for buying
            
            # 2. Directional clarity — max 30 points
            if ce_delta > 0.6:
                score += 25  # Strong bullish
            elif ce_delta > 0.5:
                score += 15  # Moderate bullish
            elif pe_delta < -0.5:
                score += 25  # Strong bearish (buy puts)
            elif pe_delta < -0.4:
                score += 15  # Moderate bearish
            
            # 3. PCR confirmation — max 20 points
            if pcr < 0.7:
                score += 20  # Call-heavy, bullish confirmation
            elif pcr > 1.3:
                score += 20  # Put-heavy, bearish confirmation
            elif 0.8 <= pcr <= 1.2:
                score += 5   # Neutral
            
            # 4. OI Flow — max 20 points
            if ce_oi_change > 10000:
                score += 15  # Strong call OI buildup
            elif ce_oi_change > 0:
                score += 10
            
            # 5. Days to expiry penalty (near expiry = theta kills buyers)
            if days <= 2:
                score -= 30
            elif days <= 5:
                score -= 15
            
            # Determine recommendation
            if score >= 60:
                recommendation = "✅ STRONG BUY"
                rec_color = "#00cc66"
            elif score >= 40:
                recommendation = "👍 BUY"
                rec_color = "#88cc00"
            elif score >= 25:
                recommendation = "⏳ WAIT"
                rec_color = "#ffaa00"
            else:
                recommendation = "🚫 AVOID"
                rec_color = "#ff4444"
            
            # Call or Put?
            if ce_delta > pe_delta and ce_delta > 0.5:
                option_type = "CALL"
            elif pe_delta < -0.4:
                option_type = "PUT"
            else:
                option_type = "—"
            
            buying_opportunities.append({
                'Symbol': symbol,
                'Score': score,
                'Recommendation': recommendation,
                'Rec_Color': rec_color,
                'Option': option_type,
                'Spot': f"₹{latest.spot_price:,.0f}",
                'IV': f"{avg_iv:.1%}" if avg_iv > 0 else "—",
                'CE_Δ': f"{ce_delta:.2f}",
                'PCR': f"{pcr:.2f}",
            })
        
        # Sort by score
        buying_opportunities.sort(key=lambda x: x['Score'], reverse=True)
        
        # Display top opportunities
        if buying_opportunities:
            # Summary cards for top 3
            top3 = buying_opportunities[:3]
            st.write("### 🔥 Top 3 Option Buying Picks")
            
            for i, opp in enumerate(top3):
                bg = opp['Rec_Color']
                st.markdown(f"""
                <div style="background: {bg}; padding: 12px; border-radius: 8px; margin: 8px 0; color: white;">
                    <strong>#{i+1} {opp['Symbol']}</strong> — {opp['Recommendation']}<br>
                    Buy <strong>{opp['Option']}</strong> | Spot: {opp['Spot']} | IV: {opp['IV']} | PCR: {opp['PCR']}<br>
                    <small>Score: {opp['Score']}/100 | CE Delta: {opp['CE_Δ']}</small>
                </div>
                """, unsafe_allow_html=True)
            
            # Full table
            st.markdown("---")
            st.write("### 📊 All Stocks Ranked")
            
            df_opps = pd.DataFrame(buying_opportunities)
            df_opps = df_opps[['Symbol', 'Score', 'Recommendation', 'Option', 'Spot', 'IV', 'CE_Δ', 'PCR']]
            st.dataframe(df_opps, use_container_width=True, hide_index=True)
            
            # Summary
            strong_buys = sum(1 for o in buying_opportunities if o['Score'] >= 60)
            buys = sum(1 for o in buying_opportunities if 40 <= o['Score'] < 60)
            avoids = sum(1 for o in buying_opportunities if o['Score'] < 25)
            
            st.markdown("---")
            c1, c2, c3, c4 = st.columns(4)
            with c1: st.metric("🔥 Strong Buy", f"{strong_buys} stocks", delta="Score ≥ 60")
            with c2: st.metric("👍 Buy", f"{buys} stocks", delta="Score 40-59")
            with c3: st.metric("🚫 Avoid", f"{avoids} stocks", delta="Score < 25")
            
            # Buyer's warning
            if days <= 5:
                st.warning(f"⚠️ Only {days} days to expiry — Theta decay accelerates! Consider next month's options or reduce position size.")
            if strong_buys == 0:
                st.info("💡 No strong buy signals right now. Patience is profitable — wait for better setups.")
    
    # ============================================================
    # ROW 2: INDIVIDUAL STOCK DEEP DIVE
    # ============================================================
    st.markdown("---")
    st.markdown('<div class="section-header">🔍 Individual Stock Analysis</div>', unsafe_allow_html=True)
    
    latest = session.query(OptionsTick)\
        .filter_by(symbol=selected_symbol)\
        .order_by(OptionsTick.timestamp.desc())\
        .first()
    
    if latest and latest.spot_price:
        time_adj = market_calendar.get_time_aware_adjustments(days)
        theta_mult = time_adj['expiry_context']['theta_acceleration']
        
        # Buyer's quick verdict
        ce_iv = latest.ce_iv or 0
        pe_iv = latest.pe_iv or 0
        avg_iv = (ce_iv + pe_iv) / 2 if (ce_iv + pe_iv) > 0 else 0
        ce_delta = latest.ce_delta or 0
        pcr = latest.pcr or 1
        
        # Determine if good for buying
        iv_ok = avg_iv < 0.35
        direction_clear = ce_delta > 0.55 or ce_delta < 0.45
        expiry_ok = days > 3
        
        if iv_ok and direction_clear and expiry_ok:
            st.success(f"✅ {selected_symbol}: FAVORABLE for option buying — IV is reasonable ({avg_iv:.1%}), direction is clear")
        elif not expiry_ok:
            st.error(f"⛔ {selected_symbol}: AVOID buying — Only {days} days to expiry! Theta will eat your premium.")
        elif not iv_ok:
            st.warning(f"⚠️ {selected_symbol}: CAUTION — IV is high ({avg_iv:.1%}). Premiums are expensive. Consider waiting for IV crush.")
        else:
            st.info(f"ℹ️ {selected_symbol}: NEUTRAL — Wait for clearer directional signal")
        
        # Key metrics
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        with col1: st.metric("Spot", f"₹{latest.spot_price:,.2f}")
        with col2: st.metric("ATM", f"₹{latest.atm_strike:,}")
        with col3: st.metric("DTE", f"{days}d", delta="⚠️ Theta risk" if days <= 3 else None)
        with col4: st.metric("PCR", f"{latest.pcr:.2f}" if latest.pcr else "-")
        with col5: st.metric("CE IV", f"{latest.ce_iv:.1%}" if latest.ce_iv else "-")
        with col6: st.metric("PE IV", f"{latest.pe_iv:.1%}" if latest.pe_iv else "-")
        
        # Theta warning for buyers
        if days <= 5 and latest.ce_theta:
            daily_theta = abs(latest.ce_theta)
            st.warning(f"⏰ THETA ALERT: CE option loses ₹{daily_theta:.2f} per day in time decay. In {days} days, that's ₹{daily_theta*days:.2f} total decay.")
        
        # Options detail
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📈 CALL")
            c1, c2, c3 = st.columns(3)
            with c1: st.metric("LTP", f"₹{latest.ce_ltp:,.2f}" if latest.ce_ltp else "-")
            with c2: st.metric("Bid", f"₹{latest.ce_bid:,.2f}" if latest.ce_bid else "-")
            with c3: st.metric("Ask", f"₹{latest.ce_ask:,.2f}" if latest.ce_ask else "-")
            c4, c5, c6 = st.columns(3)
            with c4: st.metric("OI", f"{latest.ce_oi:,.0f}" if latest.ce_oi else "-")
            with c5: st.metric("OI Δ", f"{latest.ce_oi_change:+,.0f}" if latest.ce_oi_change else "-")
            with c6: st.metric("Vol", f"{latest.ce_volume:,.0f}" if latest.ce_volume else "-")
        with col2:
            st.subheader("📉 PUT")
            c1, c2, c3 = st.columns(3)
            with c1: st.metric("LTP", f"₹{latest.pe_ltp:,.2f}" if latest.pe_ltp else "-")
            with c2: st.metric("Bid", f"₹{latest.pe_bid:,.2f}" if latest.pe_bid else "-")
            with c3: st.metric("Ask", f"₹{latest.pe_ask:,.2f}" if latest.pe_ask else "-")
            c4, c5, c6 = st.columns(3)
            with c4: st.metric("OI", f"{latest.pe_oi:,.0f}" if latest.pe_oi else "-")
            with c5: st.metric("OI Δ", f"{latest.pe_oi_change:+,.0f}" if latest.pe_oi_change else "-")
            with c6: st.metric("Vol", f"{latest.pe_volume:,.0f}" if latest.pe_volume else "-")
        
        # Greeks
        st.markdown("---")
        st.subheader("📐 Greeks (Know your risk)")
        col1, col2 = st.columns(2)
        with col1:
            g1, g2, g3, g4 = st.columns(4)
            with g1: st.metric("Δ", f"{latest.ce_delta:.3f}" if latest.ce_delta else "-", help="Delta: Probability of expiring ITM. 0.5 = 50% chance")
            with g2: st.metric("Γ", f"{latest.ce_gamma:.4f}" if latest.ce_gamma else "-", help="Gamma: How fast delta changes. Higher near expiry")
            with g3: st.metric("Θ", f"{latest.ce_theta:.4f}" if latest.ce_theta else "-", help=f"Theta: Daily time decay. You lose ₹{abs(latest.ce_theta):.2f}/day" if latest.ce_theta else "")
            with g4: st.metric("ν", f"{latest.ce_vega:.4f}" if latest.ce_vega else "-", help="Vega: Sensitivity to IV changes")
        with col2:
            g1, g2, g3, g4 = st.columns(4)
            with g1: st.metric("Δ", f"{latest.pe_delta:.3f}" if latest.pe_delta else "-")
            with g2: st.metric("Γ", f"{latest.pe_gamma:.4f}" if latest.pe_gamma else "-")
            with g3: st.metric("Θ", f"{latest.pe_theta:.4f}" if latest.pe_theta else "-")
            with g4: st.metric("ν", f"{latest.pe_vega:.4f}" if latest.pe_vega else "-")
        
        # Buyer-specific recommendations
        st.markdown("---")
        st.subheader("💡 Option Buyer's Strategy")
        
        if days > 5 and avg_iv < 0.30 and (ce_delta > 0.5 or pe_delta < -0.5):
            if ce_delta > 0.5:
                st.success(f"""
                **BUY CALL** on {selected_symbol}
                - Strike: ₹{latest.atm_strike:,} (ATM)
                - Premium: ₹{latest.ce_ltp:,.2f}
                - Reason: Low IV ({avg_iv:.1%}), clear bullish delta ({ce_delta:.2f}), {days} days to expiry
                - Max Risk: ₹{latest.ce_ltp:,.2f} per share
                - Break-even: ₹{latest.atm_strike + latest.ce_ltp:,.2f}
                """)
            else:
                st.success(f"""
                **BUY PUT** on {selected_symbol}
                - Strike: ₹{latest.atm_strike:,} (ATM)
                - Premium: ₹{latest.pe_ltp:,.2f}
                - Reason: Low IV ({avg_iv:.1%}), clear bearish signal, {days} days to expiry
                - Max Risk: ₹{latest.pe_ltp:,.2f} per share
                - Break-even: ₹{latest.atm_strike - latest.pe_ltp:,.2f}
                """)
        elif days <= 3:
            st.error(f"🚫 DO NOT BUY options on {selected_symbol} — Only {days} days left. Theta will destroy premium. Consider next month expiry.")
        elif avg_iv > 0.35:
            st.warning(f"⚠️ CAUTION — IV is high ({avg_iv:.1%}). Premiums are inflated. Wait for IV crush or consider debit spreads to reduce cost.")
        else:
            st.info(f"⏳ WAIT — No clear edge for option buying on {selected_symbol} right now. Better opportunities will come.")
    
    else:
        st.warning(f"⚠️ No data for {selected_symbol}. Start collector: `python run_collector.py`")
    
    session.close()

except Exception as e:
    st.error(f"❌ Error: {e}")

st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1: st.caption(f"📊 {len(settings.TRACKING_SYMBOLS)} stocks")
with col2: st.caption("🎯 Option Buyer's Dashboard")
with col3: st.caption(f"🕐 {datetime.now().strftime('%d-%b %H:%M:%S')}")