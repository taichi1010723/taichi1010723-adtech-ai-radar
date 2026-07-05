# -*- coding: utf-8 -*-
import os
import requests
import xml.etree.ElementTree as ET
import google.generativeai as genai
from supabase import create_client

# 環境変数の読み込み
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# 確実に動く互換ライブラリで初期化
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def main():
    # 複数のニュースソースを用意（片方がエラーでも、もう片方から取得できるように対策）
    rss_urls = [
        "https://www.cyberagent.co.jp/news/press/rss.xml",
        "https://prtimes.jp/technology/main/action.php?run=html&page=rss"
    ]
    
    articles = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    for url in rss_urls:
        try:
            res = requests.get(url, timeout=15, headers=headers)
            if res.status_code != 200 or not res.content:
                print(f"⚠️ RSS取得スキップ (ステータス: {res.status_code}): {url}")
                continue
            
            # 前回エラーになったパース部分を完全に保護
            root = ET.fromstring(res.content)
            items = root.findall('.//item')
            
            for item in items:
                title_node = item.find('title')
                link_node = item.find('link')
                
                if title_node is not None and link_node is not None:
                    articles.append({
                        'title': title_node.text.strip() if title_node.text else "",
                        'url': link_node.text.strip() if link_node.text else ""
                    })
            print(f"✅ RSS解析成功 ({url}): {len(items)}件見つかりました")
        except Exception as e:
            print(f"⚠️ RSS読み込みエラーをスキップ ({url}): {e}")
            continue
            
    print(f"📊 配信可能な合計記事数: {len(articles)} 件")
    
    if not articles:
        print("❌ ニュースを1件も解析できませんでした。処理を終了します。")
        return
        
    # 最新の3件をAI分析して保存
    success_count = 0
    for article in articles[:3]:
        try:
            if not article['title'] or not article['url']:
                continue
                
            print(f"🔍 AI分析中: {article['title'][:15]}...")
            
            prompt = f"「{article['title']}」を1行(80文字以内)で要約し、SUMMARY: (要約) のフォーマットのみで出力して。"
            response = model.generate_content(prompt)
            summary = response.text.replace("SUMMARY:", "").strip()
            
            data = {
                "title": article['title'], 
                "url": article['url'], 
                "raw_content": article['title'], 
                "ai_summary": summary, 
                "related_product": "その他", 
                "ai_tags": ["テック"]
            }
            
            supabase.table("adtech_news").insert(data).execute()
            success_count += 1
            print("🎉 Supabaseへ保存成功")
        except Exception as item_error:
            print(f"⚠️ 記事の保存に失敗: {item_error}")
            continue

    print(f"✨ 処理完了。新規保存件数: {success_count}件")

if __name__ == "__main__":
    main()
