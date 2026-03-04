import requests
import webbrowser
import os
from concurrent.futures import ThreadPoolExecutor
import xml.etree.ElementTree as ET

# 1. 配置專業財經新聞來源 (針對大馬信託顧問優化)
RSS_CONFIG = {
    '🇲🇾 Fokus Malaysia (Wajib Baca)': [
        {'name': 'The Edge Malaysia 🏆', 'url': 'https://www.theedgemarkets.com/rss/corporate.xml'},
        {'name': 'Bernama Business (Official)', 'url': 'https://www.bernama.com/en/rss/news.php?cat=biz'},
        {'name': 'The Star BizNews', 'url': 'https://www.thestar.com.my/rss/business/business-news/'},
        {'name': 'Fintech News Malaysia', 'url': 'https://fintechnews.my/feed/'},
        # BNM 通常不提供新聞 RSS，這裡改用其官方公告或新聞稿來源
        {'name': 'Bank Negara Official', 'url': 'https://www.bnm.gov.my/news-releases?p_p_id=com_liferay_asset_publisher_web_portlet_AssetPublisherPortlet_INSTANCE_XGzYvC4lYm7O&p_p_lifecycle=2&p_p_state=normal&p_p_mode=view&p_p_resource_id=getRSS&p_p_cacheability=cacheLevelPage'},
    ],
    '🌎 Fokus Global (Fund Review)': [
        {'name': 'CNBC Markets 🚀', 'url': 'https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=15839069'},
        {'name': 'Reuters Business', 'url': 'https://www.reutersagency.com/feed/?best-topics=business&post_type=best'},
        {'name': 'Bloomberg Markets', 'url': 'https://www.bloomberg.com/politics2/api/embed/sites/businessweek/rss-feed'},
        {'name': 'Yahoo Finance', 'url': 'https://finance.yahoo.com/news/rssindex'},
        {'name': 'Investing.com News', 'url': 'https://www.investing.com/rss/news_285.rss'},
    ]
}

def fetch_news(category, source):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    try:
        response = requests.get(source['url'], headers=headers, timeout=10, verify=False)
        response.encoding = 'utf-8'
        root = ET.fromstring(response.text)
        items = []
        for item in root.findall('.//item')[:5]: # 每個來源抓 5 則
            title = item.find('title').text
            link = item.find('link').text
            items.append(f'<li><a href="{link}" target="_blank">{title}</a> <span class="source">[{source["name"]}]</span></li>')
        return category, items
    except Exception as e:
        return category, [f"<li>無法讀取 {source['name']}: {str(e)}</li>"]

def generate_html():
    all_content = ""
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for cat, sources in RSS_CONFIG.items():
            for src in sources:
                futures.append(executor.submit(fetch_news, cat, src))
        
        results = {}
        for future in futures:
            cat, items = future.result()
            results.setdefault(cat, []).extend(items)

    for cat, items in results.items():
        all_content += f"<h2>{cat}</h2><ul>{''.join(items)}</ul>"

    html_template = f"""
    <!DOCTYPE html>
    <html lang="zh-Hant">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>我的財經新聞儀表板</title>
        <style>
            body {{ font-family: sans-serif; line-height: 1.6; padding: 20px; background: #f4f4f4; }}
            .container {{ max-width: 800px; margin: auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
            h2 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
            ul {{ list-style: none; padding: 0; }}
            li {{ margin-bottom: 10px; padding: 8px; border-bottom: 1px solid #eee; }}
            a {{ text-decoration: none; color: #34495e; font-weight: bold; }}
            a:hover {{ color: #3498db; }}
            .source {{ font-size: 0.8em; color: #95a5a6; margin-left: 10px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 即時新聞追蹤</h1>
            <p>最後更新時間: {os.popen('date').read()}</p>
            {all_content}
        </div>
    </body>
    </html>
    """
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_template)

if __name__ == "__main__":
    generate_html()
