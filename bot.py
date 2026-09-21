import os
import requests
from bs4 import BeautifulSoup

# 從 GitHub 的安全設定中讀取變數
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# 我們要抓取的兩個網站清單
TARGET_SITES = [
    {
        "name": "經濟日報",
        "url": "https://money.udn.com/rank/newest/1001/0/1?from=edn_navibar"
    },
    {
        "name": "鉅亨網",
        "url": "https://news.cnyes.com/news/cat/headline"
    }
]

SEEN_NEWS_FILE = 'seen_news.txt'

def load_seen_news():
    if os.path.exists(SEEN_NEWS_FILE):
        with open(SEEN_NEWS_FILE, 'r', encoding='utf-8') as f:
            return set(f.read().splitlines())
    return set()

def save_seen_news(seen_set):
    list_data = list(seen_set)[-200:]  # 因為抓兩個網站，稍微把記憶容量加大一點
    with open(SEEN_NEWS_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(list_data))

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload)

def scrape_udn(soup, seen_news):
    """解析經濟日報"""
    new_items = []
    items = soup.select('div.story.list-story tr td a, .area-content a')
    for item in items:
        title = item.text.strip()
        link = item.get('href', '')
        if title and link and len(title) > 5:
            if link.startswith('/'):
                link = 'https://money.udn.com' + link
            if title not in seen_news:
                seen_news.add(title)
                new_items.append({'title': title, 'link': link})
    return new_items

def scrape_cnyes(soup, seen_news):
    """解析鉅亨網"""
    new_items = []
    # 鉅亨網標題通常在連結標籤內
    items = soup.select('a.]._title') if soup.select('a.]._title') else soup.select('a h3, a span')
    # 使用更廣泛的選擇器來抓取鉅亨網的新聞連結
    for a in soup.find_all('a', href=True):
        link = a['href']
        if '/news/cat/' in link or ('/news/' in link and len(link) > 10):
            title = a.text.strip()
            if title and len(title) > 5:
                if link.startswith('/'):
                    link = 'https://news.cnyes.com' + link
                if title not in seen_news:
                    seen_news.add(title)
                    new_items.append({'title': title, 'link': link})
    return new_items

def check_news():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    seen_news = load_seen_news()
    all_new_items = []

    for site in TARGET_SITES:
        try:
            response = requests.get(site["url"], headers=headers, timeout=10)
            response.encoding = 'utf-8'
            if response.status_code != 200:
                continue

            soup = BeautifulSoup(response.text, 'html.parser')
            
            if "money.udn.com" in site["url"]:
                items = scrape_udn(soup, seen_news)
            else:
                items = scrape_cnyes(soup, seen_news)
            
            # 為每則新聞標註來源網站名稱
            for item in items:
                item['source'] = site["name"]
                all_new_items.append(item)
        except Exception as e:
            print(f"Error scraping {site['name']}: {e}")

    if all_new_items:
        # 限制一次最多推播 5 則，避免洗版
        for n in all_new_items[:5]:
            msg = f"🔔 *{n['source']}新即時*\n\n[{n['title']}]({n['link']})"
            send_telegram_message(msg)
        save_seen_news(seen_news)

if __name__ == "__main__":
    check_news()
