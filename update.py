#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "yfinance>=0.2",
# ]
# ///
"""yfinance で最新の株価データ (直近3ヶ月・日足) を取得し、ダッシュボードを再生成する。

使い方: uv run update.py
  - 依存 (yfinance) は uv が PEP 723 メタデータから自動で用意する
  - 取得に失敗した銘柄は既存の data/*.csv をそのまま維持する
"""

import time

import yfinance as yf

from build_dashboard import DATA_DIR, SYMBOLS, main as build


def fetch(fname: str, ticker: str) -> None:
    path = DATA_DIR / f"{fname}.csv"
    df = yf.Ticker(ticker).history(period="3mo", interval="1d")
    if df.empty:
        print(f"警告: {ticker} のデータを取得できませんでした (既存 CSV を維持)")
        return
    df.to_csv(path)
    print(f"{ticker}: {len(df)} 件 -> {path.name}")


def main() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    for fname, ticker, _name, _kind in SYMBOLS:
        try:
            fetch(fname, ticker)
        except Exception as e:  # ネットワーク障害・レート制限など
            print(f"警告: {ticker} の取得に失敗 ({e}) (既存 CSV を維持)")
        time.sleep(0.5)  # レート制限対策
    print()
    build()


if __name__ == "__main__":
    main()
