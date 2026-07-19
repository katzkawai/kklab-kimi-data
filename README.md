# 日本株ダッシュボード

Yahoo Finance のデータを使い、日本の主要株価を一覧表示する静的 HTML ダッシュボード。
単一ファイル (`index.html`) にデータを埋め込んでおり、ブラウザで開くだけで動作する。

## 表示内容

- **指数カード**: 日経平均株価 (`^N225`)、TOPIX連動ETF (`1306.T`)
- **主要銘柄カード** (10銘柄): トヨタ自動車、ソニーグループ、三菱UFJフィナンシャルG、
  ソフトバンクグループ、キーエンス、東京エレクトロン、日立製作所、任天堂、
  ファーストリテイリング、リクルートHD
- 各カード: 最新終値 / 前日比 (円・%) / 3ヶ月スパークライン / 3ヶ月騰落率
- **3ヶ月パフォーマンス比較チャート**: 期初の終値 = 100 に正規化した折れ線グラフ。
  凡例クリックで系列の表示 ON/OFF が可能
- カラー規則は日本式 (赤 = 上げ / 緑 = 下げ)

## ファイル構成

```
index.html                       ダッシュボード本体 (生成物・データ埋め込み済み)
update.py                        最新データ取得 + 再生成を一括で行うスクリプト (PEP 723 / yfinance)
build_dashboard.py               data/*.csv から index.html を再生成するスクリプト (PEP 723 / 標準ライブラリのみ)
data/*.csv                       Yahoo Finance から取得した日次データ (直近3ヶ月)
.github/workflows/update.yml     データ自動更新ワークフロー (GitHub Actions)
```

## 使い方

### 閲覧

```bash
python3 -m http.server 8931 --bind 127.0.0.1
# → http://127.0.0.1:8931/index.html
```

※ `index.html` を直接ブラウザで開いてもよい。

### データ更新

**前提**: `uv` が必要。未インストールの場合:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**手順**: プロジェクト直下で以下を実行するだけ。

```bash
uv run update.py
```

1. yfinance で全12銘柄の直近3ヶ月分 (日足) を取得し、`data/*.csv` を上書き
2. `build_dashboard.py` が自動で呼ばれ、最新データを埋め込んだ `index.html` を再生成

両スクリプトは PEP 723 形式 (インラインメタデータ) のため、uv が依存パッケージ
(yfinance 等) を自動で用意する。事前の `pip install` や venv 構築は不要。

**更新後の確認**: ブラウザで `index.html` を再読み込みし、ヘッダーの「データ基準日」が
最新営業日になっていることを確認する。

**注意**:
- 取得に失敗した銘柄は既存 CSV を維持したまま再生成される (警告が表示される)
- 既存 CSV からの再生成だけ行う場合 (データ取得なし):

```bash
uv run build_dashboard.py
```

### 自動更新 (GitHub Actions)

`.github/workflows/update.yml` により、データ更新を定期自動実行する。

- **スケジュール**: 平日 18:00 JST (東証大引け後)。cron は UTC 指定 (`0 9 * * 1-5`)
- **処理内容**: `uv run update.py` を実行し、`data/` と `index.html` に変更があれば
  `github-actions[bot]` が「データ更新 (YYYY-MM-DD)」というメッセージでコミット & プッシュ。
  変更がない場合 (休日・取得失敗時など) はコミットせず終了
- **手動実行**: GitHub の Actions タブ →「データ更新」→ Run workflow、
  または `gh workflow run update.yml`

※ プライベートリポジトリのため Actions の利用時間を消費する (1回あたり約1〜2分)。
※ `astral-sh/setup-uv` は浮動メジャータグ (`v8` 等) が存在しないため、
ワークフローではフルバージョン (`v8.3.2`) にピン留めしている。

## データ仕様

- 取得元: Yahoo Finance (kimi-datasource プラグイン経由)
- 期間: 直近3ヶ月・日足
- 表示価格は各 CSV の最新終値。データ基準日はヘッダーに表示
- `^TOPX` (TOPIX 指数) は Yahoo 側でデータを取得できないため、
  代替として TOPIX連動ETF (`1306.T`) を使用

※ AI 生成データのため、投資判断には使用しないこと。

## 更新履歴

### 2026-07-19 — GitHub Actions による自動更新

- 平日 18:00 JST に `uv run update.py` を実行し、変更を自動コミット & プッシュする
  ワークフロー (`.github/workflows/update.yml`) を追加 (手動実行での動作確認済み)
- `astral-sh/setup-uv` を `v8.3.2` にピン留め (浮動メジャータグ不在のため) 、
  cache-dependency-glob を PEP 723 用に設定
- `.gitignore` を追加 (`__pycache__` 等を除外)
- README のデータ更新手順を拡充 (前提・手順・確認方法・注意)

### 2026-07-19 — PEP 723 / uv 対応

- `update.py` を追加 (yfinance でデータ取得 → 再生成を `uv run update.py` 一発で実行)
- 両スクリプトを PEP 723 形式 (インラインメタデータ) に変更し、`uv run` 起動に対応

### 2026-07-19 — 初版

- ダッシュボード新規作成 (指数 2 + 主要銘柄 10 の計 12 シリーズ)
- 銘柄カード (終値・前日比・スパークライン・3ヶ月騰落率) を実装
- 期初 = 100 正規化のパフォーマンス比較チャートを実装 (凡例トグル対応)
- `^TOPX` が取得不可のため TOPIX連動ETF (`1306.T`) に代替
- データ基準日: 2026-07-17
