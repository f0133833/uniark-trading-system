# 从读理论到跑出第一张图：交易系统起步指南

> 写给"读了很多但没写一行"的你

---

## 这份指南是给谁的

如果你：

- 想做自己的交易系统，已经看了好几天理论文档和开源代码
- 装了 AI 编程助手（DeepSeek / Claude / GPT），让它读了一堆资料
- 但是——**还没有写出一行能跑的代码**

那这份指南就是写给你的。

如果你已经能跑出一张带 MACD 的 K 线图，请关掉这个文档,直接去主仓库读源码。

---

## 第一性原理：阅读和写代码，是不同的两个状态

一个常被忽略的事实：

> **读理论和读代码不是"学习"，是"准备学习"。真正的学习从你写出第一行代码开始。**

如果你已经在"再看一会就开始"的状态里待了 3 天以上，那很可能不是知识不够，而是开始的姿势不太对。

### 为什么会卡住

因为你给自己定的目标是"做一个交易系统"。

这个目标对大脑来说**太大、太抽象、太可怕**，于是大脑选择了一个看起来在前进、实际上在原地踏步的活动——读资料。

让 AI "帮我读这个开源项目"是同样的陷阱。AI 给你的总结读得越多，你越觉得"我懂了"，但代码却还没写出一行。

### 破局只有一个办法

**把目标缩小，缩小到不能再小。**

不是"做一个交易系统"。

是"**写四个 Python 文件，让一张 BTC 周线图在屏幕上弹出来**"。

就这一件事。先做这一件事。

---

## 终极目标：60 行代码，一张图

你要先达到的状态长这样：

```bash
$ python3 main.py
```

屏幕上弹出一张图：
- 上半部分：BTC 周线 K 线 + 均线（MA7/25/99）
- 中间：成交量
- 下半部分：MACD 三线

**就这样。仅此而已。**

不要回测、不要 web、不要多币种、不要配置文件、不要数据库。

这张图出来的那一刻，你就跨过了从"读理论的人"变成"有代码的人"的鸿沟。
**这一刻之后的所有事都是"扩展"，难度断崖式下降。**

---

## 四文件骨架

把整个 MVP 拆成四个文件，每个文件只做一件事：

```
project/
├── data.py        # 只管：获取数据
├── indicator.py   # 只管：计算指标
├── plot.py        # 只管：画图
└── main.py        # 只管：串起来
```

### `data.py` — 数据层

**唯一职责**：从某个数据源拿到 K 线数据，返回一个 pandas DataFrame。

你需要实现的函数：

```python
def get_weekly_klines(symbol, start_str, end_str=None):
    """
    从 Binance 获取周线 K 线
    返回的 DataFrame 应包含列：open, high, low, close, volume
    索引是时间（open_time）
    """
    pass
```

**未来扩展的位置**：换币种、换时间框架、加新数据源——都改这里，别的文件不动。

### `indicator.py` — 指标层

**唯一职责**：纯计算。输入价格序列，输出指标序列。

你需要实现的函数：

```python
def calc_ema(series, period):
    """计算指数移动平均"""
    pass

def calc_macd(close, fast=12, slow=26, signal=9):
    """计算 MACD，返回 macd_line, signal_line, hist 三个 series"""
    pass

def add_indicators(df):
    """给 df 加上所有需要的指标列"""
    pass
```

**这一层最容易出 bug，也最值得单元测试**。MACD 算错 5%，回测结果照样能跑，但全是错的——这种沉默 bug 最可怕。务必保持这一层纯净：不读数据、不画图，只算。

### `plot.py` — 可视化层

**唯一职责**：拿到带指标的 DataFrame，画出来。

```python
def plot_weekly(df, title, last_n=200):
    """K 线 + 均线 + 成交量 + MACD"""
    pass
```

推荐库：`mplfinance`（专为金融图表设计，比裸 matplotlib 简单很多）。

### `main.py` — 入口

**唯一职责**：把上面三个文件串起来。

```python
from data import get_weekly_klines
from indicator import add_indicators
from plot import plot_weekly

df = get_weekly_klines("BTCUSDT", start_str="1 Oct, 2022")
df = add_indicators(df)
plot_weekly(df, title="BTC Weekly", last_n=200)
```

**main.py 应该干净到一眼看完。** 任何复杂逻辑都该藏在前三个文件里。

---

## 怎么和 AI 对话（最关键的一节）

同一个 AI，不同的问法，效果天差地别。

### ❌ 错误的问法

> "帮我做一个加密货币交易系统，能识别 MACD 背离"

AI 会给你一堆架构图、概念解释、3000 行的"完整方案"。你看完依然不知道该写什么。

### ✅ 正确的问法

> "写一个 Python 函数 `get_weekly_klines(symbol, start_str)`，用 python-binance 库从 Binance 拿周线 K 线，返回包含 open/high/low/close/volume 五列的 DataFrame，索引是时间。"

AI 给你的就是 20 行可运行的代码。你复制粘贴，跑一下，要么过，要么改两行就过。

### 黄金法则

> **把"做交易系统"切成 N 个"写一个 20 行函数"的问题。**

你的工作不再是"理解 + 实现"，而是"验证 + 拼装"。

---

## 五天行动计划

每天只做下面这一件事，做完关电脑。

### Day 1：环境 + 拿到数据

- 装 Python（3.10+）
- 装库：`pip install pandas python-binance mplfinance`
- 新建 `data.py`，让 AI 帮你写 `get_weekly_klines`
- 在文件末尾加一行：`print(get_weekly_klines("BTCUSDT", "1 Oct, 2024").tail())`
- 运行 `python3 data.py`
- **看到最近几行 K 线数据被打印出来 → Day 1 完成**

到这一步，你已经赢了 90% 的同类人。

### Day 2：指标计算

- 新建 `indicator.py`
- 让 AI 写 `calc_ema` 和 `calc_macd`
- **不要无脑信任 AI 的代码**：找一根 K 线，和 TradingView 上的 MACD 数值对一下
- 实现 `add_indicators(df)`，确认 `df` 多了 `macd / signal / hist` 三列

### Day 3：画第一张图

- 新建 `plot.py`
- 让 AI 写最简单的 `plot_weekly`，先只画 K 线
- 跑通后，再让 AI 加 MACD 子图
- **此时屏幕上应该已经有一张图了**

### Day 4：串起来

- 新建 `main.py`
- 5 行代码搞定（见上面示例）
- 运行 `python3 main.py`
- **截图，发给所有催你的朋友。这是你的里程碑。**

### Day 5：欣赏 + 复盘

- 不要急着加功能
- 看着这张图，问自己：哪些走势看起来像背离？
- 在纸上手画三段结构
- 这一步是从"代码"到"交易认知"的桥梁

---

## 红线：MVP 跑通前，不要做这些事

每一条都是真实陷阱：

1. ❌ **不要写配置文件**。参数直接写在代码里。
2. ❌ **不要支持多币种**。先把 BTC 跑通。
3. ❌ **不要做命令行参数**。`argparse` 是后面的事。
4. ❌ **不要做 Web 界面**。Flask 是 MVP 之后的事。
5. ❌ **不要做数据库**。CSV 都不要存，每次重新拉。
6. ❌ **不要优化性能**。50 行代码慢不到哪去。
7. ❌ **不要写测试**（仅在 MVP 阶段）。
8. ❌ **不要重构**。代码丑没关系，能跑就行。

每一件都是无底洞，每一件都能让你卡住三天。**全部在 MVP 跑通之后再考虑。**

---

## 跑通之后呢？

恭喜你过了最难的一关。接下来：

1. **加测试**：给 `indicator.py` 写单元测试，验证 MACD 计算正确
2. **加币种**：让 `data.py` 支持任意 symbol
3. **加数据源**：Binance 失败时 fallback 到别的源
4. **三段结构识别** ← 这才是真正"你的理论"部分，AI 帮不了你太多
5. **背离检测**：基于三段结构，识别 MACD 力度衰竭
6. **回测框架**：信号 → 持仓 → 盈亏统计

每一步都是"在已有骨架上加一个文件 / 函数"，难度可控。

---

## 最后一句

> **不写代码的时间越长，写出来的可能性越低。**

合上这个文档，打开终端，输入：

```bash
mkdir my-trading-system && cd my-trading-system && touch data.py
```

剩下的事，就交给你了。

祝你一切顺利。

---

## 附录：完整范本代码

下面是这份骨架的精修版——已经清理了冗余、加了文档字符串、规范了风格，可以作为"干净代码长什么样"的参考样本。

**这是参考资料，不是起步材料。**

最理想的用法：先按前面的五天计划自己写一版，跑通之后再回头对照——你会发现自己写的版本和这里的差距其实没那么大，**这种"我也能写出这种代码"的觉察，比直接抄过来用更有价值**。

如果你卡在某个具体细节（比如 `pd.to_datetime` 该怎么传参、`mplfinance` 怎么加副图），也可以来这里查具体的某一段。

### `data.py`

```python
"""
数据层：从 Binance 获取 K 线数据

职责单一：把外部数据源的原始响应整理成下游模块能直接使用的 DataFrame。
如果未来要换数据源（Hyperliquid / OKX / 本地 CSV），只需要修改这个文件，
indicator.py 和 plot.py 完全不用动——这就是分层的价值。
"""
from binance.client import Client
import pandas as pd

client = Client()


def get_weekly_klines(symbol="BTCUSDT", start_str="1 Oct, 2022", end_str=None):
    """
    从 Binance 获取周线 K 线数据。

    参数
    ----
    symbol : str
        交易对，例如 "BTCUSDT"、"ETHUSDT"
    start_str : str
        起始日期，格式如 "1 Oct, 2022"
    end_str : str or None
        结束日期；None 表示拉到最新

    返回
    ----
    pd.DataFrame
        索引为时间（open_time），列为 open / high / low / close / volume
    """
    klines = client.get_historical_klines(
        symbol=symbol,
        interval=Client.KLINE_INTERVAL_1WEEK,
        start_str=start_str,
        end_str=end_str,
    )

    df = pd.DataFrame(klines, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_volume", "count",
        "taker_buy_base", "taker_buy_quote", "ignore",
    ])

    # 类型转换：Binance 返回的全是字符串，必须显式转换成数值才能参与计算
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
    df["open"]   = pd.to_numeric(df["open"])
    df["high"]   = pd.to_numeric(df["high"])
    df["low"]    = pd.to_numeric(df["low"])
    df["close"]  = pd.to_numeric(df["close"])
    df["volume"] = pd.to_numeric(df["volume"])

    # 只保留下游需要的 OHLCV 五列，扔掉 Binance 响应里的其他噪声字段
    df = df.set_index("open_time")
    df = df[["open", "high", "low", "close", "volume"]]

    return df
```

### `indicator.py`

```python
"""
指标层：纯计算模块

只做数学运算——输入价格序列，输出指标序列。
不读数据、不画图、不依赖任何外部状态，所以可以独立单元测试。

这是整个系统最容易出 bug 也最值得测试的地方：
MACD 算错 5%，回测照样能跑，但所有信号都会是错的。
这种"沉默 bug"非常可怕，务必保持本层纯净。
"""


def calc_ema(series, period):
    """计算指数移动平均（EMA）"""
    return series.ewm(span=period, adjust=False).mean()


def calc_macd(close, fast=12, slow=26, signal=9):
    """
    计算 MACD 三个序列。

    参数
    ----
    close : pd.Series
        收盘价序列
    fast, slow, signal : int
        MACD 三个标准周期（默认 12 / 26 / 9）

    返回
    ----
    macd_line   : 快线 = EMA(close, fast) - EMA(close, slow)
    signal_line : 慢线 = EMA(macd_line, signal)
    macd_hist   : 柱状图 = macd_line - signal_line
    """
    ema_fast = calc_ema(close, fast)
    ema_slow = calc_ema(close, slow)
    macd_line   = ema_fast - ema_slow
    signal_line = calc_ema(macd_line, signal)
    macd_hist   = macd_line - signal_line
    return macd_line, signal_line, macd_hist


def add_indicators(df):
    """
    在原 DataFrame 基础上追加 macd / signal / hist 三列。

    注意
    ----
    返回新的 DataFrame，**不修改输入**。
    这样调用方可以安全地链式调用，不用担心副作用。
    """
    df = df.copy()
    macd_dif, macd_dea, macd_hist = calc_macd(df["close"])
    df["macd"]   = macd_dif
    df["signal"] = macd_dea
    df["hist"]   = macd_hist
    return df
```

### `plot.py`

```python
"""
可视化层：K 线 + 均线 + 成交量 + MACD

输入带指标的 DataFrame，渲染成图。
不计算任何东西，也不读数据，只负责把数据呈现给人眼。
"""
import mplfinance as mpf


def get_macd_colors(hist):
    """根据 MACD 柱值的正负，返回绿/红颜色列表（用于柱状图着色）"""
    return ["g" if v >= 0 else "r" for v in hist]


def plot_weekly(df, title="BTCUSDT Weekly K-Line", last_n=200):
    """
    绘制三面板组合图：K 线主图 + 成交量 + MACD。

    参数
    ----
    df : pd.DataFrame
        必须包含 OHLCV 五列以及 macd / signal / hist 三列
    title : str
        图表标题（换币种时记得同步修改此参数）
    last_n : int
        只显示最后 N 根 K 线，避免历史太长导致挤压
    """
    df_plot = df.tail(last_n)
    macd_colors = get_macd_colors(df_plot["hist"])

    apds = [
        mpf.make_addplot(df_plot["macd"],   panel=2, color="#1f77b4"),
        mpf.make_addplot(df_plot["signal"], panel=2, color="#ff7f0e"),
        mpf.make_addplot(df_plot["hist"],   panel=2, color=macd_colors, type="bar"),
    ]

    mpf.plot(
        df_plot,
        type="candle",
        style="charles",
        title=title,
        ylabel="Price",
        volume=True,
        mav=(7, 25, 99),                  # 7/25/99 三条均线
        addplot=apds,
        panel_ratios=(4, 1, 2),           # 主图 : 成交量 : MACD = 4 : 1 : 2
        figsize=(14, 10),
    )
```

### `main.py`

```python
"""
入口：BTC 周线分析

把三个模块串起来跑：
    data.py       拉数据
    indicator.py  算指标
    plot.py       画图

整个文件保持极简——任何复杂逻辑都该藏在前三个模块里，
让读者一眼能看完整个数据流。
"""
import matplotlib

# 中文显示兼容：按 Linux / 通用 CJK / Windows / 兜底字体的顺序尝试。
# 你的系统装了哪个就用哪个，无效字体名会被自动跳过。
# 注意：此配置必须在 import plot 之前完成，否则 matplotlib 已经初始化、配置不生效。
matplotlib.rcParams["font.sans-serif"] = [
    "WenQuanYi Micro Hei", "Noto Sans CJK SC", "SimHei", "DejaVu Sans",
]
matplotlib.rcParams["axes.unicode_minus"] = False

from data import get_weekly_klines
from indicator import add_indicators
from plot import plot_weekly


if __name__ == "__main__":
    df = get_weekly_klines()
    df = add_indicators(df)
    plot_weekly(df, last_n=200)
```

### 跑起来

把四个文件保存在同一目录下，然后：

```bash
pip install pandas python-binance mplfinance
python3 main.py
```

应该弹出一张 BTC 周线 + 均线 + 成交量 + MACD 的组合图。看到这张图的那一刻，整个 MVP 就完成了——你已经从"读理论的人"变成"有代码的人"。
