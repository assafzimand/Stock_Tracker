from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo
import pytz
import atexit
import logging

from app.data.fetcher import fetch_and_store_stock_prices
from app.config.constants import SAMPLE_INTERVAL_MINUTES

# U.S. Eastern timezone
EASTERN = ZoneInfo("America/New_York")

scheduler = BackgroundScheduler()

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def is_trading_hours(now: datetime) -> bool:
    """
    Determine if the current time is within trading hours (9:30–16:00 ET on weekdays).

    Args:
        now (datetime): The current datetime in UTC.

    Returns:
        bool: True if within trading hours, False otherwise.
    """
    now_et = now.astimezone(EASTERN)

    if now_et.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
        return False

    market_open = time(9, 30)
    market_close = time(16, 0)
    return market_open <= now_et.time() <= market_close

def _scheduled_job():
    """
    Execute the fetch job every 5 minutes during the scheduler window.
    Fetches stock prices only if the current time is within market hours.
    """
    now = datetime.now(timezone.utc)
    if is_trading_hours(now):
        logging.info(f"Running fetch at {now.isoformat()}")
        fetch_and_store_stock_prices()
    else:
        logging.info(f"Outside market hours: {now.isoformat()}")

def start_scheduler():
    """
    Start the scheduler to run every N minutes, Mon–Fri, 9:00–16:30 ET.
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
    logging.info("Scheduler started.")

    atexit.register(stop_scheduler)

def stop_scheduler():
    """
    Stop the scheduler if it is running.
    """
    if scheduler.running:
        scheduler.shutdown()
        logging.info("Scheduler stopped.")
    else:
        logging.info("Scheduler was not running.")

