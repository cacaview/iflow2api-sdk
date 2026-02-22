"""iflow2api-sdk

Python SDK for iflow2api - iFlow CLI AI Service Client.

提供对 iFlow API 的同步和异步访问，支持 OpenAI 兼容的 Chat Completions API。

Example:
    >>> from iflow2api_sdk import IFlowClient
    >>> 
    >>> # 使用本地代理
    >>> client = IFlowClient(
    ...     api_key="not-needed",
    ...     base_url="http://localhost:28000/v1"
    ... )
    >>> 
    >>> # Chat Completions
    >>> response = client.chat.completions.create(
    ...     model="glm-5",
    ...     messages=[{"role": "user", "content": "你好！"}]
    ... )
    >>> print(response.choices[0].message.content)
    >>> 
    >>> # 流式响应
    >>> for chunk in client.chat.completions.create(
    ...     model="glm-5",
    ...     messages=[{"role": "user", "content": "写一首诗"}],
    ...     stream=True
    ... ):
    ...     if chunk.content:
    ...         print(chunk.content, end="", flush=True)
"""

__version__ = "0.2.0"

# 客户端
from .client import IFlowClient
from .client_async import AsyncIFlowClient

# 异常
from .exceptions import (
    APIError,
    AuthenticationError,
    ConfigurationError,
    ConnectionError,
    IFlowError,
    IFlowNotConfiguredError,
    InvalidRequestError,
    ModelNotFoundError,
    RateLimitError,
    StreamError,
    TimeoutError,
    ValidationError,
)

# 模型
from .models import (
    ChatCompletionChoice,
    ChatCompletionMessage,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionStreamChoice,
    ChatCompletionStreamChunk,
    ChatCompletionStreamDelta,
    ChatMessage,
    ModelInfo,
    ModelListResponse,
    Role,
    Usage,
    assistant,
    create_message,
    system,
    user,
)

# 流式响应
from .streaming import AsyncStreamResponse, StreamChunk, StreamResponse

# 配置
from .config import ClientConfig, RequestOptions

__all__ = [
    # 版本
    "__version__",
    # 客户端
    "IFlowClient",
    "AsyncIFlowClient",
    # 异常
    "IFlowError",
    "IFlowNotConfiguredError",
    "APIError",
    "AuthenticationError",
    "ConfigurationError",
    "ConnectionError",
    "InvalidRequestError",
    "ModelNotFoundError",
    "RateLimitError",
    "StreamError",
    "TimeoutError",
    "ValidationError",
    # 模型
    "Role",
    "ChatMessage",
    "ChatCompletionRequest",
    "ChatCompletionMessage",
    "ChatCompletionChoice",
    "ChatCompletionResponse",
    "ChatCompletionStreamDelta",
    "ChatCompletionStreamChoice",
    "ChatCompletionStreamChunk",
    "Usage",
    "ModelInfo",
    "ModelListResponse",
    # 便捷函数
    "create_message",
    "system",
    "user",
    "assistant",
    # 流式响应
    "StreamChunk",
    "StreamResponse",
    "AsyncStreamResponse",
    # 配置
    "ClientConfig",
    "RequestOptions",
]
