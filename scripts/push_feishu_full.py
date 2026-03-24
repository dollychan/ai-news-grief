#!/usr/bin/env python3
"""
飞书推送脚本 - 完整版，推送所有内容
"""

import json
import os
import urllib.request
from datetime import datetime
from pathlib import Path


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
            return True
        else:
            print(f"❌ 飞书推送失败: {result}")
            return False
    except Exception as e:
        print(f"❌ 飞书推送异常: {e}")
        return False


def send_feishu_batch(messages: list):
    """批量发送飞书消息"""
    for i, msg in enumerate(messages):
        print(f"  发送第 {i+1}/{len(messages)} 条...")
        if send_feishu_text(msg):
            print(f"  ✅ 第 {i+1} 条发送成功")
        else:
            print(f"  ❌ 第 {i+1} 条发送失败")


def parse_brief_file(content: str) -> dict:
    """解析简报文件，提取所有内容"""
    lines = content.split('\n')
    
    result = {
        "keywords": [],
        "tech_news": [],
        "product_news": [],
        "capital_news": [],
        "industry_news": [],
        "social_news": [],
        "stats": {}
    }
    
    current_section = None
    current_subsection = None
    
    for line in lines:
        # 检测大章节
        if '## 🔥 热词追踪' in line:
            current_section = 'keywords'
            continue
        elif '## 📌 今日热点' in line:
            current_section = 'hot'
            continue
        elif '## 📱 社交热点' in line:
            current_section = 'social'
            continue
        elif '## 📊 数据统计' in line:
            current_section = 'stats'
            continue
        
        # 检测子章节
        if current_section == 'hot':
            if '### 🚀 技术突破' in line:
                current_subsection = 'tech'
                continue
            elif '### 📦 产品发布' in line:
                current_subsection = 'product'
                continue
            elif '### 💰 资本动态' in line:
                current_subsection = 'capital'
                continue
            elif '### 🏭 行业应用' in line:
                current_subsection = 'industry'
                continue
        
        # 解析内容
        if current_section == 'keywords':
            if line.startswith('| **') and '|' in line[2:]:
                parts = line.split('|')
                if len(parts) >= 4:
                    kw = parts[1].replace('**', '').strip()
                    heat = parts[2].strip()
                    desc = parts[3].strip() if len(parts) > 3 else ''
                    result['keywords'].append({
                        "keyword": kw,
                        "heat": heat,
                        "desc": desc[:30] if desc else ''
                    })
        
        elif current_section == 'hot':
            if line.startswith('- ') and '[' in line and '](' in line:
                # 提取新闻
                start = line.find('[') + 1
                end = line.find(']')
                title = line[start:end]
                url_start = line.find('](') + 2
                url_end = line.find(')', url_start)
                url = line[url_start:url_end]
                
                # 提取来源
                source = ''
                if '*' in line:
                    s_start = line.rfind('*') + 1
                    s_end = line.rfind('*', 0, line.rfind('*'))
                    if s_end > 0:
                        source = line[s_end+1:s_start-1] if s_start > s_end else ''
                
                news_item = {"title": title, "url": url, "source": source}
                
                if current_subsection == 'tech':
                    result['tech_news'].append(news_item)
                elif current_subsection == 'product':
                    result['product_news'].append(news_item)
                elif current_subsection == 'capital':
                    result['capital_news'].append(news_item)
                elif current_subsection == 'industry':
                    result['industry_news'].append(news_item)
        
        elif current_section == 'social':
            if line.startswith('- **'):
                # 提取社交新闻
                source_start = line.find('**') + 2
                source_end = line.find('**', source_start)
                source = line[source_start:source_end]
                
                title_start = line.find('[', source_end) + 1
                title_end = line.find(']', title_start)
                title = line[title_start:title_end]
                
                url_start = line.find('](', title_end) + 2
                url_end = line.find(')', url_start)
                url = line[url_start:url_end]
                
                # 提取热度值
                hot_value = ''
                if '*(' in line:
                    hv_start = line.find('*(') + 2
                    hv_end = line.find(')*', hv_start)
                    hot_value = line[hv_start:hv_end]
                
                result['social_news'].append({
                    "source": source,
                    "title": title,
                    "url": url,
                    "hot_value": hot_value
                })
        
        elif current_section == 'stats':
            if '| RSS 订阅 |' in line:
                result['stats']['rss'] = line.split('|')[2].strip()
            elif '| 社交媒体 |' in line:
                result['stats']['social'] = line.split('|')[2].strip()
            elif '| 搜索引擎 |' in line:
                result['stats']['search'] = line.split('|')[2].strip()
    
    return result


def build_feishu_messages(data: dict) -> list:
    """构建飞书消息（分多条发送，确保完整）"""
    today_cn = datetime.now().strftime("%Y年%m月%d日")
    now = datetime.now().strftime("%H:%M")
    
    messages = []
    
    # 消息1: 标题 + 热词
    msg1 = f"🤖 AI每日简报 | {today_cn}\n"
    msg1 += f"⏰ {now} | 📊 {data['stats'].get('rss', '?')} RSS + {data['stats'].get('social', '?')} 社交\n\n"
    msg1 += "🔥 热词追踪 (Top 10)\n"
    for i, kw in enumerate(data['keywords'][:10], 1):
        desc = f" - {kw['desc']}" if kw['desc'] else ""
        msg1 += f"  {kw['heat']} {kw['keyword']}{desc}\n"
    messages.append(msg1)
    
    # 消息2: 技术突破 + 产品发布
    msg2 = "🚀 技术突破\n"
    for item in data['tech_news'][:5]:
        msg2 += f"  • {item['title'][:50]}\n    {item['url']}\n"
    msg2 += "\n📦 产品发布\n"
    for item in data['product_news'][:4]:
        msg2 += f"  • {item['title'][:50]}\n    {item['url']}\n"
    messages.append(msg2)
    
    # 消息3: 资本动态 + 行业应用
    msg3 = "💰 资本动态\n"
    for item in data['capital_news'][:5]:
        msg3 += f"  • {item['title'][:50]}\n    {item['url']}\n"
    msg3 += "\n🏭 行业应用\n"
    for item in data['industry_news'][:5]:
        msg3 += f"  • {item['title'][:50]}\n    {item['url']}\n"
    messages.append(msg3)
    
    # 消息4: 社交热点
    msg4 = "📱 社交热点\n"
    for item in data['social_news'][:10]:
        hv = f" ({item['hot_value']})" if item['hot_value'] else ""
        msg4 += f"  • [{item['source']}] {item['title'][:40]}{hv}\n    {item['url']}\n"
    messages.append(msg4)
    
    return messages


def main():
    """主函数"""
    today = datetime.now().strftime("%Y-%m-%d")
    brief_dir = Path.home() / ".openclaw" / "ai-news-brief"
    brief_file = brief_dir / f"{today}.md"
    
    if not brief_file.exists():
        print(f"❌ 简报文件不存在: {brief_file}")
        return
    
    print(f"📄 读取简报: {brief_file}")
    content = brief_file.read_text(encoding='utf-8')
    
    print("🔍 解析内容...")
    data = parse_brief_file(content)
    
    print(f"   热词: {len(data['keywords'])} 个")
    print(f"   技术突破: {len(data['tech_news'])} 条")
    print(f"   产品发布: {len(data['product_news'])} 条")
    print(f"   资本动态: {len(data['capital_news'])} 条")
    print(f"   行业应用: {len(data['industry_news'])} 条")
    print(f"   社交热点: {len(data['social_news'])} 条")
    
    print("\n📤 构建飞书消息...")
    messages = build_feishu_messages(data)
    print(f"   消息数量: {len(messages)} 条")
    
    print("\n🚀 推送飞书...")
    send_feishu_batch(messages)
    
    print("\n✅ 完成！")


if __name__ == "__main__":
    main()