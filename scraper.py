# -*- coding: utf-8 -*-
import os
import json
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

def main():
    # 🔗 AJA・CAオウンドメディア・YouTube・専門メディアを網羅する最強ルート
    rss_urls = [
        "https://www.cyberagent.co.jp/rss/press/",                 # サイバーエージェント（公式発表）
        "https://rss.rssad.jp/rss/markezine/new/markezine.xml",     # MarkeZine（アドテク・X/市況トレンドの代用）
        "https://webtan.impress.co.jp/rss/all.xml",                # Web担当者Forum（デジタル広告）
        "https://prtimes.jp/main/action.php?run=html&page=rss&category_id=15" # PR TIMES（競合・アドベンダー）
    ]
    
    # 既存の蓄積データ（data.json）があれば読み込む
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
            
            root = ET.fromstring(res.content)
            current_item = None
            for elem in root.iter():
                tag_name = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
                if tag_name in ['item', 'entry']:
                    if current_item and current_item.get('title') and current_item.get('url'):
                        # 重複していなければ追加
                        if current_item['url'] not in existing_urls:
                            # 判定・要約の自動組み立てロジック（AJA特化型）
                            category = "市qz・市場変化"
                            product = "なし"
                            title_lower = current_item['title'].lower()
                            
                            if "サイバーエージェント" in title_lower or "aja" in title_lower or "cyberagent" in title_lower:
                                category = "自社プロダクト"
                                product = "incrie"
                            elif "電通" in title_lower or "博報堂" in title_lower:
                                category = "競合企業情報"
                                product = "ミエルTV"
                            elif "ai" in title_lower or "動画" in title_lower or "ctv" in title_lower:
                                category = "その他トレンド"

                            # 構造化インサイトパック
                            imp = "A" if "aja" in title_lower or "cm" in title_lower else "B"
                            summary = f"{current_item['title']}に関する、デジタル広告およびテレビCM領域の最新動向です。"
                            opp = "大手メディアや競合の動きに対し、AJA独自のCTV配信技術（incrie）や地上波効果可視化（ミエルTV）を組み合わせた柔軟なプランニングで差別化し、新規獲得のチャンスです。"
                            chg = "市場データ網の強化に対して、AJAが持つプレミアムメディアのマネタイズ実績やAI動画考査（AVP）のスピード感で対抗する必要があります。"
                            need = "既存のテレビCMの枠に縛られず、デジタルやCTVを統合して『本当に効果が出る運用型広告』を低コストかつリアルタイムで管理したいという強いニーズ。"
                            prop = "クライアントに対し、『他社にはないAJA独自のリアルタイム放送監視（MITA）と運用型テレビCMの連携で、広告効果を最大化しませんか』と切り出すストーリー提案が極めて有効です。"

                            combined_summary = f"||{imp}||{summary}||{opp}||{chg}||{need}||{prop}"
                            
                            news_entry = {
                                "title": current_item['title'],
                                "url": current_item['url'],
                                "raw_content": category,
                                "ai_summary": combined_summary,
                                "related_product": product,
                                "created_at": datetime.now().strftime("%Y-%m-%d")
                            }
                            all_news.insert(0, news_entry) # 最新を先頭に
                            existing_urls.add(current_item['url'])
                            new_count += 1
                            
                    current_item = {'title': '', 'url': ''}
                if current_item is not None:
                    if tag_name == 'title' and elem.text: current_item['title'] = elem.text.strip()
                    elif tag_name == 'link':
                        u = elem.text.strip() if elem.text else elem.attrib.get('href', '').strip()
                        if u: current_item['url'] = u
        except Exception as e:
            continue

    # 💡 データを100件までに制限して保存（ファイルが大きくなりすぎないように）
    all_news = all_news[:100]
    
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(all_news, f, ensure_ascii=False, indent=2)
        
    print(f"✨ 処理完了。新着追加: {new_count}件（総蓄積数: {len(all_news)}件）")

if __name__ == "__main__":
    main()
