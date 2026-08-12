# check_expiry.py
from datetime import date, timedelta
import calendar

today = date.today()
print(f"Today: {today} ({calendar.day_name[today.weekday()]})")

# Find last Tuesday of current month
c = calendar.monthcalendar(today.year, today.month)
last_tue = max([week[1] for week in c if week[1] != 0])
expiry = date(today.year, today.month, last_tue)
print(f"This month's last Tuesday: {expiry} ({calendar.day_name[expiry.weekday()]})")

if today > expiry:
    # Move to next month
    if today.month == 12:
        next_month, next_year = 1, today.year + 1
    else:
        next_month, next_year = today.month + 1, today.year
    
    c = calendar.monthcalendar(next_year, next_month)
    last_tue = max([week[1] for week in c if week[1] != 0])
    expiry = date(next_year, next_month, last_tue)
    print(f"Next month expiry: {expiry} ({calendar.day_name[expiry.weekday()]})")

days_to_expiry = (expiry - today).days
print(f"\nDays to expiry: {days_to_expiry}")