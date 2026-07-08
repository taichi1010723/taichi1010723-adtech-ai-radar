# -*- coding: utf-8 -*-
import os
import json
import requests
import xml.etree.ElementTree as ET
import google.generativeai as genai
from datetime import datetime

def main():
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY が設定されていません。")
        return
        
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')

    # 過去24時間以内のニュースを検索
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
        except:
            continue

    print(f"📊 本日（24時間以内）の広告業界最新ニュース: {len(raw_articles)} 件")
    if not raw_articles:
        print("✨ 本日は新しいニュースがありませんでした。")
        return
        
    new_count = 0
    for article in raw_articles:
        if new_count >= 5: 
            break
        try:
            print(f"🧠 Gemini個別分析中: {article['title'][:15]}...")
            prompt = f"""
            以下の広告業界のニュースを読み、AJA AdTech（incrie, ミエルTV, AJA SSP, AVP, MITA）のビジネス・営業担当者の視点に立ち、このニュース固有の分析を行ってください。テンプレートは絶対に使わないでください。

            【最新ニュース】: {article['title']}

            【出力フォーマット】（余計な解説は含めず、この通りに出力してください）
            IMPORTANCE: (S、A、B、Cのいずれか1文字)
            SUMMARY: (ニュースの簡潔な要約)
            OPPORTUNITY: (AJAにとっての機会)
            CHALLENGE: (AJAにとっての課題)
            CLIENT_NEED: (クライアントが今求めている具体的な本音)
            PROPOSAL: (ニュースを踏まえた具体的な提案営業方法)
            CATEGORY: [自社プロダクト / 競合企業情報 / 市況・市場変化 / その他トレンド] から1つ
            PRODUCT: [incrie / ミエルTV / AJA SSP / AJA VideoPlatform / MITA / なし] から1つ
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
            all_news.insert(0, news_entry)
            new_count += 1
        except Exception as e:
            print(f"⚠️ エラー回避: {e}")
            continue

    all_news = all_news[:100]
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(all_news, f, ensure_ascii=False, indent=2)
    print(f"✨ 処理完了。ガチ新着: {new_count}件")

if __name__ == "__main__":
    main()
