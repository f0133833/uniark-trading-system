"""
BTC K线绘图 - 多周期统一入口
==============================
合并自 plot_single.py（周线）和 plot_3day.py（3日线）。
所有"周期相关"的差异都收进 INTERVAL_CONFIG，绘图核心保持单一实现。

新增周期的三步：
  1. 在 data.py 加 get_<interval>_klines
  2. 在本文件 INTERVAL_CONFIG 加一行
  3. （可选）在 main.py 的 UI 加按钮 / app.py 的前端选项加按钮

两种使用姿势：
  CLI（被 main.py 通过 subprocess 调用）：
      python plot_kline.py <interval> <start_str> <end_str>
      例: python plot_kline.py weekly "17 Aug, 2017" "30 Oct, 2025"
           python plot_kline.py 3day   "17 Aug, 2017"

  Python API（被 app.py 直接 import）：
      from plot_kline import render_chart
      fig, df, divs = render_chart('weekly', start_str, end_str)
      # 调用方自己决定 fig 是 savefig 到磁盘还是写到 BytesIO
"""
import sys
import os
import matplotlib
matplotlib.use('Agg')
matplotlib.rcParams['font.sans-serif'] = ['Noto Sans CJK JP', 'WenQuanYi Zen Hei', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False

from data import get_weekly_klines, get_3day_klines
from indicator import add_indicators
from divergence import find_three_segment_divergences
from plot_helpers import annotate_divergences, print_divergences
import mplfinance as mpf
import matplotlib.pyplot as plt
import pandas as pd


# ── 周期配置：新增周期只在这里加一行 ──────────────────────────────────
INTERVAL_CONFIG = {
    'weekly': {
        'fetch_fn':    get_weekly_klines,
        'label':       'Weekly',      # 图表标题用
        'file_prefix': 'btc_weekly',  # 输出文件名前缀
        'cn_name':     '周线',         # 中文日志用
    },
    '3day': {
        'fetch_fn':    get_3day_klines,
        'label':       '3-Day',
        'file_prefix': 'btc_3day',
        'cn_name':     '3日线',
    },
}

# ── 绘图通用常量 ──────────────────────────────────────────────────────
MA_PERIODS = (7, 25, 99)
MA_COLORS  = ('#ff9900', '#cc44ff', '#00aaff')

# ── 背离检测参数（所有周期共用）─────────────────────────────────────
MIN_BARS  = 0      # 0 = 不做噪声合并
MAX_LEVEL = None   # None = 穷尽所有可能的分层扩展

# ── 全量数据起点（所有周期共用）─────────────────────────────────────
DATA_START = "17 Aug, 2017"


def calc_ma(series, period):
    return series.rolling(window=period).mean()


def add_ma(df):
    for p in MA_PERIODS:
        df[f'ma{p}'] = calc_ma(df['close'], p)
    return df


def get_macd_colors(hist):
    return ['g' if v >= 0 else 'r' for v in hist]


def render_chart(interval, start_str=None, end_str=None):
    """
    渲染指定周期、指定时间段的 K 线 + MACD + 背离标注图。

    始终从 DATA_START 加载全量数据 → 计算指标和均线 → 然后切片，
    保证 MA99 等长周期均线没有头部缺失。

    Parameters
    ----------
    interval  : str       INTERVAL_CONFIG 的 key（如 'weekly' / '3day'）
    start_str : str|None  起点（默认 DATA_START）
    end_str   : str|None  终点（默认 None，即最新）

    Returns
    -------
    (fig, df, divergences)
        fig         : matplotlib Figure，调用方负责 savefig / plt.close
        df          : 已切片、已加指标和均线的 DataFrame
        divergences : 该时间段内检测到的所有背离（list[dict]）
    """
    if interval not in INTERVAL_CONFIG:
        raise ValueError(
            f"Unknown interval: {interval!r}. "
            f"Valid: {list(INTERVAL_CONFIG.keys())}"
        )
    cfg = INTERVAL_CONFIG[interval]

    df = cfg['fetch_fn'](start_str=DATA_START, end_str=None)
    df = add_indicators(df)
    df = add_ma(df)
    if start_str:
        df = df[df.index >= pd.Timestamp(start_str)]
    if end_str:
        df = df[df.index <= pd.Timestamp(end_str)]

    start_date = df.index[0].strftime('%Y-%m-%d')
    end_date   = df.index[-1].strftime('%Y-%m-%d')
    title = f"BTCUSDT {cfg['label']} K-Line\n{start_date} ~ {end_date}"

    macd_colors = get_macd_colors(df['hist'])
    apds = [
        mpf.make_addplot(df[f'ma{MA_PERIODS[0]}'], panel=0, color=MA_COLORS[0], width=1.2, label=f'MA{MA_PERIODS[0]}'),
        mpf.make_addplot(df[f'ma{MA_PERIODS[1]}'], panel=0, color=MA_COLORS[1], width=1.2, label=f'MA{MA_PERIODS[1]}'),
        mpf.make_addplot(df[f'ma{MA_PERIODS[2]}'], panel=0, color=MA_COLORS[2], width=1.5, label=f'MA{MA_PERIODS[2]}'),
        mpf.make_addplot(df['macd'],   panel=2, color='#1f77b4', label='MACD'),
        mpf.make_addplot(df['signal'], panel=2, color='#ff7f0e', label='Signal'),
        mpf.make_addplot(df['hist'],   panel=2, type='bar', color=macd_colors),
    ]

    fig, axes = mpf.plot(
        df,
        type='candle',
        style='charles',
        title=title,
        ylabel='Price',
        volume=True,
        addplot=apds,
        panel_ratios=(4, 1, 2),
        figsize=(14, 10),
        returnfig=True,
    )
    fig.subplots_adjust(top=0.93)

    macd_ax = axes[4] if len(axes) >= 5 else None

    divergences = find_three_segment_divergences(
        df['hist'], df['low'], df['high'],
        min_bars=MIN_BARS,
        max_level=MAX_LEVEL,
    )
    if macd_ax is not None:
        annotate_divergences(macd_ax, df, divergences)

    return fig, df, divergences


# ── CLI 入口（main.py 通过 subprocess 调用）────────────────────────
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python plot_kline.py <interval> [start_str] [end_str]")
        print(f"  interval: {list(INTERVAL_CONFIG.keys())}")
        sys.exit(1)

    interval  = sys.argv[1]
    start_str = sys.argv[2] if len(sys.argv) > 2 else DATA_START
    end_str   = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] else None

    fig, df, divs = render_chart(interval, start_str, end_str)

    cfg = INTERVAL_CONFIG[interval]
    start_date = df.index[0].strftime('%Y-%m-%d')
    end_date   = df.index[-1].strftime('%Y-%m-%d')

    print(f"时间段内共 {len(df)} 根 {cfg['cn_name']}，全部绘图")
    print(f"绘图范围: {start_date} ~ {end_date}")

    out_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        f"{cfg['file_prefix']}_{start_date}_{end_date}.png"
    )
    fig.savefig(out_path, bbox_inches='tight', pad_inches=0.8)
    plt.close(fig)

    print_divergences(df, divs)
    print(f"图片已保存: {out_path}")
