import requests
import os
from concurrent.futures import ThreadPoolExecutor
import xml.etree.ElementTree as ET
import urllib3
from datetime import datetime

# 隱藏 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 配置區 ---
# 關鍵字過濾：標題必須包含以下任一詞彙才會顯示（過濾掉床墊廣告、Wordle等）
KEYWORDS = ['finance', 'market', 'economy', 'investment', 'stock', 'bank', 'fund', 'rate', 'crypto', 'fintech', 
            'profit', 'dividend', 'inflation', 'trade', 'corporate', 'business', 'klci', 'bursa', 'fed', 'opr', 'nfp']

RSS_CONFIG = {
    '🇲🇾 Fokus Malaysia': [
        {'name': 'The Star Biz', 'url': 'https://www.thestar.com.my/rss/business/business-news/'},
        {'name': 'Bernama Biz', 'url': 'https://www.bernama.com/en/rss/news.php?cat=biz'},
        {'name': 'Fintech News MY', 'url': 'https://fintechnews.my/feed/'},
        {'name': 'The Edge', 'url': 'https://www.theedgemarkets.com/rss/corporate.xml'},
        {'name': 'BNM News', 'url': 'https://www.bnm.gov.my/news-releases?format=rss'},
    ],
    '🌎 Fokus Global': [
        {'name': 'MarketWatch', 'url': 'https://feeds.content.dowjones.io/public/rss/mw_topstories'},
        {'name': 'Fortune', 'url': 'https://fortune.com/feed'},
        {'name': 'Forbes Innovation', 'url': 'https://www.forbes.com/innovation/feed/'},
        {'name': 'Yahoo Finance', 'url': 'https://finance.yahoo.com/news/rssindex'},
        {'name': 'Investing.com', 'url': 'https://www.investing.com/rss/news_285.rss'},
    ]
}

def fetch_news(category, source):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    try:
        response = requests.get(source['url'], headers=headers, timeout=15, verify=False)
        content = response.content.strip()
        if b'<?xml' in content: content = b'<?xml' + content.split(b'<?xml')[1]
        root = ET.fromstring(content)

        items = []
        for item in root.iter('item'):
            if len(items) >= 4: break # 限制每組來源顯示 4 則，避免資訊過載
            
            title = item.find('title').text.strip() if item.find('title') is not None else ""
            link = item.find('link').text.strip() if item.find('link') is not None else "#"
            pub_date = item.find('pubDate').text[:16] if item.find('pubDate') is not None else "Recent"
            
            # --- 關鍵字過濾邏輯 ---
            title_lower = title.lower()
            if any(word in title_lower for word in KEYWORDS):
                # 自動打標籤 (Tagging)
                tag = "General"
                if any(k in title_lower for k in ['crypto', 'bitcoin', 'digital']): tag = "Crypto"
                elif any(k in title_lower for k in ['bank', 'bnm', 'rate', 'opr']): tag = "Banking"
                elif any(k in title_lower for k in ['stock', 'klci', 'bursa', 'equity']): tag = "Stocks"
                elif any(k in title_lower for k in ['fund', 'unit trust', 'invest']): tag = "Investment"

                items.append(f'''
                    <div class="news-item" data-category="{tag}">
                        <span class="tag tag-{tag.lower()}">{tag}</span>
                        <a href="{link}" target="_blank">{title}</a>
                        <div class="meta">
                            <span class="source-name">{source["name"]}</span> • 
                            <span class="date">{pub_date}</span>
                        </div>
                    </div>
                ''')
        
        if not items: return category, ""
        return category, f'<div class="news-card"><h3>{source["name"]}</h3>{"".join(items)}</div>'
    except:
        return category, ""

def generate_html():
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(fetch_news, cat, src) for cat, sources in RSS_CONFIG.items() for src in sources]
        category_data = {}
        for future in futures:
            cat, html_segment = future.result()
            if html_segment: category_data.setdefault(cat, []).append(html_segment)

    all_sections = ""
    for cat, cards in category_data.items():
        all_sections += f'<h2 class="category-title">{cat}</h2><div class="card-grid">{"".join(cards)}</div>'

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")

    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>BeritaFOMO v3.0</title>
        <style>
            :root {{ --bg: #f0f2f5; --card: #ffffff; --text: #333; --primary: #1a2a6c; --gold: #fdbb2d; --meta: #777; }}
            body.dark-mode {{ --bg: #121212; --card: #1e1e1e; --text: #e0e0e0; --primary: #4a90e2; --meta: #aaa; }}
            
            body {{ font-family: 'Segoe UI', system-ui, sans-serif; background: var(--bg); color: var(--text); transition: 0.3s; padding: 15px; margin: 0; }}
            .container {{ max-width: 1200px; margin: auto; }}
            
            header {{ background: linear-gradient(135deg, #1a2a6c, #b21f1f); color: white; padding: 40px 20px; border-radius: 0 0 30px 30px; text-align: center; margin: -15px -15px 30px -15px; }}
            .controls {{ display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 20px; align-items: center; justify-content: center; }}
            input#search {{ padding: 12px 20px; border-radius: 25px; border: 1px solid #ddd; width: 300px; outline: none; }}
            
            .btn {{ padding: 10px 20px; border-radius: 20px; border: none; cursor: pointer; background: var(--primary); color: white; font-weight: 600; }}
            .category-title {{ border-left: 6px solid var(--gold); padding-left: 15px; margin-top: 40px; }}
            
            .card-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 25px; }}
            .news-card {{ background: var(--card); padding: 20px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
            
            .news-item {{ padding: 15px 0; border-bottom: 1px solid rgba(0,0,0,0.05); }}
            .news-item a {{ text-decoration: none; color: var(--text); font-weight: 600; display: block; margin: 8px 0; font-size: 1.05em; }}
            .meta {{ font-size: 0.85em; color: var(--meta); }}
            
            .tag {{ font-size: 0.7em; padding: 3px 10px; border-radius: 10px; color: white; text-transform: uppercase; font-weight: bold; }}
            .tag-crypto {{ background: #f39c12; }} .tag-stocks {{ background: #27ae60; }} .tag-banking {{ background: #2980b9; }} .tag-investment {{ background: #8e44ad; }} .tag-general {{ background: #95a5a6; }}
            
            @media (max-width: 600px) {{ input#search {{ width: 100%; }} }}
        </style>
    </head>
    <body class="">
        <div class="container">
            <header>
                <h1>📊 BeritaFOMO v3.0</h1>
                <p>Smart Intelligence for Public Mutual Consultants</p>
                <small>Last Sync: {current_time}</small>
            </header>

            <div class="controls">
                <input type="text" id="search" placeholder="Search news or topics..." onkeyup="filterNews()">
                <button class="btn" onclick="toggleDarkMode()">🌓 Mode</button>
            </div>

            {all_sections}
        </div>

        <script>
            function toggleDarkMode() {{
                document.body.classList.toggle('dark-mode');
                localStorage.setItem('darkMode', document.body.classList.contains('dark-mode'));
            }}
            
            if (localStorage.getItem('darkMode') === 'true') {{
                document.body.classList.add('dark-mode');
            }}

            function filterNews() {{
                let val = document.getElementById('search').value.toLowerCase();
                let items = document.querySelectorAll('.news-item');
                items.forEach(item => {{
                    let text = item.innerText.toLowerCase();
                    item.style.display = text.includes(val) ? "block" : "none";
                }});
            }}
        </script>
    </body>
    </html>
    """
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_template)

if __name__ == "__main__":
    generate_html()
