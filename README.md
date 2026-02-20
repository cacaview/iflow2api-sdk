# iFlow2API SDK

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

iFlow2API 的 Python SDK，提供对 iFlow CLI AI 服务的 OpenAI 兼容 API 访问。

## 特性

- 🔐 **自动认证** - 自动处理 HMAC-SHA256 签名认证
- 🔄 **同步/异步支持** - 提供同步和异步两种客户端
- 📡 **流式响应** - 完整支持 SSE 流式响应处理
- 🛠️ **类型安全** - 使用 Pydantic 模型，完整的类型提示
- ⚡ **OpenAI 兼容** - 与 OpenAI SDK 类似的 API 设计

## 安装

```bash
pip install iflow2api-sdk
```

## 📖 [更多使用示例](EXAMPLES.md)

## 快速开始

### 同步客户端

```python
from iflow2api_sdk import IFlowClient

# 创建客户端
client = IFlowClient(
    api_key="your-api-key",
    base_url="https://apis.iflow.cn/v1"  # 可选，默认为 https://apis.iflow.cn/v1
)

# 列出可用模型
models = client.models.list()
for model in models.data:
    print(model.id)

# 创建 Chat Completion
response = client.chat.completions.create(
    model="glm-5",
    messages=[
        {"role": "user", "content": "你好，请介绍一下自己"}
    ]
)
print(response.choices[0].message.content)

# 使用上下文管理器
with IFlowClient(api_key="your-api-key") as client:
    response = client.chat.completions.create(
        model="glm-5",
        messages=[{"role": "user", "content": "Hello!"}]
    )
```

### 异步客户端

```python
import asyncio
from iflow2api_sdk import AsyncIFlowClient

async def main():
    async with AsyncIFlowClient(api_key="your-api-key") as client:
        # 列出模型
        models = await client.models.list()
        
        # 创建 Chat Completion
        response = await client.chat.completions.create(
            model="glm-5",
            messages=[{"role": "user", "content": "你好！"}]
        )
        print(response.choices[0].message.content)

asyncio.run(main())
```

### 流式响应

```python
from iflow2api_sdk import IFlowClient

client = IFlowClient(api_key="your-api-key")

# 流式 Chat Completion
stream = client.chat.completions.create(
    model="glm-5",
    messages=[{"role": "user", "content": "写一首诗"}],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

异步流式响应：

```python
import asyncio
from iflow2api_sdk import AsyncIFlowClient

async def main():
    async with AsyncIFlowClient(api_key="your-api-key") as client:
        stream = await client.chat.completions.create(
            model="glm-5",
            messages=[{"role": "user", "content": "写一首诗"}],
            stream=True
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                print(chunk.choices[0].delta.content, end="", flush=True)

asyncio.run(main())
```

## 支持的模型

### 文本模型

| 模型 ID | 描述 |
|---------|------|
| `glm-4.6` | 智谱 GLM-4.6 |
| `glm-4.7` | 智谱 GLM-4.7 |
| `glm-5` | 智谱 GLM-5（推荐） |
| `iFlow-ROME-30BA3B` | iFlow ROME 30B（快速） |
| `deepseek-v3.2-chat` | DeepSeek V3.2 对话模型 |
| `qwen3-coder-plus` | 通义千问 Qwen3 Coder Plus |
| `kimi-k2` | Moonshot Kimi K2 |
| `kimi-k2-thinking` | Moonshot Kimi K2 思考模型 |
| `kimi-k2.5` | Moonshot Kimi K2.5 |
| `kimi-k2-0905` | Moonshot Kimi K2 0905 |
| `minimax-m2.5` | MiniMax M2.5 |

### 视觉模型

| 模型 ID | 描述 |
|---------|------|
| `qwen-vl-max` | 通义千问 VL Max 视觉模型 |

> **注意**: 模型列表可能随 iFlow 服务更新而变化。建议使用 `client.models.list()` 获取最新的可用模型列表。

## API 参考

### IFlowClient

同步客户端。

**参数：**
- `api_key` (str): API 密钥
- `base_url` (str, 可选): API 基础 URL，默认为 `https://apis.iflow.cn/v1`
- `timeout` (float, 可选): 请求超时时间，默认为 300 秒
- `session_id` (str, 可选): 会话 ID，默认自动生成 UUID

### AsyncIFlowClient

异步客户端，参数与同步客户端相同。

### Chat Completions

```python
client.chat.completions.create(
    model: str,                    # 模型 ID
    messages: List[Dict],          # 消息列表
    stream: bool = False,          # 是否流式响应
    temperature: float = None,     # 温度参数
    max_tokens: int = None,        # 最大 token 数
    top_p: float = None,           # Top-p 采样
    tools: List[Dict] = None,      # 工具定义
    tool_choice: str = None,       # 工具选择策略
)
```

### Models

```python
# 列出所有模型
models = client.models.list()

# 获取特定模型
model = client.models.retrieve("glm-5")
```

## 错误处理

SDK 提供以下异常类：

```python
from iflow2api_sdk import (
    IFlowError,           # SDK 基础异常类
    APIError,             # API 错误基类
    AuthenticationError,  # 认证错误
    RateLimitError,       # 速率限制错误
    ModelNotFoundError,   # 模型不存在错误
    InvalidRequestError,  # 无效请求错误
    ValidationError,      # 参数验证错误
)

try:
    response = client.chat.completions.create(
        model="invalid-model",
        messages=[{"role": "user", "content": "Hello"}]
    )
except ModelNotFoundError as e:
    print(f"模型不存在: {e}")
except RateLimitError as e:
    print(f"速率限制: {e}")
except ValidationError as e:
    print(f"参数验证失败: {e}")
except APIError as e:
    print(f"API 错误: {e}")
```

## 认证机制

SDK 自动处理 iFlow CLI 的认证签名：

1. 使用 `User-Agent: iFlow-Cli` 标识客户端
2. 生成 HMAC-SHA256 签名：`{user_agent}:{session_id}:{timestamp}`
3. 自动添加必要的请求头

## 开发

### 安装开发依赖

```bash
git clone https://github.com/your-repo/iflow2api-sdk.git
cd iflow2api-sdk
pip install -e ".[dev]"
```

### 运行测试

```bash
pytest tests/ -v
```

### 代码格式化

```bash
black iflow2api_sdk/
isort iflow2api_sdk/
```

## 许可证

MIT License

## 相关项目

- [iflow2api](../reference/iflow2api) - iFlow CLI API 代理服务
