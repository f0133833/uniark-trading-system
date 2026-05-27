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
