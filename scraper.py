# -*- coding: utf-8 -*-
import os
import json
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

def main():
    # 🔗 広告業界・アドテクの主要ニュース配信ルート
    rss_urls = [
        "https://rss.rssad.jp/rss/markezine/new/markezine.xml",     # MarkeZine
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
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    new_count = 0
    
    for url in rss_urls:
        try:
            res = requests.get(url, timeout=15, headers=headers)
            if res.status_code != 200 or not res.content: continue
            
            # 🛑 どんなRSS/Atom形式がきても柔軟にitem/entryを全探索するロジック
            root = ET.fromstring(res.content)
            
            # item（通常のRSS）と entry（Atom形式や博報堂など）の両方を網羅
            items = root.findall('.//{http://purl.org/rss/1.0/}item') or \
                    root.findall('.//item') or \
                    root.findall('.//{http://www.w3.org/2005/Atom}entry') or \
                    root.findall('.//entry')

            for item in items:
                title_elem = item.find('title') or item.find('{http://www.w3.org/2005/Atom}title')
                link_elem = item.find('link') or item.find('{http://www.w3.org/2005/Atom}link')
                
                if title_elem is None: continue
                title = title_elem.text.strip() if title_elem.text else ""
                
                # リンクURLの抽出（タグのテキスト、または href 属性から柔軟に取得）
                url_text = ""
                if link_elem is not None:
                    url_text = link_elem.text.strip() if link_elem.text else link_elem.attrib.get('href', '').strip()
                
                if not title or not url_text: continue
                if url_text in existing_urls: continue

                # 判定・要約の自動組み立てロジック（AJA特化型）
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

                # 構造化インサイトパック
                imp = "A" if "aja" in title_lower or "cm" in title_lower or "動画" in title_lower else "B"
                summary = f"{title}に関する、デジタル広告およびテレビCM領域の最新動向です。"
                opp = "大手メディアや競合の動きに対し、AJA独自のCTV配信技術（incrie）や地上波効果可視化（ミエルTV）を組み合わせた柔軟なプランニングで差別化し、新規獲得のチャンスです。"
                chg = "市場データ網の強化に対して、AJAが持つプレミアムメディアのマネタイズ実績やAI動画考査（AVP）のスピード感で対抗する必要があります。"
                need = "既存 of テレビCMの枠に縛られず、デジタルやCTVを統合して『本当に効果が出る運用型広告』を低コストかつリアルタイムで管理したいという強いニーズ。"
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
                
            print(f"✅ 解析完了: {url.split('/')[2]}（累計ターゲット数: {len(all_news)}件）")
        except Exception as e:
            print(f"⚠️ 読み込みエラー回避 ({url}): {e}")
            continue

    # 最大100件まで蓄積
    all_news = all_news[:100]
    
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(all_news, f, ensure_ascii=False, indent=2)
        
    print(f"✨ 処理完了。新着追加: {new_count}件（総蓄積数: {len(all_news)}件）")

if __name__ == "__main__":
    main()
