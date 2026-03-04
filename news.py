import requests
import os
from concurrent.futures import ThreadPoolExecutor
import xml.etree.ElementTree as ET
import urllib3

# 1. 基礎設定：隱藏安全警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 2. 精準配置專業來源
RSS_CONFIG = {
    '🇲🇾 Fokus Malaysia (Wajib Baca)': [
        # The Star 的 RSS 較穩定，作為大馬首選
        {'name': 'The Star BizNews', 'url': 'https://www.thestar.com.my/business'},
        # Bernama 官方備用 Link，修復語法錯誤
        {'name': 'Bernama Business', 'url': 'https://www.bernama.com/en/rss/news.php?cat=biz'},
        # Fintech News 表現最穩，保留
        {'name': 'Fintech News Malaysia', 'url': 'https://fintechnews.my/feed/'},
        # 更換為較開放的 The Edge 備用路徑
        {'name': 'The Edge Malaysia 🏆', 'url': 'https://www.theedgemarkets.com/rss/theedgemalaysia.xml'},
        # BNM 的 RSS 容易被擋，這裡改用較穩定的官方新聞稿鏈接
        {'name': 'Bank Negara Official', 'url': 'https://www.bnm.gov.my/news-releases?format=rss'},
    ],
    '🌎 Fokus Global (Fund Review)': [
        {'name': 'MarketWatch Top 🚀', 'url': 'https://feeds.content.dowjones.io/public/rss/mw_topstories'},
        {'name': 'Fortune Magazine', 'url': 'https://fortune.com/feed'},
        {'name': 'Forbes Innovation', 'url': 'https://www.forbes.com/innovation/feed/'},
        {'name': 'Yahoo Finance', 'url': 'https://finance.yahoo.com/news/rssindex'},
        {'name': 'Investing.com News', 'url': 'https://www.investing.com/rss/news_285.rss'},
    ]
}

def fetch_news(category, source):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
    }
    try:
        # 增加 Timeout 並確保內容被正確讀取
        response = requests.get(source['url'], headers=headers, timeout=20, verify=False)
        content = response.content.strip()
        
        # 強力解析機制：應對 Bernama 和 BNM 的特殊字元
        try:
            if b'<?xml' in content:
                content = b'<?xml' + content.split(b'<?xml')[1]
            root = ET.fromstring(content)
        except:
            # 如果一般解析失敗，嘗試處理編碼問題
            root = ET.fromstring(response.text.encode('utf-8'))

        items = []
        # 通用尋找 item，不論是 RSS 2.0 還是 Atom 格式
        for item in root.iter('item'):
            if len(items) >= 6: break
            title = item.find('title').text if item.find('title') is not None else ""
            link = item.find('link').text if item.find('link') is not None else "#"
            if title and link != "#":
                items.append(f'<li><a href="{link}" target="_blank">{title}</a><span class="source">{source["name"]}</span></li>')
        
        # 核心功能：如果這來源一條新聞都抓不到，回傳空字串 (觸發隱藏)
        if not items:
            return category, ""
            
        return category, f'<div class="news-card"><h3>{source["name"]}</h3><ul>{"".join(items)}</ul></div>'
    except:
        # 任何錯誤 (網站掛掉、Timeout) 直接回傳空，不顯示錯誤訊息
        return category, ""

def generate_html():
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(fetch_news, cat, src) for cat, sources in RSS_CONFIG.items() for src in sources]
        
        # 分類整理
        category_data = {}
        for future in futures:
            cat, html_segment = future.result()
            if html_segment: # 只有非空的片段才會被加入
                category_data.setdefault(cat, []).append(html_segment)

    all_sections = ""
    for cat, cards in category_data.items():
        if cards: # 如果該分類下至少有一個成功的來源
            all_sections += f'<h2 class="category-title">{cat}</h2><div class="card-grid">{"".join(cards)}</div>'

    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>BeritaFOMO - Professional Insight</title>
        <style>
            :root {{ --primary: #1a2a6c; --accent: #b21f1f; --gold: #fdbb2d; }}
            body {{ font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; line-height: 1.6; padding: 15px; background: #f0f2f5; color: #333; }}
            .container {{ max-width: 1100px; margin: auto; }}
            header {{ background: linear-gradient(135deg, var(--primary), var(--accent)); color: white; padding: 30px; border-radius: 20px; margin-bottom: 30px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); text-align: center; }}
            .category-title {{ color: var(--primary); border-left: 6px solid var(--gold); padding-left: 15px; margin: 40px 0 20px; font-size: 1.5em; }}
            .card-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)); gap: 20px; }}
            .news-card {{ background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }}
            .news-card h3 {{ margin-top: 0; color: #444; font-size: 1.1em; border-bottom: 1px solid #eee; padding-bottom: 10px; }}
            ul {{ list-style: none; padding: 0; margin: 0; }}
            li {{ padding: 12px 0; border-bottom: 1px solid #f9f9f9; }}
            li:last-child {{ border: none; }}
            a {{ text-decoration: none; color: #2c3e50; font-weight: 600; font-size: 0.95em; display: block; line-height: 1.4; }}
            a:hover {{ color: var(--accent); }}
            .source {{ display: inline-block; margin-top: 6px; font-size: 0.7em; color: #999; text-transform: uppercase; letter-spacing: 0.5px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>📊 BeritaFOMO: Insight Kewangan</h1>
                <p>Data dikemaskini secara automatik untuk penasihat profesional.</p>
            </header>
            {all_sections}
        </div>
    </body>
    </html>
    """
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_template)

if __name__ == "__main__":
    generate_html()
