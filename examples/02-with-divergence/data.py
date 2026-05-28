"""
数据层：从 Binance 获取多周期 K 线数据

职责：把外部数据源的原始响应整理成下游模块能直接使用的 DataFrame。

与 01-minimal-skeleton 的区别
----------------------------
01 只需要周线，所以 `get_weekly_klines` 是顶层函数。
02 引入了"周线 + 3 日线"双周期，所以把"调用 Binance API + 转 DataFrame"
这一段共用逻辑抽到 `_fetch_klines`，每个周期是它的一个薄包装。

未来扩展：要加日线，只要再加一个 `get_daily_klines` 包装，三行代码搞定。
"""
from binance.client import Client
import pandas as pd

client = Client()


def _fetch_klines(symbol, interval, start_str, end_str):
    """
    底层 API 调用。所有周期共用此函数。

    参数
    ----
    symbol     : str   交易对，例如 "BTCUSDT"
    interval   : str   Binance 的 KLINE_INTERVAL_* 常量
    start_str  : str   起始日期，格式如 "17 Aug, 2017"
    end_str    : str or None   结束日期；None 表示拉到最新

    返回
    ----
    pd.DataFrame
        索引为时间（open_time），列为 open / high / low / close / volume
    """
    klines = client.get_historical_klines(
        symbol=symbol,
        interval=interval,
        start_str=start_str,
        end_str=end_str,
    )
    df = pd.DataFrame(klines, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_volume", "count",
        "taker_buy_base", "taker_buy_quote", "ignore",
    ])

    # 类型转换：Binance 返回的全是字符串，必须显式转换才能参与计算
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col])

    # 只保留下游需要的 OHLCV 五列，丢弃其他字段
    df = df.set_index("open_time")
    return df[["open", "high", "low", "close", "volume"]]


def get_weekly_klines(symbol="BTCUSDT", start_str="17 Aug, 2017", end_str=None):
    """获取周线 K 线。参数语义同 _fetch_klines。"""
    return _fetch_klines(symbol, Client.KLINE_INTERVAL_1WEEK, start_str, end_str)


def get_3day_klines(symbol="BTCUSDT", start_str="17 Aug, 2017", end_str=None):
    """获取 3 日线 K 线。参数语义同 _fetch_klines。"""
    return _fetch_klines(symbol, Client.KLINE_INTERVAL_3DAY, start_str, end_str)
