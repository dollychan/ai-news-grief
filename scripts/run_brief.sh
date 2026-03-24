#!/bin/bash
# AI新闻简报定时执行脚本
# 预置webhook，避免每次传递敏感参数

cd /root/.openclaw/ai-news-brief

# 设置环境变量
export FEISHU_WEBHOOK="${FEISHU_WEBHOOK:-}"  # 请通过环境变量设置，不要在此处硬编码
export TAVILY_API_KEY=''

# 执行简报生成
python3 /root/.openclaw/skills/ai-news-brief/scripts/generate_brief.py --feishu --force

echo "执行完成: $(date)"
