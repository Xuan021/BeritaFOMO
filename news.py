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
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>BeritaFOMO - Financial Dashboard</title>
        <style>
            :root {{ --primary: #1a2a6c; --accent: #b21f1f; --gold: #fdbb2d; }}
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; padding: 15px; background: #f0f2f5; color: #333; }}
            .container {{ max-width: 900px; margin: auto; }}
            header {{ background: linear-gradient(to right, var(--primary), var(--accent)); color: white; padding: 20px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
            h1 {{ margin: 0; font-size: 1.8em; }}
            .update-time {{ font-size: 0.8em; opacity: 0.8; }}
            h2 {{ color: var(--primary); border-left: 5px solid var(--gold); padding-left: 15px; margin-top: 30px; border-bottom: 1px solid #ddd; padding-bottom: 5px; }}
            ul {{ list-style: none; padding: 0; display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px; }}
            li {{ background: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); transition: 0.3s; border-top: 3px solid transparent; }}
            li:hover {{ transform: translateY(-3px); box-shadow: 0 5px 15px rgba(0,0,0,0.1); border-top: 3px solid var(--gold); }}
            a {{ text-decoration: none; color: #2c3e50; font-weight: 600; display: block; }}
            .source {{ display: inline-block; margin-top: 8px; font-size: 0.75em; padding: 2px 8px; background: #eee; border-radius: 4px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>📊 BeritaFOMO: Financial Insight</h1>
                <div class="update-time">Penyediaan data pintar untuk perancangan kewangan profesional.</div>
            </header>
            {all_content}
        </div>
    </body>
    </html>
    """
with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_template)

