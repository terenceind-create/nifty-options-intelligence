# insert_test_data.py
"""Insert realistic test data into database"""
from src.data.models import get_db_session, OptionsTick, FII_DII_Data
from datetime import datetime, timedelta
import random
import math

def insert_test_data():
    session = get_db_session()
    
    # Realistic base prices for stocks
    stock_data = {
        'RELIANCE': {'spot': 2850, 'volatility': 0.02},
        'HDFCBANK': {'spot': 1650, 'volatility': 0.018},
        'ICICIBANK': {'spot': 1250, 'volatility': 0.02},
        'INFY': {'spot': 1750, 'volatility': 0.022},
        'AXISBANK': {'spot': 1100, 'volatility': 0.025}
    }
    
    # Insert data for last 24 hours (every 5 minutes)
    for hours_ago in range(24 * 12, 0, -1):  # 24 hours * 12 (5-min intervals)
        timestamp = datetime.now() - timedelta(minutes=hours_ago * 5)
        
        for symbol, info in stock_data.items():
            base_spot = info['spot']
            volatility = info['volatility']
            
            # Add some random walk
            spot_change = random.gauss(0, base_spot * volatility)
            spot = base_spot + spot_change
            
            atm = round(spot / 50) * 50
            days_to_expiry = random.randint(0, 7)
            
            # Realistic IV based on expiry proximity
            base_iv = 0.25 + (0.01 * (7 - days_to_expiry))  # Higher IV closer to expiry
            ce_iv = max(0.15, base_iv + random.gauss(0, 0.02))
            pe_iv = max(0.15, base_iv + random.gauss(0, 0.03))
            
            # Generate realistic Greeks
            T = max(days_to_expiry / 365.0, 0.001)
            moneyness = spot / atm
            
            # CE Greeks
            ce_delta = min(0.95, max(0.05, 0.5 + (moneyness - 1) * 2))
            ce_gamma = random.uniform(0.001, 0.008) * (1 + 1/T)
            ce_theta = random.uniform(-8, -0.5)
            ce_vega = random.uniform(1, 8)
            
            # PE Greeks
            pe_delta = -min(0.95, max(0.05, 0.5 - (moneyness - 1) * 2))
            pe_gamma = random.uniform(0.001, 0.008) * (1 + 1/T)
            pe_theta = random.uniform(-8, -0.5)
            pe_vega = random.uniform(1, 8)
            
            tick = OptionsTick(
                symbol=symbol,
                timestamp=timestamp,
                spot_price=round(spot, 2),
                atm_strike=atm,
                days_to_expiry=days_to_expiry,
                ce_ltp=round(random.uniform(20, 150), 2),
                ce_bid=round(random.uniform(20, 145), 2),
                ce_ask=round(random.uniform(25, 155), 2),
                ce_oi=random.randint(50000, 500000),
                ce_oi_change=random.randint(-25000, 25000),
                ce_volume=random.randint(5000, 50000),
                ce_iv=round(ce_iv, 4),
                ce_delta=round(ce_delta, 4),
                ce_gamma=round(ce_gamma, 4),
                ce_theta=round(ce_theta, 4),
                ce_vega=round(ce_vega, 4),
                pe_ltp=round(random.uniform(20, 150), 2),
                pe_bid=round(random.uniform(20, 145), 2),
                pe_ask=round(random.uniform(25, 155), 2),
                pe_oi=random.randint(50000, 500000),
                pe_oi_change=random.randint(-25000, 25000),
                pe_volume=random.randint(5000, 50000),
                pe_iv=round(pe_iv, 4),
                pe_delta=round(pe_delta, 4),
                pe_gamma=round(pe_gamma, 4),
                pe_theta=round(pe_theta, 4),
                pe_vega=round(pe_vega, 4),
                pcr=round(random.uniform(0.6, 1.5), 2),
                is_expiry_day=(days_to_expiry == 0)
            )
            
            session.add(tick)
    
    # Insert some FII/DII data
    for days_ago in range(7, 0, -1):
        date = datetime.now().date() - timedelta(days=days_ago)
        fii_dii = FII_DII_Data(
            date=date,
            fii_net=round(random.uniform(-3000, 5000), 2),
            dii_net=round(random.uniform(-2000, 3000), 2)
        )
        session.add(fii_dii)
    
    session.commit()
    session.close()
    print("✅ Realistic test data inserted successfully!")
    print(f"   - 5 stocks × 288 timepoints = {5 * 288} option records")
    print(f"   - 7 days of FII/DII data")
    print(f"   - Data spans last 24 hours at 5-min intervals")

if __name__ == "__main__":
    insert_test_data()