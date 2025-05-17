import time
from app.data.storage import load_existing_data_if_available
from app.data.scheduler import start_scheduler

def test_data_pipeline():
    """
    Test the data pipeline by loading existing data and running the scheduler.

    This function simulates the data pipeline by loading existing data, starting the scheduler,
    and running for a short period to verify functionality.
    """
    print("📦 Loading existing data (if any)...")
    load_existing_data_if_available()

    print("⏱️ Starting scheduler (should run every ~1 minute)...")
    try:
        start_scheduler()
    except Exception as e:
        print(f"Error starting scheduler: {e}")

    print("🔄 Running for 2.5 minutes to simulate fast data pipeline...")
    try:
        time.sleep(72000)  # 2.5 minutes
    except KeyboardInterrupt:
        print("\n⛔ Interrupted by user.")

    print("✅ Done. Check app/data/stock_data.csv for results.")

if __name__ == "__main__":
    test_data_pipeline()
