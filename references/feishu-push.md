# 飞书推送配置

AI 新闻简报支持推送到飞书群或用户。

## Webhook 推送（机器人）

最简单的推送方式，通过自定义机器人 Webhook 发送消息。

### 获取 Webhook URL

1. 在飞书群中，点击「设置」→「群机器人」→「添加机器人」
2. 选择「自定义机器人」
3. 复制 Webhook URL

### 配置方式

**推荐方式：环境变量**

```bash
export FEISHU_WEBHOOK="https://open.feishu.cn/open-apis/bot/v2/hook/xxx"
```

> ⚠️ **安全提示**: 请勿在代码中硬编码 Webhook URL，始终使用环境变量。

### 使用

```bash
python3 generate_brief.py --feishu
```

## 开放 API 推送（高级）

如需推送到指定用户或私聊，需使用飞书开放 API：

### 1. 创建应用

1. 访问 [飞书开放平台](https://open.feishu.cn/app)
2. 创建企业自建应用
3. 获取 App ID 和 App Secret

### 2. 配置权限

应用需要的权限：
- `im:chat` - 获取群组信息
- `im:message:send_as_bot` - 以应用身份发消息
- `message:send_as_bot` - 发送消息

### 3. 获取目标 ID

- **群 ID**: 群设置 → 群信息 → 群 ID
- **用户 ID**: 用户个人资料 → 更多信息 → Open ID

### 4. 配置

```json
{
  "feishu": {
    "app_id": "cli_xxx",
    "app_secret": "xxx",
    "target_type": "chat",  // 或 "user"
    "target_id": "oc_xxx"   // 群 ID 或用户 Open ID
  }
}
```

## 消息格式

推送的消息格式为简洁版简报：

```
🤖 AI每日简报 | 2026年03月20日 18:48

🔥 热词追踪:
  🔥🔥🔥🔥🔥 OpenClaw
  🔥🔥🔥🔥🔥 具身智能
  🔥🔥🔥🔥🔥 Kimi

📌 今日热点:
🔥 一条被开发者踩出来的路：OpenClaw涌进飞书
🔥 2026年3月AI大模型最新排名
🔥 进入2026年，每天至少5亿元砸向具身智能

⏰ 18:48 | 📊 287 RSS + 4 社交
```

## 错误处理

常见错误：

| 错误 | 原因 | 解决方案 |
|------|------|----------|
| `code: 19001` | Webhook 无效 | 检查 URL 是否正确 |
| `code: 9499` | 参数错误 | 消息格式不正确 |
| 超时 | 网络问题 | 重试或检查网络 |

## 安全建议

- 不要在代码仓库中暴露 Webhook URL
- 使用环境变量存储敏感配置
- 定期轮换 Webhook 密钥