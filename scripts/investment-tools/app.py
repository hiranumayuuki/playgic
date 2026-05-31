"""
Playgic Investment Tools UI
銘柄スクリーナー + 証券担保ローン安全計算
"""

import sys, os, json, time, threading, webbrowser
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

app = Flask(__name__)

HTML = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Playgic Investment Tools</title>
<style>
  :root {
    --bg: #0d0d14; --card: #16161f; --border: #2a2a3a;
    --purple: #8b5cf6; --cyan: #06b6d4; --text: #e2e8f0; --muted: #64748b;
    --green: #22c55e; --yellow: #eab308; --red: #ef4444; --orange: #f97316;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: var(--bg); color: var(--text); font-family: -apple-system, BlinkMacSystemFont, sans-serif; min-height: 100vh; }
  header { border-bottom: 1px solid var(--border); padding: 20px 32px; display: flex; align-items: center; gap: 12px; }
  header h1 { font-size: 20px; font-weight: 700; background: linear-gradient(135deg, var(--purple), var(--cyan)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
  main { max-width: 1000px; margin: 0 auto; padding: 32px 24px; }
  .tabs { display: flex; gap: 8px; margin-bottom: 28px; }
  .tab { padding: 10px 24px; border-radius: 8px; border: 1px solid var(--border); background: transparent; color: var(--muted); cursor: pointer; font-size: 14px; font-weight: 600; transition: all .15s; }
  .tab.active { background: var(--purple); border-color: var(--purple); color: #fff; }
  .tab:hover:not(.active) { border-color: var(--purple); color: var(--text); }
  .panel { display: none; } .panel.active { display: block; }
  .card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 24px; margin-bottom: 20px; }
  .card h2 { font-size: 13px; color: var(--muted); text-transform: uppercase; letter-spacing: .08em; margin-bottom: 16px; }
  .form-row { display: flex; gap: 12px; flex-wrap: wrap; align-items: flex-end; margin-bottom: 16px; }
  .form-group { display: flex; flex-direction: column; gap: 6px; }
  .form-group label { font-size: 12px; color: var(--muted); }
  input[type=number], input[type=text], select {
    background: var(--bg); border: 1px solid var(--border); border-radius: 8px;
    color: var(--text); padding: 10px 12px; font-size: 14px; min-width: 120px;
  }
  input:focus, select:focus { outline: none; border-color: var(--purple); }
  .checkbox-group { display: flex; gap: 12px; flex-wrap: wrap; }
  .checkbox-label { display: flex; align-items: center; gap: 8px; cursor: pointer; font-size: 14px; padding: 8px 14px; border: 1px solid var(--border); border-radius: 8px; transition: all .15s; }
  .checkbox-label:has(input:checked) { border-color: var(--purple); color: var(--purple); background: rgba(139,92,246,.1); }
  .checkbox-label input { display: none; }
  .btn { display: inline-flex; align-items: center; gap: 8px; padding: 11px 26px; border-radius: 8px; border: none; cursor: pointer; font-size: 14px; font-weight: 700; transition: all .15s; }
  .btn-primary { background: var(--purple); color: #fff; } .btn-primary:hover { background: #7c3aed; }
  .btn-primary:disabled { opacity: .5; cursor: not-allowed; }
  .spinner { width: 14px; height: 14px; border: 2px solid rgba(255,255,255,.3); border-top-color: #fff; border-radius: 50%; animation: spin .7s linear infinite; display: inline-block; }
  @keyframes spin { to { transform: rotate(360deg); } }
  .status-box { background: var(--bg); border: 1px solid var(--border); border-radius: 8px; padding: 12px 16px; font-family: monospace; font-size: 13px; color: var(--cyan); min-height: 48px; white-space: pre-wrap; line-height: 1.6; margin-top: 14px; display: none; }

  /* スクリーナー結果テーブル */
  .results-table { width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 13px; }
  .results-table th { text-align: left; padding: 10px 12px; color: var(--muted); font-size: 11px; text-transform: uppercase; letter-spacing: .06em; border-bottom: 1px solid var(--border); }
  .results-table td { padding: 11px 12px; border-bottom: 1px solid rgba(42,42,58,.5); }
  .results-table tr:hover td { background: rgba(139,92,246,.05); }
  .results-table tr:first-child td { color: var(--purple); font-weight: 700; }
  .ticker-cell { font-weight: 700; font-size: 14px; }
  .score-cell { font-weight: 800; color: var(--cyan); }
  .rsi-low { color: var(--green); font-weight: 700; }
  .rsi-mid { color: var(--yellow); }
  .rsi-high { color: var(--red); }
  .chg-pos { color: var(--green); }
  .chg-neg { color: var(--red); }
  .rank-badge { display: inline-block; width: 22px; height: 22px; border-radius: 50%; background: var(--border); text-align: center; line-height: 22px; font-size: 11px; font-weight: 700; }
  .rank-1 { background: #fbbf24; color: #000; }
  .rank-2 { background: #9ca3af; color: #000; }
  .rank-3 { background: #b45309; color: #fff; }

  /* ローン計算 */
  .loan-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px; }
  @media (max-width: 600px) { .loan-grid { grid-template-columns: 1fr; } }
  .loan-result-card { background: var(--bg); border: 1px solid var(--border); border-radius: 10px; padding: 18px; }
  .loan-result-card.danger { border-color: var(--red); background: rgba(239,68,68,.05); }
  .loan-result-card.warning { border-color: var(--yellow); background: rgba(234,179,8,.05); }
  .loan-result-card.safe { border-color: var(--green); background: rgba(34,197,94,.05); }
  .loan-label { font-size: 12px; color: var(--muted); margin-bottom: 6px; }
  .loan-value { font-size: 26px; font-weight: 800; }
  .loan-value.big { font-size: 32px; }
  .loan-sub { font-size: 12px; color: var(--muted); margin-top: 4px; }
  .safety-bar-wrap { margin-top: 20px; }
  .safety-bar-label { display: flex; justify-content: space-between; font-size: 12px; color: var(--muted); margin-bottom: 6px; }
  .safety-bar { height: 12px; background: var(--border); border-radius: 6px; overflow: hidden; }
  .safety-bar-fill { height: 100%; border-radius: 6px; transition: width .5s; }
  .divider { border: none; border-top: 1px solid var(--border); margin: 20px 0; }
  .empty { text-align: center; padding: 48px; color: var(--muted); }
  .empty .big { font-size: 48px; margin-bottom: 12px; }
  .summary-chips { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 20px; }
  .chip { padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 600; background: rgba(139,92,246,.15); color: var(--purple); border: 1px solid rgba(139,92,246,.3); }
</style>
</head>
<body>

<header>
  <h1>📈 Playgic Investment Tools</h1>
</header>

<main>
  <div class="tabs">
    <button class="tab active" onclick="switchTab('screener')">🔬 スクリーナー</button>
    <button class="tab" onclick="switchTab('planner')">📊 トレードプランナー</button>
    <button class="tab" onclick="switchTab('backtest')">📈 バックテスト</button>
    <button class="tab" onclick="switchTab('loan')">🏦 ローン計算</button>
    <button class="tab" onclick="switchTab('manual')">📖 使い方</button>
  </div>

  <!-- スクリーナー -->
  <div class="panel active" id="panel-screener">
    <div class="card">
      <h2>スクリーニング条件</h2>
      <div class="form-row">
        <div class="form-group">
          <label>対象ユニバース</label>
          <div class="checkbox-group">
            <label class="checkbox-label"><input type="checkbox" name="universe" value="qqq" checked>🇺🇸 QQQ（NASDAQ100）</label>
            <label class="checkbox-label"><input type="checkbox" name="universe" value="smh" checked>🇺🇸 SMH（半導体）</label>
            <label class="checkbox-label"><input type="checkbox" name="universe" value="growth" checked>🇺🇸 高成長銘柄</label>
            <label class="checkbox-label"><input type="checkbox" name="universe" value="japan_nikkei">🇯🇵 日本株（主力）</label>
            <label class="checkbox-label"><input type="checkbox" name="universe" value="japan_growth">🇯🇵 日本グロース</label>
          </div>
        </div>
      </div>
      <div class="form-row">
        <div class="form-group">
          <label>RSI 上限（以下を表示）</label>
          <input type="number" id="rsi-max" value="60" min="10" max="90" step="5" style="width:100px">
        </div>
        <div class="form-group">
          <label>52週位置 上限（%以下を表示）</label>
          <input type="number" id="pos-max" value="100" min="10" max="100" step="5" style="width:100px">
        </div>
        <div class="form-group">
          <label>表示件数</label>
          <select id="limit">
            <option value="10">10件</option>
            <option value="20" selected>20件</option>
            <option value="50">50件</option>
          </select>
        </div>
      </div>
      <div class="form-row" style="margin-bottom:0">
        <label class="checkbox-label" style="border-color:var(--cyan);padding:10px 18px">
          <input type="checkbox" id="uptrend-only" checked>
          <span>📈 右肩上がりのみ（200MA上・ゴールデンクロス・1年リターンプラス）</span>
        </label>
      </div>
      <div style="font-size:12px;color:var(--muted);margin-top:8px;margin-bottom:20px">
        ※ チェックありの場合、3条件すべて満たす銘柄のみ表示。スコアにボーナス+20点。
      </div>
      <div class="form-row" style="margin-bottom:16px">
        <div class="form-group" style="width:100%">
          <label>戦略モード</label>
          <div style="display:flex;gap:10px;margin-top:4px">
            <label style="display:flex;align-items:center;gap:8px;cursor:pointer;padding:10px 18px;border:1px solid var(--border);border-radius:8px;flex:1;transition:all .15s" id="mode-dip-label">
              <input type="radio" name="mode" value="dip" checked onchange="updateModeUI()">
              <div>
                <div style="font-weight:700;font-size:14px">📉 押し目買い</div>
                <div style="font-size:11px;color:var(--muted)">RSI低い × 右肩上がり = 一時的な押し目を拾う</div>
              </div>
            </label>
            <label style="display:flex;align-items:center;gap:8px;cursor:pointer;padding:10px 18px;border:1px solid var(--border);border-radius:8px;flex:1;transition:all .15s" id="mode-bo-label">
              <input type="radio" name="mode" value="breakout" onchange="updateModeUI()">
              <div>
                <div style="font-weight:700;font-size:14px">🚀 新高値ブレイク</div>
                <div style="font-size:11px;color:var(--muted)">52週高値更新 × 出来高急増 = モメンタムに乗る</div>
              </div>
            </label>
          </div>
        </div>
      </div>
      <button class="btn btn-primary" id="screen-btn" onclick="runScreener()">🔬 スクリーニング開始</button>
    </div>
    <div class="status-box" id="screen-status"></div>
    <div id="screen-results">
      <div class="empty"><div class="big">🔬</div>条件を設定してスクリーニング開始</div>
    </div>
  </div>

  <!-- トレードプランナー -->
  <div class="panel" id="panel-planner">
    <div style="max-width:680px">

      <div class="card">
        <h2>銘柄を入力</h2>
        <div class="form-row" style="align-items:flex-end">
          <div class="form-group" style="flex:1">
            <label>ティッカーシンボル</label>
            <input type="text" id="plan-ticker" placeholder="例: NVDA / 8035.T" style="width:100%;font-size:16px;font-weight:700;letter-spacing:.05em" oninput="this.value=this.value.toUpperCase()">
          </div>
          <button class="btn btn-primary" onclick="fetchPlanData()" id="plan-fetch-btn">データ取得</button>
        </div>
        <div style="font-size:12px;color:var(--muted);margin-top:8px">スクリーナーで絞った銘柄のティッカーをそのまま入力</div>
      </div>

      <div class="card" id="plan-entry-card" style="display:none">
        <h2>エントリー判定</h2>
        <div id="plan-entry-result"></div>
      </div>

      <div class="card" id="plan-calc-card" style="display:none">
        <h2>トレードプラン計算</h2>
        <div class="form-row" style="margin-bottom:16px">
          <div class="form-group">
            <label>エントリー価格</label>
            <input type="number" id="plan-entry-price" step="0.01" style="width:140px" oninput="calcPlan()">
          </div>
          <div class="form-group">
            <label>総資産（円）</label>
            <input type="number" id="plan-total-assets" value="2000000" step="100000" style="width:150px" oninput="calcPlan()">
          </div>
          <div class="form-group">
            <label>1トレードのリスク（%）</label>
            <input type="number" id="plan-risk-pct" value="1" step="0.5" min="0.5" max="3" style="width:100px" oninput="calcPlan()">
          </div>
        </div>
        <div class="form-row" style="margin-bottom:16px">
          <div class="form-group">
            <label>損切り幅（%）</label>
            <input type="number" id="plan-stop-pct" value="7" step="0.5" min="3" max="15" style="width:100px" oninput="calcPlan()">
          </div>
          <div class="form-group">
            <label>借入額（円）※任意</label>
            <input type="number" id="plan-loan" value="500000" step="50000" style="width:140px" oninput="calcPlan()">
          </div>
          <div class="form-group">
            <label>担保掛け目（%）</label>
            <input type="number" id="plan-haircut" value="70" step="5" style="width:100px" oninput="calcPlan()">
          </div>
        </div>
        <div id="plan-result"></div>
      </div>

    </div>
  </div>

  <!-- バックテスト -->
  <div class="panel" id="panel-backtest">
    <div style="max-width:900px">

      <div style="background:rgba(234,179,8,.08);border:1px solid rgba(234,179,8,.3);border-radius:10px;padding:12px 16px;margin-bottom:20px;font-size:13px;color:#fde68a;line-height:1.7">
        ⚠️ <strong>生存バイアス注意</strong>：現在のユニバース（生き残り銘柄）のみ対象のため、実際より良い結果が出やすい。戦略の方向性チェックとして使うこと。
      </div>

      <div class="card">
        <h2>バックテスト条件</h2>
        <div class="form-row">
          <div class="form-group">
            <label>対象ユニバース</label>
            <div class="checkbox-group">
              <label class="checkbox-label"><input type="checkbox" name="bt-universe" value="qqq" checked>🇺🇸 QQQ</label>
              <label class="checkbox-label"><input type="checkbox" name="bt-universe" value="smh" checked>🇺🇸 SMH</label>
              <label class="checkbox-label"><input type="checkbox" name="bt-universe" value="growth" checked>🇺🇸 高成長</label>
              <label class="checkbox-label"><input type="checkbox" name="bt-universe" value="japan_nikkei">🇯🇵 日本株（主力）</label>
              <label class="checkbox-label"><input type="checkbox" name="bt-universe" value="japan_growth">🇯🇵 日本グロース</label>
            </div>
          </div>
        </div>
        <div class="form-row" style="margin-bottom:16px">
          <div class="form-group" style="width:100%">
            <label>戦略モード</label>
            <div style="display:flex;gap:10px;margin-top:4px">
              <label style="display:flex;align-items:center;gap:8px;cursor:pointer;padding:10px 18px;border:1px solid var(--cyan);border-radius:8px;flex:1;transition:all .15s" id="bt-mode-bo-label">
                <input type="radio" name="bt-mode" value="breakout" checked onchange="updateBtModeUI()">
                <div><div style="font-weight:700;font-size:14px">🚀 新高値ブレイク</div><div style="font-size:11px;color:var(--muted)">52週高値更新 × 出来高急増</div></div>
              </label>
              <label style="display:flex;align-items:center;gap:8px;cursor:pointer;padding:10px 18px;border:1px solid var(--border);border-radius:8px;flex:1;transition:all .15s" id="bt-mode-dip-label">
                <input type="radio" name="bt-mode" value="dip" onchange="updateBtModeUI()">
                <div><div style="font-weight:700;font-size:14px">📉 押し目買い</div><div style="font-size:11px;color:var(--muted)">RSI低い × 右肩上がり</div></div>
              </label>
            </div>
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>開始年</label>
            <select id="bt-start-year" style="width:110px">
              <option value="2020">2020年</option>
              <option value="2021" selected>2021年</option>
              <option value="2022">2022年</option>
              <option value="2023">2023年</option>
            </select>
          </div>
          <div class="form-group">
            <label>終了年</label>
            <select id="bt-end-year" style="width:110px">
              <option value="2023">2023年</option>
              <option value="2024">2024年</option>
              <option value="2025" selected>2025年</option>
            </select>
          </div>
          <div class="form-group">
            <label>損切り（%）</label>
            <input type="number" id="bt-stop" value="7" min="3" max="20" step="1" style="width:90px">
          </div>
          <div class="form-group">
            <label>保有日数</label>
            <input type="number" id="bt-hold" value="20" min="5" max="90" step="5" style="width:90px">
          </div>
          <div class="form-group" id="bt-rsi-group">
            <label>RSI上限（押し目）</label>
            <input type="number" id="bt-rsi" value="55" min="30" max="70" step="5" style="width:90px">
          </div>
        </div>
        <div class="form-row" style="margin-bottom:16px">
          <label class="checkbox-label" style="border-color:var(--cyan);padding:10px 18px">
            <input type="checkbox" id="bt-market-filter" checked>
            <span>📊 市場フィルター（QQQ 200MA上のみエントリー）</span>
          </label>
          <div style="font-size:12px;color:var(--muted);margin-top:6px;padding-left:4px">
            ✅ ON：弱気相場（2022年など）を自動スキップ　|　❌ OFF：相場関係なく全期間エントリー
          </div>
        </div>
        <button class="btn btn-primary" id="bt-btn" onclick="runBacktest()">📈 バックテスト実行</button>
        <div style="font-size:12px;color:var(--muted);margin-top:10px">※ 銘柄数・期間によって1〜3分かかります</div>
      </div>

      <div class="status-box" id="bt-status"></div>
      <div id="bt-results">
        <div class="empty"><div class="big">📈</div>条件を設定してバックテスト実行</div>
      </div>

    </div>
  </div>

  <!-- 使い方マニュアル -->
  <div class="panel" id="panel-manual">
    <div style="max-width:720px">

      <div class="card">
        <h2>このツールでできること</h2>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:4px">
          <div style="background:var(--bg);border:1px solid var(--border);border-radius:10px;padding:16px">
            <div style="font-size:20px;margin-bottom:8px">🔬</div>
            <div style="font-weight:700;margin-bottom:4px">銘柄スクリーナー</div>
            <div style="font-size:13px;color:var(--muted);line-height:1.6">「今どの銘柄が買い場か」をデータで探す。米国株・日本株に対応。</div>
          </div>
          <div style="background:var(--bg);border:1px solid var(--border);border-radius:10px;padding:16px">
            <div style="font-size:20px;margin-bottom:8px">🏦</div>
            <div style="font-weight:700;margin-bottom:4px">証券担保ローン計算</div>
            <div style="font-size:13px;color:var(--muted);line-height:1.6">野村信託銀行ルールに準拠。強制売却まであと何%か即座に計算。</div>
          </div>
        </div>
      </div>

      <div class="card">
        <h2>🔬 スクリーナーの使い方</h2>

        <div style="font-weight:700;margin-bottom:10px;color:var(--cyan)">① ユニバースを選ぶ</div>
        <table style="width:100%;border-collapse:collapse;font-size:13px;margin-bottom:20px">
          <thead><tr style="color:var(--muted);font-size:11px;text-transform:uppercase">
            <th style="text-align:left;padding:6px 10px;border-bottom:1px solid var(--border)">ユニバース</th>
            <th style="text-align:left;padding:6px 10px;border-bottom:1px solid var(--border)">内容</th>
            <th style="text-align:left;padding:6px 10px;border-bottom:1px solid var(--border)">銘柄数</th>
          </tr></thead>
          <tbody>
            <tr><td style="padding:8px 10px">🇺🇸 QQQ</td><td style="padding:8px 10px;color:var(--muted)">NASDAQ100構成銘柄（Apple, Nvidia, Meta...）</td><td style="padding:8px 10px">50銘柄</td></tr>
            <tr><td style="padding:8px 10px">🇺🇸 SMH</td><td style="padding:8px 10px;color:var(--muted)">半導体ETF（TSMC, NVDA, AMAT...）</td><td style="padding:8px 10px">25銘柄</td></tr>
            <tr><td style="padding:8px 10px">🇺🇸 高成長</td><td style="padding:8px 10px;color:var(--muted)">PLTR, DDOG, SNOW, CRWD, COIN など</td><td style="padding:8px 10px">22銘柄</td></tr>
            <tr><td style="padding:8px 10px">🇯🇵 日本株（主力）</td><td style="padding:8px 10px;color:var(--muted)">東京エレクトロン, 村田, ソニー, トヨタ など</td><td style="padding:8px 10px">24銘柄</td></tr>
            <tr><td style="padding:8px 10px">🇯🇵 日本グロース</td><td style="padding:8px 10px;color:var(--muted)">freee, ラクス, SHIFT, ソシオネクスト など</td><td style="padding:8px 10px">13銘柄</td></tr>
          </tbody>
        </table>

        <div style="font-weight:700;margin-bottom:10px;color:var(--cyan)">② 戦略モードを選ぶ</div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:20px">
          <div style="background:var(--bg);border:1px solid var(--border);border-radius:10px;padding:14px">
            <div style="font-weight:700;margin-bottom:6px">📉 押し目買い</div>
            <div style="font-size:13px;color:var(--muted);line-height:1.7">
              上昇トレンドの中で<strong style="color:var(--text)">一時的に下落した銘柄</strong>を探す。<br>
              RSI が低い（売られすぎ）× 右肩上がり = 押し目の買い場。<br><br>
              <span style="color:var(--yellow)">◎ 相場が調整しているときに使う</span>
            </div>
          </div>
          <div style="background:var(--bg);border:1px solid var(--border);border-radius:10px;padding:14px">
            <div style="font-weight:700;margin-bottom:6px">🚀 新高値ブレイク</div>
            <div style="font-size:13px;color:var(--muted);line-height:1.7">
              <strong style="color:var(--text)">52週高値を更新中の銘柄</strong>を探す。<br>
              高値更新 × 出来高急増 = モメンタムに乗る。<br><br>
              <span style="color:var(--cyan)">◎ 強い上昇相場のときに使う（右肩上がり派向き）</span>
            </div>
          </div>
        </div>

        <div style="font-weight:700;margin-bottom:10px;color:var(--cyan)">③ 結果の読み方</div>
        <table style="width:100%;border-collapse:collapse;font-size:13px;margin-bottom:8px">
          <thead><tr style="color:var(--muted);font-size:11px;text-transform:uppercase">
            <th style="text-align:left;padding:6px 10px;border-bottom:1px solid var(--border)">指標</th>
            <th style="text-align:left;padding:6px 10px;border-bottom:1px solid var(--border)">意味</th>
            <th style="text-align:left;padding:6px 10px;border-bottom:1px solid var(--border)">見方</th>
          </tr></thead>
          <tbody>
            <tr><td style="padding:8px 10px;color:var(--green);font-weight:700">RSI</td><td style="padding:8px 10px">相対力指数（0〜100）</td><td style="padding:8px 10px;color:var(--muted)">30以下=売られすぎ / 70以上=買われすぎ</td></tr>
            <tr><td style="padding:8px 10px">52W位置</td><td style="padding:8px 10px">52週高値・安値間の現在位置</td><td style="padding:8px 10px;color:var(--muted)">0%=底値圏 / 100%=天井圏（高値更新）</td></tr>
            <tr><td style="padding:8px 10px">高値比</td><td style="padding:8px 10px">52週高値に対する現在価格</td><td style="padding:8px 10px;color:var(--muted)">100%=新高値更新中 / 95%以上=ブレイク直前</td></tr>
            <tr><td style="padding:8px 10px">出来高比</td><td style="padding:8px 10px">20日平均出来高との比較</td><td style="padding:8px 10px;color:var(--muted)">×1.5以上=出来高急増（ブレイク確認シグナル）</td></tr>
            <tr><td style="padding:8px 10px;color:var(--cyan);font-weight:700">スコア</td><td style="padding:8px 10px">チャンススコア（独自指標）</td><td style="padding:8px 10px;color:var(--muted)">高いほど買いチャンス大。ランキング用</td></tr>
          </tbody>
        </table>
        <div style="font-size:12px;color:var(--muted);background:var(--bg);padding:10px 14px;border-radius:8px">
          📈 <strong>右肩上がりバッジ</strong>の条件：価格 > 200日移動平均 かつ 50MA > 200MA（ゴールデンクロス）かつ 1年リターンがプラス
        </div>
      </div>

      <div class="card">
        <h2>🏦 証券担保ローン計算の使い方</h2>

        <div style="font-weight:700;margin-bottom:10px;color:var(--cyan)">入力項目</div>
        <table style="width:100%;border-collapse:collapse;font-size:13px;margin-bottom:20px">
          <thead><tr style="color:var(--muted);font-size:11px;text-transform:uppercase">
            <th style="text-align:left;padding:6px 10px;border-bottom:1px solid var(--border)">項目</th>
            <th style="text-align:left;padding:6px 10px;border-bottom:1px solid var(--border)">内容</th>
            <th style="text-align:left;padding:6px 10px;border-bottom:1px solid var(--border)">どこで確認するか</th>
          </tr></thead>
          <tbody>
            <tr><td style="padding:8px 10px">株式評価額</td><td style="padding:8px 10px;color:var(--muted)">担保として差し入れている株の時価</td><td style="padding:8px 10px;color:var(--muted)">野村のインターネットバンキング</td></tr>
            <tr><td style="padding:8px 10px">借入額</td><td style="padding:8px 10px;color:var(--muted)">現在の借入残高</td><td style="padding:8px 10px;color:var(--muted)">同上</td></tr>
            <tr><td style="padding:8px 10px">担保掛け目</td><td style="padding:8px 10px;color:var(--muted)">評価額に掛ける割合（銘柄によって異なる）</td><td style="padding:8px 10px;color:var(--muted)">野村の契約書・明細</td></tr>
            <tr><td style="padding:8px 10px">年利</td><td style="padding:8px 10px;color:var(--muted)">証券担保ローンの金利</td><td style="padding:8px 10px;color:var(--muted)">野村の契約書</td></tr>
          </tbody>
        </table>

        <div style="font-weight:700;margin-bottom:10px;color:var(--cyan)">⚠️ 野村信託銀行ルール（重要）</div>
        <div style="background:rgba(239,68,68,.08);border:1px solid rgba(239,68,68,.3);border-radius:10px;padding:16px;font-size:13px;line-height:1.8;margin-bottom:16px">
          <strong>担保評価額が融資金額の70%を下回った場合 → 強制売却</strong><br>
          担保評価額 = 株式評価額 × 掛け目<br>
          強制売却ライン = 借入額 × 70% ÷ 掛け目（これ以下に株価が下がると強制売却）<br><br>
          売却後に不足額が残った場合は<strong>即時返済義務あり</strong>。
        </div>

        <div style="font-weight:700;margin-bottom:10px;color:var(--cyan)">見るべき数字はこれだけ</div>
        <div style="background:var(--bg);border:1px solid var(--border);border-radius:10px;padding:16px;font-size:13px;line-height:1.8">
          🚨 <strong>「強制売却まであと ◯◯% 下落」</strong>← これだけ覚えれば十分<br>
          <span style="color:var(--green)">30%以上 → 安全圏</span><br>
          <span style="color:var(--yellow)">15〜30% → 要注意（相場次第でリスクあり）</span><br>
          <span style="color:var(--red)">15%未満 → 危険（追加入金か借入減額を検討）</span>
        </div>
      </div>

      <div class="card">
        <h2>⚡ 使うタイミング</h2>
        <div style="font-size:13px;line-height:1.9;color:var(--muted)">
          <strong style="color:var(--text)">毎週月曜朝</strong>：スクリーナーを回して今週の候補を確認<br>
          <strong style="color:var(--text)">相場下落時</strong>：押し目買いモードで割安銘柄を探す<br>
          <strong style="color:var(--text)">強い上昇時</strong>：ブレイクアウトモードでモメンタム銘柄を探す<br>
          <strong style="color:var(--text)">買う前に必ず</strong>：ローン計算タブで強制売却ラインを確認<br>
          <strong style="color:var(--text)">毎月1回</strong>：評価額が変わったらローン計算を更新
        </div>
      </div>

    </div>
  </div>

  <!-- ローン計算 -->
  <div class="panel" id="panel-loan">
    <div class="card">
      <h2>現在の状況を入力</h2>
      <div class="form-row">
        <div class="form-group">
          <label>株式評価額（円）</label>
          <input type="number" id="asset-val" value="1000000" step="10000">
        </div>
        <div class="form-group">
          <label>借入額（円）</label>
          <input type="number" id="loan-amt" value="500000" step="10000">
        </div>
        <div class="form-group">
          <label>担保掛け目（%）</label>
          <input type="number" id="haircut" value="70" min="1" max="100" step="5">
        </div>
        <div class="form-group">
          <label>年利（%）</label>
          <input type="number" id="interest" value="2.5" step="0.1">
        </div>
      </div>
      <button class="btn btn-primary" onclick="calcLoan()">計算する</button>
    </div>
    <div id="loan-results">
      <div class="empty"><div class="big">🏦</div>数字を入力して計算</div>
    </div>
  </div>
</main>

<script>
function switchTab(tab) {
  document.querySelectorAll('.tab').forEach((t,i) => t.classList.toggle('active', ['screener','planner','backtest','loan','manual'][i] === tab));
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  document.getElementById('panel-' + tab).classList.add('active');
}

async function runScreener() {
  const universes = [...document.querySelectorAll('input[name=universe]:checked')].map(el => el.value);
  if (!universes.length) { alert('ユニバースを1つ以上選択してください'); return; }

  const btn = document.getElementById('screen-btn');
  const status = document.getElementById('screen-status');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> スクリーニング中...';
  status.style.display = 'block';
  status.textContent = '起動中...\\n';

  const rsiMax = parseFloat(document.getElementById('rsi-max').value);
  const posMax = parseFloat(document.getElementById('pos-max').value);
  const limit = parseInt(document.getElementById('limit').value);
  const uptrendOnly = document.getElementById('uptrend-only').checked;
  const mode = document.querySelector('input[name=mode]:checked').value;

  try {
    const resp = await fetch('/run/screen', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({universes, rsi_max: rsiMax, pos52w_max: posMax, limit, uptrend_only: uptrendOnly, mode})
    });
    const reader = resp.body.getReader();
    const dec = new TextDecoder();
    let buf = '';
    while (true) {
      const {done, value} = await reader.read();
      if (done) break;
      buf += dec.decode(value, {stream: true});
      const lines = buf.split('\\n');
      buf = lines.pop();
      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        const payload = line.slice(6);
        if (payload === '[DONE]') continue;
        try {
          const msg = JSON.parse(payload);
          if (msg.log) { status.textContent += msg.log + '\\n'; status.scrollTop = status.scrollHeight; }
          if (msg.results) renderScreenerResults(msg.results, limit);
        } catch(e){}
      }
    }
  } catch(e) {
    status.textContent += 'エラー: ' + e.message;
  } finally {
    btn.disabled = false;
    btn.innerHTML = '🔬 スクリーニング開始';
  }
}

function rsiClass(rsi) {
  if (rsi <= 35) return 'rsi-low';
  if (rsi <= 50) return 'rsi-mid';
  return 'rsi-high';
}

function rankBadge(i) {
  return `<span class="rank-badge ${i<=3?'rank-'+i:''}">${i}</span>`;
}

// ─── トレードプランナー ───
let planData = null;

async function fetchPlanData() {
  const ticker = document.getElementById('plan-ticker').value.trim();
  if (!ticker) return;
  const btn = document.getElementById('plan-fetch-btn');
  btn.disabled = true; btn.textContent = '取得中...';

  try {
    const resp = await fetch('/api/plan/fetch', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ticker})
    });
    const data = await resp.json();
    if (data.error) { alert(data.error); return; }
    planData = data;

    // エントリー判定カード
    document.getElementById('plan-entry-card').style.display = 'block';
    document.getElementById('plan-calc-card').style.display = 'block';
    document.getElementById('plan-entry-price').value = data.price;
    renderEntryJudge(data);
    calcPlan();
  } catch(e) {
    alert('データ取得失敗: ' + e.message);
  } finally {
    btn.disabled = false; btn.textContent = 'データ取得';
  }
}

function renderEntryJudge(d) {
  const checks = [
    { ok: d.near_high_pct >= 98, label: `52週高値比 ${d.near_high_pct}%`, req: '98%以上' },
    { ok: d.vol_ratio >= 1.5,    label: `出来高比 ×${d.vol_ratio}`,        req: '×1.5以上' },
    { ok: d.above_200ma,         label: `200MA ${d.above_200ma ? '上' : '下'}`, req: '200MA上' },
    { ok: d.golden_cross,        label: `ゴールデンクロス ${d.golden_cross ? 'あり' : 'なし'}`, req: '必要' },
    { ok: d.rsi >= 50 && d.rsi <= 75, label: `RSI ${d.rsi}`, req: '50〜75' },
  ];
  const allOk = checks.every(c => c.ok);
  const passCount = checks.filter(c => c.ok).length;

  const rows = checks.map(c => `
    <div style="display:flex;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid rgba(42,42,58,.5)">
      <span style="font-size:16px">${c.ok ? '✅' : '❌'}</span>
      <span style="flex:1;font-size:13px">${c.label}</span>
      <span style="font-size:12px;color:var(--muted)">条件: ${c.req}</span>
    </div>`).join('');

  const verdict = allOk
    ? `<div style="background:rgba(34,197,94,.1);border:1px solid var(--green);border-radius:10px;padding:14px 18px;margin-bottom:16px;font-weight:700;color:var(--green);font-size:15px">🚀 エントリー条件 全クリア（${passCount}/5）― 今が入りどき</div>`
    : passCount >= 3
    ? `<div style="background:rgba(234,179,8,.08);border:1px solid var(--yellow);border-radius:10px;padding:14px 18px;margin-bottom:16px;font-weight:700;color:var(--yellow);font-size:15px">⚠️ 条件 ${passCount}/5 クリア ― あと少し待つ</div>`
    : `<div style="background:rgba(239,68,68,.08);border:1px solid var(--red);border-radius:10px;padding:14px 18px;margin-bottom:16px;font-weight:700;color:var(--red);font-size:15px">🛑 条件 ${passCount}/5 ― まだ入らない</div>`;

  document.getElementById('plan-entry-result').innerHTML = verdict + rows;
}

function calcPlan() {
  if (!planData) return;
  const entry = parseFloat(document.getElementById('plan-entry-price').value) || planData.price;
  const assets = parseFloat(document.getElementById('plan-total-assets').value) || 2000000;
  const riskPct = parseFloat(document.getElementById('plan-risk-pct').value) || 1;
  const stopPct = parseFloat(document.getElementById('plan-stop-pct').value) || 7;
  const loan = parseFloat(document.getElementById('plan-loan').value) || 0;
  const haircut = parseFloat(document.getElementById('plan-haircut').value) / 100 || 0.7;
  const isJapan = planData.is_japan;
  const cur = isJapan ? '¥' : '$';
  const fmtPrice = (p) => isJapan
    ? `¥${Math.round(p).toLocaleString('ja-JP')}`
    : `$${p.toFixed(2)}`;

  // 損切りライン
  const stopPrice = entry * (1 - stopPct / 100);
  const stopLossPerShare = entry - stopPrice;

  // ポジションサイズ（リスク金額 ÷ 1株あたりリスク）
  const riskAmount = assets * riskPct / 100;
  const positionAmount = (riskAmount / stopLossPerShare) * entry;
  const shares = Math.floor(riskAmount / stopLossPerShare);

  // 利確目標（1R=損切り幅, 2R, 3R）
  const r1 = entry + stopLossPerShare * 1;
  const r2 = entry + stopLossPerShare * 2;
  const r3 = entry + stopLossPerShare * 3;

  // トレーリングストップ（最高値から-15%）
  const trailStop = entry * 0.85;

  // タイムストップ
  const now = new Date();
  const timeStop = new Date(now.getTime() + 21 * 24 * 60 * 60 * 1000);
  const timeStopStr = `${timeStop.getMonth()+1}/${timeStop.getDate()}`;

  // ローン安全確認
  const newCollateral = (assets + positionAmount) * haircut;
  const newRatio = loan > 0 ? (newCollateral / loan * 100).toFixed(1) : null;
  const loanWarning = newRatio && parseFloat(newRatio) < 100
    ? `<div style="background:rgba(239,68,68,.1);border:1px solid var(--red);border-radius:8px;padding:10px 14px;font-size:13px;color:var(--red)">🚨 このポジションを取ると担保比率が${newRatio}%になります。野村の強制売却ライン（70%）に注意。</div>`
    : newRatio
    ? `<div style="background:rgba(34,197,94,.08);border:1px solid rgba(34,197,94,.3);border-radius:8px;padding:10px 14px;font-size:13px;color:var(--green)">✅ ポジション後の担保比率: ${newRatio}%（安全）</div>`
    : '';

  const rr2 = (stopLossPerShare * 2 / stopLossPerShare).toFixed(1);
  const rr3 = (stopLossPerShare * 3 / stopLossPerShare).toFixed(1);

  document.getElementById('plan-result').innerHTML = `
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:16px">
      <div style="background:var(--bg);border:2px solid var(--red);border-radius:10px;padding:16px">
        <div style="font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;margin-bottom:6px">🛑 損切りライン</div>
        <div style="font-size:28px;font-weight:800;color:var(--red)">${fmtPrice(stopPrice)}</div>
        <div style="font-size:12px;color:var(--muted);margin-top:4px">エントリーから -${stopPct}%｜即売り・例外なし</div>
      </div>
      <div style="background:var(--bg);border:1px solid var(--border);border-radius:10px;padding:16px">
        <div style="font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;margin-bottom:6px">📦 ポジションサイズ</div>
        <div style="font-size:28px;font-weight:800;color:var(--cyan)">¥${Math.round(positionAmount).toLocaleString('ja-JP')}</div>
        <div style="font-size:12px;color:var(--muted);margin-top:4px">リスク ¥${Math.round(riskAmount).toLocaleString()} (総資産の${riskPct}%)</div>
      </div>
    </div>

    <div style="background:var(--bg);border:1px solid var(--border);border-radius:10px;padding:16px;margin-bottom:12px">
      <div style="font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;margin-bottom:12px">🎯 利確目標</div>
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px">
        <div style="text-align:center;padding:10px;border-radius:8px;background:rgba(34,197,94,.05);border:1px solid rgba(34,197,94,.2)">
          <div style="font-size:11px;color:var(--muted);margin-bottom:4px">1R目標（+${stopPct}%）</div>
          <div style="font-size:18px;font-weight:700;color:var(--green)">${fmtPrice(r1)}</div>
          <div style="font-size:11px;color:var(--muted)">RR 1:1</div>
        </div>
        <div style="text-align:center;padding:10px;border-radius:8px;background:rgba(34,197,94,.1);border:1px solid rgba(34,197,94,.4)">
          <div style="font-size:11px;color:var(--muted);margin-bottom:4px">2R目標（+${stopPct*2}%）</div>
          <div style="font-size:18px;font-weight:700;color:var(--green)">${fmtPrice(r2)}</div>
          <div style="font-size:11px;color:var(--muted)">RR 1:2</div>
        </div>
        <div style="text-align:center;padding:10px;border-radius:8px;background:rgba(34,197,94,.15);border:1px solid var(--green)">
          <div style="font-size:11px;color:var(--muted);margin-bottom:4px">3R目標（+${stopPct*3}%）★保有継続</div>
          <div style="font-size:18px;font-weight:700;color:var(--green)">${fmtPrice(r3)}</div>
          <div style="font-size:11px;color:var(--muted)">RR 1:3</div>
        </div>
      </div>
    </div>

    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px">
      <div style="background:var(--bg);border:1px solid var(--border);border-radius:10px;padding:14px">
        <div style="font-size:11px;color:var(--muted);margin-bottom:6px">📉 トレーリングストップ</div>
        <div style="font-size:18px;font-weight:700">最高値から -15%</div>
        <div style="font-size:12px;color:var(--muted);margin-top:4px">現在価格基準: ${fmtPrice(trailStop)}</div>
      </div>
      <div style="background:var(--bg);border:1px solid var(--border);border-radius:10px;padding:14px">
        <div style="font-size:11px;color:var(--muted);margin-bottom:6px">⏱ タイムストップ</div>
        <div style="font-size:18px;font-weight:700">${timeStopStr}まで</div>
        <div style="font-size:12px;color:var(--muted);margin-top:4px">3週間で +5%動かなければ撤退</div>
      </div>
    </div>

    ${loanWarning}

    <div style="background:rgba(139,92,246,.08);border:1px solid rgba(139,92,246,.3);border-radius:10px;padding:14px;margin-top:12px;font-size:13px;line-height:1.8;color:var(--muted)">
      <strong style="color:var(--text)">チェックリスト（エントリー前）</strong><br>
      □ 損切り価格 ${fmtPrice(stopPrice)} を注文に入れた<br>
      □ ポジションサイズ ¥${Math.round(positionAmount).toLocaleString()} を確認した<br>
      □ タイムストップ ${timeStopStr} をカレンダーに入れた<br>
      □ ローン担保比率を確認した
    </div>`;
}

function updateModeUI() {
  const mode = document.querySelector('input[name=mode]:checked').value;
  const dipLabel = document.getElementById('mode-dip-label');
  const boLabel = document.getElementById('mode-bo-label');
  dipLabel.style.borderColor = mode === 'dip' ? 'var(--purple)' : 'var(--border)';
  boLabel.style.borderColor = mode === 'breakout' ? 'var(--cyan)' : 'var(--border)';
  // 押し目買いモードでのみRSIフィルター表示
  document.getElementById('rsi-max').parentElement.parentElement.style.opacity = mode === 'dip' ? '1' : '0.4';
}
updateModeUI();

function tvUrl(ticker, isJapan) {
  if (isJapan) {
    return `https://www.tradingview.com/chart/?symbol=TSE:${ticker.replace('.T', '')}`;
  }
  return `https://www.tradingview.com/chart/?symbol=${ticker}`;
}

function entryBadge(r) {
  const checks = [
    r.near_high_pct >= 98,
    r.vol_ratio >= 1.5,
    r.above_200ma,
    r.golden_cross,
    r.rsi >= 50 && r.rsi <= 75,
  ];
  const pass = checks.filter(Boolean).length;
  const tips = ['高値比98%+', '出来高×1.5+', '200MA上', 'GC', 'RSI50-75'];
  const detail = checks.map((ok, i) => `${ok ? '✅' : '❌'}${tips[i]}`).join(' ');
  if (pass === 5)
    return `<span title="${detail}" style="font-size:11px;background:rgba(34,197,94,.2);color:var(--green);padding:3px 9px;border-radius:10px;font-weight:800;cursor:help;white-space:nowrap">🚀 全クリア</span>`;
  if (pass >= 3)
    return `<span title="${detail}" style="font-size:11px;background:rgba(234,179,8,.1);color:var(--yellow);padding:3px 9px;border-radius:10px;font-weight:700;cursor:help">${pass}/5</span>`;
  return `<span title="${detail}" style="font-size:11px;background:rgba(239,68,68,.08);color:var(--red);padding:3px 9px;border-radius:10px;cursor:help">${pass}/5</span>`;
}

function renderScreenerResults(data, limit) {
  const container = document.getElementById('screen-results');
  if (!data.length) {
    container.innerHTML = '<div class="empty"><div class="big">😅</div>条件に合う銘柄がありませんでした。RSI上限や52週位置の条件を緩めてみてください。</div>';
    return;
  }
  const sliced = data.slice(0, limit);
  const allClear = sliced.filter(r => {
    const c = [r.near_high_pct>=98, r.vol_ratio>=1.5, r.above_200ma, r.golden_cross, r.rsi>=50&&r.rsi<=75];
    return c.every(Boolean);
  });
  const chips = `<div class="summary-chips">
    <span class="chip">📊 ${sliced.length}銘柄ヒット</span>
    <span class="chip">🏆 トップ: ${sliced[0].ticker}</span>
    ${allClear.length ? `<span class="chip" style="background:rgba(34,197,94,.2);color:var(--green);border-color:rgba(34,197,94,.4)">🚀 全クリア: ${allClear.map(r=>r.ticker).join(', ')}</span>` : ''}
  </div>`;
  const isBreakoutMode = sliced.length > 0 && sliced[0].near_high_pct != null;

  const rows = sliced.map((r, i) => {
    const chg1d = r.chg1d != null ? `<span class="${r.chg1d>=0?'chg-pos':'chg-neg'}">${r.chg1d>=0?'+':''}${r.chg1d}%</span>` : '-';
    const chg1m = r.chg1m != null ? `<span class="${r.chg1m>=0?'chg-pos':'chg-neg'}">${r.chg1m>=0?'+':''}${r.chg1m}%</span>` : '-';
    const ret1y = r.return_1y != null ? `<span class="${r.return_1y>=0?'chg-pos':'chg-neg'}">${r.return_1y>=0?'+':''}${r.return_1y}%</span>` : '-';
    const trendBadge = r.uptrend
      ? `<span style="font-size:11px;background:rgba(34,197,94,.15);color:#22c55e;padding:2px 7px;border-radius:10px;font-weight:700">📈右肩上がり</span>`
      : (r.above_200ma ? `<span style="font-size:11px;background:rgba(234,179,8,.1);color:#eab308;padding:2px 7px;border-radius:10px">△部分的</span>`
      : `<span style="font-size:11px;background:rgba(239,68,68,.1);color:#ef4444;padding:2px 7px;border-radius:10px">✗下降中</span>`);

    const cur = r.currency || '$';
    const priceStr = cur === '¥'
      ? `¥${r.price.toLocaleString('ja-JP', {maximumFractionDigits:0})}`
      : `$${r.price.toLocaleString()}`;
    const jpFlag = r.is_japan ? '🇯🇵 ' : '';
    const tickerLink = `<a href="${tvUrl(r.ticker, r.is_japan)}" target="_blank"
      style="color:inherit;text-decoration:none;border-bottom:1px dashed var(--muted);transition:color .15s"
      onmouseover="this.style.color='var(--cyan)'" onmouseout="this.style.color='inherit'"
      title="TradingViewで開く">${jpFlag}${r.ticker} <span style="font-size:10px;opacity:.5">↗</span></a>`;

    if (isBreakoutMode) {
      const boBadge = r.is_breakout
        ? `<span style="font-size:11px;background:rgba(6,182,212,.2);color:var(--cyan);padding:2px 8px;border-radius:10px;font-weight:700">🚀 ブレイク確認</span>`
        : `<span style="font-size:11px;background:rgba(139,92,246,.1);color:var(--purple);padding:2px 8px;border-radius:10px">🔜 接近中</span>`;
      const volBadge = r.vol_ratio >= 1.5
        ? `<span style="color:var(--cyan);font-weight:700">×${r.vol_ratio}</span>`
        : `<span style="color:var(--muted)">×${r.vol_ratio}</span>`;
      return `<tr>
        <td>${rankBadge(i+1)}</td>
        <td class="ticker-cell">${tickerLink}</td>
        <td>${entryBadge(r)}</td>
        <td>${boBadge}</td>
        <td>${priceStr}</td>
        <td style="color:var(--cyan);font-weight:700">${r.near_high_pct}%</td>
        <td class="${rsiClass(r.rsi)}">${r.rsi}</td>
        <td>${volBadge}</td>
        <td>${chg1d}</td>
        <td>${ret1y}</td>
        <td class="score-cell">${r.score}</td>
      </tr>`;
    } else {
      return `<tr>
        <td>${rankBadge(i+1)}</td>
        <td class="ticker-cell">${tickerLink}</td>
        <td>${entryBadge(r)}</td>
        <td>${trendBadge}</td>
        <td>${priceStr}</td>
        <td class="${rsiClass(r.rsi)}">${r.rsi}</td>
        <td>${r.pos52w}%</td>
        <td>${chg1d}</td>
        <td>${chg1m}</td>
        <td>${ret1y}</td>
        <td class="score-cell">${r.score}</td>
      </tr>`;
    }
  }).join('');

  const headers = isBreakoutMode
    ? `<th>#</th><th>ティッカー</th><th>エントリー</th><th>ステータス</th><th>現在価格</th><th>高値比</th><th>RSI</th><th>出来高比</th><th>1日%</th><th>1年%</th><th>スコア</th>`
    : `<th>#</th><th>ティッカー</th><th>エントリー</th><th>トレンド</th><th>現在価格</th><th>RSI</th><th>52W位置</th><th>1日%</th><th>1ヶ月%</th><th>1年%</th><th>スコア</th>`;

  container.innerHTML = chips + `
    <table class="results-table">
      <thead><tr>${headers}</tr></thead>
      <tbody>${rows}</tbody>
    </table>`;
}

// ─── バックテスト ───
function updateBtModeUI() {
  const mode = document.querySelector('input[name=bt-mode]:checked').value;
  document.getElementById('bt-mode-bo-label').style.borderColor  = mode === 'breakout' ? 'var(--cyan)'   : 'var(--border)';
  document.getElementById('bt-mode-dip-label').style.borderColor = mode === 'dip'       ? 'var(--purple)' : 'var(--border)';
  document.getElementById('bt-rsi-group').style.opacity = mode === 'dip' ? '1' : '0.4';
}
updateBtModeUI();

async function runBacktest() {
  const universes = [...document.querySelectorAll('input[name=bt-universe]:checked')].map(el => el.value);
  if (!universes.length) { alert('ユニバースを1つ以上選択してください'); return; }

  const btn    = document.getElementById('bt-btn');
  const status = document.getElementById('bt-status');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> 実行中...';
  status.style.display = 'block';
  status.textContent = '起動中...\\n';

  const payload = {
    universes,
    start_year:    parseInt(document.getElementById('bt-start-year').value),
    end_year:      parseInt(document.getElementById('bt-end-year').value),
    strategy:      document.querySelector('input[name=bt-mode]:checked').value,
    stop_pct:      parseFloat(document.getElementById('bt-stop').value),
    hold_days:     parseInt(document.getElementById('bt-hold').value),
    rsi_max:       parseFloat(document.getElementById('bt-rsi').value),
    market_filter: document.getElementById('bt-market-filter').checked,
  };

  try {
    const resp = await fetch('/run/backtest', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(payload)
    });
    const reader = resp.body.getReader();
    const dec = new TextDecoder();
    let buf = '';
    while (true) {
      const {done, value} = await reader.read();
      if (done) break;
      buf += dec.decode(value, {stream: true});
      const lines = buf.split('\\n');
      buf = lines.pop();
      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        const payload2 = line.slice(6);
        if (payload2 === '[DONE]') continue;
        try {
          const msg = JSON.parse(payload2);
          if (msg.log) { status.textContent += msg.log + '\\n'; status.scrollTop = status.scrollHeight; }
          if (msg.result) renderBacktestResults(msg.result.stats, msg.result.trades, payload);
        } catch(e) {}
      }
    }
  } catch(e) {
    status.textContent += 'エラー: ' + e.message;
  } finally {
    btn.disabled = false;
    btn.innerHTML = '📈 バックテスト実行';
  }
}

function renderBacktestResults(s, trades, cfg) {
  if (!s || s.total_trades === 0) {
    document.getElementById('bt-results').innerHTML = '<div class="empty"><div class="big">😅</div>シグナルが出た銘柄がありませんでした。条件を緩めてみてください。</div>';
    return;
  }

  const pf = s.profit_factor != null ? s.profit_factor : '-';
  const pfColor = s.profit_factor > 1.5 ? 'var(--green)' : s.profit_factor > 1.0 ? 'var(--yellow)' : 'var(--red)';
  const wrColor = s.win_rate >= 55 ? 'var(--green)' : s.win_rate >= 45 ? 'var(--yellow)' : 'var(--red)';
  const trColor = s.total_return >= 0 ? 'var(--green)' : 'var(--red)';
  const ddColor = s.max_drawdown > -20 ? 'var(--yellow)' : 'var(--red)';

  const statCards = `
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:20px">
      <div style="background:var(--card);border:1px solid var(--border);border-radius:10px;padding:16px">
        <div style="font-size:11px;color:var(--muted);margin-bottom:6px">総トレード数</div>
        <div style="font-size:28px;font-weight:800">${s.total_trades}</div>
        <div style="font-size:12px;color:var(--muted);margin-top:4px">損切: ${s.stop_exits}件 / 時間: ${s.time_exits}件</div>
      </div>
      <div style="background:var(--card);border:1px solid var(--border);border-radius:10px;padding:16px">
        <div style="font-size:11px;color:var(--muted);margin-bottom:6px">勝率</div>
        <div style="font-size:28px;font-weight:800;color:${wrColor}">${s.win_rate}%</div>
        <div style="font-size:12px;color:var(--muted);margin-top:4px">勝 ${s.total_trades - s.stop_exits}件 / 負 ${s.stop_exits}件</div>
      </div>
      <div style="background:var(--card);border:1px solid var(--border);border-radius:10px;padding:16px">
        <div style="font-size:11px;color:var(--muted);margin-bottom:6px">プロフィットファクター</div>
        <div style="font-size:28px;font-weight:800;color:${pfColor}">${pf}</div>
        <div style="font-size:12px;color:var(--muted);margin-top:4px">1.5以上が理想</div>
      </div>
      <div style="background:var(--card);border:1px solid var(--border);border-radius:10px;padding:16px">
        <div style="font-size:11px;color:var(--muted);margin-bottom:6px">平均リターン / トレード</div>
        <div style="font-size:28px;font-weight:800;color:${s.avg_return>=0?'var(--green)':'var(--red)'}">${s.avg_return>=0?'+':''}${s.avg_return}%</div>
        <div style="font-size:12px;color:var(--muted);margin-top:4px">勝: +${s.avg_win}% / 負: ${s.avg_loss}%</div>
      </div>
      <div style="background:var(--card);border:1px solid var(--border);border-radius:10px;padding:16px">
        <div style="font-size:11px;color:var(--muted);margin-bottom:6px">最大ドローダウン</div>
        <div style="font-size:28px;font-weight:800;color:${ddColor}">${s.max_drawdown}%</div>
        <div style="font-size:12px;color:var(--muted);margin-top:4px">-20%以内が目安（1%リスク/トレード想定）</div>
      </div>
      <div style="background:var(--card);border:1px solid var(--border);border-radius:10px;padding:16px">
        <div style="font-size:11px;color:var(--muted);margin-bottom:6px">累積リターン（全トレード）</div>
        <div style="font-size:28px;font-weight:800;color:${trColor}">${s.total_return>=0?'+':''}${s.total_return}%</div>
        <div style="font-size:12px;color:var(--muted);margin-top:4px">${cfg.start_year}〜${cfg.end_year}年 / 損切${cfg.stop_pct}% / ${cfg.hold_days}日保有<br>市場フィルター: ${s.market_filter ? '✅ ON（QQQ 200MA）' : '❌ OFF'} / 1%リスク想定</div>
      </div>
    </div>`;

  const top100 = trades.slice(0, 100);
  const rows = top100.map(t => {
    const retStr = `<span style="color:${t.win?'var(--green)':'var(--red)'};font-weight:700">${t.return_pct>=0?'+':''}${t.return_pct}%</span>`;
    const reason = t.exit_reason === 'stop_loss'
      ? `<span style="font-size:11px;color:var(--red)">🛑 損切</span>`
      : `<span style="font-size:11px;color:var(--muted)">⏱ 時間</span>`;
    const win = t.win
      ? `<span style="font-size:11px;background:rgba(34,197,94,.15);color:var(--green);padding:2px 7px;border-radius:8px">WIN</span>`
      : `<span style="font-size:11px;background:rgba(239,68,68,.1);color:var(--red);padding:2px 7px;border-radius:8px">LOSS</span>`;
    const cur = t.is_japan ? '¥' : '$';
    const tvLink = `<a href="${tvUrl(t.ticker, t.is_japan)}" target="_blank" style="color:inherit;text-decoration:none;border-bottom:1px dashed var(--muted)" onmouseover="this.style.color='var(--cyan)'" onmouseout="this.style.color='inherit'">${t.is_japan?'🇯🇵 ':''}${t.ticker}</a>`;
    return `<tr>
      <td class="ticker-cell">${tvLink}</td>
      <td style="color:var(--muted)">${t.entry_date}</td>
      <td style="color:var(--muted)">${t.exit_date}</td>
      <td>${cur}${t.entry_price.toLocaleString()}</td>
      <td>${cur}${t.exit_price.toLocaleString()}</td>
      <td>${retStr}</td>
      <td style="color:var(--muted)">${t.days_held}日</td>
      <td>${reason}</td>
      <td>${win}</td>
    </tr>`;
  }).join('');

  document.getElementById('bt-results').innerHTML = statCards + `
    <div class="card">
      <h2>トレードログ（直近${top100.length}件）</h2>
      <div style="overflow-x:auto">
        <table class="results-table">
          <thead><tr>
            <th>ティッカー</th><th>エントリー日</th><th>イグジット日</th>
            <th>買値</th><th>売値</th><th>リターン</th><th>保有日数</th><th>理由</th><th>結果</th>
          </tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </div>
    </div>`;
}

// ─── ローン計算（野村信託銀行ルール対応）───
// 強制売却トリガー：担保評価額 < 融資金額 × 70%
function calcLoan() {
  const asset = parseFloat(document.getElementById('asset-val').value);
  const loan = parseFloat(document.getElementById('loan-amt').value);
  const haircut = parseFloat(document.getElementById('haircut').value) / 100;
  const rate = parseFloat(document.getElementById('interest').value) / 100;

  // 担保評価額 = 株式評価額 × 掛け目
  const collateral = asset * haircut;
  // 野村の強制売却ライン：担保評価額 / 融資金額 < 70%
  const NOMURA_TRIGGER = 0.70;
  const currentRatio = (collateral / loan) * 100;

  // 強制売却が発動する株式評価額ライン
  // 担保評価額 = 融資金額 × 70%  →  株式評価額 × 掛け目 = 融資金額 × 70%
  // →  株式評価額 = 融資金額 × 70% / 掛け目
  const forcedSaleAsset = (loan * NOMURA_TRIGGER) / haircut;
  const dropToForced = ((asset - forcedSaleAsset) / asset) * 100;

  // 追加借入可能額（現在の担保評価額ベース）
  const available = Math.max(0, collateral - loan);
  const monthlyInterest = loan * rate / 12;
  const yearlyInterest = loan * rate;

  // 安全度バー：70%ライン基準でマッピング
  // currentRatio が 200%なら満タン、70%なら0
  const safetyPct = Math.min(100, Math.max(0, (currentRatio - 70) / (200 - 70) * 100));
  const safetyColor = currentRatio >= 150 ? '#22c55e' : currentRatio >= 100 ? '#eab308' : '#ef4444';
  const statusClass = currentRatio >= 150 ? 'safe' : currentRatio >= 100 ? 'warning' : 'danger';
  const statusLabel = currentRatio >= 150 ? '✅ 安全圏' : currentRatio >= 100 ? '⚠️ 要注意' : '🚨 強制売却リスク';

  document.getElementById('loan-results').innerHTML = `
    <div style="background:rgba(239,68,68,.08);border:1px solid rgba(239,68,68,.3);border-radius:10px;padding:14px 18px;margin-bottom:18px;font-size:13px;color:#fca5a5;line-height:1.7">
      ⚠️ <strong>野村信託銀行ルール</strong>：担保評価額が融資金額の<strong>70%を下回ると強制売却</strong>。不足額は即時返済義務あり。
    </div>
    <div class="loan-grid">
      <div class="loan-result-card ${statusClass}">
        <div class="loan-label">現在の担保比率（担保評価額 / 融資金額）</div>
        <div class="loan-value big" style="color:${safetyColor}">${currentRatio.toFixed(1)}%</div>
        <div class="loan-sub">${statusLabel}（<strong>70%以下で強制売却</strong>）</div>
        <div class="safety-bar-wrap">
          <div class="safety-bar-label"><span>🚨 70%（強制売却）</span><span>✅ 安全</span></div>
          <div class="safety-bar"><div class="safety-bar-fill" style="width:${safetyPct}%;background:${safetyColor}"></div></div>
        </div>
      </div>
      <div class="loan-result-card ${dropToForced < 15 ? 'danger' : dropToForced < 30 ? 'warning' : 'safe'}">
        <div class="loan-label">🚨 強制売却まであと</div>
        <div class="loan-value" style="color:${dropToForced<15?'var(--red)':dropToForced<30?'var(--yellow)':'var(--green)'}">${dropToForced.toFixed(1)}%下落</div>
        <div class="loan-sub">評価額が ¥${forcedSaleAsset.toLocaleString('ja-JP', {maximumFractionDigits:0})} を下回ると強制売却発動</div>
      </div>
      <div class="loan-result-card">
        <div class="loan-label">追加借入可能額</div>
        <div class="loan-value">¥${available.toLocaleString('ja-JP', {maximumFractionDigits:0})}</div>
        <div class="loan-sub">担保評価額 ¥${collateral.toLocaleString('ja-JP', {maximumFractionDigits:0})} − 借入 ¥${loan.toLocaleString()}</div>
      </div>
      <div class="loan-result-card">
        <div class="loan-label">利息コスト</div>
        <div class="loan-value">¥${monthlyInterest.toLocaleString('ja-JP', {maximumFractionDigits:0})}<span style="font-size:16px;color:var(--muted)">/月</span></div>
        <div class="loan-sub">年間 ¥${yearlyInterest.toLocaleString('ja-JP', {maximumFractionDigits:0})}（年利 ${(rate*100).toFixed(1)}%）</div>
      </div>
    </div>
    <hr class="divider">
    <div class="loan-grid">
      <div class="loan-result-card">
        <div class="loan-label">入力内容の確認</div>
        <div style="font-size:13px;line-height:2;color:var(--muted)">
          株式評価額：¥${asset.toLocaleString()}<br>
          借入額：¥${loan.toLocaleString()}<br>
          担保掛け目：${(haircut*100).toFixed(0)}%<br>
          年利：${(rate*100).toFixed(1)}%
        </div>
      </div>
      <div class="loan-result-card">
        <div class="loan-label">📉 下落シナリオ別 担保比率（強制売却ライン：70%）</div>
        <div style="font-size:13px;line-height:2">
          ${[-10,-20,-30,-40,-50].map(pct => {
            const newAsset = asset * (1 + pct/100);
            const newRatio = (newAsset * haircut / loan * 100).toFixed(0);
            const isForcedSale = newRatio < 70;
            const color = newRatio >= 150 ? '#22c55e' : newRatio >= 100 ? '#eab308' : newRatio >= 70 ? '#f97316' : '#ef4444';
            const tag = isForcedSale ? ' ← 🚨強制売却' : '';
            return `<span style="color:${color}">資産${pct}%落：担保比率 ${newRatio}%${tag}</span>`;
          }).join('<br>')}
        </div>
      </div>
    </div>`;
}
</script>
</body>
</html>"""


from screener import screen as run_screen
from backtest import run_backtest


@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/run/screen", methods=["POST"])
def api_screen():
    data = request.json
    universes = data.get("universes", ["qqq"])
    rsi_max = float(data.get("rsi_max", 60))
    pos52w_max = float(data.get("pos52w_max", 100))
    limit = int(data.get("limit", 20))
    uptrend_only = bool(data.get("uptrend_only", False))
    mode = data.get("mode", "dip")

    def generate():
        mode_label = "🚀 新高値ブレイク" if mode == "breakout" else "📉 押し目買い"
        yield f'data: {json.dumps({"log": f"🔬 スクリーニング開始 [{mode_label}]"})}\n\n'
        trend_label = "右肩上がりのみ" if uptrend_only else "全銘柄"
        log = f"対象: {universes}  {trend_label}"
        yield f'data: {json.dumps({"log": log})}\n\n'
        try:
            results = run_screen(universes, rsi_max=rsi_max, pos52w_max=pos52w_max,
                                 uptrend_only=uptrend_only, mode=mode)
            log = f"✅ {len(results)}銘柄ヒット（上位{min(limit, len(results))}件表示）"
            yield f'data: {json.dumps({"log": log})}\n\n'
            yield f'data: {json.dumps({"results": results[:limit]})}\n\n'
        except Exception as e:
            yield f'data: {json.dumps({"log": f"エラー: {str(e)}"})}\n\n'
        yield "data: [DONE]\n\n"

    return app.response_class(
        generate(),
        mimetype="text/event-stream",
        headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"},
    )


@app.route("/run/backtest", methods=["POST"])
def api_backtest():
    data       = request.json
    universes     = data.get("universes", ["qqq"])
    start_year    = int(data.get("start_year", 2021))
    end_year      = int(data.get("end_year", 2025))
    strategy      = data.get("strategy", "breakout")
    stop_pct      = float(data.get("stop_pct", 7.0))
    hold_days     = int(data.get("hold_days", 20))
    rsi_max       = float(data.get("rsi_max", 55.0))
    market_filter = bool(data.get("market_filter", True))

    def generate():
        logs = []
        def log_fn(msg):
            logs.append(msg)

        mode_label = "🚀 新高値ブレイク" if strategy == "breakout" else "📉 押し目買い"
        yield f'data: {json.dumps({"log": f"📈 バックテスト開始 [{mode_label}] {start_year}〜{end_year}年"})}\n\n'
        try:
            trades, stats = run_backtest(
                universes, start_year=start_year, end_year=end_year,
                strategy=strategy, stop_pct=stop_pct, hold_days=hold_days,
                rsi_max=rsi_max, market_filter=market_filter, log_fn=log_fn,
            )
            for msg in logs:
                yield f'data: {json.dumps({"log": msg})}\n\n'
            yield f'data: {json.dumps({"result": {"stats": stats, "trades": trades}})}\n\n'
        except Exception as e:
            yield f'data: {json.dumps({"log": f"エラー: {str(e)}"})}\n\n'
        yield "data: [DONE]\n\n"

    return app.response_class(
        generate(),
        mimetype="text/event-stream",
        headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"},
    )


@app.route("/api/plan/fetch", methods=["POST"])
def api_plan_fetch():
    ticker = request.json.get("ticker", "").strip().upper()
    if not ticker:
        return jsonify({"error": "ティッカーを入力してください"}), 400
    try:
        import yfinance as yf
        from screener import is_uptrend, detect_breakout, calculate_rsi, get_52w_position, is_japan_ticker
        raw = yf.download(ticker, period="14mo", interval="1d", auto_adjust=True, progress=False)
        if raw.empty:
            return jsonify({"error": f"{ticker} のデータが取得できませんでした"}), 400
        close = raw["Close"].squeeze().dropna()
        volume = raw["Volume"].squeeze().dropna()
        if len(close) < 30:
            return jsonify({"error": "データが少なすぎます（30日未満）"}), 400
        current = float(close.iloc[-1])
        series_1y = close.iloc[-252:] if len(close) >= 252 else close
        high52 = float(series_1y.max())
        low52 = float(series_1y.min())
        rsi = calculate_rsi(close)
        pos52w = get_52w_position(current, low52, high52)
        trend = is_uptrend(close)
        bo = detect_breakout(close, volume)
        is_jp = is_japan_ticker(ticker)
        return jsonify({
            "ticker": ticker,
            "price": round(current, 0) if is_jp else round(current, 2),
            "rsi": rsi,
            "pos52w": pos52w,
            "high52": round(high52, 0) if is_jp else round(high52, 2),
            "low52": round(low52, 0) if is_jp else round(low52, 2),
            "is_japan": is_jp,
            "currency": "¥" if is_jp else "$",
            **trend,
            **bo,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400


if __name__ == "__main__":
    def open_browser():
        time.sleep(1.0)
        webbrowser.open("http://localhost:5051")

    threading.Thread(target=open_browser, daemon=True).start()
    print("=" * 50)
    print("📈 Playgic Investment Tools")
    print("   ブラウザで開きます → http://localhost:5051")
    print("   終了するには Ctrl+C")
    print("=" * 50)
    app.run(port=5051, debug=False)
