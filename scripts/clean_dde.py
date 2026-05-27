from pathlib import Path

import numpy as np
import pandas as pd

from clean_stock_quote import parse_cn_number, clean_stock_code


def clean_dde(input_file, output_file, trade_date):
    """
    Clean Eastmoney DDE decision data.

    Parameters
    ----------
    input_file:
        Raw DDE xlsx path.

    output_file:
        Clean parquet output path.

    trade_date:
        Trading date, e.g. '20260525'.

    Returns
    -------
    pd.DataFrame
        Cleaned DDE dataframe.
    """
    input_file = Path(input_file)
    output_file = Path(output_file)

    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    # DDE has two header rows
    df = pd.read_excel(input_file, header=[0, 1])

    # Expected columns:
    # 序, 代码, 名称, 最新, 涨幅%,
    # 当日资金流: DDX, DDY, DDZ
    # 5日资金流: 5日DDX, 5日DDY
    # 10日资金流: 10日DDX, 10日DDY
    # DDX飘红天数: 连续, 5日内, 10日内
    # 特大买入%, 特大卖出%, 特大单净比%, 大单买入%, 大单卖出%, 大单净比%

    expected_col_count = 21
    if df.shape[1] != expected_col_count:
        raise ValueError(
            f"Unexpected DDE column count: {df.shape[1]}, expected {expected_col_count}"
        )

    df.columns = [
        "seq",
        "code",
        "name",
        "close",
        "pct_chg",
        "ddx",
        "ddy",
        "ddz",
        "ddx_5d",
        "ddy_5d",
        "ddx_10d",
        "ddy_10d",
        "ddx_red_consecutive_days",
        "ddx_red_days_5d",
        "ddx_red_days_10d",
        "super_large_buy_pct",
        "super_large_sell_pct",
        "super_large_net_pct",
        "large_buy_pct",
        "large_sell_pct",
        "large_net_pct",
    ]

    # Drop useless sequence column
    df = df.drop(columns=["seq"])

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
    print("[dde]")
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