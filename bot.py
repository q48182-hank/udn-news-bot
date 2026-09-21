import os
import requests
import xml.etree.ElementTree as ET

# 從 GitHub 的安全設定中讀取變數
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# 使用各大媒體的官方 RSS 來源（穩定、不會因為網頁改版失效）
TARGET_FEEDS = [
    {
        "name": "經濟日報",
        "url": "https://money.udn.com/rssfeed/news/1001/1001/5588?from=edn_navibar"
    },
    {
        "name": "鉅亨網",
        "url": "https://news.cnyes.com/news/cat/headline?exp=rss"
    }
]

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Telegram API Error: {e}")

def fetch_rss(feed_info):
    new_items = []
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(feed_info["url"], headers=headers, timeout=10)
        if response.status_code == 200:
            # 解析 XML (RSS)
            root = ET.fromstring(response.content)
            # RSS 通常在 channel -> item 底下
            for item in root.findall('.//item'):
                title = item.find('title')
                link = item.find('link')
                
                if title is not None and link is not None:
                    t_text = title.text.strip() if title.text else ""
                    l_text = link.text.strip() if link.text else ""
                    if t_text and l_text:
                        new_items.append({
                            'source': feed_info["name"],
                            'title': t_text,
                            'link': l_text
                        })
    except Exception as e:
        print(f"Error fetching RSS for {feed_info['name']}: {e}")
    return new_items

def check_news():
    all_items = []
    for feed in TARGET_FEEDS:
        items = fetch_rss(feed)
        all_items.extend(items)

    if all_items:
        # 因為沒有 git 記錄檔，為了避免每次都重複推播歷史新聞，
        # 我們只取該次 RSS 抓到的最新前 3 則新聞發送
        for n in all_items[:3]:
            msg = f"🔔 *{n['source']}即時*\n\n[{n['title']}]({n['link']})"
            send_telegram_message(msg)

if __name__ == "__main__":
    check_news()
