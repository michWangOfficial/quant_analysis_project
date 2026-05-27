from pathlib import Path
import sys

#import the cleaning functions
from clean_stock_quote import clean_stock_quote
from clean_dde import clean_dde
from clean_staged_stat import clean_staged_stat
from clean_capital_flow import clean_capital_flow
from clean_profit_forecast import clean_profit_forecast

BASE_DIR = Path(__file__).resolve().parents[1]

DAILY_CLEANING_TASKS = [
    {
        "name": "stock_quote",
        "raw_file": "stock_quote.xlsx",
        "clean_file": "stock_quote_clean.parquet",
        "function": clean_stock_quote,
    },
    {
        "name": "dde",
        "raw_file": "dde.xlsx",
        "clean_file": "dde_clean.parquet",
        "function": clean_dde,
    },
    {
        "name": "staged_stat",
        "raw_file": "staged_stat.xlsx",
        "clean_file": "staged_stat_clean.parquet",
        "function": clean_staged_stat,
    },
    {
        "name": "capital_flow",
        "raw_file": "capital_flow.xlsx",
        "clean_file": "capital_flow_clean.parquet",
        "function": clean_capital_flow,
    },
    {
        "name": "profit_forecast",
        "raw_file": "profit_forecast.xlsx",
        "clean_file": "profit_forecast_clean.parquet",
        "function": clean_profit_forecast,
    },
]
def clean_daily_data(trade_date):
    """
    Clean all daily raw xlsx files for one trading date.

    Folder structure:

    raw_data/daily/20260527/
        stock_quote.xlsx
        capital_flow.xlsx
        dde.xlsx
        staged_stat.xlsx
        profit_forecast.xlsx

    clean_data/daily/20260527/
        stock_quote_clean.parquet
        capital_flow_clean.parquet
        dde_clean.parquet
        staged_stat_clean.parquet
        profit_forecast_clean.parquet
    """
    raw_dir = BASE_DIR / "raw_data" / "daily" / trade_date
    clean_dir = BASE_DIR / "clean_data" / "daily" / trade_date

    print("=" * 80)
    print(f"Start cleaning daily data: {trade_date}")
    print(f"Raw folder: {raw_dir}")
    print(f"Clean folder: {clean_dir}")
    print("=" * 80)

    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw data folder not found: {raw_dir}")

    for task in DAILY_CLEANING_TASKS:
        name = task["name"]
        input_file = raw_dir / task["raw_file"]
        output_file = clean_dir / task["clean_file"]
        clean_function = task["function"]

        if not input_file.exists():
            print(f"[SKIP] {name}: raw file not found: {input_file}")
            continue

        print(f"[RUN] {name}")

        clean_function(
            input_file=input_file,
            output_file=output_file,
            trade_date=trade_date,
        )

    print("=" * 80)
    print(f"Finished cleaning daily data: {trade_date}")
    print("=" * 80)
    print()


def clean_multiple_dates(trade_dates):
    for trade_date in trade_dates:
        clean_daily_data(trade_date)


def get_available_trade_dates():
    daily_raw_dir = BASE_DIR / "raw_data" / "daily"

    if not daily_raw_dir.exists():
        raise FileNotFoundError(f"Daily raw data folder not found: {daily_raw_dir}")

    trade_dates = [
        folder.name
        for folder in daily_raw_dir.iterdir()
        if folder.is_dir() and folder.name.isdigit()
    ]

    return sorted(trade_dates)


def main():
    """
    Usage:

    Clean one day:
        python scripts/clean_raw_data.py 20260527

    Clean multiple days:
        python scripts/clean_raw_data.py 20260525 20260526 20260527

    Clean all available daily folders:
        python scripts/clean_raw_data.py all
    """
    if len(sys.argv) <= 1:
        raise ValueError(
            "Please provide a trade date, e.g. "
            "python scripts/clean_raw_data.py 20260527"
        )

    args = sys.argv[1:]

    if args == ["all"]:
        trade_dates = get_available_trade_dates()
    else:
        trade_dates = args

    clean_multiple_dates(trade_dates)


if __name__ == "__main__":
    main()