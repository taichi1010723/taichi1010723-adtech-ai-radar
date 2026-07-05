# -*- coding: utf-8 -*-
import os
import requests
import xml.etree.ElementTree as ET
from google import genai
from supabase import create_client

# 環境変数の読み込み
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# クライアントの初期化（最新の google-genai ライブラリに対応）
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
ai_client = genai.Client(api_key=GEMINI_API_KEY)

def main():
    # 複数のRSSフィードを用意（片方がエラーでも、もう片方から取得できるように対策）
    rss_urls = [
        "https://prtimes.jp/technology/main/action.php?run=html&page=rss",
        "https://www.cyberagent.co.jp/news/press/rss.xml"
    ]
    
    items = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    for url in rss_urls:
        try:
            res = requests.get(url, timeout=15, headers=headers)
            if res.status_code == 200 and res.content:
                root = ET.fromstring(res.content)
                found_items = root.findall('.//item')
                if found_items:
                    items.extend(found_items)
                    print(f"✅ RSS取得成功 ({url}): {len(found_items)}件")
        except Exception as e:
            print(f"⚠️ RSS読み込みスキップ ({url}): {e}")
            continue
            
    print(f"📊 合計取得件数: {len(items)}")
    
    if not items:
        print("❌ ニュースを1件も取得できませんでした。処理を終了します。")
        return
        
    # 最新の3件をAI分析して保存
    for item in items[:3]:
        try:
            title_node = item.find('title')
            link_node = item.find('link')
            
            if title_node is None or link_node is None:
                continue
                
            title = title_node.text
            url = link_node.text
            print(f"🔍 AI分析中: {title[:15]}...")
            
            # 最新の生成AIモデル「gemini-2.5-flash」と推奨される呼び出し方に変更
            prompt = f"「{title}」を1行(80文字以内)で要約し、SUMMARY: (要約) のフォーマットのみで出力して。"
            response = ai_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            summary = response.text.replace("SUMMARY:", "").strip()
            
            data = {
                "title": title, 
                "url": url, 
                "raw_content": title, 
                "ai_summary": summary, 
                "related_product": "その他", 
                "ai_tags": ["テック"]
            }
            
            supabase.table("adtech_news").insert(data).execute()
            print("🎉 Supabaseへ保存成功")
        except Exception as item_error:
            print(f"⚠️ 記事の保存に失敗: {item_error}")
            continue

if __name__ == "__main__":
    main()
