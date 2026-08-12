# test_setup.py
print("Testing project setup...")

# Test 1: Imports
try:
    from config.settings import settings
    print("✅ Settings imported")
except Exception as e:
    print(f"❌ Settings error: {e}")

# Test 2: Database
try:
    from src.data.models import get_db_session
    session = get_db_session()
    print("✅ Database connected")
    session.close()
except Exception as e:
    print(f"❌ Database error: {e}")

# Test 3: Greeks Calculator
try:
    from src.analysis.greeks_calculator import GreeksCalculator
    calc = GreeksCalculator()
    greeks = calc.calculate_all_greeks('call', 2500, 2500, 5/365, 0.065, 0.3)
    print(f"✅ Greeks Calculator working: Delta={greeks['delta']}")
except Exception as e:
    print(f"❌ Greeks error: {e}")

print("\nSetup test complete!")