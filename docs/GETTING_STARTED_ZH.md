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

## 第一性原理：你不是在学习，你是在拖延

先说一句不好听的真话：

> **读理论和读代码不是"学习"，是"准备学习"。真正的学习从你写出第一行代码开始。**

如果你卡在"再看一会就开始"的状态超过 3 天，那不是知识不够，是开始的姿势不对。

### 为什么会卡住

因为你给自己定的目标是"做一个交易系统"。

这个目标对大脑来说**太大、太抽象、太可怕**，于是大脑选择了一个看起来在前进、实际上在原地踏步的活动——读资料。

让 AI "帮我读这个开源项目"是同样的陷阱。AI 给你的总结读得越多，你越觉得"我懂了"，但你的手指还没碰过键盘。

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

剩下的事，从这里开始。
