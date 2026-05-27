from pathlib import Path
import numpy as np
import pandas as pd

def parse_cn_number(x):
    """
    Convert Chinese-style numeric strings to float.

    Examples:
    '1.47亿' -> 147000000
    '66.0万' -> 660000
    '10.03%' -> 10.03
    '—' / '--' -> NaN
    """
    if pd.isna(x):
        return np.nan

    if isinstance(x, (int, float)):
        return float(x)

    s = str(x).strip().replace(",", "")

    if s in ["—", "--", "-", "", "nan", "None"]:
        return np.nan

    if s.endswith("%"):
        s = s[:-1]

    multiplier = 1

    if s.endswith("亿"):
        multiplier = 100000000
        s = s[:-1]
    elif s.endswith("万"):
        multiplier = 10000
        s = s[:-1]

    try:
        return float(s) * multiplier
    except ValueError:
        return np.nan

def clean_stock_code(x):
    """
    Convert stock code to 6-digit string.

    Examples:
    926 -> '000926'
    2526 -> '002526'
    600519 -> '600519'
    """
    if pd.isna(x):
        return np.nan

    s = str(x).strip()

    if s.endswith(".0"):
        s = s[:-2]

    return s.zfill(6)

def clean_stock_quote(input_file, output_file, trade_date):
    """
    Clean Eastmoney stock quote xlsx file and save as parquet.

    Parameters
    ----------
    input_file : str or Path
        Raw xlsx file path.

    output_file : str or Path
        Clean parquet output path.

    trade_date : str
        Trading date, e.g. '20260525'.

    Returns
    -------
    pd.DataFrame
        Cleaned stock quote dataframe.
    """
    input_file = Path(input_file)
    output_file = Path(output_file)

    df = pd.read_excel(input_file, dtype={"代码": str})

    df.columns = [str(c).strip() for c in df.columns]

    # Drop useless or empty columns
    drop_cols = []
    for col in df.columns:
        if col == "序" or col.startswith("Unnamed"):
            drop_cols.append(col)

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
        "涨跌": "price_change",
        "总量": "total_volume_lot",
        "现量": "current_volume_lot",
        "买入价": "bid_price",
        "卖出价": "ask_price",
        "涨速%": "speed_pct",
        "换手%": "turnover_rate",
        "金额": "amount",
        "市盈率(动)": "pe_ttm",
        "所属行业": "industry",
        "最高": "high",
        "最低": "low",
        "开盘": "open",
        "昨收": "pre_close",
        "振幅%": "amplitude",
        "量比": "volume_ratio",
        "委比%": "order_ratio",
        "委差": "order_diff",
        "均价": "avg_price",
        "内盘": "inner_volume_lot",
        "外盘": "outer_volume_lot",
        "内外比": "inner_outer_ratio",
        "买一量": "bid1_volume_lot",
        "卖一量": "ask1_volume_lot",
        "市净率": "pb",
        "总股本": "total_shares",
        "总市值": "total_market_cap",
        "流通股本": "float_shares",
        "流通市值": "float_market_cap",
        "3日涨幅%": "pct_chg_3d",
        "6日涨幅%": "pct_chg_6d",
        "3日换手%": "turnover_3d",
        "6日换手%": "turnover_6d",
        "连涨天数": "consecutive_up_days",
        "本月涨幅%": "pct_chg_this_month",
        "今年涨幅%": "pct_chg_this_year",
        "近一月涨幅%": "pct_chg_1m",
        "近一年涨幅%": "pct_chg_1y",
    }

    df = df.rename(columns=rename_map)

    non_numeric_cols = ["trade_date", "code", "name", "industry"]

    for col in df.columns:
        if col not in non_numeric_cols:
            df[col] = df[col].apply(parse_cn_number)

    # Add risk flag
    df["is_st"] = df["name"].astype(str).str.contains("ST", na=False)

    # Basic checks
    print("[stock_quote]")
    print("Input:", input_file)
    print("Shape:", df.shape)
    print("Duplicate codes:", df["code"].duplicated().sum())
    print("Missing codes:", df["code"].isna().sum())

    output_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_file, index=False)

    print("Saved:", output_file)
    print()

    return df