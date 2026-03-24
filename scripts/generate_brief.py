#!/usr/bin/env python3
"""
AI新闻简报生成器 v3
- 整合68个RSS源
- 增强社交媒体抓取（微博、知乎、B站、Hacker News、Reddit、Product Hunt）
- 智能热词追踪（从内容中提取新兴技术和趋势词汇）
- 时效性过滤（优先24小时内）
"""

import json
import os
import re
import sys
import time
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

try:
    from tavily import TavilyClient
    HAS_TAVILY = True
except ImportError:
    HAS_TAVILY = False
    print("⚠️ tavily-python未安装，请运行: pip3 install tavily-python")

try:
    from duckduckgo_search import DDGS
    HAS_DDGS = True
except ImportError:
    HAS_DDGS = False
    print("⚠️ duckduckgo-search未安装，请运行: pip3 install duckduckgo-search")

try:
    import feedparser
    HAS_FEEDPARSER = True
except ImportError:
    HAS_FEEDPARSER = False
    print("⚠️ feedparser未安装，请运行: pip3 install feedparser")

# ========== 配置（优先从环境变量读取，避免硬编码敏感信息）==========
# Tavily API 密钥 - 用于 AI 优化的搜索引擎
# 设置方式: export TAVILY_API_KEY="your-api-key"
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")

# 飞书 Webhook URL - 用于推送简报消息
# 设置方式: export FEISHU_WEBHOOK="https://open.feishu.cn/open-apis/bot/v2/hook/xxx"
FEISHU_WEBHOOK = os.environ.get("FEISHU_WEBHOOK", "")

# 获取脚本所在目录，支持从任意位置调用
SCRIPT_DIR = Path(__file__).parent.resolve()
SKILL_DIR = SCRIPT_DIR.parent
RSS_FILE = SKILL_DIR / "references" / "rss.txt"

# 默认输出目录（可通过 --output 参数覆盖）
DEFAULT_OUTPUT_DIR = Path.home() / ".openclaw" / "ai-news-brief"

# ========== 从 keywords.md 加载热词库 ==========
def _load_keywords_from_md():
    """解析 references/keywords.md，返回 (emerging_dict, generic_set)"""
    md_file = SKILL_DIR / "references" / "keywords.md"
    emerging = {}
    generic = set()

    if not md_file.exists():
        print(f"⚠️ 关键词文件不存在: {md_file}")
        return emerging, generic

    current_category = None
    is_generic = False

    with open(md_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.rstrip()

            if line.startswith('## '):
                m = re.search(r'\((\w+)\)', line)
                if m:
                    current_category = m.group(1)
                    is_generic = False
                    emerging.setdefault(current_category, [])
                elif '泛化' in line:
                    current_category = None
                    is_generic = True
                else:
                    current_category = None
                    is_generic = False

            elif line.startswith('- ') and (current_category or is_generic):
                # 拆分逗号分隔的关键词，括号内为注释（如"可灵"、"泛指"），直接去除
                for raw in line[2:].split(','):
                    kw = re.sub(r'\s*\(.*?\)', '', raw).strip()
                    if not kw:
                        continue
                    if is_generic:
                        generic.add(kw)
                    else:
                        emerging[current_category].append(kw)

    return emerging, generic


_all_kw, GENERIC_KEYWORDS = _load_keywords_from_md()

# 从全量字典中分离特殊用途分类，不参与热词统计
# 新增/修改这些词汇只需编辑 references/keywords.md
ARXIV_FILTER_KEYWORDS  = [kw.lower() for kw in _all_kw.pop('arxiv_filter', [])]
SOCIAL_FILTER_KEYWORDS = _all_kw.pop('social_filter', [])
CAT_TECH_KEYWORDS      = [kw.lower() for kw in _all_kw.pop('cat_tech', [])]
CAT_PRODUCT_KEYWORDS   = [kw.lower() for kw in _all_kw.pop('cat_product', [])]
CAT_BIZ_KEYWORDS       = [kw.lower() for kw in _all_kw.pop('cat_biz', [])]

# 剩余分类作为热词追踪词库
EMERGING_TECH_KEYWORDS = _all_kw

# 将热词合并为一个集合，用于全文匹配
ALL_TECH_KEYWORDS = set()
for keywords in EMERGING_TECH_KEYWORDS.values():
    ALL_TECH_KEYWORDS.update(kw.lower() for kw in keywords)

# ========== RSS 源配置（从 rss.txt 解析）==========
def load_rss_sources():
    """从 rss.txt 加载 RSS 源"""
    sources = []
    if not RSS_FILE.exists():
        print(f"⚠️ RSS配置文件不存在: {RSS_FILE}")
        return sources
    
    with open(RSS_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split('\t')
            if len(parts) >= 4:
                category = parts[0]
                name = parts[1]
                lang = parts[2]
                url = parts[3]
                status = parts[4] if len(parts) > 4 else ""
                sources.append({
                    "category": category,
                    "name": name,
                    "lang": lang,
                    "url": url,
                    "status": status,
                })
    return sources


def parse_rss_feed(url: str, source_name: str, max_items: int = 10) -> list:
    """解析 RSS feed，返回新闻条目"""
    items = []
    
    if HAS_FEEDPARSER:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:max_items]:
                title = entry.get('title', '')
                link = entry.get('link', '')
                summary = entry.get('summary', '') or entry.get('description', '')
                published = entry.get('published', '') or entry.get('pubDate', '')
                
                if title and link:
                    items.append({
                        "source": source_name,
                        "title": title,
                        "url": link,
                        "snippet": summary[:200] if summary else "",
                        "date": published,
                        "freshness": calculate_freshness(title, summary),
                    })
        except Exception as e:
            print(f"    RSS解析失败 [{source_name}]: {e}")
    else:
        # 使用原生 XML 解析
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (compatible; OpenClawNewsBot/3.0)'
            })
            resp = urllib.request.urlopen(req, timeout=15).read()
            root = ET.fromstring(resp)
            
            # RSS 2.0 格式
            for item in root.findall('.//item')[:max_items]:
                title_elem = item.find('title')
                link_elem = item.find('link')
                desc_elem = item.find('description')
                pub_elem = item.find('pubDate')
                
                if title_elem is not None and link_elem is not None:
                    items.append({
                        "source": source_name,
                        "title": title_elem.text or "",
                        "url": link_elem.text or "",
                        "snippet": (desc_elem.text or "")[:200] if desc_elem is not None else "",
                        "date": pub_elem.text if pub_elem is not None else "",
                        "freshness": calculate_freshness(
                            title_elem.text or "", 
                            desc_elem.text or ""
                        ),
                    })
        except Exception as e:
            print(f"    RSS解析失败 [{source_name}]: {e}")
    
    return items


def is_arxiv_source(source: dict) -> bool:
    return 'arxiv' in source.get('url', '').lower()


def passes_arxiv_filter(item: dict) -> bool:
    """检查 arXiv 论文是否与目标技术方向相关"""
    text = (item.get('title', '') + ' ' + item.get('snippet', '')).lower()
    return any(kw in text for kw in ARXIV_FILTER_KEYWORDS)


def fetch_all_rss_feeds(sources: list) -> list:
    """抓取所有 RSS 源"""
    all_items = []
    stable_sources = [s for s in sources if '稳定' in s.get('status', '')]
    rsshub_sources = [s for s in sources if 'rsshub' in s.get('url', '').lower()]

    print(f"\n📡 抓取 RSS 源...")
    print(f"  稳定源: {len(stable_sources)} 个")
    print(f"  RSSHub源: {len(rsshub_sources)} 个")

    # 优先抓取稳定源
    for source in stable_sources:
        print(f"  ✓ {source['name']}", end="")
        # arXiv 源拉取更多条目后按关键词过滤，提升相关性
        max_items = 50 if is_arxiv_source(source) else 10
        items = parse_rss_feed(source['url'], source['name'], max_items=max_items)
        if is_arxiv_source(source):
            before = len(items)
            items = [i for i in items if passes_arxiv_filter(i)]
            print(f" ✓ {len(items)}/{before}条（arXiv过滤）")
        else:
            print(f" ✓ {len(items)}条")
        all_items.extend(items)
        time.sleep(0.3)  # 避免请求过快

    # 抓取 RSSHub 源（部分可能不可用）
    for source in rsshub_sources[:15]:  # 限制数量
        print(f"  ○ {source['name']}", end="")
        try:
            items = parse_rss_feed(source['url'], source['name'], max_items=5)
            if items:
                all_items.extend(items)
                print(f" ✓ {len(items)}条")
            else:
                print(" ✗ 无数据")
        except:
            print(" ✗ 失败")
        time.sleep(0.5)

    return all_items


# ========== 社交媒体抓取 ==========
def fetch_weibo_hot() -> list:
    """抓取微博热搜"""
    items = []

    try:
        req = urllib.request.Request(
            "https://m.weibo.cn/api/container/getIndex?containerid=106003type%3D25%26t%3D3%26disable_hot%3D1%26filter_type%3Drealtimehot",
            headers={'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)'}
        )
        resp = urllib.request.urlopen(req, timeout=10).read().decode()
        data = json.loads(resp)
        cards = data.get('data', {}).get('cards', [])
        
        for card in cards:
            item_group = card.get('card_group', [])
            for item in item_group:
                title = item.get('desc', '') or item.get('title_sub', '')
                if any(kw in title for kw in SOCIAL_FILTER_KEYWORDS):
                    items.append({
                        "source": "微博热搜",
                        "title": title,
                        "url": f"https://s.weibo.com/weibo?q={urllib.parse.quote(title)}",
                        "freshness": 95,
                        "hot_value": item.get('desc_extr', ''),
                    })
    except Exception as e:
        print(f"    微博获取失败: {e}")
    
    return items


def fetch_zhihu_hot() -> list:
    """抓取知乎热榜"""
    items = []

    try:
        req = urllib.request.Request(
            "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=50",
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        resp = urllib.request.urlopen(req, timeout=10).read().decode()
        data = json.loads(resp)
        
        for item in data.get('data', []):
            target = item.get('target', {})
            title = target.get('title', '')
            if any(kw in title for kw in SOCIAL_FILTER_KEYWORDS):
                url = target.get('url', '') or f"https://www.zhihu.com/question/{target.get('id', '')}"
                items.append({
                    "source": "知乎热榜",
                    "title": title,
                    "url": url,
                    "freshness": 90,
                    "hot_value": item.get('detail_text', ''),
                })
    except Exception as e:
        print(f"    知乎获取失败: {e}")
    
    return items


def fetch_bilibili_hot() -> list:
    """抓取B站热门"""
    items = []

    try:
        req = urllib.request.Request(
            "https://api.bilibili.com/x/web-interface/ranking/v2?rid=0&type=all",
            headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'https://www.bilibili.com'}
        )
        resp = urllib.request.urlopen(req, timeout=10).read().decode()
        data = json.loads(resp)
        
        for item in data.get('data', {}).get('list', []):
            title = item.get('title', '')
            if any(kw in title for kw in SOCIAL_FILTER_KEYWORDS):
                bvid = item.get('bvid', '')
                items.append({
                    "source": "B站热门",
                    "title": title,
                    "url": f"https://www.bilibili.com/video/{bvid}",
                    "freshness": 85,
                    "hot_value": f"{item.get('stat', {}).get('view', 0)}播放",
                })
    except Exception as e:
        print(f"    B站获取失败: {e}")
    
    return items


def fetch_hackernews() -> list:
    """抓取 Hacker News Top"""
    items = []
    
    try:
        # 获取 top stories
        req = urllib.request.Request(
            "https://hacker-news.firebaseio.com/v0/topstories.json",
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        resp = urllib.request.urlopen(req, timeout=10).read().decode()
        story_ids = json.loads(resp)[:50]
        
        for sid in story_ids[:20]:
            try:
                req = urllib.request.Request(
                    f"https://hacker-news.firebaseio.com/v0/item/{sid}.json",
                    headers={'User-Agent': 'Mozilla/5.0'}
                )
                resp = urllib.request.urlopen(req, timeout=5).read().decode()
                story = json.loads(resp)
                
                if story and story.get('title'):
                    title = story['title']
                    url = story.get('url', '') or f"https://news.ycombinator.com/item?id={sid}"
                    score = story.get('score', 0)
                    
                    # 过滤 AI 相关
                    if any(kw.lower() in title.lower() for kw in SOCIAL_FILTER_KEYWORDS):
                        items.append({
                            "source": "Hacker News",
                            "title": title,
                            "url": url,
                            "freshness": 88,
                            "hot_value": f"{score} points",
                        })
            except:
                continue
    except Exception as e:
        print(f"    Hacker News获取失败: {e}")
    
    return items


def fetch_reddit_ml() -> list:
    """抓取 Reddit r/MachineLearning 和 r/LocalLLaMA"""
    items = []
    
    for subreddit in ["MachineLearning", "LocalLLaMA"]:
        try:
            req = urllib.request.Request(
                f"https://www.reddit.com/r/{subreddit}/hot.json?limit=25",
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            resp = urllib.request.urlopen(req, timeout=10).read().decode()
            data = json.loads(resp)
            
            for post in data.get('data', {}).get('children', []):
                post_data = post.get('data', {})
                title = post_data.get('title', '')
                url = post_data.get('url', '')
                score = post_data.get('score', 0)
                
                if title:
                    items.append({
                        "source": f"Reddit r/{subreddit}",
                        "title": title,
                        "url": url or f"https://reddit.com{post_data.get('permalink', '')}",
                        "freshness": 85,
                        "hot_value": f"{score} upvotes",
                    })
        except Exception as e:
            print(f"    Reddit r/{subreddit}获取失败: {e}")
    
    return items


def fetch_all_social() -> list:
    """抓取所有社交媒体"""
    all_items = []
    
    print(f"\n📱 抓取社交媒体热点...")
    
    print("  微博热搜...")
    all_items.extend(fetch_weibo_hot())
    
    print("  知乎热榜...")
    all_items.extend(fetch_zhihu_hot())
    
    print("  B站热门...")
    all_items.extend(fetch_bilibili_hot())
    
    print("  Hacker News...")
    all_items.extend(fetch_hackernews())
    
    print("  Reddit...")
    all_items.extend(fetch_reddit_ml())
    
    return all_items


# ========== 搜索引擎补充 ==========
def get_time_queries():
    """时效性搜索查询"""
    today = datetime.now()
    
    return [
        # 技术突破
        (f"AI model release {today.strftime('%B %Y')}", "tech"),
        (f"AI breakthrough March 2026", "tech"),
        (f"大模型 发布 2026年3月", "tech"),
        ("AI reasoning model latest", "tech"),
        
        # 产品动态
        (f"AI agent launch {today.strftime('%B %Y')}", "product"),
        (f"AI product news {today.strftime('%Y-%m')}", "product"),
        ("AI coding tool release", "product"),
        
        # 企业动态
        (f"AI startup funding March 2026", "biz"),
        (f"人工智能 融资 {today.strftime('%Y年%m月')}", "biz"),
        
        # 国内动态
        ("DeepSeek 智谱 月之暗面 最新", "cn"),
        ("国产大模型 最新发布", "cn"),
    ]


def tavily_search(query: str, max_results: int = 5) -> list:
    """Tavily 搜索"""
    if not HAS_TAVILY:
        return []
    results = []
    try:
        client = TavilyClient(api_key=TAVILY_API_KEY)
        response = client.search(
            query=query,
            search_depth="basic",
            max_results=max_results,
            days=3
        )
        for r in response.get("results", []):
            results.append({
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "snippet": r.get("content", ""),
                "date": r.get("published_date", ""),
            })
    except Exception as e:
        print(f"    Tavily搜索失败 [{query}]: {e}")
    return results


def duckduckgo_search(query: str, max_results: int = 5) -> list:
    """DuckDuckGo 搜索"""
    if not HAS_DDGS:
        return []
    results = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results, timelimit="d"):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", ""),
                    "date": r.get("published", ""),
                })
    except Exception as e:
        print(f"    搜索失败 [{query}]: {e}")
    return results


# ========== GitHub 开源项目追踪 ==========
# 追踪目标：高星 AI 仓库 + 新建但增速迅速的仓库
GITHUB_AI_TOPICS = [
    "llm", "large-language-model", "ai-agent", "rag",
    "llama", "diffusion-model", "transformer", "mcp",
    "vibe-coding", "deepseek", "qwen",
]

def fetch_github_repos() -> list:
    """通过 GitHub Search API 抓取 AI 相关热门/新兴仓库（无需 Token）"""
    items = []
    seen = set()
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    queries = [
        # 近 7 天新建、已有一定 star → 增速迅速的新项目
        (f"topic:llm created:>{week_ago} stars:>30", "新兴"),
        (f"topic:ai-agent created:>{week_ago} stars:>20", "新兴"),
        (f"topic:large-language-model created:>{week_ago} stars:>30", "新兴"),
        # 持续热门：近期活跃的高 star 仓库
        (f"topic:llm stars:>500 pushed:>{week_ago}", "热门"),
        (f"topic:ai-agent stars:>200 pushed:>{week_ago}", "热门"),
        (f"topic:rag stars:>200 pushed:>{week_ago}", "热门"),
        (f"topic:mcp stars:>100 pushed:>{week_ago}", "热门"),
    ]

    print(f"\n🐙 抓取 GitHub 开源动态...")
    for q, tag in queries:
        try:
            url = ("https://api.github.com/search/repositories"
                   f"?q={urllib.parse.quote(q)}&sort=stars&order=desc&per_page=5")
            req = urllib.request.Request(url, headers={
                'User-Agent': 'OpenClawNewsBot/3.0',
                'Accept': 'application/vnd.github.v3+json',
            })
            resp = urllib.request.urlopen(req, timeout=10).read().decode()
            data = json.loads(resp)

            for repo in data.get('items', []):
                full_name = repo.get('full_name', '')
                if full_name in seen:
                    continue
                seen.add(full_name)
                stars = repo.get('stargazers_count', 0)
                items.append({
                    'source': 'GitHub',
                    'title': full_name,
                    'url': repo.get('html_url', ''),
                    'snippet': repo.get('description', '') or '',
                    'stars': stars,
                    'language': repo.get('language', '') or '',
                    'created_at': repo.get('created_at', '')[:10],
                    'tag': tag,
                    'freshness': 85,
                })
            time.sleep(0.8)  # GitHub API rate limit
        except Exception as e:
            print(f"    GitHub查询失败: {e}")

    items.sort(key=lambda x: x['stars'], reverse=True)
    print(f"  发现 {len(items)} 个相关仓库")
    return items


# ========== 智能热词提取 ==========
def extract_trending_keywords(all_items: list) -> list:
    """从新闻内容中提取趋势关键词"""
    # 收集所有文本
    all_text = ""
    for item in all_items:
        all_text += item.get('title', '') + " "
        all_text += item.get('snippet', '') + " "
    
    # 匹配技术关键词
    found_keywords = Counter()

    for keyword in ALL_TECH_KEYWORDS:
        # 纯 ASCII 关键词加词边界，避免匹配到单词内部（如 "dit" 匹配 "Reddit"）
        # 中文/混合关键词直接匹配
        if re.match(r'^[a-zA-Z0-9][a-zA-Z0-9\s\-\.]*$', keyword):
            pattern = re.compile(r'\b' + re.escape(keyword) + r'\b', re.I)
        else:
            pattern = re.compile(re.escape(keyword), re.I)
        matches = pattern.findall(all_text)
        if matches:
            most_common = Counter(matches).most_common(1)[0][0]
            found_keywords[most_common] = len(matches)
    
    # 过滤泛化词汇
    trending = []
    for keyword, count in found_keywords.most_common(20):
        if keyword.lower() not in {k.lower() for k in GENERIC_KEYWORDS}:
            trending.append({
                "keyword": keyword,
                "count": count,
                "trend": "🔥" * min(5, max(1, count // 2)),
            })
    
    return trending[:15]


def get_keyword_context(keyword: str, all_items: list) -> str:
    """获取关键词的上下文描述"""
    for item in all_items:
        title = item.get('title', '')
        if keyword.lower() in title.lower():
            # 从标题中提取简短描述
            return title[:30] + "..." if len(title) > 30 else title
    return ""


# ========== 新闻去重工具 ==========
def normalize_title(title: str) -> str:
    """标准化标题用于去重"""
    # 移除常见前缀后缀
    title = re.sub(r'^【.*?】', '', title)
    title = re.sub(r'\[.*?\]', '', title)
    title = re.sub(r'\|.*$', '', title)
    title = re.sub(r'[-_|]\s*OpenAI|Anthropic|Google|Meta|微软|阿里|腾讯|百度', '', title, flags=re.I)
    # 移除多余空格
    title = ' '.join(title.split())
    return title.strip().lower()


def calculate_similarity(title1: str, title2: str) -> float:
    """计算两个标题的相似度（词重叠率）"""
    words1 = set(normalize_title(title1).split())
    words2 = set(normalize_title(title2).split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1 & words2
    union = words1 | words2
    
    return len(intersection) / len(union)


def deduplicate_news(items: list, similarity_threshold: float = 0.6) -> tuple:
    """智能去重，返回 (去重后列表, 重复数量)"""
    if not items:
        return [], 0
    
    # 先按新鲜度排序
    sorted_items = sorted(items, key=lambda x: x.get('freshness', 50), reverse=True)
    
    unique = []
    duplicates = 0
    
    for item in sorted_items:
        title = item.get('title', '')
        is_duplicate = False
        
        # 检查是否与已有的新闻相似
        for existing in unique:
            existing_title = existing.get('title', '')
            
            # 1. 完全相同的标题
            if normalize_title(title) == normalize_title(existing_title):
                is_duplicate = True
                break
            
            # 2. 一个标题包含另一个（报道同一事件的短/长版本）
            norm_title = normalize_title(title)
            norm_existing = normalize_title(existing_title)
            if norm_title in norm_existing or norm_existing in norm_title:
                # 保留较长的标题（通常信息更完整）
                if len(title) < len(existing_title) * 0.8:
                    is_duplicate = True
                    break
            
            # 3. 高相似度（词重叠超过阈值）
            if calculate_similarity(title, existing_title) >= similarity_threshold:
                is_duplicate = True
                break
        
        if is_duplicate:
            duplicates += 1
        else:
            unique.append(item)
    
    return unique, duplicates


# ========== 时效性计算 ==========
def calculate_freshness(title: str, text: str = "") -> int:
    """计算新鲜度"""
    combined = (title + " " + text).lower()
    score = 50
    
    today = datetime.now()
    today_str = today.strftime("%m月%d日")
    yesterday_str = (today - timedelta(days=1)).strftime("%m月%d日")
    
    if today_str in combined:
        score += 40
    elif yesterday_str in combined:
        score += 30
    
    if any(kw in combined for kw in ["刚刚", "分钟前", "小时前"]):
        score += 35
    if any(kw in combined for kw in ["今日", "最新", "突发", "重磅"]):
        score += 20
    if any(kw in combined for kw in ["2026", "2025"]):
        score += 15
    
    return min(100, score)


# ========== 简报生成 ==========
def generate_brief_markdown(rss_items: list, social_items: list, search_results: dict, trending_keywords: list, github_items: list = None) -> str:
    """生成 Markdown 简报"""
    today = datetime.now().strftime("%Y年%m月%d日")
    now = datetime.now().strftime("%H:%M")
    
    brief = f"""# 🤖 AI每日简报 | {today}

> 生成时间: {now} GMT+8 | 数据源: RSS + 社交媒体 + 搜索引擎

---

## 🔥 热词追踪

| 热词 | 热度 | 说明 |
|------|------|------|
"""
    
    # 添加热词（说明最多50字符）
    for kw in trending_keywords[:10]:
        context = get_keyword_context(kw['keyword'], rss_items + social_items)
        brief += f"| **{kw['keyword']}** | {kw['trend']} | {context[:50] if context else '-'} |\n"
    
    brief += """
---

## 📌 今日热点

"""
    
    # 合并所有新闻
    all_items = rss_items + social_items
    for _, results in search_results.items():
        for r in results:
            r['freshness'] = calculate_freshness(r.get('title', ''), r.get('snippet', ''))
            r['source'] = '搜索'
            all_items.append(r)
    
    # 智能去重
    unique_items, duplicate_count = deduplicate_news(all_items)

    print(f"  去重: {len(all_items)} → {len(unique_items)} 条（移除 {duplicate_count} 条重复）")

    # arXiv 论文单独提取，不参与 freshness 排序
    arxiv_papers = [i for i in unique_items if 'arxiv' in i.get('source', '').lower()]
    non_arxiv_items = [i for i in unique_items if 'arxiv' not in i.get('source', '').lower()]

    # 分类（只处理非论文条目，避免 arXiv 被 freshness 挤出）
    categories = {
        "🚀 技术突破": [],
        "📦 产品发布": [],
        "💰 资本动态": [],
        "🏭 行业应用": [],
    }


    for item in non_arxiv_items[:40]:
        title_lower = item.get('title', '').lower()
        source = item.get('source', '')

        if any(kw in title_lower for kw in CAT_TECH_KEYWORDS):
            categories["🚀 技术突破"].append(item)
        elif any(kw in title_lower for kw in CAT_PRODUCT_KEYWORDS):
            categories["📦 产品发布"].append(item)
        elif any(kw in title_lower for kw in CAT_BIZ_KEYWORDS) or '36氪' in source or 'VentureBeat' in source:
            categories["💰 资本动态"].append(item)
        else:
            categories["🏭 行业应用"].append(item)
    
    for cat, items in categories.items():
        if items:
            brief += f"### {cat}\n\n"
            for item in items[:6]:
                title = item['title'][:80]  # 增加到80字符
                url = item['url']
                source = item.get('source', '')
                freshness = item.get('freshness', 50)
                marker = "🔥 " if freshness > 70 else ""
                brief += f"- {marker}[{title}]({url}) *{source}*\n"
            brief += "\n"
    
    # 前沿论文板块（arXiv，单独展示，不受 freshness 排序影响）
    if arxiv_papers:
        brief += "---\n\n## 📄 前沿论文\n\n"
        for paper in arxiv_papers[:12]:
            title = paper['title'][:100]
            url = paper['url']
            source = paper.get('source', '')
            brief += f"- [{title}]({url}) *{source}*\n"
        brief += "\n"

    # 社交媒体热点（从已去重的列表中提取，避免重复）
    # 收集已出现在分类和论文中的标题
    shown_titles = set()
    for items in categories.values():
        for item in items:
            shown_titles.add(normalize_title(item.get('title', '')))
    for paper in arxiv_papers:
        shown_titles.add(normalize_title(paper.get('title', '')))
    
    # 只显示未在分类中出现的社交热点
    social_sources = ['微博热搜', '知乎热榜', 'B站热门', 'Hacker News', 'Reddit r/MachineLearning', 'Reddit r/LocalLLaMA']
    social_only = []
    for item in unique_items:
        if item.get('source') in social_sources:
            norm_title = normalize_title(item.get('title', ''))
            if norm_title not in shown_titles:
                social_only.append(item)
                shown_titles.add(norm_title)  # 防止社交热点内部重复
    
    if social_only:
        brief += "---\n\n## 📱 社交热点\n\n"
        for item in social_only[:10]:
            hot_value = item.get('hot_value', '')
            brief += f"- **{item['source']}**: [{item['title'][:70]}]({item['url']})"  # 增加到70字符
            if hot_value:
                brief += f" *({hot_value})*"
            brief += "\n"
    
    # GitHub 开源动态板块
    if github_items:
        brief += "---\n\n## 🐙 开源动态\n\n"
        brief += "| 仓库 | Stars | 语言 | 简介 |\n"
        brief += "|------|-------|------|------|\n"
        for repo in github_items[:15]:
            name = repo['title']
            url = repo['url']
            stars = f"⭐{repo['stars']:,}"
            lang = repo.get('language', '') or '-'
            desc = (repo.get('snippet', '') or '')[:50]
            tag = repo.get('tag', '')
            tag_str = f" `{tag}`" if tag == "新兴" else ""
            brief += f"| [{name}]({url}){tag_str} | {stars} | {lang} | {desc} |\n"
        brief += "\n"

    # 来源统计
    rss_count = len([i for i in rss_items if i])
    social_count = len([i for i in social_items if i])
    search_count = sum(len(v) for v in search_results.values())
    
    brief += f"""
---

## 📊 数据统计

| 来源 | 数量 |
|------|------|
| RSS 订阅 | {rss_count} 条 |
| 社交媒体 | {social_count} 条 |
| 搜索引擎 | {search_count} 条 |
| GitHub 仓库 | {len(github_items) if github_items else 0} 个 |
| **去重后** | **{len(unique_items)} 条** |

*🧹 已过滤 {duplicate_count} 条重复内容*

---

*🔍 简报由 OpenClaw 自动生成 | 时效性优先*
"""
    
    return brief


def generate_feishu_messages(rss_items: list, social_items: list, trending_keywords: list, search_results: dict = None) -> list:
    """生成飞书消息（单条，内容完整）"""
    today = datetime.now().strftime("%Y年%m月%d日")
    now = datetime.now().strftime("%H:%M")
    
    # 合并所有新闻（包括搜索结果）
    all_items = rss_items + social_items
    if search_results:
        for _, results in search_results.items():
            for r in results:
                r['freshness'] = calculate_freshness(r.get('title', ''), r.get('snippet', ''))
                r['source'] = '搜索'
                all_items.append(r)
    
    # 智能去重
    unique, duplicate_count = deduplicate_news(all_items)
    
    # 分类新闻
    categories = {
        "🚀 技术突破": [],
        "📦 产品发布": [],
        "💰 资本动态": [],
        "🏭 行业应用": [],
    }
    

    for item in unique[:50]:
        title_lower = item.get('title', '').lower()
        source = item.get('source', '')
        
        if any(kw in title_lower for kw in CAT_TECH_KEYWORDS):
            categories["🚀 技术突破"].append(item)
        elif any(kw in title_lower for kw in CAT_PRODUCT_KEYWORDS):
            categories["📦 产品发布"].append(item)
        elif any(kw in title_lower for kw in CAT_BIZ_KEYWORDS):
            categories["💰 资本动态"].append(item)
        else:
            categories["🏭 行业应用"].append(item)
    
    # 构建消息
    msg = f"🤖 AI每日简报 | {today}\n\n"
    
    # 热词追踪（带说明）
    if trending_keywords:
        msg += "🔥 热词追踪\n"
        for kw in trending_keywords[:8]:
            context = get_keyword_context(kw['keyword'], all_items)
            context_display = f" - {context[:30]}" if context else ""
            msg += f"  {kw['trend']} {kw['keyword']}{context_display}\n"
        msg += "\n"
    
    # 各分类热点（每类5条，带链接）
    shown_titles = set()
    for cat_name, items in categories.items():
        if items:
            msg += f"{cat_name}\n"
            for item in items[:5]:
                title = item['title'][:65]
                url = item['url']
                msg += f"  • {title}\n    {url}\n"
                shown_titles.add(normalize_title(item.get('title', '')))
            msg += "\n"
    
    # 社交热点（排除已在分类中出现的）
    social_sources = ['微博热搜', '知乎热榜', 'B站热门', 'Hacker News', 'Reddit r/MachineLearning', 'Reddit r/LocalLLaMA']
    social_only = []
    for item in unique:
        if item.get('source') in social_sources:
            norm_title = normalize_title(item.get('title', ''))
            if norm_title not in shown_titles:
                social_only.append(item)
                shown_titles.add(norm_title)
    
    if social_only:
        msg += "📱 社交热点\n"
        for item in social_only[:8]:
            title = item['title'][:50]
            url = item['url']
            source = item.get('source', '')
            hot_value = item.get('hot_value', '')
            hot_str = f" ({hot_value})" if hot_value else ""
            msg += f"  • [{source}] {title}{hot_str}\n    {url}\n"
        msg += "\n"
    
    # 数据统计
    msg += f"📊 {len(unique)} 条新闻（已去重 {duplicate_count} 条）| ⏰ {now}"
    
    return [msg]


def send_feishu(msg: str) -> bool:
    """发送到飞书（单条消息）"""
    data = json.dumps({
        'msg_type': 'text',
        'content': {'text': msg}
    }).encode('utf-8')
    
    try:
        req = urllib.request.Request(
            FEISHU_WEBHOOK, 
            data=data, 
            headers={'Content-Type': 'application/json'}
        )
        resp = urllib.request.urlopen(req, timeout=30).read().decode()
        result = json.loads(resp)
        if result.get('code') == 0:
            print("✅ 飞书推送成功")
            return True
        else:
            print(f"❌ 飞书推送失败: {result}")
            return False
    except Exception as e:
        print(f"❌ 飞书推送异常: {e}")
        return False


def send_feishu_batch(messages: list) -> bool:
    """发送飞书消息（单条）"""
    if not messages:
        return False
    return send_feishu(messages[0])


def parse_args():
    """解析命令行参数"""
    import argparse
    parser = argparse.ArgumentParser(description='AI新闻简报生成器')
    parser.add_argument('--output', '-o', type=str, default=None,
                        help='输出目录路径')
    parser.add_argument('--feishu', '-f', action='store_true',
                        help='推送到飞书')
    parser.add_argument('--no-search', action='store_true',
                        help='跳过搜索引擎补充')
    parser.add_argument('--force', action='store_true',
                        help='强制重新生成（忽略去重检查）')
    return parser.parse_args()


def check_lock_file(brief_dir: Path) -> bool:
    """检查是否有运行中的实例（防止并发）"""
    lock_file = brief_dir / ".generating.lock"
    if lock_file.exists():
        # 检查锁文件是否过期（超过10分钟视为过期）
        import time
        lock_age = time.time() - lock_file.stat().st_mtime
        if lock_age < 600:  # 10分钟内
            print(f"⚠️ 检测到其他实例正在运行（锁文件存在 {int(lock_age)}秒）")
            print(f"   如需强制运行，请删除锁文件或使用 --force 参数")
            return False
        else:
            print(f"⚠️ 锁文件已过期（{int(lock_age/60)}分钟前），忽略")
    return True


def create_lock_file(brief_dir: Path):
    """创建锁文件"""
    lock_file = brief_dir / ".generating.lock"
    lock_file.touch()


def remove_lock_file(brief_dir: Path):
    """删除锁文件"""
    lock_file = brief_dir / ".generating.lock"
    if lock_file.exists():
        lock_file.unlink()


def check_today_exists(brief_dir: Path, force: bool = False) -> bool:
    """检查今日简报是否已存在"""
    today = datetime.now().strftime("%Y-%m-%d")
    output_file = brief_dir / f"{today}.md"
    
    if output_file.exists():
        # 检查文件是否够新（2小时内生成的）
        import time
        file_age = time.time() - output_file.stat().st_mtime
        file_age_hours = file_age / 3600
        
        if file_age_hours < 2 and not force:
            print(f"⚠️ 今日简报已存在且在2小时内生成（{int(file_age_hours*60)}分钟前）")
            print(f"   文件: {output_file}")
            print(f"   如需重新生成，请使用 --force 参数")
            return True
    return False


def main():
    args = parse_args()
    
    # 确定输出目录
    if args.output:
        brief_dir = Path(args.output)
    else:
        brief_dir = DEFAULT_OUTPUT_DIR
    
    brief_dir.mkdir(parents=True, exist_ok=True)
    
    # ========== 去重检查 ==========
    # 1. 检查今日是否已生成（2小时内）
    if check_today_exists(brief_dir, args.force):
        return 0  # 已存在且够新，跳过
    
    # 2. 检查是否有并发实例
    if not args.force and not check_lock_file(brief_dir):
        return 1  # 有其他实例在运行
    
    # 创建锁文件
    create_lock_file(brief_dir)
    
    print(f"\n{'='*60}")
    print(f"🤖 AI新闻简报生成器 v3")
    print(f"{'='*60}")
    print(f"[{datetime.now()}] 开始采集...")
    print(f"📁 输出目录: {brief_dir}")
    
    # 设置全局变量供其他函数使用
    global BRIEF_DIR
    BRIEF_DIR = brief_dir
    
    # 1. 加载并抓取 RSS 源
    rss_sources = load_rss_sources()
    print(f"📋 已加载 {len(rss_sources)} 个 RSS 源")
    rss_items = fetch_all_rss_feeds(rss_sources)
    
    # 2. 抓取社交媒体
    social_items = fetch_all_social()
    
    # 3. 搜索引擎补充
    search_results = {}
    if HAS_TAVILY:
        print(f"\n🔍 Tavily 搜索...")
        for query, cat in get_time_queries():
            print(f"  [{cat}] {query[:35]}...")
            results = tavily_search(query, max_results=4)
            if results:
                search_results[query] = results
            time.sleep(0.2)
    elif HAS_DDGS:
        print(f"\n🔍 DuckDuckGo 搜索...")
        for query, cat in get_time_queries():
            print(f"  [{cat}] {query[:35]}...")
            results = duckduckgo_search(query, max_results=4)
            if results:
                search_results[query] = results
            time.sleep(0.3)
    
    # 4. GitHub 开源动态
    github_items = fetch_github_repos()

    # 5. 智能热词提取
    print(f"\n🔥 提取趋势热词...")
    all_items = rss_items + social_items
    for results in search_results.values():
        all_items.extend(results)
    trending_keywords = extract_trending_keywords(all_items)
    print(f"  发现 {len(trending_keywords)} 个趋势热词")
    for kw in trending_keywords[:5]:
        print(f"    {kw['trend']} {kw['keyword']} ({kw['count']}次)")

    # 6. 生成简报
    print(f"\n📝 生成简报...")
    brief = generate_brief_markdown(rss_items, social_items, search_results, trending_keywords, github_items)
    
    # 7. 保存
    today = datetime.now().strftime("%Y-%m-%d")
    output_file = BRIEF_DIR / f"{today}.md"
    output_file.write_text(brief, encoding="utf-8")
    print(f"💾 已保存: {output_file}")
    
    # 8. 推送飞书
    if args.feishu:
        print("\n🚀 推送飞书...")
        
        # 推送去重：检查今天是否已推送
        push_flag_file = BRIEF_DIR / f"{today}.pushed"
        if push_flag_file.exists() and not args.force:
            print(f"⚠️ 今日已推送过飞书（标记文件存在）")
            print(f"   如需重新推送，请使用 --force 参数")
        elif FEISHU_WEBHOOK:
            feishu_messages = generate_feishu_messages(rss_items, social_items, trending_keywords, search_results)
            if send_feishu_batch(feishu_messages):
                # 推送成功，创建标记文件
                push_flag_file.touch()
                print("📝 已记录推送状态，今日不会重复推送")
        else:
            print("❌ FEISHU_WEBHOOK 环境变量未设置，无法推送")
            print("   设置方式: export FEISHU_WEBHOOK='https://open.feishu.cn/open-apis/bot/v2/hook/xxx'")
    else:
        print("\n⏭️ 飞书推送已跳过（使用 --feishu 启用）")
    
    # 统计
    print(f"\n{'='*60}")
    print(f"✅ 完成!")
    print(f"   RSS 新闻: {len(rss_items)} 条")
    print(f"   社交热点: {len(social_items)} 条")
    print(f"   搜索结果: {sum(len(v) for v in search_results.values())} 条")
    print(f"   趋势热词: {len(trending_keywords)} 个")
    print(f"{'='*60}\n")
    
    # 清理锁文件
    remove_lock_file(brief_dir)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
