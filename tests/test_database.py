# tests/test_database.py
from src.data.models import get_db_session, OptionsTick, FII_DII_Data
from datetime import datetime

def test_database():
    """Test database connection and basic operations"""
    session = get_db_session()
    
    try:
        # Test insert
        test_tick = OptionsTick(
            symbol='TEST',
            timestamp=datetime.now(),
            spot_price=100.0,
            atm_strike=100,
            days_to_expiry=5
        )
        session.add(test_tick)
        session.commit()
        
        # Test query
        result = session.query(OptionsTick).filter_by(symbol='TEST').first()
        print(f"✅ Database working! Test record: {result.symbol} @ {result.spot_price}")
        
        # Clean up
        session.delete(result)
        session.commit()
        
    except Exception as e:
        print(f"❌ Database error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    test_database()