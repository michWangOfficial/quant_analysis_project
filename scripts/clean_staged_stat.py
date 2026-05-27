from pathlib import Path

import pandas as pd

from clean_stock_quote import parse_cn_number, clean_stock_code


def clean_staged_stat(input_file, output_file, trade_date):
    """
    Clean Eastmoney staged statistics data.

    Parameters
    ----------
    input_file:
        Raw staged_stat xlsx path.

    output_file:
        Clean parquet output path.

    trade_date:
        Trading date, e.g. '20260525'.

    Returns
    -------
    pd.DataFrame
        Cleaned staged_stat dataframe.
    """
    input_file = Path(input_file)
    output_file = Path(output_file)

    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    df = pd.read_excel(input_file, dtype={"代码": str})

    # Clean column names
    df.columns = [str(col).strip() for col in df.columns]

    # Drop useless columns
    drop_cols = [col for col in df.columns if col == "序" or col.startswith("Unnamed")]
    if drop_cols:
        df = df.drop(columns=drop_cols)

    # Add trade date
    df.insert(0, "trade_date", pd.to_datetime(trade_date))

    # Clean stock code
    df["代码"] = df["代码"].apply(clean_stock_code)

    rename_map = {
        "代码": "code",
        "名称": "name",
        "最新": "close",
        "涨幅%": "pct_chg",
        "换手%": "turnover_rate",
        "总量": "total_volume_lot",
        "5日涨幅%": "pct_chg_5d",
        "10日涨幅%": "pct_chg_10d",
        "20日涨幅%": "pct_chg_20d",
        "5日换手率%": "turnover_5d",
        "10日换手率%": "turnover_10d",
        "20日换手率%": "turnover_20d",
        "5日跑赢大盘天数": "outperform_market_days_5d",
        "10日跑赢大盘天数": "outperform_market_days_10d",
        "20日跑赢大盘天数": "outperform_market_days_20d",
    }

    df = df.rename(columns=rename_map)

    # Convert numeric columns
    non_numeric_cols = ["trade_date", "code", "name"]

    for col in df.columns:
        if col not in non_numeric_cols:
            df[col] = df[col].apply(parse_cn_number)

    # Basic validation
    print("[staged_stat]")
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