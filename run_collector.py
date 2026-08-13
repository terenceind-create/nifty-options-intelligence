# run_collector.py
import sys
import time
import argparse
from src.data.collector import DataCollector

def main():
    parser = argparse.ArgumentParser(description='Nifty Options Data Collector')
    parser.add_argument('--refresh', '-r', type=int, default=60,
                       choices=[60, 180, 300],
                       help='Refresh interval: 180 (3min), 300 (5min), 900 (15min)')
    args = parser.parse_args()
    
    refresh_map = {60: "1 minute", 180: "3 minutes", 300: "5 minutes"}
    
    print("\n" + "="*60)
    print("NIFTY OPTIONS DATA COLLECTOR")
    print("="*60)
    print(f"\nRefresh interval: {refresh_map.get(args.refresh, str(args.refresh))}")
    print(f"Tracking 20 Nifty stocks")
    print("\nPress Ctrl+C to stop\n")
    
    collector = DataCollector(refresh_interval=args.refresh)
    collector.start_collection()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping collector...")
        collector.stop_collection()
        print("Stopped.")

if __name__ == "__main__":
    main()