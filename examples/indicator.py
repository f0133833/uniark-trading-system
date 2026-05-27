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
