#!/bin/bash
# AI新闻简报每日任务
# 由系统crontab调用，每天8:00执行

LOG_FILE="/root/.openclaw/ai-news-brief/cron.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$DATE] 开始执行AI新闻简报..." >> "$LOG_FILE"

# 设置环境变量
export FEISHU_WEBHOOK="${FEISHU_WEBHOOK:-}"  # 请通过环境变量设置，不要在此处硬编码

# 执行脚本
/usr/bin/python3 /root/.openclaw/skills/ai-news-brief/scripts/generate_brief.py --feishu --force >> "$LOG_FILE" 2>&1

echo "[$DATE] 执行完成" >> "$LOG_FILE"
