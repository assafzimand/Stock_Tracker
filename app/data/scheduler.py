from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, time
import pytz
import atexit

from app.data.fetcher import fetch_and_store_stock_prices
from app.config.constants import SAMPLE_INTERVAL_MINUTES

# U.S. Eastern timezone
EASTERN = pytz.timezone("US/Eastern")

scheduler = BackgroundScheduler()

def is_trading_hours(now: datetime) -> bool:
    """
    Returns True if current time is within trading hours (9:30–16:00 ET on weekdays).
    """
    now_et = now.astimezone(EASTERN)

    if now_et.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
        return False

    market_open = time(9, 30)
    market_close = time(16, 0)
    return market_open <= now_et.time() <= market_close

def _scheduled_job():
    """
    Called every 5 minutes during the scheduler window.
    Executes fetch only if current time is within market hours.
    """
    now = datetime.now(pytz.utc)
    if is_trading_hours(now):
        print(f"[INFO] Running fetch at {now.isoformat()}")
        fetch_and_store_stock_prices()
    else:
        print(f"[SKIP] Outside market hours: {now.isoformat()}")

def start_scheduler():
    """
    Starts the scheduler to run every N minutes, Mon–Fri, 9:00–16:30 ET.
    """
    trigger = CronTrigger(
        day_of_week='mon-fri',
        hour='9-16',
        minute=f'*/{SAMPLE_INTERVAL_MINUTES}',
        timezone=EASTERN
    )

    scheduler.add_job(
        _scheduled_job,
        trigger=trigger,
        name="Stock Price Fetcher",
        replace_existing=True
    )
    scheduler.start()
    print("[INFO] Scheduler started.")

    atexit.register(stop_scheduler)

def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        print("[INFO] Scheduler stopped.")
    else:
        print("[INFO] Scheduler was not running.")

