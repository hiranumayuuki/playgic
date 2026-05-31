"""
Playgic Backtest Engine
過去データで戦略の勝率・PF・最大DDを検証する

⚠️ 生存バイアス注意：現在のユニバース（生き残り銘柄）のみ対象のため
   実際より良い結果が出やすい。あくまで戦略の方向性チェックに使うこと。
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import timedelta
from screener import UNIVERSE_MAP, is_japan_ticker


def run_backtest(
    universes: list,
    start_year: int = 2021,
    end_year: int = 2025,
    strategy: str = "breakout",   # "breakout" | "dip"
    stop_pct: float = 7.0,
    hold_days: int = 20,
    rsi_max: float = 55.0,
    market_filter: bool = True,   # QQQ 200MA上のみエントリー
    log_fn=None,
) -> tuple:
    """
    Returns: (trades: list[dict], stats: dict)
    """
    tickers = []
    for u in universes:
        tickers += UNIVERSE_MAP.get(u, [])
    tickers = list(dict.fromkeys(tickers))

    start_dt = pd.Timestamp(f"{start_year}-01-01")
    end_dt   = pd.Timestamp(f"{end_year}-12-31")
    # MA200 の warmup に320日分余分に取得
    dl_start = (start_dt - timedelta(days=320)).strftime("%Y-%m-%d")
    dl_end   = (end_dt + timedelta(days=2)).strftime("%Y-%m-%d")

    if log_fn:
        log_fn(f"📥 {len(tickers)}銘柄 {start_year}〜{end_year}年データ取得中...")

    raw = yf.download(
        tickers,
        start=dl_start, end=dl_end,
        interval="1d", auto_adjust=True,
        progress=False, threads=True,
    )

    if raw.empty:
        if log_fn: log_fn("❌ データ取得失敗")
        return [], {}

    if isinstance(raw.columns, pd.MultiIndex):
        c_all = raw["Close"]
        v_all = raw["Volume"]
    else:
        c_all = raw[["Close"]]; c_all.columns = tickers[:1]
        v_all = raw[["Volume"]]; v_all.columns = tickers[:1]

    # ── 市場フィルター：QQQ 200MA ──────────────────────────────────
    regime_dict = {}
    if market_filter:
        if log_fn: log_fn("📊 市場フィルター用 QQQ データ取得中...")
        qqq_raw = yf.download("QQQ", start=dl_start, end=dl_end,
                              interval="1d", auto_adjust=True, progress=False)
        if not qqq_raw.empty:
            qqq_c   = qqq_raw["Close"].squeeze().dropna()
            qqq_ma  = qqq_c.rolling(200).mean()
            regime  = qqq_c > qqq_ma
            regime_dict = regime.to_dict()   # {Timestamp: bool}

    if log_fn:
        log_fn(f"✅ データ取得完了。指標計算・シミュレーション開始...")

    all_trades = []

    for n, ticker in enumerate(tickers):
        if ticker not in c_all.columns:
            continue
        c = c_all[ticker].dropna()
        v = v_all[ticker].reindex(c.index).fillna(0) if ticker in v_all.columns else pd.Series(0.0, index=c.index)

        if len(c) < 210:
            continue

        # ── ベクトル化で一括計算（ルックアヘッドバイアスなし）───────────
        delta   = c.diff()
        gain    = delta.clip(lower=0).rolling(14).mean()
        loss    = (-delta.clip(upper=0)).rolling(14).mean()
        rsi_s   = 100 - 100 / (1 + gain / loss)
        ma50    = c.rolling(50).mean()
        ma200   = c.rolling(200).mean()
        h52     = c.rolling(252, min_periods=60).max()
        nhp_s   = c / h52 * 100                          # 高値比 %
        ret1y_s = c.pct_change(252)                      # 1年リターン
        vol_avg = v.rolling(20).mean().replace(0, np.nan)
        vr_s    = (v / vol_avg).fillna(0)                # 出来高比
        new_hi  = (c > c.shift(1).rolling(252, min_periods=60).max()).astype(int)

        # ── トレード状態マシン ──────────────────────────────────────
        is_jp  = is_japan_ticker(ticker)
        si     = c.index.searchsorted(start_dt)
        in_pos = False
        e_px   = 0.0
        e_dt   = None

        for i in range(si, len(c)):
            date = c.index[i]
            if date > end_dt:
                break
            px = float(c.iloc[i])
            if px != px or px <= 0:
                continue

            if in_pos:
                elapsed  = (date - e_dt).days
                stop_hit = px <= e_px * (1 - stop_pct / 100)
                time_hit = elapsed >= hold_days

                if stop_hit or time_hit:
                    ret = (px / e_px - 1) * 100
                    all_trades.append({
                        "ticker":      ticker,
                        "is_japan":    is_jp,
                        "entry_date":  e_dt.strftime("%Y-%m-%d"),
                        "exit_date":   date.strftime("%Y-%m-%d"),
                        "entry_price": round(e_px, 0 if is_jp else 2),
                        "exit_price":  round(px,   0 if is_jp else 2),
                        "return_pct":  round(ret, 2),
                        "days_held":   elapsed,
                        "exit_reason": "stop_loss" if stop_hit else "time_exit",
                        "win":         ret > 0,
                    })
                    in_pos = False
            else:
                rsi  = float(rsi_s.iloc[i])
                nhp  = float(nhp_s.iloc[i])
                vr   = float(vr_s.iloc[i])
                m200 = float(ma200.iloc[i])
                m50  = float(ma50.iloc[i])
                r1y  = float(ret1y_s.iloc[i])
                nhi  = int(new_hi.iloc[i])

                # NaN スキップ
                if rsi != rsi or nhp != nhp or m200 != m200:
                    continue

                above200 = px > m200
                gc       = (m50 == m50) and m50 > m200
                uptrend  = above200 and gc and (r1y == r1y) and r1y > 0

                if strategy == "breakout":
                    sig = nhp >= 98 and (vr >= 1.3 or nhi >= 1) and above200
                else:  # dip
                    sig = (rsi == rsi) and rsi <= rsi_max and uptrend

                # 市場フィルター：QQQ が 200MA を下回っていたらエントリーしない
                if sig and market_filter and regime_dict:
                    sig = regime_dict.get(date, False)

                if sig:
                    in_pos = True
                    e_px   = px
                    e_dt   = date

        if log_fn and (n + 1) % 10 == 0:
            pct = round((n + 1) / len(tickers) * 100)
            log_fn(f"  {n+1}/{len(tickers)} ({pct}%) 処理中...")

    if log_fn:
        log_fn(f"✅ シミュレーション完了。総トレード数: {len(all_trades)}")

    if not all_trades:
        return [], {}

    # ── 統計計算 ───────────────────────────────────────────────────
    df    = pd.DataFrame(all_trades)
    wins  = df[df["win"]]
    loses = df[~df["win"]]
    gp    = float(wins["return_pct"].sum())       if len(wins)  else 0.0
    gl    = abs(float(loses["return_pct"].sum())) if len(loses) else 1.0

    # ポジションサイジング：1トレードあたり1%リスク想定
    # position_size = 1% / stop_pct（例: 7%損切りなら14.3%ポジション）
    pos_frac = 0.01 / (stop_pct / 100)

    cum = 1.0; peak = 1.0; max_dd = 0.0
    for r in df.sort_values("entry_date")["return_pct"]:
        cum *= (1 + r / 100 * pos_frac)
        if cum > peak:
            peak = cum
        dd = (cum - peak) / peak * 100
        if dd < max_dd:
            max_dd = dd

    stats = {
        "total_trades":  len(df),
        "win_rate":      round(len(wins) / len(df) * 100, 1),
        "avg_return":    round(float(df["return_pct"].mean()), 2),
        "avg_win":       round(float(wins["return_pct"].mean()), 2) if len(wins) else 0,
        "avg_loss":      round(float(loses["return_pct"].mean()), 2) if len(loses) else 0,
        "profit_factor": round(gp / gl, 2) if gl > 0 else None,
        "max_drawdown":  round(max_dd, 1),
        "total_return":  round((cum - 1) * 100, 1),
        "stop_exits":     int((df["exit_reason"] == "stop_loss").sum()),
        "time_exits":     int((df["exit_reason"] == "time_exit").sum()),
        "market_filter":  market_filter,
    }

    return df.sort_values("entry_date", ascending=False).to_dict("records"), stats
