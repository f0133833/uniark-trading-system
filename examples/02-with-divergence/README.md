# 02-with-divergence — 集成背离检测的演化阶段

这是 [docs/INTEGRATION_GUIDE_ZH.md](../../docs/INTEGRATION_GUIDE_ZH.md) 的**起点状态**。

在 [01-minimal-skeleton/](../01-minimal-skeleton/) 跑出 K 线图之后，本目录展示"如何把 `divergence.py` 接进系统、画出 ▲▼ 标注、再拆出 Web 入口"的完整中间态。

## 与 01 的区别

```
01-minimal-skeleton            02-with-divergence
─────────────────              ─────────────────
data.py            ─────►      data.py            ← 扩展为支持周线 + 3 日线
indicator.py       ─────►      indicator.py       ← 完全一致
plot.py            ─────►      plot_helpers.py    ← 拆出：背离标注逻辑
                               plot_kline.py      ← 拆出：多周期绘图入口
                               divergence.py      ← 新增：381 行核心算法
main.py            ─────►      main.py            ← 改写为 Tkinter UI
                               app.py             ← 新增：Flask Web UI
```

## 文件清单

| 文件 | 职责 |
|------|------|
| `data.py` | Binance API 拉取（周线 + 3 日线） |
| `indicator.py` | EMA / MACD 计算 |
| `divergence.py` | **三段背离判定核心算法（381 行初版）** |
| `plot_helpers.py` | 背离结构在图上的视觉表达 |
| `plot_kline.py` | 多周期统一绘图入口（CLI + Python API 双用） |
| `main.py` | Tkinter 桌面 UI（中英双语切换） |
| `app.py` | Flask Web UI（浏览器访问） |

## 跑起来

```bash
cd examples/02-with-divergence
pip install pandas python-binance mplfinance flask

# 桌面 UI
python main.py

# 或 Web UI
python app.py
# 然后打开 http://127.0.0.1:5000
```

第一次运行会拉 Binance 的全量周线数据（默认从 2017-08 开始），大概 1-2 秒。

## 关于 divergence.py 的"不成熟"

本目录里的 `divergence.py` 是 381 行的**初版**，故意保留四个真实问题——它们正是进阶指南第 5 章逐一演示的内容：

1. **同末段位置双重标注**（缺 `_dedupe_same_terminal`）
2. **末段未封口的暂定信号**（缺 `provisional` 字段）
3. **动量先于价格的极值漏检**（缺 `find_missed_extremes`）
4. **L1 屏障漏洞**（屏障规则不对称）

这版**只用于学习**。要用于实战，请切换到仓库根目录的 `code_zh/divergence.py`（500+ 行最终版，所有补丁齐全）——API 完全向后兼容，无缝替换。

详细说明见 [docs/INTEGRATION_GUIDE_ZH.md](../../docs/INTEGRATION_GUIDE_ZH.md) 第 2 章和第 5 章。

---

# 02-with-divergence — Integration Stage

This is the **starting state** for [docs/INTEGRATION_GUIDE.md](../../docs/INTEGRATION_GUIDE.md).

After getting the K-line chart running in [01-minimal-skeleton/](../01-minimal-skeleton/), this directory demonstrates the complete intermediate state for "integrating `divergence.py` into the system, drawing ▲▼ annotations, and splitting out a Web entry."

## Differences from 01

```
01-minimal-skeleton            02-with-divergence
─────────────────              ─────────────────
data.py            ─────►      data.py            ← Extended for weekly + 3-day
indicator.py       ─────►      indicator.py       ← Identical
plot.py            ─────►      plot_helpers.py    ← Split out: divergence annotation
                               plot_kline.py      ← Split out: multi-timeframe entry
                               divergence.py      ← New: 381-line core algorithm
main.py            ─────►      main.py            ← Rewritten as Tkinter UI
                               app.py             ← New: Flask Web UI
```

## Run it

```bash
cd examples/02-with-divergence
pip install pandas python-binance mplfinance flask

# Desktop UI
python main.py

# Or Web UI
python app.py
# Then open http://127.0.0.1:5000
```

## About `divergence.py`'s "incompleteness"

The `divergence.py` here is the 381-line **early version**, intentionally preserving four real issues that the integration guide's Chapter 5 demonstrates one by one. This version is **for learning only**. For production use, switch to `code_en/divergence.py` (500+ line final version) — fully backward-compatible.

See [docs/INTEGRATION_GUIDE.md](../../docs/INTEGRATION_GUIDE.md) Chapters 2 and 5.
