# -*- coding: utf-8 -*-
import os
import requests
import xml.etree.ElementTree as ET
import google.generativeai as genai
from supabase import create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

def main():
    # 🔗 2026年現在、アドテク市場・CA関連のニュースを最も拾える正しいURLに厳選！
    rss_urls = [
        "https://www.cyberagent.co.jp/rss/press/", # 自社（CA・AJA）情報
        "https://prtimes.jp/main/action.php?run=html&page=rss&category_id=15", # IT・特許・新技術（アドテク含む）
        "https://rss.itmedia.co.jp/rss/2.0/aiplus.xml" # AI市況・技術トレンド
    ]
    
    articles = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    for url in rss_urls:
        try:
            res = requests.get(url, timeout=15, headers=headers)
            if res.status_code != 200 or not res.content:
                continue
            
            root = ET.fromstring(res.content)
            all_elements = root.iter()
            
            current_item = None
            for elem in all_elements:
                tag_name = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
                if tag_name == 'item':
                    if current_item and current_item.get('title') and current_item.get('url'):
                        articles.append(current_item)
                    current_item = {'title': '', 'url': ''}
                if current_item is not None:
                    if tag_name == 'title' and elem.text:
                        current_item['title'] = elem.text.strip()
                    elif tag_name == 'link' and elem.text:
                        current_item['url'] = elem.text.strip()
            if current_item and current_item.get('title') and current_item.get('url'):
                articles.append(current_item)
        except Exception as e:
            continue
            
    print(f"📊 配信可能な合計記事数: {len(articles)} 件")
    if not articles: return
        
    success_count = 0
    # 最新の10件を厳選して濃く分析
    for article in articles[:10]:
        try:
            # すでに保存済みのURLはスキップ（重複防止）
            existing = supabase.table("adtech_news").select("id").eq("url", article['url']).execute()
            if existing.data:
                continue

            print(f"🔍 AI特化分析中: {article['title'][:15]}...")
            
            # 🔥 Geminiにタブ分け（カテゴリ）の判断を完全に叩き込むプロンプト
            prompt = f"""
            以下のニュースを読み、AJA AdTech（インクリー, ミエルTV, AJA SSP, AJA VideoPlatform, MITA）のビジネス観点で分析し、指定のフォーマットのみで出力してください。

            【ニュースタイトル】: {article['title']}

            【カテゴリ分類ルール】
            以下の条件から、最も適切なものを1つだけ選んで「CATEGORY:」に指定してください。
            - 自社プロダクト: サイバーエージェント、AJA、インクリー、ミエルTV、AJA SSP、AVP、MITAに関する新機能、リリース、成果。
            - 競合企業情報: 他の広告プラットフォーム、SSP/DSP、TVCM効果可視化ツールなどの競合他社の動き。
            - 市況・市場変化: CTV（コネクテッドTV）市場、運用型テレビCM、デジタル広告業界全体のデータ、規制、トレンド。
            - その他トレンド: 上記に当てはまらない一般的なAIやテクノロジーニュース。

            【製品分類ルール】
            関連するAJA製品を [incrie, ミエルTV, AJA SSP, AJA VideoPlatform, MITA, なし] から1つ選んで「PRODUCT:」に指定。

            【出力フォーマット】（これ以外の文字は一切出力しないでください）
            SUMMARY: (1行・80文字以内の日本語要約)
            CATEGORY: (自社プロダクト / 競合企業情報 / 市況・市場変化 / その他トレンド から1つ)
            PRODUCT: (製品名)
            TAGS: (キーワード3つ、カンマ区切り)
            """
            
            response = model.generate_content(prompt)
            lines = response.text.strip().split('\n')
            
            summary, category, product, tags = "", "その他トレンド", "なし", ["テック"]
            for line in lines:
                if line.startswith("SUMMARY:"): summary = line.replace("SUMMARY:", "").strip()
                elif line.startswith("CATEGORY:"): category = line.replace("CATEGORY:", "").strip()
                elif line.startswith("PRODUCT:"): product = line.replace("PRODUCT:", "").strip()
                elif line.startswith("TAGS:"): tags = [t.strip() for t in line.replace("TAGS:", "").split(",")]
            
            if not summary:
                summary = article['title']

            data = {
                "title": article['title'], 
                "url": article['url'], 
                "raw_content": category, # 👈 ここに「カテゴリ名」を逃がして保存し、フロントで使います！
                "ai_summary": summary, 
                "related_product": product, 
                "ai_tags": tags
            }
            
            supabase.table("adtech_news").insert(data).execute()
            success_count += 1
            print(f"🎉 保存成功: [{category}]")
        except Exception as e:
            print(f"⚠️ エラー回避: {e}")
            continue

    print(f"✨ 新規保存件数: {success_count}件")

if __name__ == "__main__":
    main()
