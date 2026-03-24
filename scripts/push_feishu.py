#!/usr/bin/env python3
"""
飞书推送脚本 - 读取今日简报并推送到飞书
"""

import json
import os
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

def send_feishu_card(title: str, content: str) -> bool:
    """发送飞书卡片消息"""
    feishu_webhook = os.environ.get("FEISHU_WEBHOOK", "")
    
    if not feishu_webhook:
        print("❌ FEISHU_WEBHOOK 环境变量未设置")
        return False
    
    # 构建消息卡片
    card = {
        "msg_type": "interactive",
        "card": {
            "config": {
                "wide_screen_mode": True
            },
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": title
                },
                "template": "blue"
            },
            "elements": [
                {
                    "tag": "markdown",
                    "content": content
                },
                {
                    "tag": "note",
                    "elements": [
                        {
                            "tag": "plain_text",
                            "content": f"⏰ {datetime.now().strftime('%H:%M')} | 🔍 OpenClaw 自动生成"
                        }
                    ]
                }
            ]
        }
    }
    
    data = json.dumps(card).encode('utf-8')
    
    try:
        req = urllib.request.Request(
            feishu_webhook,
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


def send_feishu_text(msg: str) -> bool:
    """发送飞书文本消息"""
    feishu_webhook = os.environ.get("FEISHU_WEBHOOK", "")
    
    if not feishu_webhook:
        print("❌ FEISHU_WEBHOOK 环境变量未设置")
        return False
    
    data = json.dumps({
        'msg_type': 'text',
        'content': {'text': msg}
    }).encode('utf-8')
    
    try:
        req = urllib.request.Request(
            feishu_webhook, 
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


def read_brief_and_push():
    """读取今日简报并推送"""
    today = datetime.now().strftime("%Y-%m-%d")
    brief_dir = Path.home() / ".openclaw" / "ai-news-brief"
    brief_file = brief_dir / f"{today}.md"
    
    if not brief_file.exists():
        print(f"❌ 简报文件不存在: {brief_file}")
        return False
    
    content = brief_file.read_text(encoding='utf-8')
    
    # 提取关键内容
    lines = content.split('\n')
    
    # 提取热词部分
    keywords = []
    in_keywords = False
    for line in lines:
        if '## 🔥 热词追踪' in line:
            in_keywords = True
            continue
        if in_keywords:
            if line.startswith('##'):
                break
            if line.startswith('| **'):
                # 提取关键词
                parts = line.split('|')
                if len(parts) >= 4:
                    kw = parts[1].replace('**', '').strip()
                    heat = parts[2].strip()
                    keywords.append(f"{heat} {kw}")
    
    # 提取热点新闻
    hot_news = []
    in_hot = False
    for line in lines:
        if '## 📌 今日热点' in line:
            in_hot = True
            continue
        if in_hot:
            if line.startswith('## '):
                break
            if line.startswith('- 🔥') or line.startswith('- ['):
                # 提取新闻
                if '[' in line and '](' in line:
                    start = line.find('[') + 1
                    end = line.find(']')
                    title = line[start:end]
                    url_start = line.find('](') + 2
                    url_end = line.find(')', url_start)
                    url = line[url_start:url_end]
                    source = line[line.find('*') + 1:line.rfind('*')] if '*' in line else ""
                    hot_news.append({
                        "title": title,
                        "url": url,
                        "source": source
                    })
    
    # 提取社交热点
    social_news = []
    in_social = False
    for line in lines:
        if '## 📱 社交热点' in line:
            in_social = True
            continue
        if in_social:
            if line.startswith('##'):
                break
            if line.startswith('- **'):
                # 提取社交新闻
                if '[' in line and '](' in line:
                    source = line[line.find('**') + 2:line.rfind('**')]
                    start = line.find('[') + 1
                    end = line.find(']')
                    title = line[start:end]
                    url_start = line.find('](') + 2
                    url_end = line.find(')', url_start)
                    url = line[url_start:url_end]
                    social_news.append({
                        "source": source,
                        "title": title,
                        "url": url
                    })
    
    # 提取统计
    stats = {}
    for line in lines:
        if '| RSS 订阅 |' in line:
            stats['rss'] = line.split('|')[2].strip().replace('条', '').strip()
        if '| 社交媒体 |' in line:
            stats['social'] = line.split('|')[2].strip().replace('条', '').strip()
        if '| 搜索引擎 |' in line:
            stats['search'] = line.split('|')[2].strip().replace('条', '').strip()
    
    # 构建飞书消息
    today_cn = datetime.now().strftime("%Y年%m月%d日")
    title = f"🤖 AI每日简报 | {today_cn}"
    
    # 构建消息内容
    msg = f"🤖 AI每日简报 | {today_cn}\n\n"
    
    # 热词
    if keywords:
        msg += "🔥 热词追踪\n"
        for kw in keywords[:6]:
            msg += f"  {kw}\n"
        msg += "\n"
    
    # 热点新闻
    if hot_news:
        msg += "📌 今日热点\n"
        for item in hot_news[:8]:
            msg += f"  • {item['title'][:45]}\n    {item['url']}\n"
        msg += "\n"
    
    # 社交热点
    if social_news:
        msg += "📱 社交热点\n"
        for item in social_news[:4]:
            msg += f"  • {item['title'][:40]}\n    {item['url']}\n"
        msg += "\n"
    
    # 统计
    stats_str = f"📊 {stats.get('rss', '?')} RSS + {stats.get('social', '?')} 社交"
    msg += f"{stats_str}\n"
    
    print(f"\n📤 准备推送飞书...")
    print(f"   热词: {len(keywords)} 个")
    print(f"   热点: {len(hot_news)} 条")
    print(f"   社交: {len(social_news)} 条")
    
    return send_feishu_text(msg)


if __name__ == "__main__":
    read_brief_and_push()