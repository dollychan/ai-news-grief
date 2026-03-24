# AI 热词关键词库

本文档定义用于智能热词追踪的关键词分类。关键词应当具体、有辨别力，而非泛泛的 AI 通用词。

## 模型名称 (models)

具体的大模型和 AI 产品名称：

### 国际闭源模型
- GPT-4.5, GPT-5, o1, o3, o4-mini
- Claude 3.5, Claude 3.5 Sonnet, Claude 4
- Gemini 2.0, Gemini 2.5, Gemini 3
- Mistral Large, Mistral Small, Mistral Medium

### 国产模型
- DeepSeek V3, DeepSeek R1, DeepSeek Coder
- Llama 4, Llama 3.3, Llama 3.2
- Qwen 2.5, Qwen 3, Qwen-Max
- GLM-4, GLM-4V
- Kimi, Moonshot
- 豆包, Doubao
- 文心一言 4, Ernie 4
- 通义千问 3, Tongyi Qianwen
- 智谱清言
- 讯飞星火

### 生成模型
- Sora, Kling (可灵), Runway Gen-3, Pika
- Stable Diffusion 3, SDXL, FLUX
- Midjourney V6, Midjourney V7
- DALL-E 3
- Suno, Udio (音乐生成)
- ElevenLabs (语音)

### 其他模型
- Whisper v3
- Cosmos (NVIDIA)
- Aria (多模态)
- RWKV
- Mamba, Jamba
- Phi-4, Phi-5 (Microsoft)

## 技术架构 (architectures)

底层技术架构和训练方法：

### 模型架构
- Mixture of Experts, MoE
- Sparse Attention, Linear Attention
- State Space Model, SSM
- RetNet
- Mamba, Jamba
- Diffusion Transformer, DiT
- Flow Matching
- Transformer-XL
- Longformer, LongNet

### 训练方法
- Test-Time Compute
- Chain of Thought, CoT
- Self-Play
- Constitutional AI
- RLHF (Reinforcement Learning from Human Feedback)
- RLAIF (RL from AI Feedback)
- DPO (Direct Preference Optimization)
- GRPO (Group Relative Policy Optimization)
- SFT (Supervised Fine-Tuning)

### 能力扩展
- RAG (Retrieval-Augmented Generation)
- GraphRAG
- Long Context, 1M Context, 2M Context
- Multimodal, Native Multimodal
- Vision Language Model, VLM
- World Model, World Simulator
- Tool Learning

## 应用范式 (paradigms)

AI 应用的模式和形态：

### Agent 生态
- Agentic AI, AI Agent
- Multi-Agent, Multi-Agent System
- Agent Workflow
- Agent Framework
- MCP (Model Context Protocol)

### 开发工具
- Vibe Coding
- Cursor, Cursor Composer
- Windsurf
- Replit, Replit Agent
- Bolt.new
- v0.dev
- Lovable

### 设计理念
- AI Native, AI First, AI Powered
- Copilot, Autopilot, Autonomous
- Human-in-the-loop
- Computer Use
- Function Calling, Tool Use
- Code Interpreter
- Artifact (Claude)
- Canvas (OpenAI)

## 行业垂直 (verticals)

AI 在特定行业的应用：

### 机器人
- 具身智能, Embodied AI
- 人形机器人, Humanoid Robot
- Figure, Figure 01
- Tesla Optimus
- Boston Dynamics
- Unitree

### 自动驾驶
- 自动驾驶, Autonomous Driving
- FSD (Full Self-Driving)
- L4, Level 4
- Robotaxi
- Waymo
- Apollo

### AI 芯片
- AI芯片, AI Accelerator
- NPU, TPU, LPU
- H100, H200, B200, GB200
- Blackwell
- 推理芯片, Inference Chip
- Groq, Cerebras
- Intel Gaudi
- 华为昇腾
- 寒武纪

### 其他垂直
- AI制药, AI Drug Discovery
- AlphaFold, AlphaFold 3
- Protein Folding
- 边缘AI, Edge AI
- On-Device AI, Mobile AI
- AI for Science

## 企业产品 (products)

重要的 AI 产品和平台：

### 开发平台
- OpenClaw, 龙虾
- Hugging Face
- Replicate
- Together AI
- Anyscale

### AI 编程
- Cursor
- Windsurf
- GitHub Copilot
- Amazon CodeWhisperer

### 搜索与对话
- Perplexity
- Poe
- You.com
- Phind

### 创意工具
- Notion AI
- Figma AI
- Canva AI
- Adobe Firefly
- Gamma

### 企业服务
- Microsoft Copilot, Copilot Studio
- AWS Bedrock
- Google Vertex AI
- Azure AI
- 阿里云百炼
- 百度智能云

## 热门话题 (topics)

行业热点讨论方向：

### 技术热点
- Reasoning Model, Reasoning
- Planning, Reflection
- Chain-of-Thought
- Temperature, Sampling

### 安全治理
- AI Safety, AI Alignment
- AI Governance
- AI Regulation
- EU AI Act
- Responsible AI

### 数据话题
- Synthetic Data
- Data Curation
- Data Quality
- Data Contamination

### 商业话题
- Inference Cost, Inference Speed
- Latency, Throughput
- Open Weights, Open Source AI
- Open Model
- Enterprise AI, B2B AI
- AI Monetization

---

## arXiv过滤 (arxiv_filter)

用于筛选 arXiv 论文的关键词（大小写不敏感，命中任意一个即保留）：

### 主要实验室 / 公司
- deepseek, qwen, bytedance, moonshot, kimi
- anthropic, claude, openai, google, gemini
- mistral, meta, llama, microsoft

### Agent 与工具
- agent, multi-agent, tool use, function call
- agentic, autonomous, workflow, orchestration

### 上下文 / 记忆 / 检索
- context, prompt, memory, rag
- retrieval, retrieval-augmented, long context, kv cache

### 推理 / 规划
- reasoning, chain-of-thought, planning, reflection
- test-time, inference-time, self-play

### 架构 / 训练
- moe, mixture of experts, mamba, ssm, transformer
- diffusion, flow matching, rlhf, rlaif, dpo, grpo, sft

### 多模态 / 安全
- multimodal, vision language, vlm
- alignment, safety, jailbreak, red teaming

---

## 社交过滤 (social_filter)

用于从微博、知乎、B站、HN 等平台筛选 AI 相关内容（大小写敏感，中文精确匹配）：

### 通用 AI
- AI, 人工智能, 大模型, LLM

### 主流模型 / 产品
- ChatGPT, GPT, Claude, DeepSeek, Sora, Gemini, Kimi, 豆包

### 公司 / 机构
- OpenAI, Anthropic, 智谱, 月之暗面

### 技术概念
- Agent, 智能体, 具身智能, 算法, 算力, 芯片

### 英文技术词
- machine learning, deep learning, neural, model

### 开发 / 社区
- 编程, 程序员, 代码, 开源

### 硬件生态
- 英伟达, 华为昇腾

---

## 资讯分类-技术 (cat_tech)

用于将新闻归入"技术突破"分类的识别词：

- model, release, breakthrough, training
- 技术, 模型, 算法, 架构, 推理

## 资讯分类-产品 (cat_product)

用于将新闻归入"产品发布"分类的识别词：

- launch, product
- 发布, 产品, 工具, 平台

## 资讯分类-资本 (cat_biz)

用于将新闻归入"资本动态"分类的识别词：

- funding, startup, IPO, acquisition, valuation
- 融资, 投资, 估值, 收购, 上市

---

## 泛化词汇（不计入热词）

以下词汇太过常见，不计入热词追踪：

- AI, 人工智能, Artificial Intelligence
- 大模型, LLM, Large Language Model
- Machine Learning, ML, 深度学习, Deep Learning
- Neural Network, 神经网络
- ChatGPT, GPT (泛指), Claude (泛指), Gemini (泛指)
- OpenAI, Google, Microsoft, Meta (泛指公司名)

## 更新日志

关键词库应定期更新，添加新兴技术和产品名称。建议每月审核一次。

- 2026-03: 初始版本
