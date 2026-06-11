# 股票日频数据清洗与合并流程

这个项目用于把每日导出的原始 Excel 数据清洗成统一的 parquet 文件，并进一步合并成单日建模数据。

当前流程分两步：

1. `clean`：把 `raw_data` 下的原始 xlsx 文件清洗成标准字段的 parquet。
2. `merge`：把同一天的多张 clean parquet 按 `trade_date + code` 合并成一张表。

## 环境准备

建议使用 Python 3.11 创建并激活虚拟环境，避免 3.14 这类版本在安装 NumPy / pyarrow 时出现兼容性问题。

创建 Python 3.11 虚拟环境：

```powershell
py -3.11 -m venv .venv
```

激活虚拟环境：

```powershell
.\.venv\Scripts\Activate.ps1
```

安装依赖：

```powershell
pip install -r requirements.txt
```

如果你想确认当前环境是 3.11，可以运行：

```powershell
python -V
```

## 目录结构

原始数据放在：

```text
raw_data/daily/{trade_date}/
```

例如：

```text
raw_data/daily/20260527/
    stock_quote.xlsx
    capital_flow.xlsx
    dde.xlsx
    staged_stat.xlsx
    profit_forecast.xlsx
```

清洗后的数据会输出到：

```text
clean_data/daily/{trade_date}/
```

例如：

```text
clean_data/daily/20260527/
    stock_quote_clean.parquet
    capital_flow_clean.parquet
    dde_clean.parquet
    staged_stat_clean.parquet
    profit_forecast_clean.parquet
```

合并后的结果会输出到：

```text
clean_data/merged_data/{trade_date}.parquet
```

例如：

```text
clean_data/merged_data/20260527.parquet
```

## Clean：清洗原始数据

总入口是：

```text
scripts/clean_raw_data.py
```

它会根据交易日目录，依次调用下面 5 个清洗脚本：

| 数据类型 | 原始文件 | 清洗脚本 | 输出文件 |
| --- | --- | --- | --- |
| 股票行情 | `stock_quote.xlsx` | `clean_stock_quote.py` | `stock_quote_clean.parquet` |
| 资金流 | `capital_flow.xlsx` | `clean_capital_flow.py` | `capital_flow_clean.parquet` |
| DDE 决策 | `dde.xlsx` | `clean_dde.py` | `dde_clean.parquet` |
| 阶段统计 | `staged_stat.xlsx` | `clean_staged_stat.py` | `staged_stat_clean.parquet` |
| 盈利预测 | `profit_forecast.xlsx` | `clean_profit_forecast.py` | `profit_forecast_clean.parquet` |

运行单个交易日：

```bash
python scripts/clean_raw_data.py 20260527
```

运行多个交易日：

```bash
python scripts/clean_raw_data.py 20260525 20260526 20260527
```

运行 `raw_data/daily/` 下所有可用交易日：

```bash
python scripts/clean_raw_data.py all
```

### Clean 具体做什么

清洗阶段主要做这些事情：

- 读取东方财富导出的 xlsx 文件。
- 删除无用列，例如序号列、空列、`Unnamed` 列等。
- 给每一行加入 `trade_date`。
- 把股票代码统一清洗为 6 位字符串，例如 `926` 变成 `000926`。
- 把中文数字、百分号、金额单位等转成可计算的数值。
- 把中文原始列名重命名成英文标准字段名。
- 打印基础检查信息，包括数据形状、重复 code 数量、缺失 code 数量。
- 保存为 parquet，方便后续快速读取和建模。

### 各清洗脚本重点

`clean_stock_quote.py`

- 清洗每日行情数据。
- 保留价格、涨跌幅、成交量、成交额、换手率、行业、估值、市值、短周期涨幅等字段。
- 额外生成 `is_st` 字段，用于标记股票名称中是否包含 `ST`。

`clean_capital_flow.py`

- 清洗资金流数据。
- 原始文件有两行表头，脚本会按固定列数校验结构。
- 输出主力净流入、竞价净流入、超大单/大单/中单/小单的流入、流出、净流入和净占比。

`clean_dde.py`

- 清洗 DDE 决策数据。
- 原始文件有两行表头，脚本会按固定列数校验结构。
- 输出 `ddx`、`ddy`、`ddz`、5 日/10 日 DDX 和 DDY、DDX 飘红天数，以及大单买卖比例等字段。

`clean_staged_stat.py`

- 清洗阶段统计数据。
- 输出 5 日、10 日、20 日涨幅，5 日、10 日、20 日换手率，以及跑赢大盘天数。

`clean_profit_forecast.py`

- 清洗盈利预测和机构评级数据。
- 原始文件有两行表头，脚本会按固定列数校验结构。
- 删除网页跳转类字段，只保留研报数量、评级数量、实际 EPS、预测 EPS 和预测 PE。

## Merge：合并清洗后的数据

合并入口是：

```text
scripts/merge_clean_data.py
```

它读取同一天的 5 个 clean parquet：

```text
stock_quote_clean.parquet
capital_flow_clean.parquet
dde_clean.parquet
staged_stat_clean.parquet
profit_forecast_clean.parquet
```

然后输出到：

```text
clean_data/merged_data/{trade_date}.parquet
```

运行单个交易日：

```bash
python scripts/merge_clean_data.py 20260527
```

运行多个交易日：

```bash
python scripts/merge_clean_data.py 20260525 20260526 20260527
```

运行 `clean_data/daily/` 下所有可用交易日：

```bash
python scripts/merge_clean_data.py all
```

### Merge 具体做什么

合并阶段主要做这些事情：

- 以 `stock_quote_clean.parquet` 作为主表。
- 每张表只保留 `KEEP_COLS` 中定义的建模字段。
- 按 `trade_date + code` 左连接其他表。
- 每次合并使用 `validate="one_to_one"`，防止重复股票代码导致行数膨胀。
- 合并完成后保存为 `clean_data/merged_data/{trade_date}.parquet`。

### Merge 的数据校验

合并前，每张 clean 表都会检查：

- parquet 文件是否存在。
- 需要保留的字段是否都存在。
- `code` 是否为空。
- `code` 是否重复。
- 文件内是否只包含一个 `trade_date`。

此外，下面几张表必须和 `stock_quote` 股票池完全一致：

```text
capital_flow
dde
staged_stat
```

如果这些表缺少股票或多出股票，脚本会直接报错。这通常说明上游数据导出不完整，或者不同表不是同一个交易日/同一个股票范围。

`profit_forecast` 不强制和 `stock_quote` 股票池一致，因为盈利预测和研报覆盖通常只包含部分股票。合并时仍然左连接，没有预测数据的股票会在对应字段上保留空值。

## 推荐运行顺序

先清洗：

```bash
python scripts/clean_raw_data.py 20260527
```

再合并：

```bash
python scripts/merge_clean_data.py 20260527
```

如果要处理所有已准备好的日期：

```bash
python scripts/clean_raw_data.py all
python scripts/merge_clean_data.py all
```

## 常见问题

如果 clean 阶段提示原始文件不存在：

- 检查文件是否放在 `raw_data/daily/{trade_date}/`。
- 检查文件名是否和脚本约定一致，例如 `stock_quote.xlsx`、`capital_flow.xlsx`。

如果 clean 阶段提示列数不符合预期：

- 通常说明东方财富导出的表头结构变了。
- 需要打开原始 xlsx，确认列顺序和脚本里的字段映射是否仍然匹配。

如果 merge 阶段提示缺少字段：

- 说明上游 clean parquet 没有生成 merge 所需字段。
- 先重新运行对应日期的 clean 脚本，再检查具体清洗脚本的 `rename_map` 或字段列表。

如果 merge 阶段提示股票池不一致：

- 优先检查 `stock_quote`、`capital_flow`、`dde`、`staged_stat` 是否来自同一天、同一个导出范围。
- `profit_forecast` 不参与严格股票池一致性检查。
