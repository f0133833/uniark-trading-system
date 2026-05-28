"""
BTC K线分析 - Web App
本机浏览器访问: http://127.0.0.1:5000

绘图核心已抽到 plot_kline.render_chart，本文件只剩 Flask 壳 + 前端模板。
"""
import os
import sys
import io
import base64
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from flask import Flask, render_template_string, request, jsonify

_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _DIR)

from plot_kline import render_chart, INTERVAL_CONFIG

app = Flask(__name__)

RANGES = [
    ("2017-08 ~ 2020-05", "17 Aug, 2017", "30 May, 2020"),
    ("2020-03 ~ 2022-11", "17 Mar, 2020", "30 Nov, 2022"),
    ("2022-10 ~ 2025-10", "17 Oct, 2022", "30 Oct, 2025"),
    ("2025-04 ~ 2027-11", "17 Apr, 2025", "30 Nov, 2027"),
]


def generate_chart(interval, range_idx):
    """渲染指定周期 + 时间段，返回 base64 编码的 PNG。"""
    _, start_str, end_str = RANGES[range_idx]
    fig, _, _ = render_chart(interval, start_str, end_str)

    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.8)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')


HTML = """
<!DOCTYPE html>
<html lang="en" id="html-root">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>BTC K-Line Generator</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { background: #1e1e2e; color: #e0e0f0;
           font-family: 'Segoe UI', 'Noto Sans', sans-serif;
           min-height: 100vh; padding: 20px 16px; }
    .top-bar { display: flex; justify-content: flex-end; margin-bottom: 16px; }
    .lang-switcher { display: flex; border: 1px solid #44446a;
                     border-radius: 6px; overflow: hidden; }
    .lang-btn { padding: 5px 14px; cursor: pointer; font-size: 0.85rem;
                font-weight: bold; background: #2a2a3e; color: #8888aa;
                transition: all 0.2s; user-select: none; }
    .lang-btn.active { background: #3a3a5e; color: #7c6af7; }
    .lang-divider { width: 1px; background: #44446a; }
    h1 { color: #7c6af7; text-align: center; font-size: 1.4rem;
         margin-bottom: 18px; }
    .section-title { font-size: 0.78rem; color: #7c6af7; font-weight: bold;
                     text-transform: uppercase; letter-spacing: 1px;
                     margin-bottom: 8px; margin-top: 14px; }
    .card-group { display: flex; gap: 10px; margin-bottom: 4px; }
    .card { flex: 1; padding: 12px; background: #2a2a3e;
            border: 1px solid #44446a; border-radius: 8px;
            text-align: center; cursor: pointer; transition: all 0.15s;
            font-weight: bold; user-select: none; }
    .card:hover  { border-color: #7c6af7; }
    .card.active { background: #3a3a5e; border-color: #7c6af7;
                   color: #7c6af7; }
    .range-list { display: flex; flex-direction: column; gap: 6px;
                  margin-bottom: 4px; }
    .range-item { padding: 10px 14px; background: #2a2a3e;
                  border: 1px solid #44446a; border-radius: 6px;
                  cursor: pointer; transition: all 0.15s; user-select: none; }
    .range-item:hover  { border-color: #7c6af7; }
    .range-item.active { background: #3a3a5e; border-color: #7c6af7;
                         color: #7c6af7; }
    .btn { width: 100%; padding: 12px; background: #7c6af7;
           color: #fff; border: none; border-radius: 8px;
           font-size: 0.95rem; font-weight: bold; cursor: pointer;
           transition: background 0.15s; margin-top: 14px; }
    .btn:hover    { background: #9b8dff; }
    .btn:disabled { background: #44446a; cursor: not-allowed; }
    #status { text-align: center; font-size: 0.88rem; color: #8888aa;
              margin-bottom: 14px; min-height: 1.2em; }
    #status.ok  { color: #50fa7b; }
    #status.err { color: #ff5555; }
    #chart-wrap { text-align: center; }
    #chart-img  { max-width: 100%; border-radius: 8px;
                  box-shadow: 0 4px 20px rgba(0,0,0,0.5); }
    .spinner { display: none; margin: 20px auto; width: 36px; height: 36px;
               border: 4px solid #44446a; border-top-color: #7c6af7;
               border-radius: 50%; animation: spin 0.8s linear infinite; }
    @keyframes spin { to { transform: rotate(360deg); } }
  </style>
</head>
<body>

  <div class="top-bar">
    <div class="lang-switcher">
      <div class="lang-btn active" id="btn-en" onclick="switchLang('en')">EN</div>
      <div class="lang-divider"></div>
      <div class="lang-btn"        id="btn-zh" onclick="switchLang('zh')">中文</div>
    </div>
  </div>

  <h1 id="title">📈 BTC K-Line Generator</h1>

  <div class="section-title" id="lbl-interval">Interval</div>
  <div class="card-group">
    <div class="card active" data-val="weekly" onclick="selectInterval(this)" id="card-weekly">Weekly</div>
    <div class="card"        data-val="3day"   onclick="selectInterval(this)" id="card-3day">3-Day</div>
  </div>

  <div class="section-title" id="lbl-range">Time Range</div>
  <div class="range-list">
    {% for i, label in ranges %}
    <div class="range-item {% if i==2 %}active{% endif %}"
         data-idx="{{ i }}" onclick="selectRange(this)">{{ label }}</div>
    {% endfor %}
  </div>

  <button class="btn" id="gen-btn" onclick="generate()">Generate Chart</button>
  <div id="status"></div>
  <div class="spinner" id="spinner"></div>
  <div id="chart-wrap"><img id="chart-img" src="" style="display:none"></div>

<script>
  const i18n = {
    en: {
      title:      '📈 BTC K-Line Generator',
      interval:   'INTERVAL',
      weekly:     'Weekly',
      '3day':     '3-Day',
      timerange:  'TIME RANGE',
      generate:   'Generate Chart',
      generating: 'Generating...',
      done:       'Done ✓',
      error:      'Error ✗',
    },
    zh: {
      title:      '📈 BTC K线生成器',
      interval:   '周期',
      weekly:     '周线',
      '3day':     '3日线',
      timerange:  '时间段',
      generate:   '生成图表',
      generating: '正在生成...',
      done:       '完成 ✓',
      error:      '错误 ✗',
    }
  };

  let curLang     = 'en';
  let selInterval = 'weekly';
  let selRangeIdx = 2;

  function switchLang(lang) {
    curLang = lang;
    const tx = i18n[lang];
    document.getElementById('title').textContent        = tx.title;
    document.getElementById('lbl-interval').textContent = tx.interval;
    document.getElementById('lbl-range').textContent    = tx.timerange;
    document.getElementById('card-weekly').textContent  = tx.weekly;
    document.getElementById('card-3day').textContent    = tx['3day'];
    document.getElementById('gen-btn').textContent      = tx.generate;
    document.getElementById('btn-en').classList.toggle('active', lang==='en');
    document.getElementById('btn-zh').classList.toggle('active', lang==='zh');
  }

  function selectInterval(el) {
    document.querySelectorAll('.card').forEach(c => c.classList.remove('active'));
    el.classList.add('active');
    selInterval = el.dataset.val;
  }

  function selectRange(el) {
    document.querySelectorAll('.range-item').forEach(r => r.classList.remove('active'));
    el.classList.add('active');
    selRangeIdx = parseInt(el.dataset.idx);
  }

  async function generate() {
    const btn     = document.getElementById('gen-btn');
    const status  = document.getElementById('status');
    const spinner = document.getElementById('spinner');
    const img     = document.getElementById('chart-img');
    const tx      = i18n[curLang];

    btn.disabled = true;
    status.className = '';
    status.textContent = tx.generating;
    spinner.style.display = 'block';
    img.style.display = 'none';

    try {
      const resp = await fetch('/generate', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({interval: selInterval, range_idx: selRangeIdx})
      });
      const data = await resp.json();
      if (data.ok) {
        img.src = 'data:image/png;base64,' + data.img;
        img.style.display = 'block';
        status.textContent = tx.done;
        status.className = 'ok';
      } else {
        status.textContent = tx.error + ': ' + data.error;
        status.className = 'err';
      }
    } catch(e) {
      status.textContent = tx.error + ': ' + e;
      status.className = 'err';
    } finally {
      btn.disabled = false;
      spinner.style.display = 'none';
    }
  }
</script>
</body>
</html>
"""

@app.route('/')
def index():
    ranges = [(i, r[0]) for i, r in enumerate(RANGES)]
    return render_template_string(HTML, ranges=ranges)


@app.route('/generate', methods=['POST'])
def generate():
    data      = request.get_json()
    interval  = data.get('interval', 'weekly')
    range_idx = int(data.get('range_idx', 2))
    try:
        img_b64 = generate_chart(interval, range_idx)
        return jsonify({'ok': True, 'img': img_b64})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)})


if __name__ == '__main__':
    # 安全默认：只在本机回环地址监听。
    # 浏览器访问 http://127.0.0.1:5000 即可。
    #
    # 如需手机/同 WiFi 设备访问，把 host 改为 '0.0.0.0'，然后用本机 IP 访问。
    # ⚠️ 注意：'0.0.0.0' 会把服务暴露到当前局域网，公共 WiFi 下慎用。
    HOST = '127.0.0.1'
    PORT = 5000
    print(f"启动服务: http://{HOST}:{PORT}")
    app.run(host=HOST, port=PORT, debug=False)
