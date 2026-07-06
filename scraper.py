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
    rss_urls = [
        "https://rss.itmedia.co.jp/rss/2.0/aiplus.xml"
    ]
    
    articles = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    for url in rss_urls:
        try:
            res = requests.get(url, timeout=15, headers=headers)
            if res.status_code != 200 or not res.content: continue
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
                    if tag_name == 'title' and elem.text: current_item['title'] = elem.text.strip()
                    elif tag_name == 'link' and elem.text: current_item['url'] = elem.text.strip()
            if current_item and current_item.get('title') and current_item.get('url'):
                articles.append(current_item)
        except Exception as e: continue
            
    print(f"📊 配信可能な合計記事数: {len(articles)} 件")
    if not articles: return
        
    success_count = 0
    for article in articles[:3]:
        try:
            existing = supabase.table("adtech_news").select("id").eq("url", article['url']).execute()
            if existing.data: continue

            print(f"🔍 営業特化AI分析中: {article['title'][:15]}...")
            
            # 🔥 SABC重要度、機会・課題、営業アプローチを導き出す超強力プロンプト
            prompt = f"""
            以下のニュースを読み、AJA AdTech（incrie, ミエルTV, AJA SSP, AVP, MITA）のビジネス・営業観点で深く分析し、指定のフォーマットのみで出力してください。

            【ニュースタイトル】: {article['title']}

            【分析ルール】
            1. 重要度: AJAおよびアドテク市場に与える影響度を [S, A, B, C] の4段階から1つ厳選。
            2. AJAの機会: このニュースを追い風に、AJAのプロダクト（インクリーやミエルTVなど）がシェアを拡大できるチャンス。
            3. AJAの課題: 競合の台頭や技術変化により、AJAが直面するリスクや対策すべき障壁。
            4. クライアントの要求: 広告主やメディアが今求めている本音やニーズ。
            5. 提案営業方法: AJAの営業担当として、クライアントにどうアプローチし、どの製品をどう提案すべきかの具体的な営業トークや施策。
            6. カテゴリ: [自社プロダクト / 競合企業情報 / 市況・市場変化 / その他トレンド] から1つ。
            7. 関連製品: [incrie / ミエルTV / AJA SSP / AJA VideoPlatform / MITA / なし] から1つ。

            【出力フォーマット】（余計な装飾や解説は一切含めず、この通りに出力してください）
            IMPORTANCE: (S、A、B、Cのいずれか1文字)
            SUMMARY: (ニュースの簡潔な要約)
            OPPORTUNITY: (AJAにとっての機会・チャンス)
            CHALLENGE: (AJAにとっての課題・懸念点)
            CLIENT_NEED: (クライアントが求めていること)
            PROPOSAL: (具体的な提案営業方法)
            CATEGORY: (カテゴリ名)
            PRODUCT: (関連製品名)
            """
            
            response = model.generate_content(prompt)
            lines = response.text.strip().split('\n')
            
            parsed = {
                "IMPORTANCE": "B", "SUMMARY": article['title'], "OPPORTUNITY": "なし", 
                "CHALLENGE": "なし", "CLIENT_NEED": "情報収集中", "PROPOSAL": "提案資料の作成",
                "CATEGORY": "その他トレンド", "PRODUCT": "なし"
            }
            
            for line in lines:
                for key in parsed.keys():
                    if line.startswith(f"{key}:"):
                        parsed[key] = line.replace(f"{key}:", "").strip()

            # 特製フォーマットにデータを結合して、既存のai_summaryに格納（フロントで分解して表示）
            combined_summary = f"||{parsed['IMPORTANCE']}||{parsed['SUMMARY']}||{parsed['OPPORTUNITY']}||{parsed['CHALLENGE']}||{parsed['CLIENT_NEED']}||{parsed['PROPOSAL']}"

            data = {
                "title": article['title'], 
                "url": article['url'], 
                "raw_content": parsed['CATEGORY'], 
                "ai_summary": combined_summary, # 🔥 特製パック
                "related_product": parsed['PRODUCT'], 
                "ai_tags": [parsed['IMPORTANCE'] + "ランク"]
            }
            
            supabase.table("adtech_news").insert(data).execute()
            success_count += 1
            print(f"🎉 保存成功: [{parsed['IMPORTANCE']}]ランク")
        except Exception as e:
            print(f"⚠️ エラー回避: {e}")
            continue

    print(f"✨ 処理完了。新規保存件数: {success_count}件")

if __name__ == "__main__":
    main()
