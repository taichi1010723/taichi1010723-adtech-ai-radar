# -*- coding: utf-8 -*-
import os
import json
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

def main():
    # 🔗 広告業界・アドテクの主要ニュース配信ルート（URLを修正＆安定ルートに最適化）
    rss_urls = [
        "https://markezine.jp/rss/new/",                            # 🔥 MarkeZineの最新正しいURL
        "https://webtan.impress.co.jp/rss/all.xml",                # Web担当者Forum
        "https://www.cyberagent.co.jp/rss/press/",                 # サイバーエージェント
        "https://www.dentsu.co.jp/news/rss/press.xml",              # 電通グループ
        "https://www.hakuhodo.co.jp/news/pressrelease/feed",       # 博報堂
        "https://prtimes.jp/main/action.php?run=html&page=rss&category_id=15" # PR TIMES
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
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    
    new_count = 0
    
    for url in rss_urls:
        # 💡 各メディアごとに完全に独立して処理。1つがエラーになっても他へ絶対に影響させない！
        try:
            print(f"📡 接続テスト中: {url.split('/')[2]}")
            res = requests.get(url, timeout=10, headers=headers)
            if res.status_code != 200 or not res.content:
                print(f"⚠️ ステータスコード異常によりパス: {res.status_code}")
                continue
            
            root = ET.fromstring(res.content)
            
            # 各種RSS/Atomの階層タグを徹底探索
            items = root.findall('.//{http://purl.org/rss/1.0/}item') or \
                    root.findall('.//item') or \
                    root.findall('.//{http://www.w3.org/2005/Atom}entry') or \
                    root.findall('.//entry')

            media_success_count = 0
            for item in items:
                title_elem = item.find('title') or item.find('{http://www.w3.org/2005/Atom}title')
                link_elem = item.find('link') or item.find('{http://www.w3.org/2005/Atom}link')
                
                if title_elem is None: continue
                title = title_elem.text.strip() if title_elem.text else ""
                
                url_text = ""
                if link_elem is not None:
                    url_text = link_elem.text.strip() if link_elem.text else link_elem.attrib.get('href', '').strip()
                
                if not title or not url_text: continue
                if url_text in existing_urls: continue

                # AJA特化型のインサイト分類・判定ロジック
                category = "市況・市場変化"
                product = "なし"
                title_lower = title.lower()
                
                if "サイバーエージェント" in title_lower or "aja" in title_lower or "cyberagent" in title_lower:
                    category = "自社プロダクト"
                    product = "incrie"
                elif "電通" in title_lower or "博報堂" in title_lower:
                    category = "競合企業情報"
                    product = "ミエルTV"
                elif "ai" in title_lower or "動画" in title_lower or "ctv" in title_lower or "トレンド" in title_lower:
                    category = "その他トレンド"

                # 構造化インサイト生成
                imp = "A" if "aja" in title_lower or "cm" in title_lower or "動画" in title_lower else "B"
                summary = f"{title}に関する、デジタル広告およびテレビCM領域の最新動向です。"
                opp = "大手メディアや競合の動きに対し、AJA独自のCTV配信技術（incrie）や地上波効果可視化（ミエルTV）を組み合わせた柔軟なプランニングで差別化し、新規獲得のチャンスです。"
                chg = "市場データ網の強化に対して、AJAが持つプレミアムメディアのマネタイズ実績やAI動画考査（AVP）のスピード感で対抗する必要があります。"
                need = "既存のテレビCMの枠に縛られず、デジタルやCTVを統合して『本当に効果が出る運用型広告』を低コストかつリアルタイムで管理したいという強いニーズ。"
                prop = "クライアントに対し、『他社にはないAJA独自のリアルタイム放送監視（MITA）と運用型テレビCMの連携で、広告効果を最大化しませんか』と切り出すストーリー提案が極めて有効です。"

                combined_summary = f"||{imp}||{summary}||{opp}||{chg}||{need}||{prop}"
                
                news_entry = {
                    "title": title,
                    "url": url_text,
                    "raw_content": category,
                    "ai_summary": combined_summary,
                    "related_product": product,
                    "created_at": datetime.now().strftime("%Y-%m-%d")
                }
                all_news.insert(0, news_entry)
                existing_urls.add(url_text)
                new_count += 1
                media_success_count += 1
                
            print(f"✅ 解析完了: {url.split('/')[2]}（このメディアから {media_success_count}件 抽出）")
        except Exception as e:
            print(f"⚠️ このメディアの解析をスキップして次へ進みます ({url.split('/')[2]}): {e}")
            continue

    # 最大100件までデータをキープ
    all_news = all_news[:100]
    
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(all_news, f, ensure_ascii=False, indent=2)
        
    print(f"✨ 全処理完了。今回新しく追記された新着: {new_count}件（総蓄積数: {len(all_news)}件）")

if __name__ == "__main__":
    main()
