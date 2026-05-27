"""
获取 Binance K 线数据
"""
from binance.client import Client
import pandas as pd

client = Client()


def _fetch_klines(symbol, interval, start_str, end_str):
    klines = client.get_historical_klines(
        symbol=symbol,
        interval=interval,
        start_str=start_str,
        end_str=end_str,
    )
    df = pd.DataFrame(klines, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_volume", "count", "taker_buy_base", "taker_buy_quote", "ignore"
    ])
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col])
    df = df.set_index("open_time")
    return df[["open", "high", "low", "close", "volume"]]


def get_weekly_klines(symbol="BTCUSDT", start_str="17 Aug, 2017", end_str=None):
    return _fetch_klines(symbol, Client.KLINE_INTERVAL_1WEEK, start_str, end_str)


def get_3day_klines(symbol="BTCUSDT", start_str="17 Aug, 2017", end_str=None):
    return _fetch_klines(symbol, Client.KLINE_INTERVAL_3DAY, start_str, end_str)
