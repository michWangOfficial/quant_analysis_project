from pathlib import Path

import pandas as pd

from clean_stock_quote import parse_cn_number, clean_stock_code


def clean_profit_forecast(input_file, output_file, trade_date):
    """
    Clean Eastmoney profit forecast data.

    Parameters
    ----------
    input_file:
        Raw profit_forecast xlsx path.

    output_file:
        Clean parquet output path.

    trade_date:
        Trading date, e.g. '20260525'.

    Returns
    -------
    pd.DataFrame
        Cleaned profit_forecast dataframe.
    """
    input_file = Path(input_file)
    output_file = Path(output_file)

    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    # profit_forecast has two header rows
    df = pd.read_excel(input_file, header=[0, 1])

    expected_col_count = 22

    if df.shape[1] != expected_col_count:
        raise ValueError(
            f"Unexpected profit_forecast column count: {df.shape[1]}, "
            f"expected {expected_col_count}. Please inspect the raw columns."
        )

    df.columns = [
        "seq",
        "code",
        "name",

        # These two columns are just Eastmoney clickable labels, not useful for modeling
        "related_report",
        "related_quote",

        "pf_close",
        "pf_pct_chg",
        "research_report_count",

        "rating_buy_count_6m",
        "rating_overweight_count_6m",
        "rating_neutral_count_6m",
        "rating_underweight_count_6m",
        "rating_sell_count_6m",

        "actual_eps_2025",

        "forecast_eps_2026",
        "forecast_pe_2026",

        "forecast_eps_2027",
        "forecast_pe_2027",

        "forecast_eps_2028",
        "forecast_pe_2028",

        "forecast_eps_2029",
        "forecast_pe_2029",
    ]

    # Drop useless columns
    df = df.drop(columns=["seq", "related_report", "related_quote"])

    # Add trade date
    df.insert(0, "trade_date", pd.to_datetime(trade_date))

    # Clean stock code
    df["code"] = df["code"].apply(clean_stock_code)

    # Convert numeric columns
    non_numeric_cols = ["trade_date", "code", "name"]

    for col in df.columns:
        if col not in non_numeric_cols:
            df[col] = df[col].apply(parse_cn_number)

    # Basic validation
    print("[profit_forecast]")
    print(f"Input file: {input_file}")
    print(f"Output file: {output_file}")
    print(f"Shape: {df.shape}")
    print(f"Duplicate codes: {df['code'].duplicated().sum()}")
    print(f"Missing codes: {df['code'].isna().sum()}")
    print(df.head())

    output_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_file, index=False)

    print("Saved successfully.")
    print()

    return df