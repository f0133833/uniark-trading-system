"""
绘图辅助：把 divergence.py 检测到的背离结构标注到 MACD 面板上。

单一实现，供 plot_kline.py / app.py 复用。
任何与背离视觉表达相关的改动（颜色、形状、字号、布局）都只在本文件里改。

设计要点
--------
- 形状：底背离 = 上三角 ▲（暗示反转向上），顶背离 = 下三角 ▼（暗示反转向下）。
        箭头方向与"未来走势的预期方向"对齐。
- 布局：箭头紧贴 hist 极值柱（直观锚定触发位置），
        文字搬到 0 轴的对侧（hist 不会延伸的空旷区）。

        例（顶背离）：
              ▼               <- 箭头在绿柱上方
            (绿柱)
            ─0────────         <- 0 轴
            L2                 <- Lv 标识在 0 轴下方
            38%                <- 百分比再下一行

        例（底背离）：
            36%                <- 百分比
            L2                 <- Lv 标识
            ─0────────         <- 0 轴
            (红柱)
              ▲               <- 箭头在红柱下方

        这样：
        1. 同向背离的文字基线统一（顶背离全部对齐到 0 轴下方某一行，
           底背离全部对齐到 0 轴上方某一行），横向比较强度容易；
        2. 文字不再挤压 hist 柱周边，长期紧贴 hist 的视觉拥堵消失；
        3. 箭头依然指向真实触发位置，不影响读图直觉。

- 占位：水平宽度 ≈ 1 根 K 线宽。
- Lv1 时 Lv 行留空（不显示 "L1"），保持百分比对齐，密集触发时百分比依然
  在同一水平线上。
"""

# 颜色：红=底背离（看涨反转），绿=顶背离（看跌反转）
COLOR_BULLISH = '#ff3344'
COLOR_BEARISH = '#22aa44'

# 视觉参数（要再压扁/放大就改这里）
MARKER_SIZE       = 80      # 三角形 scatter 的 size
MARKER_EDGE       = 0.6     # 白色描边宽度（让箭头在 hist 柱上浮起来）
LABEL_FONTSIZE    = 7

# 偏移参数（相对 MACD 面板高度的百分比）
OFFSET_MARKER_PCT = 0.05    # 箭头距 hist 极值柱的距离

# 文字搬到 0 轴对侧。两行从 0 轴向对侧依次延伸：
TEXT_FIRST_PCT    = 0.08    # 第一行文字（紧邻 0 轴的那一行）距 0 轴的距离
TEXT_SECOND_PCT   = 0.15    # 第二行文字距 0 轴的距离
# 行序约定（无论顶/底背离）：
#   "近 0 轴的一行" = Lv 标识（Lv1 留空）
#   "远 0 轴的一行" = 百分比


def annotate_divergences(macd_ax, df, divergences):
    """
    在 MACD 面板上为每条 divergence 画一个紧凑的图标化标记。
    箭头紧贴 hist 极值柱，文字落在 0 轴对侧的空旷区。

    Parameters
    ----------
    macd_ax     : matplotlib.axes.Axes
                  MACD hist 所在的面板。
    df          : pandas.DataFrame
                  含 'hist' 列，下标必须与 divergence 中的 s3_start/s3_end 对齐
                  （即调用方传入的就是用于检测的同一份 df）。
    divergences : list[dict]
                  find_three_segment_divergences 的返回值。
    """
    if not divergences:
        return

    y_min, y_max = macd_ax.get_ylim()
    y_range = y_max - y_min
    off_marker      = y_range * OFFSET_MARKER_PCT
    text_lv_offset  = y_range * TEXT_FIRST_PCT      # Lv 行（近 0 轴）
    text_pct_offset = y_range * TEXT_SECOND_PCT     # 百分比行（远 0 轴）

    for div in divergences:
        s3s, s3e   = div['s3_start'], div['s3_end']
        ratio_pct  = div['ratio'] * 100
        level      = div['level']
        is_bullish = div['kind'] == 'bullish'
        x_mid      = (s3s + s3e) / 2

        if is_bullish:
            # 底背离：箭头在 hist 红柱下方，文字搬到 0 轴上方
            extreme   = df['hist'].iloc[s3s:s3e + 1].min()   # 最深红柱（负值）
            marker    = '^'
            color     = COLOR_BULLISH
            y_marker  = extreme - off_marker
            y_lv      = +text_lv_offset       # 0 轴上方第一行
            y_pct     = +text_pct_offset      # 0 轴上方第二行（更高）
            va_text   = 'center'
        else:
            # 顶背离：箭头在 hist 绿柱上方，文字搬到 0 轴下方
            extreme   = df['hist'].iloc[s3s:s3e + 1].max()   # 最高绿柱（正值）
            marker    = 'v'
            color     = COLOR_BEARISH
            y_marker  = extreme + off_marker
            y_lv      = -text_lv_offset       # 0 轴下方第一行
            y_pct     = -text_pct_offset      # 0 轴下方第二行（更低）
            va_text   = 'center'

        # ── 箭头：紧贴 hist 极值柱 ────────────────────────────────────────
        macd_ax.scatter(
            [x_mid], [y_marker],
            marker=marker, s=MARKER_SIZE,
            color=color, edgecolors='white', linewidths=MARKER_EDGE,
            zorder=5,
        )

        # ── Lv 行：0 轴对侧第一行（Lv2+ 才显示，Lv1 留空保持对齐）───────
        if level >= 2:
            macd_ax.text(
                x_mid, y_lv, f'L{level}',
                fontsize=LABEL_FONTSIZE, color=color,
                ha='center', va=va_text, fontweight='bold',
            )

        # ── 百分比行：0 轴对侧第二行（始终显示）─────────────────────────
        macd_ax.text(
            x_mid, y_pct, f'{ratio_pct:.0f}%',
            fontsize=LABEL_FONTSIZE, color=color,
            ha='center', va=va_text, fontweight='bold',
        )


def print_divergences(df, divergences):
    """
    把每条背离的诊断信息打印到 stdout。

    与 annotate_divergences 是正交的——前者是图像，后者是文本日志。
    plot_kline.py 的 CLI 入口会用；app.py（web 服务）不需要。
    """
    if not divergences:
        print("No divergences detected.")
        return

    for div in divergences:
        kind_str = 'Bullish' if div['kind'] == 'bullish' else 'Bearish'
        s3s, s3e = div['s3_start'], div['s3_end']
        print(
            f"[{kind_str} Div. Lv{div['level']}] "
            f"S3/P={div['ratio'] * 100:.1f}% "
            f"S3:{df.index[s3s].strftime('%Y-%m-%d')}~"
            f"{df.index[s3e].strftime('%Y-%m-%d')} "
            f"P={div['s1_area']:.0f}({div['s1_bars']}b) "
            f"S3={div['s3_area']:.0f}({div['s3_bars']}b)"
        )
