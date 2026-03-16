"""
CS2 News Fetcher - 获取 CS2 饰品相关的消息面数据

双通道消息获取:
1. Steam 官方公告 - 爬取 blog.counter-strike.net 和 steamcommunity.com/news
2. 联网搜索 - 使用 WebSearch 获取 CS2 新闻

返回格式:
[{
    "source": "官方公告" | "搜索结果",
    "title": "...",
    "date": "2026-03-14",
    "content": "...",
    "url": "..."
}]
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time
import re

# Try to import search tools
try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


def fetch_cs2_official_news(max_items: int = 10) -> List[Dict]:
    """
    爬取 Steam 官方公告

    Args:
        max_items: 最大获取数量

    Returns:
        新闻列表
    """
    news_items = []

    # 数据源 1: CS2 官方博客
    cs2_blog_url = "https://blog.counter-strike.net/"

    # 数据源 2: Steam 社区新闻 (CS2 标签)
    steam_news_url = "https://steamcommunity.com/news/app/730"

    # 尝试爬取 CS2 官方博客
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

        response = requests.get(cs2_blog_url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            # 解析博客文章列表
            posts = soup.find_all('div', class_='post')

            for post in posts[:max_items]:
                try:
                    title_elem = post.find('h2') or post.find('h3')
                    title = title_elem.get_text(strip=True) if title_elem else "无标题"

                    date_elem = post.find('span', class_='date') or post.find('time')
                    date_str = date_elem.get_text(strip=True) if date_elem else ""

                    # 尝试解析日期
                    pub_date = parse_date(date_str)

                    # 获取内容摘要
                    content_elem = post.find('div', class_='content') or post.find('p')
                    content = content_elem.get_text(strip=True)[:300] if content_elem else ""

                    # 获取链接
                    link_elem = post.find('a')
                    url = link_elem.get('href', '') if link_elem else cs2_blog_url

                    if title and title != "无标题":
                        news_items.append({
                            "source": "CS2官方博客",
                            "title": title,
                            "date": pub_date.strftime("%Y-%m-%d") if pub_date else date_str,
                            "content": content,
                            "url": url
                        })
                except Exception as e:
                    continue
    except Exception as e:
        print(f"[WARN] Failed to fetch CS2 blog: {e}")

    # 尝试爬取 Steam 社区新闻
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

        response = requests.get(steam_news_url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            # 解析新闻帖子
            posts = soup.find_all('div', class_='newssteam_Post')

            for post in posts[:max_items]:
                try:
                    title_elem = post.find('div', class_='newssteam_PostTitle')
                    title = title_elem.get_text(strip=True) if title_elem else "无标题"

                    date_elem = post.find('div', class_='newssteam_PostDate')
                    date_str = date_elem.get_text(strip=True) if date_elem else ""

                    pub_date = parse_date(date_str)

                    content_elem = post.find('div', class_='newssteam_PostContent')
                    content = content_elem.get_text(strip=True)[:300] if content_elem else ""

                    link_elem = post.find('a')
                    url = link_elem.get('href', '') if link_elem else steam_news_url

                    if title and title != "无标题":
                        news_items.append({
                            "source": "Steam社区新闻",
                            "title": title,
                            "date": pub_date.strftime("%Y-%m-%d") if pub_date else date_str,
                            "content": content,
                            "url": url
                        })
                except Exception as e:
                    continue
    except Exception as e:
        print(f"[WARN] Failed to fetch Steam community news: {e}")

    # 去重并返回
    return deduplicate_news(news_items)[:max_items]


def search_cs2_news(query: str, max_items: int = 5) -> List[Dict]:
    """
    使用 DuckDuckGo 搜索 CS2 相关新闻

    Args:
        query: 搜索关键词
        max_items: 最大获取数量

    Returns:
        新闻列表
    """
    news_items = []

    # 重试机制 - 增加到5次
    for attempt in range(5):
        try:
            # 使用 DuckDuckGo HTML 版本
            search_query = f"CS2 {query}"
            ddg_url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(search_query)}"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }

            response = requests.get(ddg_url, headers=headers, timeout=20)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                # 查找结果
                results = soup.find_all('a', class_='result__a')

                # 如果没找到，尝试其他方式
                if not results:
                    results = soup.find_all(class_=lambda x: x and 'result' in str(x).lower())

                for result in results[:max_items]:
                    try:
                        title = result.get_text(strip=True) if result else "无标题"

                        # 获取原始链接
                        href = result.get('href', '')
                        url = href
                        if 'uddg=' in href:
                            import urllib.parse
                            url = urllib.parse.unquote(href.split('uddg=')[1].split('&')[0])

                        if title and title != "无标题" and len(title) > 3 and 'duckduckgo' not in title.lower():
                            news_items.append({
                                "source": "搜索结果",
                                "title": title,
                                "date": datetime.now().strftime("%Y-%m-%d"),
                                "content": "",
                                "url": url
                            })
                    except Exception as e:
                        continue

                if news_items:
                    break  # 成功获取结果

        except Exception as e:
            pass

        # 等待后重试
        time.sleep(1 + attempt)

    return news_items


def fetch_item_related_news(item_name: str, max_items: int = 10) -> List[Dict]:
    """
    根据饰品名称获取相关消息

    整合官方公告 + 搜索结果

    Args:
        item_name: 饰品名称 (如 "AK-47 霓虹革命", "武器箱")
        max_items: 最大获取数量

    Returns:
        综合新闻列表
    """
    all_news = []

    # 1. 获取官方公告
    print(f"[NEWS] Fetching official CS2 news...")
    official_news = fetch_cs2_official_news(max_items=5)
    all_news.extend(official_news)

    # 2. 根据饰品名构造搜索关键词
    keywords = extract_keywords(item_name)

    # 搜索相关消息 - 使用更长的等待时间避免限流
    for kw in keywords[:3]:  # 最多搜索3个关键词
        print(f"[NEWS] Searching for: {kw}")
        search_results = search_cs2_news(kw, max_items=3)
        all_news.extend(search_results)
        time.sleep(2)  # 等待2秒避免请求过快被限流

    # 如果搜索结果为空，添加默认提示
    if len(all_news) <= len(official_news):
        print(f"[NEWS] Adding fallback news content...")
        all_news.extend(get_fallback_news(item_name))

    # 去重并返回
    return deduplicate_news(all_news)[:max_items]


def get_fallback_news(item_name: str) -> List[Dict]:
    """
    当搜索失败时的默认消息内容

    Args:
        item_name: 饰品名称

    Returns:
        默认新闻列表
    """
    return [{
        "source": "系统提示",
        "title": "消息面数据获取失败",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "content": f"当前无法获取 {item_name} 的最新消息面数据。请关注以下渠道获取最新信息：1) Steam官方博客 blog.counter-strike.net 2) Steam社区新闻 3) CS2相关资讯网站。建议结合技术面进行分析。",
        "url": "https://blog.counter-strike.net/"
    }]


def extract_keywords(item_name: str) -> List[str]:
    """
    从饰品名称提取搜索关键词

    Args:
        item_name: 饰品名称

    Returns:
        关键词列表
    """
    # 常见饰品类型关键词
    item_types = ["武器箱", "箱子", "胶囊", "印花", "贴纸", "刀", "手套", "AK-47", "M4A1", "USP", "格洛克", "AWP"]

    keywords = []

    # 检查是否包含特定关键词
    for it in item_types:
        if it in item_name:
            keywords.append(it)

    # 如果没有匹配，添加整个名称
    if not keywords:
        keywords.append(item_name)

    # 添加通用搜索词
    keywords.append("CS2 更新")
    keywords.append("CS2 饰品")

    return keywords


def parse_date(date_str: str) -> Optional[datetime]:
    """
    解析日期字符串

    支持格式:
    - 2026-03-14
    - March 14, 2026
    - 2026年3月14日
    - 3 days ago
    """
    if not date_str:
        return None

    date_str = date_str.strip()

    # 尝试解析相对时间
    if "ago" in date_str.lower() or "天前" in date_str or "日前" in date_str:
        # 提取数字
        match = re.search(r'(\d+)', date_str)
        if match:
            days = int(match.group(1))
            return datetime.now() - timedelta(days=days)

    # 尝试标准格式
    formats = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%B %d, %Y",
        "%b %d, %Y",
        "%Y年%m月%d日",
        "%d %B %Y",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    return None


def deduplicate_news(news_list: List[Dict]) -> List[Dict]:
    """
    新闻去重

    基于标题相似度去重
    """
    seen_titles = set()
    unique_news = []

    for news in news_list:
        # 标准化标题用于比较
        normalized = re.sub(r'[^\w\u4e00-\u9fff]', '', news['title'].lower())

        if normalized not in seen_titles and len(normalized) > 5:
            seen_titles.add(normalized)
            unique_news.append(news)

    return unique_news


def format_news_for_prompt(news_list: List[Dict]) -> str:
    """
    将新闻列表格式化为 prompt 文本

    Args:
        news_list: 新闻列表

    Returns:
        格式化的文本
    """
    if not news_list:
        return "无最新消息"

    lines = []
    lines.append("## 最近消息面动态\n")

    for i, news in enumerate(news_list[:8], 1):  # 最多显示8条
        lines.append(f"### {i}. {news['title']}")
        lines.append(f"- 来源: {news['source']}")
        lines.append(f"- 日期: {news['date']}")
        if news.get('content'):
            lines.append(f"- 摘要: {news['content'][:150]}...")
        if news.get('url'):
            lines.append(f"- 链接: {news['url']}")
        lines.append("")

    return "\n".join(lines)


# 测试函数
if __name__ == "__main__":
    print("=" * 60)
    print("Testing News Fetcher")
    print("=" * 60)

    # 测试获取官方公告
    print("\n[1] Fetching official CS2 news...")
    official = fetch_cs2_official_news(max_items=5)
    print(f"Got {len(official)} official news")
    for n in official[:3]:
        print(f"  - {n['title'][:50]} ({n['source']})")

    # 测试搜索
    print("\n[2] Searching CS2 news...")
    search = search_cs2_news("武器箱 掉落", max_items=3)
    print(f"Got {len(search)} search results")
    for n in search[:3]:
        print(f"  - {n['title'][:50]}")

    # 测试综合获取
    print("\n[3] Fetching item-related news for 'AK-47 霓虹革命'...")
    item_news = fetch_item_related_news("AK-47 霓虹革命", max_items=10)
    print(f"Got {len(item_news)} total news items")

    # 测试格式化
    print("\n[4] Formatting news for prompt:")
    formatted = format_news_for_prompt(item_news)
    print(formatted[:500])
