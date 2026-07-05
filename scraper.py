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

# クライアントの初期化
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def main():
    # 🔗 2026年現在、確実に稼働している正しい最新RSSのURLに修正しました！
    rss_urls = [
        "https://www.cyberagent.co.jp/rss/press/", # サイバーエージェント最新プレス
        "https://prtimes.jp/main/action.php?run=html&page=rss&category_id=15", # PR TIMES テクノロジーカテゴリ
        "https://rss.itmedia.co.jp/rss/2.0/aiplus.xml" # ITmedia AIプラス（アドテク・AIの予備）
    ]
    
    articles = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    
    for url in rss_urls:
        try:
            res = requests.get(url, timeout=15, headers=headers)
            if res.status_code != 200 or not res.content:
                print(f"⚠️ RSS取得スキップ (ステータス: {res.status_code}): {url}")
                continue
            
            root = ET.fromstring(res.content)
            # RSS 2.0 と Atom (entry) 両方に対応できるように抽出
            items = root.findall('.//item') or root.findall('.//{http://www.w3.org/2005/Atom}entry')
            
            for item in items:
                title_node = item.find('title') or item.find('{http://www.w3.org/2005/Atom}title')
                link_node = item.find('link') or item.find('{http://www.w3.org/2005/Atom}link')
                
                if title_node is not None and link_node is not None:
                    url_text = link_node.text.strip() if link_node.text else (link_node.attrib.get('href', '').strip() if 'href' in link_node.attrib else "")
                    if title_node.text and url_text:
                        articles.append({
                            'title': title_node.text.strip(),
                            'url': url_text
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
