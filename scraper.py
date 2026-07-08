name: AdTech News Auto Scraper

on:
  schedule:
    - cron: '0 0 * * *' # 毎日自動実行
  workflow_dispatch: # 手動ボタンも有効

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: write # 生成したdata.jsonを自動でリポジトリに保存するための権限

    steps:
    - name: Checkout repository
      uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.10'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        # 💡 requests に加えて、Geminiを動かすためのライブラリをここで確実に入れます！
        pip install requests google-generativeai

    - name: Run scraper
      env:
        # 💡 Gemini APIキーをPythonプログラムに安全に渡す設定
        GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
      run: python scraper.py

    # 生成・更新された data.json を自動でGitにコミットして保存するステップ
    - name: Commit and Push Changes
      run: |
        git config --local user.email "actions@github.com"
        git config --local user.name "GitHub Actions"
        git add data.json
        git diff --quiet && git diff --staged --quiet || (git commit -m "🚀 Auto-update news data with Gemini insight" && git push)
