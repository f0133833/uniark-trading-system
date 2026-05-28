# Examples — 演化阶段范本代码

> *English version below / 英文版见下*

本目录按"项目演化阶段"组织，每个子目录是一个**可独立运行的中间态**，对应一份指南文档。读者可以一边读指南，一边在对应子目录里看到完整可跑的代码。

## 子目录索引

### `01-minimal-skeleton/` — 入门骨架（4 个文件）

**对应文档**：[docs/GETTING_STARTED_ZH.md](../docs/GETTING_STARTED_ZH.md)

```
01-minimal-skeleton/
├── data.py        # 从 Binance 拉 K 线
├── indicator.py   # EMA / MACD 计算
├── plot.py        # 单一绘图函数（K 线 + 均线 + 成交量 + MACD）
└── main.py        # 串联三者
```

读完入门指南并按其方法自己实现一遍后，可以拿这里的代码对照——它是"干净代码长什么样"的参考样本。

跑起来：
```bash
cd examples/01-minimal-skeleton
pip install pandas python-binance mplfinance
python3 main.py
```

应该弹出一张 BTC 周线 K 线 + MACD 组合图。

### `02-with-divergence/` — 集成背离检测（7+ 个文件）

**对应文档**：[docs/INTEGRATION_GUIDE_ZH.md](../docs/INTEGRATION_GUIDE_ZH.md)

```
02-with-divergence/
├── data.py            # 扩展为支持周线 / 3 日线
├── indicator.py       # 同 01
├── divergence.py      # ← 381 行初版（进阶指南的讲解起点）
├── plot_helpers.py    # 背离标注辅助
├── plot_kline.py      # 多周期绘图入口
├── app.py             # Flask Web UI
└── main.py            # 桌面入口
```

读进阶指南时，第 1 章让从这里拷 `divergence.py` 到自己项目。这一版是**学习用**的初版——结构清晰、注释友好，但有四个真实问题（进阶指南第 5 章逐一演示）。生产环境请用 `code_zh/divergence.py`。

## 为什么 examples 和 code_zh 并存？

- **`code_zh/` 和 `code_en/`** —— 仓库的**生产版完整代码**，经过四轮迭代加固，包含 `provisional` / `same_terminal_l1` / `find_missed_extremes` 等所有补丁。直接用于实际项目时选这个。

- **`examples/`** —— **教学用的演化阶段标本**。如果想理解"这套代码是怎么一步步演化到今天的形态"，按 `01-` → `02-` → `code_zh/` 的顺序读。

两个目录都不接受 issue / PR / 维护，符合项目根 README 的发布政策。

---

# Examples — Reference Code by Evolution Stage

This directory is organized by **project evolution stage**. Each subdirectory is a self-contained, runnable intermediate state corresponding to a specific guide document. Read the guide alongside the code in the matching subdirectory.

## Subdirectory Index

### `01-minimal-skeleton/` — Onboarding Skeleton (4 files)

**Corresponding doc**: [docs/GETTING_STARTED.md](../docs/GETTING_STARTED.md)

```
01-minimal-skeleton/
├── data.py        # Fetch K-lines from Binance
├── indicator.py   # EMA / MACD calculation
├── plot.py        # Single rendering function (candles + MA + volume + MACD)
└── main.py        # Wires the three together
```

After reading the onboarding guide and implementing it from scratch, you can compare your version against this code — it's a reference for "what clean code looks like."

Run it:
```bash
cd examples/01-minimal-skeleton
pip install pandas python-binance mplfinance
python3 main.py
```

A BTC weekly K-line + MACD composite chart should pop up.

### `02-with-divergence/` — With Divergence Detection (7+ files)

**Corresponding doc**: [docs/INTEGRATION_GUIDE.md](../docs/INTEGRATION_GUIDE.md)

```
02-with-divergence/
├── data.py            # Extended to support weekly + 3-day
├── indicator.py       # Same as 01
├── divergence.py      # ← 381-line early version (the starting point of the integration guide)
├── plot_helpers.py    # Divergence annotation helpers
├── plot_kline.py      # Multi-timeframe rendering entry
├── app.py             # Flask Web UI
└── main.py            # Desktop entry
```

Chapter 1 of the integration guide instructs the reader to copy `divergence.py` from here into their own project. This version is the **learning version** — clear structure, friendly comments — but it has four real issues (demonstrated one by one in Chapter 5). For production use, switch to `code_zh/divergence.py`.

## Why does `examples/` coexist with `code_zh/`?

- **`code_zh/` and `code_en/`** are the repository's **production-ready, complete code**, hardened through four iterations and including all patches (`provisional`, `same_terminal_l1`, `find_missed_extremes`, etc.). Use these for actual projects.

- **`examples/`** holds **educational evolution-stage specimens**. To understand "how this codebase evolved into what it is today," read in order: `01-` → `02-` → `code_zh/`.

Neither directory accepts issues / PRs / maintenance, consistent with the publication policy in the root README.
