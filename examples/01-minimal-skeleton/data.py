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
