"""
Playgic Investment Screener
RSI・52週位置・モメンタムで買い候補を自動スクリーニング
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# ─────────────────────────────────────────────
# 銘柄ユニバース
# ─────────────────────────────────────────────

QQQ_TICKERS = [
    "AAPL","MSFT","NVDA","AMZN","META","GOOGL","TSLA","AVGO","COST","NFLX",
    "AMD","ADBE","QCOM","CSCO","INTU","CMCSA","ISRG","BKNG","VRTX","PANW",
    "LRCX","KLAC","CRWD","SNPS","CDNS","MELI","ABNB","DXCM","FTNT","WDAY",
    "TEAM","TTD","ZS","PYPL","MRVL","PCAR","CTAS","MAR","ON","TXN",
    "SBUX","ORLY","FAST","PAYX","IDXX","MNST","ROST","DLTR","GILD","TMUS",
]

SMH_TICKERS = [
    "NVDA","ASML","TSM","AVGO","QCOM","TXN","AMAT","LRCX","KLAC","INTC",
    "MCHP","MU","ON","MPWR","NXPI","SWKS","MRVL","TER","ENTG","WOLF",
    "COHU","ADI","MTSI","ALGM","RMBS",
]

GROWTH_TICKERS = [
    "PLTR","DDOG","SNOW","NET","MDB","CRWD","ZS","HUBS","COIN","MSTR",
    "U","RBLX","GTLB","PATH","BILL","AXON","CAVA","APP","HOOD","AFRM",
    "BTC-USD","ETH-USD",
]

# 日本株ユニバース
JAPAN_NIKKEI = [
    "8035.T",  # 東京エレクトロン（半導体製造装置）
    "6857.T",  # アドバンテスト（半導体テスト）
    "6146.T",  # ディスコ（半導体ダイシング）
    "4063.T",  # 信越化学（シリコンウェーハ）
    "6981.T",  # 村田製作所（電子部品）
    "6762.T",  # TDK（電子部品）
    "6963.T",  # ローム（半導体）
    "6861.T",  # キーエンス（センサー・FA）
    "6367.T",  # ダイキン工業
    "6594.T",  # ニデック（モーター）
    "6902.T",  # デンソー（車載電子）
    "6501.T",  # 日立製作所
    "6702.T",  # 富士通
    "9984.T",  # ソフトバンクグループ（AI投資）
    "6758.T",  # ソニーグループ
    "7974.T",  # 任天堂
    "4519.T",  # 中外製薬
    "4543.T",  # テルモ
    "7203.T",  # トヨタ自動車
    "9432.T",  # NTT
    "9983.T",  # ファーストリテイリング
    "8031.T",  # 三井物産
    "8058.T",  # 三菱商事
    "8306.T",  # 三菱UFJ
]

JAPAN_GROWTH = [
    "4478.T",  # freee（会計SaaS）
    "3923.T",  # ラクス（業務SaaS）
    "4448.T",  # Chatwork
    "3697.T",  # SHIFT（QAテスト）
    "4307.T",  # 野村総合研究所
    "3659.T",  # ネクソン（ゲーム）
    "4776.T",  # サイボウズ
    "3626.T",  # TIS（IT）
    "9613.T",  # NTTデータ
    "2432.T",  # DeNA
    "3765.T",  # ガンホー（ゲーム）
    "4911.T",  # 資生堂
    "6526.T",  # ソシオネクスト（半導体設計）
]

UNIVERSE_MAP = {
    "qqq": QQQ_TICKERS,
    "smh": SMH_TICKERS,
    "growth": GROWTH_TICKERS,
    "japan_nikkei": JAPAN_NIKKEI,
    "japan_growth": JAPAN_GROWTH,
}

# 日本株ユニバースかどうか判定
def is_japan_ticker(ticker: str) -> bool:
    return ticker.endswith(".T")


def calculate_rsi(prices: pd.Series, period: int = 14) -> float:
    """RSI(14)を計算して最新値を返す"""
    delta = prices.diff().dropna()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return round(float(rsi.iloc[-1]), 1) if not rsi.empty else None


def get_52w_position(current: float, low52: float, high52: float) -> float:
    """52週高値・安値の間で今の価格が何%の位置にいるか（0=底値 / 100=天井）"""
    if high52 == low52:
        return 50.0
    return round((current - low52) / (high52 - low52) * 100, 1)


def is_uptrend(series: pd.Series) -> dict:
    """
    右肩上がり判定
    - 価格 > 200MA：長期上昇トレンド
    - 50MA > 200MA：ゴールデンクロス状態
    - 1年リターンがプラス：実際に上がり続けてる
    """
    if len(series) < 200:
        return {"uptrend": False, "above_200ma": False, "golden_cross": False, "return_1y": None, "ma50": None, "ma200": None}

    current = float(series.iloc[-1])
    ma50 = float(series.rolling(50).mean().iloc[-1])
    ma200 = float(series.rolling(200).mean().iloc[-1])
    # 1年リターン：直近252営業日前の価格と比較
    price_1y_ago = float(series.iloc[-252]) if len(series) >= 252 else float(series.iloc[0])
    ret1y = round((current / price_1y_ago - 1) * 100, 1)

    above_200ma = current > ma200
    golden_cross = ma50 > ma200

    # 右肩上がり = 3条件すべて満たす
    uptrend = above_200ma and golden_cross and ret1y > 0

    return {
        "uptrend": uptrend,
        "above_200ma": above_200ma,
        "golden_cross": golden_cross,
        "return_1y": ret1y,
        "ma50": round(ma50, 2),
        "ma200": round(ma200, 2),
    }


def score_ticker(rsi: float, pos52w: float, uptrend: bool = False) -> float:
    """
    買いチャンススコア（高いほど割安・チャンス大）
    RSIが低いほど高得点、52週位置が低いほど高得点
    右肩上がりならボーナス +20点
    """
    if rsi is None:
        return 0.0
    rsi_score = max(0, 70 - rsi)
    pos_score = max(0, 60 - pos52w)
    trend_bonus = 20 if uptrend else 0
    return round(rsi_score + pos_score + trend_bonus, 1)


def detect_breakout(series: pd.Series, volume: pd.Series) -> dict:
    """
    新高値ブレイク検出
    - 52週高値の98%以上にいる（ブレイク直前・直後）
    - 出来高が20日平均の1.3倍以上（確認シグナル）
    - 直近5日で高値更新した
    """
    if len(series) < 60:
        return {"is_breakout": False, "near_high_pct": 0, "vol_ratio": 0, "new_high_days": 0}

    current = float(series.iloc[-1])
    high_52w = float(series.iloc[-252:].max()) if len(series) >= 252 else float(series.max())

    # 高値との距離（100%=新高値タッチ, 98%=あと2%でブレイク）
    near_high_pct = round(current / high_52w * 100, 1)

    # 出来高比率
    vol_ratio = 0.0
    if volume is not None and len(volume) >= 20:
        vol_today = float(volume.iloc[-1])
        vol_avg20 = float(volume.rolling(20).mean().iloc[-1])
        vol_ratio = round(vol_today / vol_avg20, 2) if vol_avg20 > 0 else 0

    # 直近5日で新高値更新した日数
    recent = series.iloc[-5:]
    rolling_max = series.iloc[:-5].max() if len(series) > 5 else series.max()
    new_high_days = int((recent > rolling_max).sum())

    is_breakout = near_high_pct >= 98 and (vol_ratio >= 1.3 or new_high_days >= 1)

    return {
        "is_breakout": is_breakout,
        "near_high_pct": near_high_pct,
        "vol_ratio": vol_ratio,
        "new_high_days": new_high_days,
    }


def breakout_score(near_high_pct: float, vol_ratio: float, new_high_days: int, rsi: float) -> float:
    """
    ブレイクアウトスコア（高いほどブレイク強度大）
    """
    # 高値に近いほど高得点（最大40点）
    proximity = max(0, (near_high_pct - 90) * 4)
    # 出来高急増ボーナス（最大30点）
    vol_bonus = min(30, (vol_ratio - 1) * 20) if vol_ratio > 1 else 0
    # 新高値更新日数ボーナス（最大20点）
    high_days_bonus = new_high_days * 10
    # RSI 55-75 がモメンタムゾーン（最大10点）
    rsi_bonus = 10 if rsi and 55 <= rsi <= 75 else 0
    return round(proximity + vol_bonus + high_days_bonus + rsi_bonus, 1)


def screen(universes: list[str], rsi_max: float = 60, pos52w_max: float = 100,
           uptrend_only: bool = False, mode: str = "dip") -> list[dict]:
    """
    指定ユニバースをスクリーニングして結果リストを返す
    uptrend_only: Trueなら右肩上がり銘柄だけ返す
    """
    tickers = []
    for u in universes:
        tickers += UNIVERSE_MAP.get(u, [])
    tickers = list(dict.fromkeys(tickers))

    print(f"  {len(tickers)}銘柄をダウンロード中...")
    data = yf.download(
        tickers,
        period="14mo",
        interval="1d",
        auto_adjust=True,
        progress=False,
        threads=True,
    )

    if isinstance(data.columns, pd.MultiIndex):
        close = data["Close"]
        volume_data = data["Volume"]
    else:
        close = data[["Close"]]
        close.columns = tickers[:1]
        volume_data = data[["Volume"]]
        volume_data.columns = tickers[:1]

    results = []
    for ticker in tickers:
        if ticker not in close.columns:
            continue
        series = close[ticker].dropna()
        vol = volume_data[ticker].dropna() if ticker in volume_data.columns else None
        if len(series) < 30:
            continue

        current = float(series.iloc[-1])
        series_1y = series.iloc[-252:] if len(series) >= 252 else series
        high52 = float(series_1y.max())
        low52 = float(series_1y.min())
        rsi = calculate_rsi(series)
        pos52w = get_52w_position(current, low52, high52)
        chg1d = round((current / float(series.iloc[-2]) - 1) * 100, 2) if len(series) >= 2 else None
        chg1m = round((current / float(series.iloc[-22]) - 1) * 100, 2) if len(series) >= 22 else None

        trend = is_uptrend(series)
        bo = detect_breakout(series, vol)

        if uptrend_only and not trend["uptrend"]:
            continue

        if mode == "dip":
            # 押し目買いモード
            if rsi is not None and rsi > rsi_max:
                continue
            if pos52w > pos52w_max:
                continue
            final_score = score_ticker(rsi, pos52w, trend["uptrend"])
        else:
            # ブレイクアウトモード：高値圏のみ
            if bo["near_high_pct"] < 95:
                continue
            final_score = breakout_score(bo["near_high_pct"], bo["vol_ratio"], bo["new_high_days"], rsi)

        is_jp = is_japan_ticker(ticker)
        results.append({
            "ticker": ticker,
            "is_japan": is_jp,
            "currency": "¥" if is_jp else "$",
            "price": round(current, 0) if is_jp else round(current, 2),
            "rsi": rsi,
            "pos52w": pos52w,
            "high52": round(high52, 2),
            "low52": round(low52, 2),
            "chg1d": chg1d,
            "chg1m": chg1m,
            "return_1y": trend["return_1y"],
            "above_200ma": trend["above_200ma"],
            "golden_cross": trend["golden_cross"],
            "uptrend": trend["uptrend"],
            "ma50": trend["ma50"],
            "ma200": trend["ma200"],
            # ブレイクアウト情報
            "is_breakout": bo["is_breakout"],
            "near_high_pct": bo["near_high_pct"],
            "vol_ratio": bo["vol_ratio"],
            "new_high_days": bo["new_high_days"],
            "score": final_score,
        })

    return sorted(results, key=lambda x: x["score"], reverse=True)


if __name__ == "__main__":
    print("=" * 55)
    print("🔬 Playgic Investment Screener")
    print(f"実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 55)

    results = screen(["qqq", "smh", "growth"], rsi_max=55, pos52w_max=50)

    print(f"\n🏆 買い候補 ランキング（RSI≤55 かつ 52週位置≤50%）")
    print(f"{'#':<3} {'Ticker':<10} {'価格':>8} {'RSI':>6} {'52W位置':>8} {'1D%':>6} {'1M%':>6} {'スコア':>7}")
    print("-" * 58)
    for i, r in enumerate(results[:20], 1):
        chg1d_str = f"{r['chg1d']:+.1f}" if r['chg1d'] is not None else "  N/A"
        chg1m_str = f"{r['chg1m']:+.1f}" if r['chg1m'] is not None else "  N/A"
        print(f"#{i:<2} {r['ticker']:<10} ${r['price']:>7.2f} {r['rsi']:>6.1f} {r['pos52w']:>7.1f}% {chg1d_str:>6} {chg1m_str:>6} {r['score']:>7.1f}")
