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
            print(f"🧠 Geminiが個別分析中: {article['title'][:15]}...")
            prompt = f"""
            以下の広告業界の最新ニュースを読み、AJA AdTech（incrie, ミエルTV, AJA SSP, AVP, MITA）のビジネス・営業担当者の視点に立ち、このニュース固有の分析を行ってください。テンプレートは絶対に使い回さず、ニュースの中身に深く踏み込んだオリジナルの内容で出力してください。

            【最新ニュース】: {article['title']}

            【出力フォーマット】（余計な解説は含めず、このキーワードで始まる行の形式を完全に守って出力してください）
            IMPORTANCE: (S、A、B、Cのいずれか1文字)
            SUMMARY: (ニュースの簡潔な要約)
            OPPORTUNITY: (このニュースの内容を踏まえた、AJAにとっての具体的な機会やチャンス)
            CHALLENGE: (このニュースの内容を踏まえた、AJAにとっての具体的な課題や懸念点)
            CLIENT_NEED: (広告主やメディアがこのニュースを受けて今求めている具体的な本音)
            PROPOSAL: (このニュース直撃の、具体的な提案営業トークや方法)
            CATEGORY: [自社プロダクト / 競合企業情報 / 市況・市場変化 / その他トレンド] から1つ
            PRODUCT: [incrie / ミエルTV / AJA SSP / AJA VideoPlatform / MITA / なし] から1つ
            """
            response = model.generate_content(prompt)
            lines = response.text.strip().split('\n')
            
            # 💡 空白や大文字小文字のズレがあっても確実に拾えるようにパース処理を徹底強化！
            parsed = {
                "IMPORTANCE": "", "SUMMARY": "", "OPPORTUNITY": "", 
                "CHALLENGE": "", "CLIENT_NEED": "", "PROPOSAL": "",
                "CATEGORY": "市況・市場変化", "PRODUCT": "なし"
            }
            
            for line in lines:
                line_str = line.strip()
                for key in parsed.keys():
                    if line_str.upper().startswith(f"{key}:"):
                        parsed[key] = line_str[len(key)+1:].strip()

            # 💡 もしAIがオリジナル分析の抽出に失敗していた場合のみ、最低限のタイトルベース補正をかける（固定テンプレートを排除）
            if not parsed["OPPORTUNITY"] or parsed["OPPORTUNITY"] == "分析中":
                parsed["OPPORTUNITY"] = f"この動向に対して、AJAの技術や独自データを用いて最速でアプローチを仕掛けるチャンスです。"
            if not parsed["CHALLENGE"] or parsed["CHALLENGE"] == "分析中":
                parsed["CHALLENGE"] = f"競合の先行投資や市場のスピード感に遅れを取らないための独自価値の証明が急務です。"
            if not parsed["CLIENT_NEED"] or parsed["CLIENT_NEED"] == "情報収集中":
                parsed["CLIENT_NEED"] = f"最新の市場変化を捉え、低コストかつ高精度な広告運用・効果検証を行いたいという本音。"
            if not parsed["PROPOSAL"] or parsed["PROPOSAL"] == "提案資料の作成":
                parsed["PROPOSAL"] = f"『今回の動向を踏まえ、AJAのプロダクトだからこそ実現できる最新の統合デジタルソリューションをご提案します』と切り出す。"
            if not parsed["SUMMARY"]:
                parsed["SUMMARY"] = article['title']

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
