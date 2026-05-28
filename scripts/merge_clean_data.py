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
    #基本信息
    "trade_date",
    "code",
    "name",

    # 当日价格表现
    "close",
    "pct_chg",
    "price_change",
    "open",
    "high",
    "low",
    "pre_close",
    "amplitude",
    "avg_price",

    # 当日成交活跃度
    "total_volume_lot",
    "turnover_rate",
    "amount",
    "volume_ratio",

    # 板块与估值/规模
    "industry",
    "pe_ttm",
    "pb",
    "total_shares",
    "total_market_cap",
    "float_shares",
    "float_market_cap",

    # 短周期趋势
    "pct_chg_3d",
    "pct_chg_6d",
    "turnover_3d",
    "turnover_6d",
    "consecutive_up_days",

    # 中期位置
    "pct_chg_this_month",
    "pct_chg_this_year",
    "pct_chg_1m",
    "pct_chg_1y",

    # 风险标记
    "is_st",
]