import os
import json
import random
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt

from app.analysis import detect_cup_and_handle, plot_prices
from app.config.constants import STOCK_SYMBOLS


def test_detect_random_company():
    # === Setup paths relative to this script ===
    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_dir = os.path.join(base_dir, "..", "app", "data", "synth_data_json", "labels_json")
    output_csv_path = os.path.join(base_dir, "..", "app", "data", "stock_data.csv")

    required_samples = 234
    end_time = datetime.utcnow().replace(hour=16, minute=0, second=0, microsecond=0)

    company_symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA"]
    json_files = [f for f in os.listdir(json_dir) if f.endswith(".json")]
    selected_files = random.sample(json_files, 7)

    all_data = []
    for file, symbol in zip(selected_files, company_symbols):
        with open(os.path.join(json_dir, file), "r") as f:
            raw_data = json.load(f)
        prices = [entry["close"] for entry in raw_data["ohlcv_data"]][-required_samples:]
        timestamps = [end_time - timedelta(minutes=5 * i) for i in reversed(range(required_samples))]
        all_data.extend({
            "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
            "symbol": symbol,
            "price": price
        } for ts, price in zip(timestamps, prices))

    df = pd.DataFrame(all_data)
    df.to_csv(output_csv_path, index=False)
    print(f"Generated {output_csv_path}")
    
    companies = list(STOCK_SYMBOLS.values())
    
    for company in companies:
        result, pattern_points = detect_cup_and_handle(company)

        print(f"Pattern detected for {company}: {result}")
        
        # Create result directory once
        if 'result_dir' not in locals():
            timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
            result_dir = os.path.join(os.path.dirname(__file__), "test_results", timestamp)
            os.makedirs(result_dir, exist_ok=True)

        # Save plot to PNG file
        fig = plot_prices(
            company,
            title=f"{company} - Pattern Detected: {result}",
            pattern_points=pattern_points if result else None
        )
        plot_path = os.path.join(result_dir, f"{company}.png")
        fig.savefig(plot_path)
        plt.close(fig)



if __name__ == "__main__":
    random.seed(40)  # Set seed for reproducibility
    test_detect_random_company()
