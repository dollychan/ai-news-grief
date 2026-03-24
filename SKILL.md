---
name: ai-news-brief
description: Generate comprehensive AI news briefs with trending keywords analysis. Use when user asks for AI news, daily brief, tech news summary, trending AI topics, or wants to understand what's happening in AI industry. Triggers on "AI新闻", "AI简报", "AI news", "AI trends", "AI热点", "AI每日", "科技简报", "生成简报".
---

# AI 新闻简报生成器

生成全面的 AI 行业每日简报，包含热点新闻、社交媒体动态和智能热词追踪。

## 快速使用

```bash
# 生成今日简报
python3 ~/.openclaw/skills/ai-news-brief/scripts/generate_brief.py

# 指定输出目录
python3 ~/.openclaw/skills/ai-news-brief/scripts/generate_brief.py --output ~/my-briefs

# 推送到飞书
python3 ~/.openclaw/skills/ai-news-brief/scripts/generate_brief.py --feishu
```

## 数据源架构

简报聚合三类数据源，确保信息全面且时效性强：

| 数据源 | 数量 | 特点 |
|--------|------|------|
| RSS 订阅 | 68个 | 专业媒体，内容准确 |
| 社交媒体 | 6个平台 | 实时热点，传播快 |
| 搜索引擎 | Tavily/DDG | 补充最新动态 |

### RSS 源分类

- **中文AI专媒** (6): 机器之心、量子位、新智元、AI科技评论、PaperWeekly、DeepTech
- **中文科技综合** (9): 36氪、虎嗅、少数派、InfoQ、钛媒体、雷锋网、爱范儿、澎湃科技
- **英文AI媒体** (9): TechCrunch AI、The Verge AI、VentureBeat AI、MIT Tech Review、Wired AI 等
- **AI公司官方博客** (9): OpenAI、Anthropic、Google DeepMind、Meta AI、Hugging Face 等
- **学术/研究** (7): arXiv CS.AI/CS.LG/CS.CL/CS.CV、Towards Data Science、The Batch
- **热榜/社区** (8): 微博热搜、知乎热榜、Hacker News、Reddit r/MachineLearning、r/LocalLLaMA、Product Hunt
- **国际主流媒体** (5): BBC Technology、Reuters Technology、NYT Technology

### 社交媒体平台

- **微博热搜** - 国内舆论风向标
- **知乎热榜** - 深度讨论
- **B站热门** - 科普视频热度
- **Hacker News** - 开发者社区
- **Reddit** - ML/Llama 社区
- **Product Hunt** - AI 新产品发布

## 智能热词追踪

热词追踪自动识别新兴技术和趋势词汇，而非泛泛的 AI 通用词。

### 热词分类

热词库包含以下类别（详见 `references/keywords.md`）：

- **models**: 具体模型名称 (GPT-4.5, DeepSeek V3, Llama 4, Sora, etc.)
- **architectures**: 技术架构 (MoE, Mamba, Diffusion Transformer, etc.)
- **paradigms**: 应用范式 (Agentic AI, Vibe Coding, Computer Use, etc.)
- **verticals**: 行业垂直 (具身智能, AI芯片, AI制药, etc.)
- **products**: 企业产品 (OpenClaw, Cursor, Perplexity, etc.)
- **topics**: 热门话题 (Reasoning Model, AI Safety, Synthetic Data, etc.)

### 热词提取逻辑

1. 从所有新闻标题和摘要中匹配关键词
2. 统计出现频次
3. 过滤泛化词汇（AI, LLM, 大模型等）
4. 按热度排序输出

## 输出格式

简报保存为 Markdown 文件，结构如下：

```markdown
# 🤖 AI每日简报 | YYYY年MM月DD日

## 🔥 热词追踪
| 热词 | 热度 | 说明 |

## 📌 今日热点
### 🚀 技术突破
### 📦 产品发布
### 💰 资本动态
### 🏭 行业应用

## 📱 社交热点

## 📊 数据统计
```

## 配置

### 环境变量（必需）

脚本通过环境变量读取敏感配置，**请勿在代码中硬编码**：

| 变量名 | 说明 | 获取方式 |
|--------|------|----------|
| `TAVILY_API_KEY` | Tavily 搜索 API 密钥 | https://tavily.com |
| `FEISHU_WEBHOOK` | 飞书机器人 Webhook URL | 飞书群设置 → 添加机器人 |

```bash
# 设置环境变量
export TAVILY_API_KEY="tvly-dev-xxx"
export FEISHU_WEBHOOK="https://open.feishu.cn/open-apis/bot/v2/hook/xxx"

# 或写入 ~/.bashrc 永久生效
echo 'export TAVILY_API_KEY="tvly-dev-xxx"' >> ~/.bashrc
echo 'export FEISHU_WEBHOOK="https://..."' >> ~/.bashrc
```

### 依赖安装

```bash
pip3 install feedparser tavily-python duckduckgo-search
```

## 定时任务配置

使用 cron 每日自动生成：

```bash
# 每日 8:00 生成简报
0 8 * * * python3 ~/.openclaw/skills/ai-news-brief/scripts/generate_brief.py
```

## 扩展参考

- **关键词库**: `references/keywords.md` - 完整的热词分类
- **RSS 源列表**: `references/rss-sources.md` - 数据源详情
- **飞书推送**: `references/feishu-push.md` - 推送配置指南
