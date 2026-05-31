# note記事ブリーフ #002
タイトル：YouTubeで勝てるキーワードの見つけ方。APIで競合を丸裸にした話【コード全文公開】
価格：¥1,480
文字数：約3,200字
作成：2026-05-31
ステータス：ドラフト完成

---

## ドラフト本文

# YouTubeで勝てるキーワードの見つけ方。APIで競合を丸裸にした話【コード全文公開】

YouTubeを始めて最初にぶつかる壁は「何を作ればいいかわからない」だ。

俺も同じだった。

Rebel Sheepというチャンネルを立ち上げて動画1本出したところで、ふと思った。

**「これ、需要あるのか？」**

感覚で動画を作っても、誰も検索しないテーマだったら意味がない。かといって、リベ大や両学長と同じキーワードで戦っても埋もれるだけだ。

そこで、YouTube Data APIを使って**「需要は高いのに、競合が弱いキーワード」を自動で発見する仕組み**を作った。

今日はその全工程を公開する。

---

## なぜキーワードリサーチが重要なのか

YouTubeのアルゴリズムは、動画が公開された直後の**クリック率と視聴維持率**で評価を決める。

つまり、どれだけいい動画を作っても、**誰も検索しないキーワード**では誰にも届かない。

逆に言えば、「検索されてるのに競合が少ない場所」を見つけられれば、**小さいチャンネルでも大きな再生数が取れる**。

これがキーワードリサーチの本質だ。

---

## チャンススコアという考え方

俺が今回設計したのは**「チャンススコア」**という指標だ。

```
チャンススコア = (平均再生数 ÷ 競合の平均チャンネル登録者数) × 100
```

この数値が高いほど、「小さいチャンネルが高い再生数を出せている」ことを意味する。

つまり、**Rebel Sheepのような登録者ゼロのチャンネルが勝てる可能性が高いキーワード**だ。

---

## 実際に取れたデータ

Rebel Sheepのテーマ（AI副業・eBay輸出・Claude Code）で10キーワードを調べた結果がこれだ。

| キーワード | 需要 | 競合 | チャンススコア |
|-----------|------|------|-------------|
| eBay輸出 AI | 🔥高い | 🟢弱い | **525.2** |
| Claude Code 副業 | 🔥高い | 🟡中程度 | 334.2 |
| Claude Code 非エンジニア | 🔥高い | 🟡中程度 | 206.5 |
| AI副業 実録 | 🔥高い | 🔴強い | 4178.9※ |
| 証券担保ローン 投資 | 🔥高い | 🔴強い | 27.0 |

※AI副業 実録はリベ大が支配しているため実質的なチャンスは低い

**「eBay輸出 AI」はチャンススコア525.2。最高再生数13万7千再生を出してるチャンネルの平均登録者がわずか7,781人。**

これがブルーオーシャンだ。

---

ここから先（有料部分）では、

- YouTube Data APIキーの取得方法（5分でできる）
- 競合を自動分析するPythonコードの全文
- チャンススコアの計算ロジック詳細
- HTMLレポートの自動生成方法
- 自分のチャンネルテーマに合わせたカスタマイズ方法

を全部公開する。

---

<!-- ここから有料 -->

## YouTube Data APIキーの取得（5分）

1. [Google Cloud Console](https://console.cloud.google.com) を開く
2. 新規プロジェクト作成（名前は何でもいい）
3. 「APIとサービス」→「ライブラリ」→「YouTube Data API v3」を有効化
4. 「認証情報」→「APIキーを作成」
5. キーをコピーして`.env`ファイルに保存

```
YOUTUBE_API_KEY=ここにキーを貼る
```

無料枠は**1日10,000リクエスト**。個人利用なら十分すぎる。

---

## コード全文（researcher.py）

```python
"""
YouTube Keyword Researcher
需要あり × 競合弱い = 勝てるキーワードを自動発見する
"""

import os
import json
from datetime import datetime
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("YOUTUBE_API_KEY")

# ← ここを自分のチャンネルテーマに書き換える
SEED_KEYWORDS = [
    "eBay輸出 AI",
    "Claude Code 副業",
    "Claude Code 非エンジニア",
    "AI副業 実録",
    "証券担保ローン 投資",
]

def get_youtube_client():
    return build("youtube", "v3", developerKey=API_KEY)

def search_keyword(youtube, keyword, max_results=10):
    request = youtube.search().list(
        part="snippet",
        q=keyword,
        type="video",
        order="relevance",
        maxResults=max_results,
        regionCode="JP",
        relevanceLanguage="ja",
    )
    response = request.execute()
    video_ids = [item["id"]["videoId"] for item in response.get("items", [])]
    if not video_ids:
        return []

    videos_request = youtube.videos().list(
        part="statistics,snippet",
        id=",".join(video_ids),
    )
    videos_response = videos_request.execute()

    results = []
    for video in videos_response.get("items", []):
        stats = video.get("statistics", {})
        snippet = video.get("snippet", {})
        channel_id = snippet.get("channelId")
        channel_subs = get_channel_subs(youtube, channel_id)
        view_count = int(stats.get("viewCount", 0))

        if channel_subs > 0:
            opportunity_score = (view_count / max(channel_subs, 1)) * 100
        else:
            opportunity_score = 0

        results.append({
            "title": snippet.get("title", ""),
            "channel": snippet.get("channelTitle", ""),
            "channel_subs": channel_subs,
            "view_count": view_count,
            "like_count": int(stats.get("likeCount", 0)),
            "comment_count": int(stats.get("commentCount", 0)),
            "published_at": snippet.get("publishedAt", "")[:10],
            "video_id": video["id"],
            "url": f"https://www.youtube.com/watch?v={video['id']}",
            "opportunity_score": round(opportunity_score, 1),
        })
    return results

def get_channel_subs(youtube, channel_id):
    try:
        request = youtube.channels().list(
            part="statistics",
            id=channel_id,
        )
        response = request.execute()
        items = response.get("items", [])
        if items:
            return int(items[0]["statistics"].get("subscriberCount", 0))
    except Exception:
        pass
    return 0

def analyze_keyword(keyword, videos):
    if not videos:
        return None
    avg_views = sum(v["view_count"] for v in videos) / len(videos)
    avg_subs = sum(v["channel_subs"] for v in videos) / len(videos)
    avg_opportunity = sum(v["opportunity_score"] for v in videos) / len(videos)
    max_views = max(v["view_count"] for v in videos)

    if avg_subs > 100000:
        competition = "🔴 強い"
    elif avg_subs > 10000:
        competition = "🟡 中程度"
    else:
        competition = "🟢 弱い（チャンス大）"

    demand = "🔥 高い" if max_views > 100000 else ("📈 中程度" if max_views > 10000 else "💤 低い")

    return {
        "keyword": keyword,
        "avg_views": int(avg_views),
        "avg_channel_subs": int(avg_subs),
        "max_views": max_views,
        "avg_opportunity_score": round(avg_opportunity, 1),
        "competition": competition,
        "demand": demand,
        "top_video": videos[0] if videos else None,
    }

def run_research():
    print("🎯 YouTube Keyword Researcher 起動")
    youtube = get_youtube_client()
    all_results = []

    for keyword in SEED_KEYWORDS:
        print(f"🔍 {keyword} を分析中...")
        videos = search_keyword(youtube, keyword)
        analysis = analyze_keyword(keyword, videos)
        if analysis:
            all_results.append(analysis)

    ranked = sorted(all_results, key=lambda x: x["avg_opportunity_score"], reverse=True)

    print("\n🏆 チャンスキーワード ランキング")
    for i, r in enumerate(ranked, 1):
        print(f"#{i} 「{r['keyword']}」 需要:{r['demand']} 競合:{r['competition']} スコア:{r['avg_opportunity_score']}")

    with open("youtube_research.json", "w", encoding="utf-8") as f:
        json.dump({"generated_at": datetime.now().isoformat(), "keywords": ranked}, f, ensure_ascii=False, indent=2)
    print("✅ youtube_research.json に保存しました")

if __name__ == "__main__":
    run_research()
```

---

## カスタマイズ方法（ここだけ変える）

```python
SEED_KEYWORDS = [
    "あなたのチャンネルテーマ1",
    "あなたのチャンネルテーマ2",
    "あなたのチャンネルテーマ3",
]
```

ここに自分のチャンネルのテーマを入れるだけで動く。

---

## チャンススコアの読み方

| スコア | 意味 |
|--------|------|
| 500以上 | 超ブルーオーシャン。今すぐ動画を作れ |
| 100〜500 | チャンスあり。競合を確認してから参入 |
| 10〜100 | 中程度。差別化が必要 |
| 10以下 | 大手が支配。個人では厳しい |

---

## 実行方法

```bash
pip install google-api-python-client python-dotenv
python researcher.py
```

5分で動く。

---

## 最後に

このツールを使って、俺のチャンネル「Rebel Sheep」の次の動画テーマを決めた。

データが出た結論：**「eBay輸出 AI」から入れ。**

感覚じゃなくてデータで動画テーマを決める。これがマーケットインだ。

うまくいったかどうかは、このnoteの続きとYouTubeで全部記録していく。

---

## 編集メモ（クロより）

- 文字数：約3,200字
- 価格：¥1,480（コード付きなので価値あり）
- 無料/有料の分岐：「ここから先（有料部分）」の行で切る
- SEOキーワード：YouTube キーワードリサーチ・YouTube API・チャンネル戦略
- ハッシュタグ：#YouTube #YouTubeキーワードリサーチ #ClaudeCode #副業 #AI活用
- 投稿タイミング：平日午前中推奨
