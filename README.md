# AI 每日简报 (ai-news-brief)

自动聚合 AI 行业每日动态，涵盖新闻资讯、前沿论文、社交热点、开源项目和智能热词追踪。

## 功能

- **新闻聚合** — 68 个 RSS 源（中英文 AI 媒体、公司博客、学术机构）
- **前沿论文** — arXiv CS.AI/LG/CL/CV，按技术方向关键词过滤
- **社交热点** — 微博、知乎、B站、Hacker News、Reddit
- **开源动态** — GitHub 热门/新兴 AI 仓库（无需 Token）
- **搜索补充** — Tavily / DuckDuckGo 补充最新动态
- **热词追踪** — 从全量内容中提取新兴技术词汇
- **飞书推送** — 支持 Webhook 推送到飞书群

## 快速使用

```bash
# 生成今日简报
python3 scripts/generate_brief.py

# 强制重新生成
python3 scripts/generate_brief.py --force

# 生成并推送到飞书
python3 scripts/generate_brief.py --feishu

# 跳过搜索引擎（加快速度）
python3 scripts/generate_brief.py --no-search

# 指定输出目录
python3 scripts/generate_brief.py --output ~/my-briefs
```

## 环境配置

```bash
# Tavily 搜索 API（可选，有则优先使用）
export TAVILY_API_KEY="tvly-dev-xxx"

# 飞书 Webhook（使用 --feishu 时必填）
export FEISHU_WEBHOOK="https://open.feishu.cn/open-apis/bot/v2/hook/xxx"
```

## 依赖安装

```bash
pip3 install feedparser tavily-python duckduckgo-search
```

## 输出结构

简报保存为 Markdown，默认路径 `~/.openclaw/ai-news-brief/YYYY-MM-DD.md`：

```
## 🔥 热词追踪
## 📌 今日热点
  ### 🚀 技术突破
  ### 📦 产品发布
  ### 💰 资本动态
  ### 🏭 行业应用
## 📄 前沿论文
## 📱 社交热点
## 🐙 开源动态
## 📊 数据统计
```

## 关键词管理

所有关键词统一在 [`references/keywords.md`](references/keywords.md) 中维护，包括：

| 章节 | 用途 |
|------|------|
| `models` / `architectures` / `paradigms` / `verticals` / `products` / `topics` | 热词追踪 |
| `arxiv_filter` | arXiv 论文过滤 |
| `social_filter` | 社交媒体内容过滤 |
| `cat_tech` / `cat_product` / `cat_biz` | 新闻分类 |
| 泛化词汇 | 排除过于常见的词 |

新增关键词只需编辑 `keywords.md`，无需修改 Python 代码。

## 数据源

| 类型 | 数量 | 说明 |
|------|------|------|
| RSS 订阅 | 54 个 | 中英文 AI 媒体、公司博客、学术机构、社区热榜 |
| 社交媒体 | 6 个平台 | 微博、知乎、B站、HN、Reddit、Product Hunt |
| 搜索引擎 | Tavily / DDG | 补充最新动态 |
| GitHub API | 7 个查询 | AI 相关热门/新兴仓库 |

详见 [`references/rss-sources.md`](references/rss-sources.md)。

## 定时任务

```bash
# 每日 8:00 自动生成并推送飞书
0 8 * * * TAVILY_API_KEY="..." FEISHU_WEBHOOK="..." python3 ~/.openclaw/skills/ai-news-brief/scripts/generate_brief.py --feishu
```
