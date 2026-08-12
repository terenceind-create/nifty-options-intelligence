# find_instrument.py
import requests
import csv
import io

print("Downloading NSE equity instruments...")
url = "https://assets.upstox.com/market-quote/instruments/exchange/NSE_EQ.csv"
r = requests.get(url)

if r.status_code == 200:
    content = r.text
    reader = csv.reader(io.StringIO(content))
    
    # Find Reliance
    for row in reader:
        if len(row) > 3 and 'RELIANCE' in row[3].upper():
            print(f"Found: {row}")
            print(f"Instrument Key: {row[0]}")
            print(f"Trading Symbol: {row[3]}")
            print(f"Name: {row[4] if len(row) > 4 else 'N/A'}")
            break
else:
    print(f"Failed to download: {r.status_code}")