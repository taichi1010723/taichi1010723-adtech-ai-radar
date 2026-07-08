# -*- coding: utf-8 -*-
import os
import json
import requests
import xml.etree.ElementTree as ET
import google.generativeai as genai
from datetime import datetime

def main():
    # 環境変数の読み込み（Gemini APIを再起動！）
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY が設定されていません。ActionsのSettingsからSecretを確認してください。")
        return
        
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')

    # 🔗 検索ワードの末尾に「 when:1d 」を追加！これで【過去24時間以内の超最新ニュース】だけを指定してぶち抜きます
    rss_urls = [
        "https://news.google.com/rss/search?q=サイバーエージェント+OR+AJA+アドテク+when:1d&hl=ja&gl=JP&ceid=JP:ja",
        "https://news.google.com/rss/search?q=電通+広告+OR+マーケティング+when:1d&hl=ja&gl=JP&ceid=JP:ja",
        "https://news.google.com/rss/search?q=博報堂+広告+when:1d&hl=ja&gl=JP&ceid=JP:ja",
        "https://news.google.com/rss/search?q=運用型CM+OR+CTV+動画広告+when:1d&hl=ja&gl=JP&ceid=JP:ja"
    ]
    
    json_file = "data.json"
    if os.path.exists(json_file):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                all_news = json.load(f)
        except:
            all_news = []
    else:
        all_news = []

    existing_urls = {item["url"] for item in all_news}
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    raw_articles = []
    
    # 1. 24時間以内のニュースをスキャン
    for url in rss_urls:
        try:
            res = requests.get(url, timeout=15, headers=headers)
            if res.status_code != 200 or not res.content: continue
                
            root = ET.fromstring(res.content)
            items = root.findall('.//item')

            for item in items:
                title_elem = item.find('title')
                link_elem = item.find('link')
                if title_elem is None or link_elem is None: continue
                
                title = title_elem.text.strip() if title_elem.text else ""
                url_text = link_elem.text.strip() if link_elem.text else ""
                
                if title and url_text and url_text not in existing_urls:
                    raw_articles.append({"title": title, "url": url_text})
        except Exception as e:
            continue

    print(f"📊 本日（24時間以内）に発表された広告業界の最新ニュース: {len(raw_articles)} 件")
    
    if not raw_articles:
        print("✨ 本日は新しいニュースがありませんでした。処理を終了します。")
        return
        
    new_count = 0
    # 2. 🔥 最新ニュースの上位「最大5件」に対して、Geminiにガチで1件ずつ個別分析させる！
    for article in raw_articles:
        if new_count >= 5: # 無料枠20回のうち5回だけ贅沢に消費
            break
            
        try:
            print(f"🧠 Geminiが最新ニュースを本気で個別分析中: {article['title'][:15]}...")
            
            prompt = f"""
            以下の広告業界の【超最新ニュース】を読み、AJA AdTech（incrie, ミエルTV, AJA SSP, AVP, MITA）のビジネス・営業担当者の視点に立ち、このニュース固有のリアルな分析を行ってください。
            定型文やテンプレートは絶対に使い回さず、ニュースの内容に深く踏み込んだ具体的な営業提案を導き出してください。

            【最新ニュース】: {article['title']}

            【分析ルール】
            1. 重要度: AJAおよびアドテク市場に与える影響度を [S, A, B, C] の4段階から1つ厳選。
            2. AJAの機会: この最新動向に対して、AJAのプロダクト（インクリーやミエルTVなど）がどう攻め込めるか、リプレイスできるチャンス。
            3. AJAの課題: 競合の動きや技術変化により、AJAが直面するリスクや対策すべき障壁。
            4. クライアントの要求: 広告主やメディアがこのニュースを受けて今求めている本音やニーズ。
            5. 提案営業方法: AJAの営業として、どの製品をどう提案すべきか、ニュースの内容に沿った具体的な営業トークや施策。
            6. カテゴリ: [自社プロダクト / 競合企業情報 / 市況・市場変化 / その他トレンド] から1つ。
            7. 関連製品: [incrie / ミエルTV / AJA SSP / AJA VideoPlatform / MITA / なし] から1つ。

            【出力フォーマット】（余計な解説は一切含めず、この通りに出力してください）
            IMPORTANCE: (S、A、B、Cのいずれか1文字)
            SUMMARY: (ニュースの簡潔な要約)
            OPPORTUNITY: (ニュースを踏まえたAJAにとっての機会)
            CHALLENGE: (ニュースを踏まえたAJAにとっての課題)
            CLIENT_NEED: (クライアントが今求めている具体的な本音)
            PROPOSAL: (ニュース直撃の具体的な提案営業トークや方法)
            CATEGORY: (カテゴリ名)
            PRODUCT: (関連製品名)
            """
            
            response = model.generate_content(prompt)
            lines = response.text.strip().split('\n')
            
            parsed = {
                "IMPORTANCE": "B", "SUMMARY": article['title'], "OPPORTUNITY": "分析中", 
                "CHALLENGE": "分析中", "CLIENT_NEED": "情報収集中", "PROPOSAL": "提案資料の作成",
                "CATEGORY": "市況・市場変化", "PRODUCT": "なし"
            }
            
            for line in lines:
                for key in parsed.keys():
                    if line.startswith(f"{key}:"):
                        parsed[key] = line.replace(f"{key}:", "").strip()

            combined_summary = f"||{parsed['IMPORTANCE']}||{parsed['SUMMARY']}||{parsed['OPPORTUNITY']}||{parsed['CHALLENGE']}||{parsed['CLIENT_NEED']}||{parsed['PROPOSAL']}"
            
            news_entry = {
                "title": article['title'],
                "url": article['url'],
                "raw_content": parsed['CATEGORY'],
                "ai_summary": combined_summary,
                "related_product": parsed['PRODUCT'],
                "created_at": datetime.now().strftime("%Y-%m-%d")
            }
            all_news.insert(0, news_entry) # 最新を一番上に
            new_count += 1
            
        except Exception as e:
            print(f"⚠️ 個別分析エラー回避: {e}")
            continue

    # 過去ログとして最大100件まで蓄積キープ
    all_news = all_news[:100]
    
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(all_news, f, ensure_ascii=False, indent=2)
        
    print(f"✨ 処理完了。本日のガチ新着: {new_count}件（総蓄積数: {len(all_news)}件）")

if __name__ == "__main__":
    main()
