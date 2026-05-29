# 从 K 线图到背离系统：进阶集成指南

> 写给"已经跑通四文件骨架、想把 divergence.py 接进自己系统"的开发者

---

## 这份指南是给谁的

如果有以下情况：

- 已经按 [GETTING_STARTED_ZH](GETTING_STARTED_ZH.md) 跑通了 BTC 周线 + MACD 的图
- 读过 [THEORY_ZH](THEORY_ZH.md)，理解了"三段结构 / 力度 / 背离"的公理化定义
- 看过 [LIBRARY_ZH](LIBRARY_ZH.md) 的 API 签名——能调，但不知道怎么接进自己的系统
- 看过 [TUTORIAL_ZH](TUTORIAL_ZH.md) 的完整样例——能跑，但不理解为什么字段这样设计、参数为什么是这些值

这份指南就是为这类读者而写的。

如果还没跑通四文件骨架，请先回 [GETTING_STARTED_ZH](GETTING_STARTED_ZH.md)。

---

## 这份指南的独特价值

仓库里已经有四份关于 divergence.py 的文档，分工是这样的：

| 文档 | 回答的问题 |
|------|-----------|
| LIBRARY_ZH | 函数怎么调、返回什么 |
| TUTORIAL_ZH | 完整调用样例、参数怎么调 |
| NOTES_FOR_DEVELOPERS_ZH | 代码化这类理论的方法论 |
| **本指南** | **怎么把库接进自己骨架，以及为什么这个库长这样** |

本指南守住自己的领地：**不重写 API、不重述方法论**，只回答两个问题：

1. **集成视角**：从四文件骨架演化到完整背离系统，每一步都是可运行的中间态
2. **演化视角**：以 `examples/02-with-divergence/divergence.py` 这个 381 行的初版作为讲解起点，完整走一遍"为什么后来加了 dedupe / provisional / 极值补检 / L1 屏障修正"

读完之后，应能做到：
- 在自己的项目里看到带 ▲▼ 标注的 K 线图
- 用自己的话讲清楚 divergence.py 在做什么
- 读最终版（`code_zh/divergence.py`）的 docstring 时，每一段都能秒懂

---

## 整体路线

```
GETTING_STARTED 终点                  本指南终点
──────────────────                  ──────────────
  data.py                             data.py
  indicator.py                        indicator.py
  plot.py            ─────────►       divergence.py    ← 新增（核心）
  main.py                             plot_helpers.py  ← 从 plot.py 拆出
                                      plot_kline.py    ← 从 plot.py 拆出
                                      main.py          ← 微调
```

四个文件变七个，新增的三个里有两个其实是从 plot.py 拆出来的——结构变化比想象中小。

---

# 第 1 章：把背离检测接进现有骨架

这一章的目标：**让 `divergence.py` 在系统里跑起来，终端能打印背离信号**。不碰可视化，先确认数据流通。

## 1.1 拷贝 divergence.py 到项目目录

从仓库的 `examples/02-with-divergence/` 目录拷一份 `divergence.py` 到项目目录（和现有 `data.py / indicator.py / plot.py / main.py` 放在一起）。

> **为什么是 `examples/02-with-divergence/` 下的初版而不是 `code_zh/` 下的最终版？**
> 简短回答：初版只有 381 行、结构清晰，是最好的学习版本；最终版加了四轮补丁，密度太高，新读者拆不开"主干"和"补丁"。完整理由见第 2 章。

## 1.2 修改 main.py 调用 divergence.py

在 `add_indicators(df)` 之后调用 `find_three_segment_divergences`：

```python
from data import get_weekly_klines
from indicator import add_indicators
from divergence import find_three_segment_divergences
from plot import plot_weekly

df = get_weekly_klines()
df = add_indicators(df)

# ↓↓↓ 新增 ↓↓↓
divs = find_three_segment_divergences(
    hist_series=df['hist'],
    low_series=df['low'],
    high_series=df['high'],
    min_bars=0,
    ratio_threshold=0.5,
    max_level=None,        # 穷尽所有层级
    block_by_opposite=True,
)
print(f"检测到 {len(divs)} 条背离")
# ↑↑↑ 新增 ↑↑↑

plot_weekly(df, last_n=200)
```

跑一下 `python3 main.py`，终端应该会打印类似：

```
检测到 4 条背离
```

如果是 0，把 `max_level` 留为 `None`、把 `start_str` 拉得更早一些（比如 `"1 Jan, 2020"`），让数据足够长。

## 1.3 打印每条背离的诊断信息

光有数量没用，要看到每条的细节。在 `print` 之后加：

```python
for d in divs:
    kind = '底背离' if d['kind'] == 'bullish' else '顶背离'
    t_start = df.index[d['s3_start']].strftime('%Y-%m-%d')
    t_end   = df.index[d['s3_end']].strftime('%Y-%m-%d')
    print(f"[{kind} Lv{d['level']}] "
          f"力度比={d['ratio']*100:.0f}% "
          f"S3 窗口: {t_start} ~ {t_end}")
```

跑出来大概是：

```
[底背离 Lv1] 力度比=34% S3 窗口: 2022-11-21 ~ 2022-12-26
[顶背离 Lv2] 力度比=41% S3 窗口: 2023-09-04 ~ 2023-10-09
...
```

## 1.4 第一个里程碑 ✓

终端里看到带时间戳的背离信号列表。

**注意此刻已经做到的事**：在不写任何算法、不画任何图的情况下，系统已经能识别 MACD 背离了。这是因为 `divergence.py` 是个完全独立的纯函数模块——它不依赖项目里的 `data.py`，不依赖 `plot.py`，只要给它三个 pandas Series 就能工作。这种"任何带 OHLC 的项目都能直接用"的解耦设计，是它最大的工程价值。

---

# 第 2 章：为什么从初版讲起

## 2.1 仓库里其实有两个版本

```
uniark-trading-system/
├── examples/02-with-divergence/divergence.py    ← 381 行，初版（学习用）
└── code_zh/divergence.py                        ← 500+ 行，最终版（生产用）
```

两版的**核心几何**完全相同：分段、三段窗口、力度比、反向屏障。差别在最终版多了四组"上线后才发现要补"的逻辑：

1. `_dedupe_same_terminal`（末段去重）
2. `provisional` 字段（暂定信号标记）
3. `find_missed_extremes`（极值补检）
4. L1 屏障规则的不对称修正

每一组补丁都对应初版的一个真实问题——这些问题不亲眼看到，光看 docstring 是不会有体感的。

## 2.2 直接读最终版会卡住

最终版的 docstring 里有这样的段落：

> "早期版本曾让 level<2 无条件幸存，理由是 '3 段 r-g-r 或 g-r-g 的开区间内只有 1 个反色段'。这个推理偷换了'反向背离'和'反向背离的触发点'两个概念..."

如果没在初版上亲手看到这个 bug 的现象，这段话读起来就是"作者在自言自语修一个我看不见的问题"。

整份最终版的 docstring 里类似的"修正说明"有六七处。它们对作者来说是宝贵的工程记忆，对新读者来说是认知噪声。

## 2.3 学习策略：先吃主干，再加补丁

```
第 3 章 → 用初版讲清核心几何
第 4 章 → 用初版画第一张带背离的图
第 5 章 → 演示初版的四个真实坑
第 6 章 → 升级到最终版，秒懂所有修正注释
```

读完之后再翻最终版 docstring，那些"自言自语"全部变成了"啊原来在说这个"。

## 2.4 一条警告

**初版可学，不可用于生产。**

第 5 章会演示初版的四个真实问题，每一个都能在实盘上造成误判。学完之后请切换到最终版，不要把初版直接用进策略。

---

# 第 3 章：读懂初版的核心几何

这一章的目标：**能用自己的话讲清楚 divergence.py 在做什么**。

如果已经熟透了 THEORY_ZH 和 LIBRARY_ZH，可以跳到第 4 章——但建议至少扫一遍 3.5 的里程碑题目，自测一下。

## 3.1 第一层：把 hist 切成段

`find_hist_segments(hist_series)` 做的事情极简——按 hist 值的正负号切段：

```
hist:  + + + + - - - + + - - - - +
       └─ S1 ─┘└ S2 ┘└S3┘└─ S4 ─┘└ S5...
       pos     neg   pos  neg     pos
```

每个段是一个 dict：`{'sign': 'pos'|'neg', 'start': int, 'end': int, 'area': float, 'bars': int}`。

**这一步是公理化骨架的基石。** NOTES_FOR_DEVELOPERS 里讨论过：缠论代码化最难的"什么是一段走势"，本项目用"hist 翻号"来兜底定义。换得到的是零歧义、可机械确定的段。

## 3.2 第二层：三段窗口扫描

在段序列上滑动一个长度为 3 的窗口，看 `S1, S2, S3` 三段：

- **符号约束**：S1 和 S3 同向，S2 反向
- **力度衰竭**：`S3.area / S1.area < ratio_threshold`（默认 0.5）
- **价格新高/新低**：底背离要求 S3 段内最低价 < S1 段内最低价；顶背离反之

三个条件都满足，就是一条 L1 背离。

`ratio_threshold=0.5` 这个魔数从哪来？是项目作者在加密货币周线/日线上的经验值。日线想更严可以调到 0.3 至 0.4 之间，4 小时以下噪声大可以调到 0.6 至 0.7 之间。它不是公理，是工程参数。

## 3.3 第三层：分层扩展（这是体系最聪明的一步）

把 `P1 = S1 + S2 + S3` 视为一个**复合段**：

- `P1.sign = S1.sign`（也等于 S3.sign）
- `P1.area = S1.area + S3.area`（S2 反向不计）
- `P1.span` 从 S1.start 到 S3.end

然后在 `P1 + S4 + S5` 上**再套用同一个三段背离判定**：

- 符号约束：P1 和 S5 同向（都等于 S1.sign），S4 反向 ✓
- 力度衰竭：`S5.area / P1.area < 0.5`
- 价格新高/新低：S5 内极值 vs **P 内所有同向段（S1 和 S3）极值的并集**

满足就是 L2 背离。同理 L3 = `P2 + S6 + S7`，P2 = P1 + S4 + S5。

**为什么这步聪明**：它把"基础三段背离"和"趋势级别背离"统一成了同一套代码。没有这层抽象，要么写两套独立的检测逻辑（维护噩梦），要么放弃趋势级别（信号太弱）。

代码上对应 `_scan_levels` 函数，用 `2k+1` 段窗口枚举所有层级。

## 3.4 第四层：反向屏障

这是最难的一步，也是体系最有思想深度的地方。

**几何定义**：第 k≥2 层背离 D 被否决，当且仅当存在一个反向背离 D' 使得 D'.s3_end 严格落在 D 的开区间 (s1_start, s3_end) 之内。

**直观解释**：`s3_end` 是背离的"触发点"——反转生效的那一根 K 线。一旦这个瞬间落在某个正在搭建的同向结构内部，结构两端就分属"趋势切换前"和"趋势切换后"两个不同机制，不应合并成同一个 P。

**举个例子**：

```
时间轴 ────────────────────────────────────────►

        ↓ D 的 s1_start                     ↓ D 的 s3_end
        ├──────────────────────────────────┤   ← D（同向 L2 背离的跨度）
                    ↑ D' 的 s3_end
                    （反向 L1 的触发点，落在 D 的开区间内）
```

D 想说"从 s1_start 到 s3_end 这段是一个连续的下跌结构"，但中间已经出现过一个反向反转信号 D'。两侧的下跌不属于同一波——D 应被否决。

代码上对应 `_filter_by_opposite_barriers`，求解顺序按 `s3_end` 升序（早触发先定生死），一遍线性扫描收敛。

## 3.5 第二个里程碑 ✓

不看代码、不看文档，能在白板上画出：

1. 一段 hist 序列被切成 7 段，标出 L1、L2、L3 三个候选窗口的位置
2. 一个 L2 背离被反向 L1 屏障否决的场景

如果画不出，回头读 3.3 和 3.4。这两节是整个体系的脊梁，不通过这里，后面所有内容都是浮的。

---

# 第 4 章：把背离画到图上

这一章的目标：**让 K 线图上出现红色 ▲（底背离）和绿色 ▼（顶背离）**。

## 4.1 为什么要拆 plot.py

第 1 章已经有了背离数据，但还是平面打印。要把它画到图上，`plot.py` 现在的 40 行就不够了——需要：

- 在 MACD 面板上根据每条 div 的位置画三角形
- 计算文字的偏移（避免压在 hist 柱上）
- 处理 ylim 自动外扩（避免标记越界）

把这些视觉逻辑塞进 `plot.py` 会让它变得不可维护。所以拆成两个文件：

```
plot_helpers.py  ← 背离标注逻辑（怎么画 ▲▼ 和文字）
plot_kline.py    ← 主绘图入口（K 线 + MACD + 调用 helpers）
```

`plot.py` 现在退役。

## 4.2 plot_helpers.py 最小骨架

仓库里的 `plot_helpers.py` 有 150+ 行——把箭头、文字、ylim 外扩、双三角等全部处理了。学习阶段先实现最简版本：

```python
"""
plot_helpers.py（学习版）
绘图辅助：把 divergences 标注到 MACD 面板上。
"""

COLOR_BULLISH = '#ff3344'  # 红：底背离
COLOR_BEARISH = '#22aa44'  # 绿：顶背离

def annotate_divergences(macd_ax, df, divergences):
    """在 MACD 面板的 hist 上画三角形 + 力度比文字。"""
    if not divergences:
        return

    y_min, y_max = macd_ax.get_ylim()
    y_range = y_max - y_min

    for d in divergences:
        s3_start, s3_end = d['s3_start'], d['s3_end']
        x_mid = (s3_start + s3_end) / 2

        # hist 段内极值（决定箭头锚点）
        hist_segment = df['hist'].iloc[s3_start:s3_end + 1]
        if d['kind'] == 'bullish':
            y_anchor = hist_segment.min()
            y_marker = y_anchor - y_range * 0.05  # 红柱下方
            marker = '^'
            color = COLOR_BULLISH
        else:
            y_anchor = hist_segment.max()
            y_marker = y_anchor + y_range * 0.05  # 绿柱上方
            marker = 'v'
            color = COLOR_BEARISH

        macd_ax.scatter([x_mid], [y_marker], marker=marker,
                        s=80, color=color, edgecolors='white',
                        linewidths=0.6, zorder=5)

        # 力度比文字（放在 0 轴对侧）
        text_y = y_range * 0.1 if d['kind'] == 'bearish' else -y_range * 0.1
        label = f"L{d['level']} {d['ratio']*100:.0f}%" if d['level'] >= 2 \
                else f"{d['ratio']*100:.0f}%"
        macd_ax.text(x_mid, text_y, label,
                     fontsize=7, color=color, ha='center', va='center')
```

这 30 行实现了仓库版的核心视觉。学完第 5、6 章后可以再去看仓库版怎么处理双三角、暂定信号 `?` 后缀、ylim 外扩等细节。

## 4.3 plot_kline.py 改造原 plot.py

原 `plot.py` 直接调 `mpf.plot`，没办法在画完之后再加东西。需要改用 `returnfig=True` 拿到 figure 和 axes：

```python
"""
plot_kline.py
K 线 + MACD + 背离标注的统一入口。
"""
import mplfinance as mpf
from plot_helpers import annotate_divergences


def get_macd_colors(hist):
    return ['g' if v >= 0 else 'r' for v in hist]


def plot_with_divergences(df, divergences,
                          title='BTCUSDT Weekly',
                          last_n=200):
    df_plot = df.tail(last_n)
    # 子集化后，divergence 的下标需要平移
    offset = len(df) - len(df_plot)
    divs_plot = [
        {**d,
         's1_start': d['s1_start'] - offset,
         's1_end':   d['s1_end']   - offset,
         's3_start': d['s3_start'] - offset,
         's3_end':   d['s3_end']   - offset}
        for d in divergences
        if d['s3_start'] >= offset   # 过滤掉窗口外的
    ]

    macd_colors = get_macd_colors(df_plot['hist'])
    apds = [
        mpf.make_addplot(df_plot['macd'],   panel=2, color='#1f77b4'),
        mpf.make_addplot(df_plot['signal'], panel=2, color='#ff7f0e'),
        mpf.make_addplot(df_plot['hist'],   panel=2,
                         type='bar', color=macd_colors),
    ]

    fig, axes = mpf.plot(
        df_plot, type='candle', style='charles',
        title=title, ylabel='Price', volume=True,
        mav=(7, 25, 99), addplot=apds,
        panel_ratios=(4, 1, 2), figsize=(14, 10),
        returnfig=True,
    )

    # 拿到 MACD 面板（panel=2 对应 axes 索引按 mplfinance 约定推算）
    macd_ax = axes[-2]   # 倒数第二个是 MACD 主轴（最后一个是它的孪生）
    annotate_divergences(macd_ax, df_plot, divs_plot)

    import matplotlib.pyplot as plt
    plt.show()
```

**注意 `offset` 平移**：`tail(last_n)` 之后，新 df 的下标从 0 开始重新计数，但 `divergences` 里的下标还是基于原始 df 的。必须平移。

## 4.4 改造 main.py

```python
import matplotlib
matplotlib.rcParams['font.sans-serif'] = [
    'WenQuanYi Micro Hei', 'Noto Sans CJK SC', 'SimHei', 'DejaVu Sans',
]
matplotlib.rcParams['axes.unicode_minus'] = False

from data import get_weekly_klines
from indicator import add_indicators
from divergence import find_three_segment_divergences
from plot_kline import plot_with_divergences


if __name__ == "__main__":
    df = get_weekly_klines()
    df = add_indicators(df)
    divs = find_three_segment_divergences(
        df['hist'], df['low'], df['high'],
        max_level=None, block_by_opposite=True,
    )
    plot_with_divergences(df, divs, last_n=200)
```

## 4.5 第三个里程碑 ✓

跑 `python3 main.py`，图上出现红色 ▲ 和绿色 ▼ 标记，下方有 `L2 41%` 这样的文字。

恭喜——系统已经能可视化背离信号了。这就是仓库主截图里那个效果的简化版。

---

# 第 5 章：初版的四个真实坑

**这一章是本指南的核心。** 每一节都是一个可复现的现象 → 问题分析 → 最终版的补丁。

读完这一章会发现：最终版 docstring 里那些晦涩的"修正注释"，其实每一条都对应一个亲眼见过的现象。

## 5.1 坑 1：同末段位置的双重标注

### 现象演示

让 `max_level=None`，跑一遍 BTC 周线。仔细看图——某些位置上**同时叠着两个百分比**：一个 `L2 38%`、一个 `42%`，挤在一起。

为什么？因为同一段 S_last 可能同时满足多个层级的背离条件：

- L2 触发：S5 vs P(S1+S3) 力度比 38%
- L1 触发：S5 vs S3 力度比 42%（用最近的 S3 作 S1 重新看）

初版的 `find_three_segment_divergences` 把两条都返回，绘图层就在同一根 K 线上叠了两个标签。

### 为什么是问题

视觉上拥挤难读不说，**两条信号代表的实际上是同一个背离**——只是从不同尺度看而已。回测时也会被重复计数。

### 最终版的补丁：`_dedupe_same_terminal`

最终版加了一个去重函数：同 `kind` 同 `(s3_start, s3_end)` 位置，只保留 `level` 最大的那条。规则：**趋势背离优先于三段背离**。

如果被合并掉的低层级里**也**独立成立（说明这个位置的力度衰竭在多个尺度同时生效），保留下来的那条记录会带上 `same_terminal_l1=True` 标记。UI 画双三角，语义是"信号更强"。

### 要不要补

如果只在 `max_level=1` 下使用，**这个问题不会出现**，不用补。

如果打开 `max_level>=2`，**必须补**。最简实现：

```python
def dedupe_same_terminal(divs):
    """同 kind 同末段位置，只保留 level 最大的那条。"""
    by_key = {}
    for d in divs:
        key = (d['kind'], d['s3_start'], d['s3_end'])
        if key not in by_key or d['level'] > by_key[key]['level']:
            by_key[key] = d
    return list(by_key.values())
```

调用方在 `find_three_segment_divergences` 之后加一行：

```python
divs = find_three_segment_divergences(...)
divs = dedupe_same_terminal(divs)   # ← 新增
```

或者直接用最终版的 `_dedupe_same_terminal`——它额外维护了 `same_terminal_l1` 字段，UI 体验更好。

## 5.2 坑 2：末段未封口的暂定信号

### 现象演示

拉**最新**的数据跑（`end_str=None`，数据延伸到当前时刻）。记下打印出来的最后一条背离的 ratio。

第二天、或者过几个小时再跑一遍——会发现：

```
昨天：[底背离 Lv1] 力度比=34% S3 窗口: 2026-05-15 ~ 2026-05-22
今天：[底背离 Lv1] 力度比=37% S3 窗口: 2026-05-15 ~ 2026-05-29
```

S3 的窗口延长了，ratio 也变了。

### 为什么是问题

`hist` 的最末段还没"封口"——只要 hist 还没翻号回去，S_last 就在持续延伸。这意味着：

- ratio 是个**快照**，下一根 K 线进来就会变
- 如果 ratio 还没到 0.5 但主观"觉得它快了"，这是主观判断，不是公理
- **回测里如果不小心把这种暂定信号当成已确认信号用，会引入 lookahead bias**——"在 t 时刻看到的"和"t 时刻真正能下决策的"是两件事

### 最终版的补丁：`provisional` 字段

最终版返回的每条记录多了一个 `provisional` 字段：

- `provisional=False`：S_last 已封口（后面已经出现反向 hist），信号确定
- `provisional=True`：S_last 延伸到数据末端，信号暂定

UI 上对暂定信号用蓝色 + `?` 后缀显示（参考 README 里的"可视化标记"表）。回测时一行代码过滤掉：

```python
confirmed = [d for d in divs if not d['provisional']]
```

### 要不要补

**如果做实时盯盘或回测，必须补**。如果只是看历史图（end_str 是过去某个日期），不需要——历史数据里最末段总是封口的。

最简补法：

```python
def mark_provisional(divs, hist_series):
    """末段延伸到序列末端的，标记为 provisional。"""
    n = len(hist_series)
    for d in divs:
        d['provisional'] = (d['s3_end'] == n - 1)
    return divs
```

这只是粗糙近似——最终版用了"末段的 hist 是否已开始反向"作为更严格的判定，建议直接用最终版的实现。

## 5.3 坑 3：动量先于价格的极值漏检

### 现象演示

找一段熟悉的真实行情，价格的真实顶（或底）落在 hist 已经翻号之后的位置。比如：

```
价格：  ↗↗↗↗↗ peak ↘     ← 真实顶在这里
hist：  + + + ─ ─ ─ ─     ← hist 已经翻号到负值
                ↑
                这一根的 hist=负，按 find_hist_segments 归入"负段"
                但价格的真实高点在它上面那根
```

调用 `find_three_segment_divergences`，**这个真实顶会被漏掉**——它不在任何 `pos` 段内，标准的三段顶背离扫描看不见它。

### 为什么是问题

这是 MACD 指标的固有性质——它是动量指标，**动量拐点先于价格拐点**。NOTES_FOR_DEVELOPERS 的"七坑"第 5 条详细讨论了这一点。

后果：会漏掉一部分真实的极值背离信号。漏多少取决于所研究的市场——加密货币周线上漏检率较低，4 小时线及以下漏检率显著。

### 最终版的补丁：`find_missed_extremes`

最终版加了一个独立的补检函数 `find_missed_extremes`，专门处理这种漏检。它的工作方式：

- 扫描相邻的两段反向 hist（绿段紧跟红段，或红段紧跟绿段）
- 顶极值判据：红段 R 内最高价 > 前面绿段 G 内最高价 → R 段里那根 K 线是漏检的顶
- 底极值判据：绿段 G 内最低价 < 前面红段 R 内最低价 → G 段里那根 K 线是漏检的底
- 短反向段过滤：相邻两段任一长度小于 `MISSED_EXTREME_MIN_BARS` 跳过（默认 10，避免 hist 在零轴附近频繁过零造成的噪声刷屏）

`find_missed_extremes` 返回的记录字段结构**与 `find_three_segment_divergences` 完全不同**——只有 `kind`、`peak_idx`、`prev_end`、`curr_start`、`curr_end` 五个字段，没有 `level`、`ratio`、`s1_area` 等。这是刻意为之：

- 不合并进同一个列表 → 标准三段背离的去重 / 屏障 / provisional 逻辑一行不改
- 不参与下游钻取 → 极值只是定位标注，不需要"段范围"语义
- 视觉上用**空心 △▽**（区别于标准背离的实心 ▲▼），读者一眼能区分两类信号

整个集成只多加 5 行代码：`plot_kline.py` 在调完 `annotate_divergences` 之后多调一次 `annotate_extremes(axes[0], df, extremes)`，把空心三角画在主价格面板上（不是 MACD 面板）。

### 关于噪声阈值

`MISSED_EXTREME_MIN_BARS=10` 不是公理，是工程参数。最初取 4，但在持续单边走势中（比如 BTC 周线 2018 全年下跌）hist 在零轴附近反复翻号，会刷出大量"虚假的极值漏检"。实测 10 根在周/日/小时多数主流周期上噪声显著减少——如果你的市场更平缓可以下调，更躁动可以上调。

## 5.4 坑 4：L1 屏障漏洞（逻辑 bug）

### 现象演示

这个坑最隐蔽，需要构造特定数据才能稳定复现。简化描述：

```
反向 L2：  ────D'────D'.s3_end────
                              ↓ 触发点落在下面 L1 的开区间内
正向 L1：  ──D.s1_start────────────────D.s3_end──
```

初版第 287-303 行的 `_filter_by_opposite_barriers` 写着：

```python
if d['level'] < 2:
    survivors.append(d)
    continue
```

意思是：L1 候选**无条件幸存**，不接受屏障判定。

但上面那个例子里：反向 L2 的触发点（D'.s3_end）确实严格落在正向 L1 的开区间 (D.s1_start, D.s3_end) 内——按公理这条 L1 应该被屏蔽（它的 S1 和 S3 分属趋势切换前后两个不同机制）。**初版会保留这条本该被屏蔽的 L1。**

### 为什么是问题

初版的逻辑推理偷换了概念。原话："3 段 r-g-r 或 g-r-g 的开区间内只有 1 个反色段，凑不出反向背离的触发点。"

这个推理只成立于"反向背离本身完全装进 L1 的开区间内"——但屏障规则要求的不是"反向背离完全装进来"，而是"反向背离的**触发点**落在开区间内"。L1 的那一个反向段（S2），完全可以充当某个**更高层级反向背离**（L≥2）的 S_last，而这个反向 L≥2 的触发点正是 S2 的末端，严格落在 L1 的开区间内。

实战影响：在趋势切换处会出现"L1 信号没被屏蔽，继续显示"，给读者错误的"这里还是同一波趋势"的暗示。

### 最终版的补丁：L1 的不对称处理

最终版把屏障规则拆成两个方向：

- **L1 作为被屏蔽方**：参与屏障判定。反向 L≥2 的触发点落在 L1 开区间内时，L1 被屏蔽。
- **L1 作为屏障方**：不构成屏障。两个相邻的同级 L1（如 S1+S2+S3 底背离紧接 S2+S3+S4 顶背离）是市场转折的典型双重信号，几何上必然互相"跨过"对方的开区间，若让 L1 互屏会两败俱伤。

这个不对称设计**不是对公理的修正**，而是公理之上加的一层应用筛选——明确认定"L1 反向触发的强度不足以否决一个跨过它的同向结构"。

代码上对应最终版的 `max_level_at` 预计算（按"同末段位置达到的最高 level"判定屏障资格）。

### 要不要补

**实战中遇到这个 bug 的概率不高，但一旦遇到就是误信号。** 建议直接切到最终版。

如果坚持用初版自行修，最小改法：

```python
def _filter_by_opposite_barriers(divs):
    # 先算每个 (kind, s3_start, s3_end) 位置达到的最高 level
    max_level_at = {}
    for d in divs:
        key = (d['kind'], d['s3_start'], d['s3_end'])
        max_level_at[key] = max(max_level_at.get(key, 0), d['level'])

    sorted_divs = sorted(divs, key=lambda d: (d['s3_end'], d['level']))
    survivors = []
    for d in sorted_divs:
        # 不再无条件保留 L1——所有 level 都参与屏障判定
        blocked = False
        for s in survivors:
            if s['kind'] == d['kind']:
                continue
            s_key = (s['kind'], s['s3_start'], s['s3_end'])
            # 屏障方在该位置的最高 level 必须 > 1
            if max_level_at.get(s_key, 0) <= 1:
                continue
            if d['s1_start'] < s['s3_end'] < d['s3_end']:
                blocked = True
                break
        if not blocked:
            survivors.append(d)
    return survivors
```

这一段是整个项目里最不平凡的算法逻辑。看懂这 18 行为什么这么写，就真正理解了反向屏障规则——而不只是会调 API。

## 5.5 第五个里程碑 ✓

四个坑读完，请合上文档自测：

1. 不看代码，能用自己的话讲清楚 `_dedupe_same_terminal` 在做什么、为什么需要它
2. 能解释什么是 lookahead bias，以及为什么 `provisional` 字段能避免
3. 能解释"动量先于价格"在 MACD 上的具体表现
4. 能在白板上画一个让 L1 应被屏蔽的反向 L2 场景

四题都能过，进入第 6 章。

---

# 第 6 章：升级到最终版

## 6.1 切换文件

从仓库 `code_zh/` 目录拷贝 `divergence.py` 替换项目里之前从 `examples/02-with-divergence/` 拷过来的同名文件。

API 完全向后兼容——`find_three_segment_divergences(...)` 的调用方式不需要任何改动。新增的字段是**附加**的，老代码不读这些字段就跟以前一样工作。

## 6.2 现在能读懂的东西

打开最终版的 docstring，会发现：

- "L1 同样接受屏障判定（被屏蔽方）" 这一段——5.4 中见过现象，秒懂
- "触发反向背离 = 下一个同向结构的起点" 这个公理表述——3.4 已在白板上画过，秒懂
- "屏障力度按'同末段位置的最高 level'算" 这一段——5.4 的最简改法里就用了这个，秒懂
- "same_terminal_l1 标记" 字段说明——5.1 中见过双重标注现象，秒懂
- "极值补检独立路径、空心 △▽ 视觉区分" 这一段——5.3 中见过现象，秒懂

整个最终版 docstring 不再是"作者自言自语"，而是**一份能完全跟上的工程日志**。

## 6.3 利用新字段

最常用的两个新字段：

```python
# 回测时过滤暂定信号
confirmed = [d for d in divs if not d.get('provisional', False)]

# UI 上为"多尺度共振"画双三角
for d in divs:
    if d.get('same_terminal_l1'):
        draw_double_triangle(...)
    else:
        draw_single_triangle(...)
```

## 6.4 第六个里程碑 ✓

完整解释最终版 docstring 的每一段。这是真正"读懂这个库"的标志——比"会调 API"高一个台阶。

---

# 第 7 章：登堂入室之后

## 7.1 这个项目还能加什么

按工程难度排：

| 难度 | 任务 | 涉及文件 |
|------|------|----------|
| ★ | 多币种支持（symbol 参数化） | `data.py` |
| ★ | 多数据源 fallback（Binance → Hyperliquid → ...） | `data.py` |
| ★★ | 多周期支持（daily / 4h / 1h） | `data.py` + `plot_kline.py` |
| ★★ | 单元测试（`indicator.py` + `divergence.py`） | 新增 `tests/` |
| ★★★ | 批量扫描器（在 N 个币种 × M 个周期上找信号） | 新增 `scanner.py` |
| ★★★ | 多周期钻取（点击高周期段进入低周期） | 引入 `navigation.py` |
| ★★★★ | Web UI 或桌面 UI | 引入 `app.py` 或 `main.py`（Tk） |
| ★★★★★ | 回测框架 | 新增整个模块 |

## 7.2 关于多周期钻取

仓库的 `navigation.py` 实现了"点击周线某一段 → 进入 3-Day 视图 → 再点 → 进入 daily → ... → 15m"的金字塔钻取。这是 README 里截图展示的核心交互。

核心思路：根据当前图的 K 线根数动态计算段数 `段数 = floor(N_next/BARS_PER_SEGMENT_TARGET) + 1`。具体实现见 `navigation.py` 里的 `compute_segment_count` 和 `compute_subranges`。

**这一块不展开**——它已经偏离"背离系统"主题，是 UI/UX 设计问题，不是算法问题。如果项目不需要这个交互，跳过即可。

## 7.3 关于 UI

- **桌面 UI**（`main.py` Tk 版）：跨平台、单文件可分发、适合本地工具
- **Web UI**（`app.py` Flask 版）：浏览器访问、移动端友好、适合多人共享

两者**共享同一份算法和数据层**——这是分层设计的红利。如果未来想加第三种 UI（比如 Streamlit），照样不用动 `divergence.py` 一行代码。

**这一块也不展开**——选哪个完全看部署场景，仓库里两份都有完整实现可参考。

## 7.4 真正难的事，不在代码里

至此已拥有一套能在 K 线图上标出背离信号的系统。但这不等于"能赚钱的系统"。

README 的免责声明和 NOTES_FOR_DEVELOPERS 第七节都说过：**代码化的难，只有一半在技术；另一半在统计验证和实战决策**。

具体来说，真正决定盈亏的问题是：

- 什么周期的背离信号值得交易？
- 仓位怎么设？背离失败怎么止损？
- 滑点 + 手续费 + 税费扣完，还剩多少？
- 对照"买入持有"这个被动基准，超额收益显著吗？
- 哪些品种适合这个框架？哪些不适合？

这些都需要**历史数据上的统计回测**才能回答，不是公理化能直接给出的。本项目的可视化工具可以**辅助**做这些观察，但**不替代**这些观察。

---

## 最后一句

至此已经走完了从"读理论的人"→"有 K 线图的人"→"有完整背离系统的人"→"真正读懂这个库的人"的全部四个阶段。

这份指南到此结束。继续前进的方向有两个：

- **向工程深处**：测试、扫描器、回测框架、自己的 UI
- **向决策深处**：用这套工具在历史数据上反复验证、形成自己的交易认知

两条路都不容易，但已经过了最难的"动手 + 理解"那道关。

剩下的事，就靠自己摸索了。

祝一切顺利。
