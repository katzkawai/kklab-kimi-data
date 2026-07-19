#!/usr/bin/env python3
"""data/*.csv (Yahoo Finance 日次データ) から日本株ダッシュボード index.html を生成する。"""

import csv
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
DATA_DIR = BASE / "data"
OUT = BASE / "index.html"

# 表示順: (ファイル名, ティッカー, 表示名, 種別)
SYMBOLS = [
    ("N225", "^N225", "日経平均株価", "index"),
    ("1306.T", "1306.T", "TOPIX連動ETF", "index"),
    ("7203.T", "7203.T", "トヨタ自動車", "stock"),
    ("6758.T", "6758.T", "ソニーグループ", "stock"),
    ("8306.T", "8306.T", "三菱UFJフィナンシャルG", "stock"),
    ("9984.T", "9984.T", "ソフトバンクグループ", "stock"),
    ("6861.T", "6861.T", "キーエンス", "stock"),
    ("8035.T", "8035.T", "東京エレクトロン", "stock"),
    ("6501.T", "6501.T", "日立製作所", "stock"),
    ("7974.T", "7974.T", "任天堂", "stock"),
    ("9983.T", "9983.T", "ファーストリテイリング", "stock"),
    ("6098.T", "6098.T", "リクルートHD", "stock"),
]

JST = timezone(timedelta(hours=9))


def load_csv(path: Path):
    dates, closes, volumes = [], [], []
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                dt = datetime.fromisoformat(row["Date"].replace("Z", "+00:00")).astimezone(JST)
                close = float(row["Close"])
                vol = float(row.get("Volume") or 0)
            except (ValueError, KeyError):
                continue
            dates.append(dt.strftime("%Y-%m-%d"))
            closes.append(close)
            volumes.append(vol)
    return dates, closes, volumes


def main():
    series = []
    for fname, ticker, name, kind in SYMBOLS:
        path = DATA_DIR / f"{fname}.csv"
        if not path.exists():
            print(f"skip {ticker}: {path} なし")
            continue
        dates, closes, volumes = load_csv(path)
        if len(closes) < 2:
            print(f"skip {ticker}: データ不足 ({len(closes)} 件)")
            continue
        series.append({
            "ticker": ticker,
            "name": name,
            "kind": kind,
            "dates": dates,
            "closes": [round(c, 2) for c in closes],
            "volumes": volumes,
            "last": round(closes[-1], 2),
            "prev": round(closes[-2], 2),
            "chg": round(closes[-1] - closes[-2], 2),
            "chgPct": round((closes[-1] - closes[-2]) / closes[-2] * 100, 2),
            "periodChgPct": round((closes[-1] - closes[0]) / closes[0] * 100, 2),
            "asOf": dates[-1],
        })
        print(f"loaded {ticker}: {len(closes)} 件, 終値 {closes[-1]:,.2f} ({dates[-1]})")

    if not series:
        raise SystemExit("有効な CSV がありません")

    as_of = max(s["asOf"] for s in series)
    payload = {"asOf": as_of, "generatedAt": datetime.now(JST).strftime("%Y-%m-%d %H:%M JST"),
               "series": series}

    html = TEMPLATE.replace("__DATA__", json.dumps(payload, ensure_ascii=False))
    OUT.write_text(html, encoding="utf-8")
    print(f"\n{OUT} を生成しました ({len(series)} シリーズ, 基準日 {as_of})")


TEMPLATE = r"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>日本株ダッシュボード</title>
<style>
  :root {
    --bg: #0f1420; --panel: #1a2130; --border: #2a3450;
    --text: #e8ecf4; --muted: #8b94ab;
    --up: #e5484d; --down: #2fa36b; --flat: #8b94ab; /* 日本式: 赤=上げ / 緑=下げ */
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: var(--bg); color: var(--text); font-family: "Hiragino Kaku Gothic ProN", "Noto Sans JP", sans-serif; padding: 24px; }
  header { display: flex; align-items: baseline; gap: 16px; flex-wrap: wrap; margin-bottom: 20px; }
  h1 { font-size: 22px; }
  header .meta { color: var(--muted); font-size: 13px; }
  .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 14px; }
  .card { background: var(--panel); border: 1px solid var(--border); border-radius: 12px; padding: 14px 16px; }
  .card.index { border-color: #4a5a86; background: #1d2540; }
  .card .name { font-size: 13px; color: var(--muted); }
  .card .ticker { font-size: 11px; color: var(--muted); opacity: .7; }
  .card .price { font-size: 24px; font-weight: 700; margin-top: 4px; font-variant-numeric: tabular-nums; }
  .card .chg { font-size: 13px; margin-top: 2px; font-variant-numeric: tabular-nums; }
  .up { color: var(--up); } .down { color: var(--down); } .flat { color: var(--flat); }
  .card svg { display: block; width: 100%; height: 48px; margin-top: 10px; }
  .card .period { font-size: 11px; color: var(--muted); margin-top: 6px; }
  section.chart { background: var(--panel); border: 1px solid var(--border); border-radius: 12px; padding: 18px; margin-top: 22px; }
  section.chart h2 { font-size: 16px; margin-bottom: 4px; }
  section.chart .sub { font-size: 12px; color: var(--muted); margin-bottom: 12px; }
  #cmp { width: 100%; height: 380px; display: block; }
  .legend { display: flex; flex-wrap: wrap; gap: 8px 16px; margin-top: 12px; font-size: 12px; }
  .legend span { display: inline-flex; align-items: center; gap: 6px; cursor: pointer; user-select: none; }
  .legend span.off { opacity: .35; }
  .legend i { display: inline-block; width: 14px; height: 3px; border-radius: 2px; }
  footer { margin-top: 18px; color: var(--muted); font-size: 11px; }
</style>
</head>
<body>
<header>
  <h1>🇯🇵 日本株ダッシュボード</h1>
  <span class="meta" id="meta"></span>
</header>
<div class="grid" id="cards"></div>
<section class="chart">
  <h2>3ヶ月パフォーマンス比較</h2>
  <div class="sub">期初の終値 = 100 として正規化。凡例クリックで表示 ON/OFF。</div>
  <canvas id="cmp"></canvas>
  <div class="legend" id="legend"></div>
</section>
<footer>データ: Yahoo Finance (kimi-datasource 経由) / AI 生成。投資助言ではありません。</footer>
<script>
const DATA = __DATA__;
const COLORS = ["#f6c344","#4ea1ff","#e5484d","#b57edc","#2fa36b","#ff8c42","#5ad1c9","#e86ea8","#9acd32","#c0c8dc","#d2a26c","#7f9cf5"];

document.getElementById("meta").textContent =
  `データ基準日: ${DATA.asOf} / 生成: ${DATA.generatedAt}`;

const fmt = (n, d=2) => n.toLocaleString("ja-JP", {minimumFractionDigits: d, maximumFractionDigits: d});
const cls = v => v > 0 ? "up" : v < 0 ? "down" : "flat";
const sign = v => (v > 0 ? "+" : "") + fmt(v);

// ---- カード + スパークライン ----
const cards = document.getElementById("cards");
DATA.series.forEach((s, i) => {
  const card = document.createElement("div");
  card.className = "card" + (s.kind === "index" ? " index" : "");
  const isIdx = s.kind === "index";
  card.innerHTML = `
    <div class="name">${s.name}</div>
    <div class="ticker">${s.ticker}</div>
    <div class="price">${fmt(s.last, isIdx ? 2 : s.last >= 10000 ? 0 : 1)}</div>
    <div class="chg ${cls(s.chg)}">${sign(s.chg)} (${s.chgPct > 0 ? "+" : ""}${fmt(s.chgPct)}%) 前日比</div>
    <svg viewBox="0 0 220 48" preserveAspectRatio="none"></svg>
    <div class="period">3ヶ月騰落率: <b class="${cls(s.periodChgPct)}">${s.periodChgPct > 0 ? "+" : ""}${fmt(s.periodChgPct)}%</b></div>`;
  const svg = card.querySelector("svg");
  const min = Math.min(...s.closes), max = Math.max(...s.closes), span = max - min || 1;
  const pts = s.closes.map((c, j) =>
    `${(j / (s.closes.length - 1) * 220).toFixed(1)},${(44 - (c - min) / span * 40).toFixed(1)}`).join(" ");
  const col = s.periodChgPct > 0 ? "var(--up)" : s.periodChgPct < 0 ? "var(--down)" : "var(--flat)";
  svg.innerHTML = `<polyline points="${pts}" fill="none" stroke="${col}" stroke-width="1.5"/>`;
  cards.appendChild(card);
});

// ---- 比較チャート (期初=100 正規化) ----
const canvas = document.getElementById("cmp");
const ctx = canvas.getContext("2d");
const norm = DATA.series.map((s, i) => ({
  name: s.name, color: COLORS[i % COLORS.length],
  points: s.closes.map(c => c / s.closes[0] * 100),
  dates: s.dates, visible: true,
}));
const labels = DATA.series.reduce((a, s) => s.dates.length > a.length ? s.dates : a, []);

const legend = document.getElementById("legend");
norm.forEach((s, i) => {
  const el = document.createElement("span");
  el.innerHTML = `<i style="background:${s.color}"></i>${s.name}`;
  el.onclick = () => { s.visible = !s.visible; el.classList.toggle("off", !s.visible); draw(); };
  legend.appendChild(el);
});

function draw() {
  const dpr = window.devicePixelRatio || 1;
  const W = canvas.clientWidth, H = canvas.clientHeight;
  canvas.width = W * dpr; canvas.height = H * dpr;
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, W, H);
  const padL = 44, padR = 12, padT = 10, padB = 28;
  const vis = norm.filter(s => s.visible);
  if (!vis.length) return;
  const all = vis.flatMap(s => s.points);
  let min = Math.min(...all, 100), max = Math.max(...all, 100);
  const pad = (max - min) * 0.05 || 1; min -= pad; max += pad;
  const X = j => padL + j / (labels.length - 1) * (W - padL - padR);
  const Y = v => padT + (1 - (v - min) / (max - min)) * (H - padT - padB);
  // グリッド
  ctx.strokeStyle = "#2a3450"; ctx.fillStyle = "#8b94ab"; ctx.lineWidth = 1;
  ctx.font = "11px sans-serif"; ctx.textAlign = "right";
  for (let g = 0; g <= 4; g++) {
    const v = min + (max - min) * g / 4, y = Y(v);
    ctx.beginPath(); ctx.moveTo(padL, y); ctx.lineTo(W - padR, y); ctx.stroke();
    ctx.fillText(v.toFixed(0), padL - 6, y + 4);
  }
  // 基準線 100
  ctx.strokeStyle = "#4a5a86"; ctx.setLineDash([4, 4]);
  ctx.beginPath(); ctx.moveTo(padL, Y(100)); ctx.lineTo(W - padR, Y(100)); ctx.stroke();
  ctx.setLineDash([]);
  // X 軸ラベル (月ごと)
  ctx.textAlign = "center";
  let lastMonth = "";
  labels.forEach((d, j) => {
    const m = d.slice(0, 7);
    if (m !== lastMonth) { lastMonth = m; ctx.fillText(m, X(j), H - 8); }
  });
  // ライン
  vis.forEach(s => {
    ctx.strokeStyle = s.color; ctx.lineWidth = 1.8; ctx.beginPath();
    s.points.forEach((v, j) => { const x = X(j), y = Y(v); j ? ctx.lineTo(x, y) : ctx.moveTo(x, y); });
    ctx.stroke();
  });
}
new ResizeObserver(draw).observe(canvas);
draw();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
