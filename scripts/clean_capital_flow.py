from pathlib import Path

import pandas as pd

from clean_stock_quote import parse_cn_number, clean_stock_code


def clean_capital_flow(input_file, output_file, trade_date):
    """
    Clean Eastmoney capital flow data.

    Parameters
    ----------
    input_file:
        Raw capital_flow xlsx path.

    output_file:
        Clean parquet output path.

    trade_date:
        Trading date, e.g. '20260525'.

    Returns
    -------
    pd.DataFrame
        Cleaned capital_flow dataframe.
    """
    input_file = Path(input_file)
    output_file = Path(output_file)

    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    # capital_flow has two header rows
    df = pd.read_excel(input_file, header=[0, 1])

    # Expected structure:
    # 序, 代码, 名称, 最新, 涨幅%
    # 主力净流入, 主力净比
    # 超大单流入, 超大单流出, 超大单净额, 超大单净比
    # 大单流入, 大单流出, 大单净额, 大单净比
    # 中单流入, 中单流出, 中单净额, 中单净比
    # 小单流入, 小单流出, 小单净额, 小单净比

    expected_col_count = 23

    if df.shape[1] != expected_col_count:
        raise ValueError(
            f"Unexpected capital_flow column count: {df.shape[1]}, "
            f"expected {expected_col_count}. "
            f"Please inspect the raw columns."
        )

    df.columns = [
        "seq",
        "code",
        "name",
        "cf_close",
        "cf_pct_chg",

        "main_net_inflow",
        "main_net_inflow_pct",

        "super_large_inflow",
        "super_large_outflow",
        "super_large_net_inflow",
        "super_large_net_inflow_pct",

        "large_inflow",
        "large_outflow",
        "large_net_inflow",
        "large_net_inflow_pct",

        "medium_inflow",
        "medium_outflow",
        "medium_net_inflow",
        "medium_net_inflow_pct",

        "small_inflow",
        "small_outflow",
        "small_net_inflow",
        "small_net_inflow_pct",
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
    print("[capital_flow]")
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