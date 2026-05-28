"""
BTC K线分析 - 时间段选择 UI（中英文切换版）

架构说明
--------
本文件是桌面入口，做两件事：
  1. 用 Tkinter 渲染一个"选周期 + 选时段 + 生成"的窗口
  2. 用户点"生成图表"时，通过 subprocess 调用 plot_kline.py

为什么用 subprocess，而不是直接 `from plot_kline import render_chart`？
  matplotlib 和 Tkinter 都是 GUI 框架，在同一进程里共用主线程时容易冲突：
  - matplotlib 的字体配置 / 后端会被 Tk 干扰
  - 每生成一张图，matplotlib 的 figure 缓存会累积，长时间使用内存涨
  - 报错栈混在一起难以调试

  用 subprocess 把绘图扔到子进程，每次干净启动、干净退出。代价是启动
  慢 0.3 秒，但换来稳定性和可调试性，对桌面工具来说很划算。

  Web 版（app.py）不需要 subprocess——Flask 是后端框架，没有 GUI 主线程
  竞争问题，直接 `import render_chart` 就行。

文件分工
--------
  main.py        本文件：Tk 窗口 + 用户输入
  plot_kline.py  绘图核心：被本文件 subprocess 调用、被 app.py 直接 import
  app.py        Web 版入口：另一种 UI 形态，共用 plot_kline.py
"""
import tkinter as tk
from tkinter import ttk
import subprocess
import sys
import os

_DIR = os.path.dirname(os.path.abspath(__file__))

# ── 配色 ──────────────────────────────────────────────────
BG        = "#1e1e2e"
BG_CARD   = "#2a2a3e"
ACCENT    = "#7c6af7"
ACCENT2   = "#f7a26a"
FG        = "#e0e0f0"
FG_DIM    = "#8888aa"
SEL_BG    = "#3a3a5e"
BTN_BG    = "#7c6af7"
BTN_FG    = "#ffffff"
BTN_HOVER = "#9b8dff"
OK_COLOR  = "#50fa7b"
ERR_COLOR = "#ff5555"
LANG_BG   = "#2a2a3e"
LANG_SEL  = "#3a3a5e"

FONT_TITLE  = ("Noto Sans", 13, "bold")
FONT_OPTION = ("Noto Sans", 12)
FONT_BTN    = ("Noto Sans", 12, "bold")
FONT_STATUS = ("Noto Sans", 10)
FONT_LANG   = ("Noto Sans", 10, "bold")

RANGES = [
    ("2017-08  ~  2020-05", "17 Aug, 2017", "30 May, 2020"),
    ("2020-03  ~  2022-11", "17 Mar, 2020", "30 Nov, 2022"),
    ("2022-10  ~  2025-10", "17 Oct, 2022", "30 Oct, 2025"),
    ("2025-04  ~  2027-11", "17 Apr, 2025", "30 Nov, 2027"),
]

# ── 多语言文本 ────────────────────────────────────────────
I18N = {
    'en': {
        'title':       "BTC K-Line Generator",
        'interval':    "▸  Interval",
        'weekly':      "Weekly",
        '3day':        "3-Day",
        'timerange':   "▸  Time Range",
        'generate':    "Generate Chart",
        'generating':  "Generating",
        'done':        "Done ✓",
        'error':       "Error ✗",
    },
    'zh': {
        'title':       "BTC K线生成器",
        'interval':    "▸  周期",
        'weekly':      "周线",
        '3day':        "3日线",
        'timerange':   "▸  时间段",
        'generate':    "生成图表",
        'generating':  "正在生成",
        'done':        "完成 ✓",
        'error':       "错误 ✗",
    }
}

# ── 状态 ──────────────────────────────────────────────────
lang         = 'en'
var_interval = None
var_range    = None

# ── 主窗口 ────────────────────────────────────────────────
root = tk.Tk()
root.configure(bg=BG)
root.geometry("560x570")
root.resizable(False, False)

# ── 动态控件引用（用于切换语言时更新文字）────────────────
refs = {}   # key -> widget or list of widgets

def t(key):
    return I18N[lang][key]

def apply_lang():
    root.title(t('title'))
    refs['lbl_interval'].configure(text=t('interval'))
    refs['btn_weekly'].configure(text=t('weekly'))
    refs['btn_3day'].configure(text=t('3day'))
    refs['lbl_timerange'].configure(text=t('timerange'))
    refs['gen_btn'].configure(text=t('generate'))
    # 语言切换按钮高亮
    refs['lang_en'].configure(bg=LANG_SEL if lang=='en' else LANG_BG,
                              fg=ACCENT   if lang=='en' else FG_DIM)
    refs['lang_zh'].configure(bg=LANG_SEL if lang=='zh' else LANG_BG,
                              fg=ACCENT   if lang=='zh' else FG_DIM)

def switch_lang(new_lang):
    global lang
    lang = new_lang
    apply_lang()

# ── 顶部栏：语言切换 ──────────────────────────────────────
top_bar = tk.Frame(root, bg=BG)
top_bar.pack(fill="x", padx=30, pady=(14, 0))

tk.Frame(top_bar, bg=BG).pack(side="left", expand=True)   # 弹性空白

lang_frame = tk.Frame(top_bar, bg=BG_CARD, highlightthickness=1,
                      highlightbackground="#44446a")
lang_frame.pack(side="right")

btn_en = tk.Label(lang_frame, text="EN", font=FONT_LANG, bg=LANG_SEL,
                  fg=ACCENT, padx=12, pady=4, cursor="hand2")
btn_en.pack(side="left")
btn_en.bind("<Button-1>", lambda e: switch_lang('en'))

tk.Frame(lang_frame, bg="#44446a", width=1).pack(side="left", fill="y")

btn_zh = tk.Label(lang_frame, text="中文", font=FONT_LANG, bg=LANG_BG,
                  fg=FG_DIM, padx=12, pady=4, cursor="hand2")
btn_zh.pack(side="left")
btn_zh.bind("<Button-1>", lambda e: switch_lang('zh'))

refs['lang_en'] = btn_en
refs['lang_zh'] = btn_zh

# ── 工具函数 ──────────────────────────────────────────────
def make_section(text_key):
    lbl = tk.Label(root, text=t(text_key), font=FONT_TITLE,
                   bg=BG, fg=ACCENT, anchor="w")
    lbl.pack(fill="x", padx=30, pady=(16, 6))
    return lbl

# ── 周期选择 ──────────────────────────────────────────────
refs['lbl_interval'] = make_section('interval')

var_interval = tk.StringVar(value="weekly")
iv_frame = tk.Frame(root, bg=BG)
iv_frame.pack(fill="x", padx=30)

def make_interval_btn(parent, value, text_key):
    btn = tk.Label(parent, text=t(text_key), font=FONT_OPTION,
                   bg=BG_CARD, fg=FG, padx=20, pady=8,
                   cursor="hand2", width=12)
    def select(*_):
        var_interval.set(value)
        refs['btn_weekly'].configure(
            bg=SEL_BG if var_interval.get() == 'weekly' else BG_CARD,
            fg=ACCENT if var_interval.get() == 'weekly' else FG,
        )
        refs['btn_3day'].configure(
            bg=SEL_BG if var_interval.get() == '3day'  else BG_CARD,
            fg=ACCENT if var_interval.get() == '3day'  else FG,
        )
    btn.bind("<Button-1>", select)
    return btn, select

btn_weekly, sel_weekly = make_interval_btn(iv_frame, 'weekly', 'weekly')
btn_weekly.pack(side="left", padx=(0, 8))
refs['btn_weekly'] = btn_weekly

btn_3day, sel_3day = make_interval_btn(iv_frame, '3day', '3day')
btn_3day.pack(side="left")
refs['btn_3day'] = btn_3day

sel_weekly()   # 默认选 weekly

# ── 时间段选择 ────────────────────────────────────────────
refs['lbl_timerange'] = make_section('timerange')

var_range = tk.IntVar(value=2)
range_btns = []

def select_range(idx):
    var_range.set(idx)
    for i, b in enumerate(range_btns):
        b.configure(bg=SEL_BG if i == idx else BG_CARD,
                    fg=ACCENT if i == idx else FG)

for idx, (label, _, _) in enumerate(RANGES):
    btn = tk.Label(root, text=label, font=FONT_OPTION,
                   bg=BG_CARD, fg=FG, anchor="w", pady=9, cursor="hand2")
    btn.pack(fill="x", padx=8)
    btn.bind("<Button-1>", lambda e, i=idx: select_range(i))
    range_btns.append(btn)

select_range(2)

# ── Generate 按钮 ─────────────────────────────────────────
def generate():
    idx       = var_range.get()
    interval  = var_interval.get()
    start_str = RANGES[idx][1]
    end_str   = RANGES[idx][2]
    script    = os.path.join(_DIR, "plot_kline.py")
    iv_label  = t('weekly') if interval == "weekly" else t('3day')

    status_var.set(f"{t('generating')}  {iv_label}  {RANGES[idx][0]} ...")
    status_lbl.configure(fg=FG_DIM)
    root.update()

    result = subprocess.run(
        [sys.executable, script, interval, start_str, end_str],
        capture_output=True, text=True
    )
    output = (result.stdout + result.stderr).strip()
    if result.returncode == 0:
        status_var.set(output if output else t('done'))
        status_lbl.configure(fg=OK_COLOR)
    else:
        status_var.set(output if output else t('error'))
        status_lbl.configure(fg=ERR_COLOR)

btn_frame = tk.Frame(root, bg=BG)
btn_frame.pack(pady=18)

gen_btn = tk.Button(btn_frame, text=t('generate'),
                    font=FONT_BTN, bg=BTN_BG, fg=BTN_FG,
                    activebackground=BTN_HOVER, activeforeground=BTN_FG,
                    relief="flat", bd=0, padx=32, pady=10,
                    cursor="hand2", command=generate)
gen_btn.pack()
gen_btn.bind("<Enter>", lambda e: gen_btn.configure(bg=BTN_HOVER))
gen_btn.bind("<Leave>", lambda e: gen_btn.configure(bg=BTN_BG))
refs['gen_btn'] = gen_btn

# ── 状态栏 ────────────────────────────────────────────────
status_var = tk.StringVar(value="")
status_lbl = tk.Label(root, textvariable=status_var, font=FONT_STATUS,
                      bg=BG, fg=FG_DIM, wraplength=500, justify="left")
status_lbl.pack(padx=30, pady=(0, 10))

apply_lang()
root.mainloop()
