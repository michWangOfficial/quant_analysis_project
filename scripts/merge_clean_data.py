"""
合并每日清洗后的股票数据。

这个脚本做的事情：
1. 从 clean_data/daily/{trade_date}/ 读取已经清洗好的 parquet 文件。
2. 每张表只保留建模需要的字段，避免重复字段进入最终数据。
3. 检查每张表的基础质量，包括文件是否存在、字段是否齐全、code 是否为空或重复、
   单个文件内是否只包含一个 trade_date。
4. 以 stock_quote_clean.parquet 作为主表，按 trade_date + code 左连接其他特征表。
5. 对 capital_flow、dde、staged_stat 强制检查股票池是否和 stock_quote 一致。
6. 对 profit_forecast 不强制股票池一致，因为研报预测数据可能只覆盖部分股票。
7. 输出合并后的 clean_data/daily/{trade_date}/merged_data.parquet。

命令行用法：
    python scripts/merge_clean_data.py 20260527
    python scripts/merge_clean_data.py 20260525 20260526 20260527
    python scripts/merge_clean_data.py all
"""

from pathlib import Path
import sys

import pandas as pd


# 项目根目录。当前脚本在 scripts/ 下，所以 parents[1] 指向项目根目录。
BASE_DIR = Path(__file__).resolve().parents[1]

# 每类清洗后数据对应的 parquet 文件名。
CLEAN_FILES = {
    "stock_quote": "stock_quote_clean.parquet",
    "capital_flow": "capital_flow_clean.parquet",
    "dde": "dde_clean.parquet",
    "staged_stat": "staged_stat_clean.parquet",
    "profit_forecast": "profit_forecast_clean.parquet",
}

# DROP_COLS 主要作为字段边界说明：这些字段通常已经在上游清洗阶段删除。
# 当前合并逻辑实际使用 KEEP_COLS 来决定最终保留哪些字段。
STOCK_QUOTE_DROP_COLS = [
    "current_volume_lot",
    "bid_price",
    "ask_price",
    "speed_pct",
    "order_ratio",
    "order_diff",
    "inner_volume_lot",
    "outer_volume_lot",
    "inner_outer_ratio",
    "bid1_volume_lot",
    "ask1_volume_lot",
]

STOCK_QUOTE_KEEP_COLS = [
    "trade_date",
    "code",
    "name",
    "close",
    "pct_chg",
    "price_change",
    "open",
    "high",
    "low",
    "pre_close",
    "amplitude",
    "avg_price",
    "total_volume_lot",
    "turnover_rate",
    "amount",
    "volume_ratio",
    "industry",
    "pe_ttm",
    "pb",
    "total_shares",
    "total_market_cap",
    "float_shares",
    "float_market_cap",
    "pct_chg_3d",
    "pct_chg_6d",
    "turnover_3d",
    "turnover_6d",
    "consecutive_up_days",
    "pct_chg_this_month",
    "pct_chg_this_year",
    "pct_chg_1m",
    "pct_chg_1y",
    "is_st",
]

CAPITAL_FLOW_DROP_COLS = [
    "name",
    "cf_close",
    "cf_pct_chg",
]

CAPITAL_FLOW_KEEP_COLS = [
    "trade_date",
    "code",
    "main_net_inflow",
    "call_auction_net_inflow",
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

DDE_DROP_COLS = [
    "name",
    "close",
    "pct_chg",
]

DDE_KEEP_COLS = [
    "trade_date",
    "code",
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

STAGED_STAT_DROP_COLS = [
    "name",
    "close",
    "pct_chg",
    "turnover_rate",
    "total_volume_lot",
]

STAGED_STAT_KEEP_COLS = [
    "trade_date",
    "code",
    "pct_chg_5d",
    "pct_chg_10d",
    "pct_chg_20d",
    "turnover_5d",
    "turnover_10d",
    "turnover_20d",
    "outperform_market_days_5d",
    "outperform_market_days_10d",
    "outperform_market_days_20d",
]

PROFIT_FORECAST_DROP_COLS = [
    "name",
    "pf_close",
    "pf_pct_chg",
]

PROFIT_FORECAST_KEEP_COLS = [
    "trade_date",
    "code",
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

KEEP_COLS = {
    "stock_quote": STOCK_QUOTE_KEEP_COLS,
    "capital_flow": CAPITAL_FLOW_KEEP_COLS,
    "dde": DDE_KEEP_COLS,
    "staged_stat": STAGED_STAT_KEEP_COLS,
    "profit_forecast": PROFIT_FORECAST_KEEP_COLS,
}

# 这些表理论上应该覆盖和 stock_quote 一样的股票池。
# 如果缺股票或多股票，说明上游数据可能不完整，合并时直接报错。
STRICT_CODE_ALIGNMENT_TABLES = {
    "capital_flow",
    "dde",
    "staged_stat",
}


def get_clean_dir(trade_date):
    """返回某个交易日的清洗数据目录。"""
    return BASE_DIR / "clean_data" / "daily" / str(trade_date)


def get_output_file(trade_date):
    """返回某个交易日合并结果的输出文件路径。"""
    return BASE_DIR / "clean_data" / "merged_data" / f"{trade_date}.parquet"


def read_clean_table(clean_dir, table_name):
    """
    读取单张清洗后的 parquet 表，并做基础校验。

    校验内容：
    - 文件必须存在。
    - KEEP_COLS 中要求的字段必须全部存在。
    - code 不能为空。
    - code 不能重复，保证后续 one_to_one 合并不会放大行数。
    - 单个文件内只能包含一个 trade_date。
    """
    file_path = clean_dir / CLEAN_FILES[table_name]

    if not file_path.exists():
        raise FileNotFoundError(f"Clean file not found: {file_path}")

    df = pd.read_parquet(file_path)
    keep_cols = KEEP_COLS[table_name]

    missing_cols = [col for col in keep_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(
            f"{table_name} is missing columns: {missing_cols}\n"
            f"Available columns: {df.columns.tolist()}"
        )

    df = df[keep_cols].copy()

    if df["code"].isna().any():
        raise ValueError(f"{table_name} has missing code values.")

    duplicated_codes = df.loc[df["code"].duplicated(), "code"].unique().tolist()
    if duplicated_codes:
        raise ValueError(
            f"{table_name} has duplicated code values: {duplicated_codes[:10]}"
        )

    if df["trade_date"].nunique(dropna=False) != 1:
        raise ValueError(f"{table_name} has multiple trade_date values.")

    return df


def check_code_alignment(base_df, other_df, table_name):
    """
    检查其他表的股票池是否与 stock_quote 完全一致。

    这个检查只用于高覆盖率日频表，不用于 profit_forecast。
    """
    base_codes = set(base_df["code"])
    other_codes = set(other_df["code"])
    only_in_base = sorted(base_codes - other_codes)
    only_in_other = sorted(other_codes - base_codes)

    if only_in_base or only_in_other:
        raise ValueError(
            f"Code universe mismatch between stock_quote and {table_name}. "
            f"Only in stock_quote: {len(only_in_base)}; "
            f"only in {table_name}: {len(only_in_other)}."
        )


def merge_clean_data(trade_date):
    """
    合并某一个交易日的所有清洗后数据，并返回 DataFrame。

    合并顺序：
    1. stock_quote 作为主表。
    2. 依次左连接 capital_flow、dde、staged_stat、profit_forecast。
    3. 每次 merge 使用 validate="one_to_one"，避免重复 code 造成行数异常膨胀。

    注意：
    profit_forecast 仍然左连接，但不要求股票池和 stock_quote 完全一致，因为研报预测
    可能只覆盖部分股票；没有预测数据的股票会在相关字段上保留为空值。
    """
    clean_dir = get_clean_dir(trade_date)

    if not clean_dir.exists():
        raise FileNotFoundError(f"Clean data directory not found: {clean_dir}")

    merged_df = read_clean_table(clean_dir, "stock_quote")

    for table_name in ["capital_flow", "dde", "staged_stat", "profit_forecast"]:
        df = read_clean_table(clean_dir, table_name)

        if table_name in STRICT_CODE_ALIGNMENT_TABLES:
            check_code_alignment(merged_df, df, table_name)

        merged_df = merged_df.merge(
            df,
            on=["trade_date", "code"],
            how="left",
            validate="one_to_one",
        )

    if merged_df["code"].isna().any():
        raise ValueError("Merged data has missing code values.")

    if merged_df["code"].duplicated().any():
        raise ValueError("Merged data has duplicated code values.")

    if merged_df["trade_date"].nunique(dropna=False) != 1:
        raise ValueError("Merged data has multiple trade_date values.")

    return merged_df


def save_merged_data(merged_df, trade_date):
    """
    保存合并后的 DataFrame。

    输出位置：
    clean_data/daily/{trade_date}/merged_data.parquet
    """
    output_file = get_output_file(trade_date)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    merged_df.to_parquet(output_file, index=False)
    print(f"Merged data saved to: {output_file}")


def merge_and_save(trade_date):
    """合并并保存某一个交易日的数据，同时打印运行信息。"""
    print("=" * 80)
    print(f"Start merging clean data: {trade_date}")
    print(f"Clean folder: {get_clean_dir(trade_date)}")
    print(f"Output file: {get_output_file(trade_date)}")
    print("=" * 80)

    merged_df = merge_clean_data(trade_date)
    save_merged_data(merged_df, trade_date)

    print(f"Final shape: {merged_df.shape}")
    print()

    return merged_df


def get_available_clean_dates():
    """扫描 clean_data/daily/，返回所有可用的数字交易日目录。"""
    daily_clean_dir = BASE_DIR / "clean_data" / "daily"

    if not daily_clean_dir.exists():
        raise FileNotFoundError(f"Daily clean folder not found: {daily_clean_dir}")

    trade_dates = [
        folder.name
        for folder in daily_clean_dir.iterdir()
        if folder.is_dir() and folder.name.isdigit()
    ]

    return sorted(trade_dates)


def main(trade_date=None):
    """
    命令行入口，也兼容在其他 Python 代码里直接调用 main(trade_date)。

    示例：
    python scripts/merge_clean_data.py 20260527
    python scripts/merge_clean_data.py 20260525 20260526 20260527
    python scripts/merge_clean_data.py all
    """
    if trade_date is not None:
        return merge_and_save(trade_date)

    if len(sys.argv) <= 1:
        raise ValueError(
            "Please provide trade date, e.g. "
            "python scripts/merge_clean_data.py 20260527"
        )

    args = sys.argv[1:]
    trade_dates = get_available_clean_dates() if args == ["all"] else args

    for date in trade_dates:
        merge_and_save(date)

    return None


if __name__ == "__main__":
    main()
