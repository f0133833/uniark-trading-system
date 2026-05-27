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
