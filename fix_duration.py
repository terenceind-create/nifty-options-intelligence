# fix_duration.py
content = open('src/dashboard/app.py', 'r', encoding='utf-8').read()

# Add timedelta import
old_import = "from datetime import datetime"
new_import = "from datetime import datetime, timedelta"
content = content.replace(old_import, new_import)

# Add signal duration tracking in the action plan building loop
# Find where we classify actions and add duration tracking
old_classify = """        action_plans.append({
            'Symbol': symbol, 'ActionType': action_type, 'Card': card_class,
            'Spot': latest.spot_price, 'Strike': latest.atm_strike,
            'IV': avg_iv, 'CE_Δ': ce_delta, 'PE_Δ': pe_delta, 'PCR': pcr,
            'CE_OIΔ': ce_oi_chg, 'PE_OIΔ': pe_oi_chg,
            'CE_LTP': ce_ltp, 'PE_LTP': pe_ltp,
            'CE_Vol': ce_volume, 'PE_Vol': pe_volume,
            'M_Bull': m_bullish, 'M_Bear': m_bearish,
            'I_Bull': i_bullish, 'I_Bear': i_bearish,
        })"""

new_classify = """        # Check how long this signal has been active
        signal_duration_minutes = 0
        signal_start_time = None
        
        if action_type != 'WAIT':
            # Look back through history (up to 60 minutes = 60 records at 1-min refresh)
            history_ticks = session.query(OptionsTick)\\
                .filter(OptionsTick.symbol == symbol)\\
                .order_by(OptionsTick.timestamp.desc())\\
                .limit(60)\\
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
        })"""

content = content.replace(old_classify, new_classify)

# Update card display to show duration
old_card_display = """            lot_size = LOT_SIZES.get(plan['Symbol'], 100)
            capital_1_lot = premium * lot_size
            capital_2_lots = premium * lot_size * 2"""

new_card_display = """            lot_size = LOT_SIZES.get(plan['Symbol'], 100)
            capital_1_lot = premium * lot_size
            capital_2_lots = premium * lot_size * 2
            
            # Signal duration text
            duration = plan.get('SignalDuration', 0)
            if duration > 0:
                if duration < 5:
                    duration_text = f"🆕 Fresh signal — just appeared ({duration} min)"
                    duration_color = "#00ffcc"
                elif duration < 15:
                    duration_text = f"🔥 Building momentum — active for {duration} min"
                    duration_color = "#ffcc00"
                elif duration < 30:
                    duration_text = f"📈 Confirmed signal — active for {duration} min"
                    duration_color = "#00ff77"
                else:
                    duration_text = f"⚠️ Mature signal — {duration} min old, may be late"
                    duration_color = "#ffaa00"
            else:
                duration_text = "— signal age not available yet"
                duration_color = "#ffffff\"""" 

# Actually let me use a cleaner replacement
old_card_section = """            lot_size = LOT_SIZES.get(plan['Symbol'], 100)
            capital_1_lot = premium * lot_size
            capital_2_lots = premium * lot_size * 2
            """

new_card_section = """            lot_size = LOT_SIZES.get(plan['Symbol'], 100)
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
                duration_text = "⏳ calculating..."
                duration_color = "#ffffff"
            """

content = content.replace(old_card_section, new_card_section)

# Add duration line in the card HTML
old_card_html = """                <hr style="margin:8px 0; border-color:rgba(255,255,255,0.3)">
                📦 Lot Size: <strong>{lot_size}</strong> shares<br>"""

new_card_html = """                <hr style="margin:8px 0; border-color:rgba(255,255,255,0.3)">
                ⏱️ <span style="color:{duration_color}; font-weight:bold;">{duration_text}</span><br>
                📦 Lot Size: <strong>{lot_size}</strong> shares<br>"""

content = content.replace(old_card_html, new_card_html)

open('src/dashboard/app.py', 'w', encoding='utf-8').write(content)
print('Signal duration tracking added!')