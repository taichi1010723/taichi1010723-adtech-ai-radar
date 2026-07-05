# -*- coding: utf-8 -*-
import os, requests, google.generativeai as genai
import xml.etree.ElementTree as ET
from supabase import create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def main():
    res = requests.get("https://prtimes.jp/technology/main/action.php?run=html&page=rss", timeout=10)
    root = ET.fromstring(res.content)
    items = root.findall('.//item')
    print(f"取得件数: {len(items)}")
    
    for item in items[:3]:
        title = item.find('title').text
        url = item.find('link').text
        print(f"分析中: {title[:15]}")
        
        prompt = f"「{title}」を1行(80文字以内)で要約し、SUMMARY: (要約) のフォーマットのみで出力して。"
        response = model.generate_content(prompt)
        summary = response.text.replace("SUMMARY:", "").strip()
        
        data = {"title": title, "url": url, "raw_content": title, "ai_summary": summary, "related_product": "その他", "ai_tags": ["テック"]}
        supabase.table("adtech_news").insert(data).execute()
        print("🎉 Supabaseへ保存成功")

if __name__ == "__main__":
    main()
