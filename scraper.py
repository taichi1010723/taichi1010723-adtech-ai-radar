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
    # 確実に20件取得できているITmediaを先頭に、URLを少し調整してセット
    rss_urls = [
        "https://rss.itmedia.co.jp/rss/2.0/aiplus.xml",
        "https://www.cyberagent.co.jp/news/press/",
        "https://prtimes.jp/main/html/index.php"
    ]
    
    articles = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    for url in rss_urls:
        try:
            res = requests.get(url, timeout=15, headers=headers)
            if res.status_code != 200 or not res.content:
                continue
            
            # XMLを解析
            root = ET.fromstring(res.content)
            
            # どんな構造（名前空間）のRSSでも、とにかく「item」か「entry」をすべて探す柔軟な指定
            items = root.findall('.//item') or root.findall('.//*[{http://www.w3.org/2005/Atom}entry]') or root.findall('.//*')
            
            for item in items:
                # タグ名に「item」や「entry」が含まれている、または親がitemの場合に抽出
                tag_name = item.tag.lower()
                if 'item' in tag_name or 'entry' in tag_name:
                    # 子要素からタイトルとリンクを優しく、かつ確実に探す
                    title_node = item.find('title') or item.find('.//{http://www.w3.org/2005/Atom}title') or item.find('text')
                    link_node = item.find('link') or item.find('.//{http://www.w3.org/2005/Atom}link')
                    
                    title_text = title_node.text.strip() if title_node is not None and title_node.text else ""
                    url_text = ""
                    if link_node is not None:
                        url_text = link_node.text.strip() if link_node.text else link_node.attrib.get('href', '').strip()
                    
                    if title_text and url_text:
                        # 重複を防ぎつつ追加
                        if not any(a['url'] == url_text for a in articles):
                            articles.append({'title': title_text, 'url': url_text})
                            
            print(f"✅ RSS解析完了 ({url}): 現在の合計キープ件数 {len(articles)}件")
        except Exception as e:
            print(f"⚠️ RSS読み込みスキップ ({url}): {e}")
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
