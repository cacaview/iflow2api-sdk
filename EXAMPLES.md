# iFlow2API SDK 使用示例

本文档提供 iFlow2API SDK 的详细使用示例，帮助您快速上手和深入使用。

## 目录

- [基础用法](#基础用���)
  - [同步客户端](#同步客户端)
  - [异步客户端](#异步客户端)
  - [上下文管理器](#上下文管理器)
- [Chat Completions](#chat-completions)
  - [基本对话](#基本对话)
  - [多轮对话](#多轮对话)
  - [系统提示词](#系统提示词)
  - [流式响应](#流式响应)
  - [参数控制](#参数控制)
- [模型管理](#模型管理)
  - [列出所有模型](#列出所有模型)
  - [获取特定模型信息](#获取特定模型信息)
- [高级用法](#高级用法)
  - [使用便捷函数创建消息](#使用便捷函数创建消息)
  - [使用 Pydantic 模型](#使用-pydantic-模型)
  - [自定义超时设置](#自定义超时设置)
  - [环境变量配置](#环境变量配置)
- [错误处理](#错误处理)
  - [基本错误处理](#基本错误处理)
  - [重试机制](#重试机制)
  - [错误类型详解](#错误类型详解)
- [实际应用场景](#实际应用场景)
  - [构建聊天机器人](#构建聊天机器人)
  - [批量处理请求](#批量处理请求)
  - [异步并发请求](#异步并发请求)
  - [流式输出到 Web](#流式输出到-web)

---

## 基础用法

### 同步客户端

最简单的使用方式：

```python
from iflow2api_sdk import IFlowClient

# 创建客户端
client = IFlowClient(
    api_key="your-api-key",
    base_url="http://localhost:28000"  # 可选，默认为 https://apis.iflow.cn/v1
)

# 发送请求
response = client.chat.completions.create(
    model="glm-5",
    messages=[{"role": "user", "content": "你好，请介绍一下自己"}]
)

print(response.choices[0].message.content)

# 记得关闭客户端
client.close()
```

### 异步客户端

适用于高并发场景：

```python
import asyncio
from iflow2api_sdk import AsyncIFlowClient

async def main():
    # 创建异步客户端
    client = AsyncIFlowClient(api_key="your-api-key")
    
    # 发送请求
    response = await client.chat.completions.create(
        model="glm-5",
        messages=[{"role": "user", "content": "你好！"}]
    )
    
    print(response.choices[0].message.content)
    
    # 关闭客户端
    await client.close()

asyncio.run(main())
```

### 上下文管理器

推荐使用上下文管理器，自动管理资源：

```python
from iflow2api_sdk import IFlowClient

# 同步客户端使用 with 语句
with IFlowClient(api_key="your-api-key") as client:
    response = client.chat.completions.create(
        model="glm-5",
        messages=[{"role": "user", "content": "Hello!"}]
    )
    print(response.choices[0].message.content)
# 自动关闭客户端
```

异步版本：

```python
import asyncio
from iflow2api_sdk import AsyncIFlowClient

async def main():
    async with AsyncIFlowClient(api_key="your-api-key") as client:
        response = await client.chat.completions.create(
            model="glm-5",
            messages=[{"role": "user", "content": "Hello!"}]
        )
        print(response.choices[0].message.content)

asyncio.run(main())
```

---

## Chat Completions

### 基本对话

```python
from iflow2api_sdk import IFlowClient

with IFlowClient(api_key="your-api-key") as client:
    response = client.chat.completions.create(
        model="glm-5",
        messages=[
            {"role": "user", "content": "什么是机器学习？"}
        ]
    )
    
    print(f"回答: {response.choices[0].message.content}")
    print(f"使用的 tokens: {response.usage.total_tokens}")
```

### 多轮对话

```python
from iflow2api_sdk import IFlowClient

with IFlowClient(api_key="your-api-key") as client:
    # 维护对话历史
    messages = [
        {"role": "user", "content": "我叫张三"},
        {"role": "assistant", "content": "你好张三，很高兴认识你！"},
        {"role": "user", "content": "你还记得我的名字吗？"},
    ]
    
    response = client.chat.completions.create(
        model="glm-5",
        messages=messages
    )
    
    print(response.choices[0].message.content)
    # 输出类似: "当然记得，你叫张三。"
```

### 系统提示词

使用系统消息设定 AI 的行为：

```python
from iflow2api_sdk import IFlowClient

with IFlowClient(api_key="your-api-key") as client:
    response = client.chat.completions.create(
        model="glm-5",
        messages=[
            {"role": "system", "content": "你是一个专业的 Python 编程助手，回答要简洁专业。"},
            {"role": "user", "content": "如何读取 JSON 文件？"}
        ]
    )
    
    print(response.choices[0].message.content)
```

### 流式响应

实时获取输出，适合长文本生成：

```python
from iflow2api_sdk import IFlowClient

with IFlowClient(api_key="your-api-key") as client:
    stream = client.chat.completions.create(
        model="glm-5",
        messages=[{"role": "user", "content": "写一首关于春天的诗"}],
        stream=True
    )
    
    print("AI: ", end="")
    for chunk in stream:
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)
    print()  # 换行
```

异步流式响应：

```python
import asyncio
from iflow2api_sdk import AsyncIFlowClient

async def main():
    async with AsyncIFlowClient(api_key="your-api-key") as client:
        stream = await client.chat.completions.create(
            model="glm-5",
            messages=[{"role": "user", "content": "写一首关于春天的诗"}],
            stream=True
        )
        
        print("AI: ", end="")
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                print(chunk.choices[0].delta.content, end="", flush=True)
        print()

asyncio.run(main())
```

### 参数控制

控制生成行为的各种参数：

```python
from iflow2api_sdk import IFlowClient

with IFlowClient(api_key="your-api-key") as client:
    response = client.chat.completions.create(
        model="glm-5",
        messages=[{"role": "user", "content": "给我讲个笑话"}],
        temperature=0.7,      # 控制随机性 (0-2)，越高越随机
        top_p=0.9,            # 核采样参数
        max_tokens=500,       # 最大生成 token 数
        presence_penalty=0.5, # 存在惩罚，减少重复
        frequency_penalty=0.5, # 频率惩罚，减少重复
        stop=["\n\n"],        # 停止词
    )
    
    print(response.choices[0].message.content)
```

---

## 模型管理

### 列出所有模型

```python
from iflow2api_sdk import IFlowClient

with IFlowClient(api_key="your-api-key") as client:
    models = client.models.list()
    
    print("可用模型列表:")
    for model in models.data:
        print(f"  - {model.id}")
```

### 获取特定模型信息

```python
from iflow2api_sdk import IFlowClient

with IFlowClient(api_key="your-api-key") as client:
    model = client.models.retrieve("glm-5")
    print(f"模型 ID: {model.id}")
    print(f"创建时间: {model.created}")
```

---

## 高级用法

### 使用便捷函数创建消息

SDK 提供了便捷函数来创建消息：

```python
from iflow2api_sdk import IFlowClient, system, user, assistant

with IFlowClient(api_key="your-api-key") as client:
    messages = [
        system("你是一个有帮助的助手。"),
        user("你好！"),
        assistant("你好！有什么我可以帮助你的吗？"),
        user("请介绍一下 Python。")
    ]
    
    response = client.chat.completions.create(
        model="glm-5",
        messages=messages
    )
    
    print(response.choices[0].message.content)
```

使用 `create_message` 函数：

```python
from iflow2api_sdk import create_message

# 创建基本消息
msg = create_message("user", "你好")

# 创建带额外字段的消息
msg = create_message("user", "请分析这张图片", image_url="https://example.com/image.jpg")
```

### 使用 Pydantic 模型

SDK 使用 Pydantic 模型，提供类型安全：

```python
from iflow2api_sdk import IFlowClient, ChatMessage

with IFlowClient(api_key="your-api-key") as client:
    # 使用 Pydantic 模型创建消息
    messages = [
        ChatMessage(role="system", content="你是一个助手"),
        ChatMessage(role="user", content="你好"),
    ]
    
    response = client.chat.completions.create(
        model="glm-5",
        messages=messages
    )
    
    # 响应也是 Pydantic 模型
    choice = response.choices[0]
    print(f"角色: {choice.message.role}")
    print(f"内容: {choice.message.content}")
    print(f"结束原因: {choice.finish_reason}")
```

### 自定义超时设置

```python
from iflow2api_sdk import IFlowClient

# 设置请求超时时间
client = IFlowClient(
    api_key="your-api-key",
    timeout=120.0,        # 请求超时（秒）
    connect_timeout=5.0   # 连接超时（秒）
)

# 对于长时间运行的任务
response = client.chat.completions.create(
    model="glm-5",
    messages=[{"role": "user", "content": "写一篇长篇小说"}],
    max_tokens=4000
)

client.close()
```

### 环境变量配置

推荐使用环境变量管理 API 密钥：

```bash
# 设置环境变量
export IFLOW_API_KEY="your-api-key"
```

```python
import os
from iflow2api_sdk import IFlowClient

# 自动从环境变量读取 IFLOW_API_KEY
client = IFlowClient()  # 无需显式传递 api_key

# 或者显式指定
api_key = os.environ.get("IFLOW_API_KEY")
client = IFlowClient(api_key=api_key)
```

---

## 错误处理

### 基本错误处理

```python
from iflow2api_sdk import IFlowClient, APIError, AuthenticationError, RateLimitError

try:
    with IFlowClient(api_key="your-api-key") as client:
        response = client.chat.completions.create(
            model="invalid-model",
            messages=[{"role": "user", "content": "Hello"}]
        )
except AuthenticationError as e:
    print(f"认证失败: {e}")
except RateLimitError as e:
    print(f"请求过于频繁，请 {e.retry_after} 秒后重试")
except APIError as e:
    print(f"API 错误: {e}")
    print(f"状态码: {e.status_code}")
    print(f"错误类型: {e.error_type}")
```

### 重试机制

实现简单的重试逻辑：

```python
import time
from iflow2api_sdk import IFlowClient, RateLimitError, APIError

def chat_with_retry(client, messages, max_retries=3):
    """带重试机制的聊天函数"""
    for attempt in range(max_retries):
        try:
            return client.chat.completions.create(
                model="glm-5",
                messages=messages
            )
        except RateLimitError as e:
            if attempt < max_retries - 1:
                wait_time = e.retry_after or 5
                print(f"触发限流，等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
            else:
                raise
        except APIError as e:
            if e.status_code >= 500 and attempt < max_retries - 1:
                print(f"服务器错误，重试中... ({attempt + 1}/{max_retries})")
                time.sleep(2 ** attempt)  # 指数退避
            else:
                raise

with IFlowClient(api_key="your-api-key") as client:
    response = chat_with_retry(client, [{"role": "user", "content": "Hello"}])
    print(response.choices[0].message.content)
```

### 错误类型详解

SDK 提供以下异常类型：

| 异常类型 | 说明 | 常见原因 |
|---------|------|---------|
| `IFlowError` | SDK 基础异常 | 所有错误的基类 |
| `APIError` | API 错误 | 服务器返回错误 |
| `AuthenticationError` | 认证错误 | API Key 无效或过期 |
| `RateLimitError` | 速率限制 | 请求过于频繁 |
| `ModelNotFoundError` | 模型不存在 | 使用了无效的模型 ID |
| `InvalidRequestError` | 无效请求 | 请求参数格式错误 |
| `ValidationError` | 验证错误 | 参数验证失败 |
| `TimeoutError` | 超时错误 | 请求超时 |
| `ConnectionError` | 连接错误 | 无法连接到服务器 |
| `StreamError` | 流式错误 | 流式响应处理失败 |

```python
from iflow2api_sdk import (
    IFlowError,
    APIError,
    AuthenticationError,
    RateLimitError,
    ModelNotFoundError,
    InvalidRequestError,
    ValidationError,
    TimeoutError,
    ConnectionError,
    StreamError,
)

try:
    # ... 你的代码
    pass
except ModelNotFoundError as e:
    print(f"模型不存在: {e.model_id}")
except InvalidRequestError as e:
    print(f"请求无效: {e}")
except ValidationError as e:
    print(f"验证失败，字段: {e.field}, 错误: {e.message}")
except TimeoutError as e:
    print(f"请求超时: {e}")
except ConnectionError as e:
    print(f"连接失败: {e}")
except StreamError as e:
    print(f"流式响应错误: {e}")
except APIError as e:
    print(f"API 错误 (状态码: {e.status_code}): {e}")
except IFlowError as e:
    print(f"SDK 错误: {e}")
```

---

## 实际应用场景

### 构建聊天机器人

```python
from iflow2api_sdk import IFlowClient, system

class ChatBot:
    def __init__(self, api_key: str, system_prompt: str = None):
        self.client = IFlowClient(api_key=api_key)
        self.messages = []
        if system_prompt:
            self.messages.append(system(system_prompt))
    
    def chat(self, user_input: str) -> str:
        # 添加用户消息
        self.messages.append({"role": "user", "content": user_input})
        
        # 获取回复
        response = self.client.chat.completions.create(
            model="glm-5",
            messages=self.messages
        )
        
        # 保存助手回复
        assistant_message = response.choices[0].message.content
        self.messages.append({"role": "assistant", "content": assistant_message})
        
        return assistant_message
    
    def close(self):
        self.client.close()

# 使用示例
bot = ChatBot(
    api_key="your-api-key",
    system_prompt="你是一个友好的聊天机器人，名叫小助手。"
)

while True:
    user_input = input("你: ")
    if user_input.lower() in ["退出", "exit", "quit"]:
        break
    
    response = bot.chat(user_input)
    print(f"小助手: {response}")

bot.close()
```

### 批量处理请求

```python
from iflow2api_sdk import IFlowClient

def batch_process(prompts: list[str], api_key: str) -> list[str]:
    """批量处理多个提示"""
    results = []
    
    with IFlowClient(api_key=api_key) as client:
        for i, prompt in enumerate(prompts):
            print(f"处理第 {i+1}/{len(prompts)} 个任务...")
            
            response = client.chat.completions.create(
                model="glm-5",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3  # 低温度保证一致性
            )
            
            results.append(response.choices[0].message.content)
    
    return results

# 使用示例
prompts = [
    "翻译成英文：你好世界",
    "翻译成英文：机器学习",
    "翻译成英文：深度学习",
]

results = batch_process(prompts, "your-api-key")
for prompt, result in zip(prompts, results):
    print(f"{prompt} -> {result}")
```

### 异步并发请求

```python
import asyncio
from iflow2api_sdk import AsyncIFlowClient

async def process_single(client, prompt: str) -> str:
    """处理单个请求"""
    response = await client.chat.completions.create(
        model="glm-5",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

async def batch_process_async(prompts: list[str], api_key: str) -> list[str]:
    """异步批量处理"""
    async with AsyncIFlowClient(api_key=api_key) as client:
        tasks = [process_single(client, prompt) for prompt in prompts]
        results = await asyncio.gather(*tasks)
    return results

# 使用示例
async def main():
    prompts = [f"请说一句问候语 {i}" for i in range(10)]
    results = await batch_process_async(prompts, "your-api-key")
    
    for prompt, result in zip(prompts, results):
        print(f"{prompt}: {result}")

asyncio.run(main())
```

### 流式输出到 Web

结合 FastAPI 实现流式输出：

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from iflow2api_sdk import IFlowClient
import json

app = FastAPI()

@app.post("/chat/stream")
async def chat_stream(message: str):
    """流式聊天接口"""
    def generate():
        with IFlowClient(api_key="your-api-key") as client:
            stream = client.chat.completions.create(
                model="glm-5",
                messages=[{"role": "user", "content": message}],
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    data = json.dumps({"content": chunk.choices[0].delta.content})
                    yield f"data: {data}\n\n"
            
            yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )

# 运行: uvicorn app:app --reload
```

---

## 更多资源

- [README.md](README.md) - 项目概述和快速开始
- [API 参考](README.md#api-参考) - 详细的 API 文档
- [支持的模型](README.md#支持的模型) - 可用模型列表

如有问题或建议，欢迎提交 Issue！
