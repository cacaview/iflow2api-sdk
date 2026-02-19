"""数据模型模块

导出所有数据模型。
"""

from .common import (
    BaseResponse,
    ModelInfo,
    ModelListResponse,
    Usage,
)
from .chat import (
    ChatCompletionChoice,
    ChatCompletionMessage,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionStreamChoice,
    ChatCompletionStreamChunk,
    ChatCompletionStreamDelta,
    ChatMessage,
    Role,
    assistant,
    create_message,
    system,
    user,
)

__all__ = [
    # 通用模型
    "BaseResponse",
    "Usage",
    "ModelInfo",
    "ModelListResponse",
    # Chat 模型
    "Role",
    "ChatMessage",
    "ChatCompletionRequest",
    "ChatCompletionMessage",
    "ChatCompletionChoice",
    "ChatCompletionResponse",
    "ChatCompletionStreamDelta",
    "ChatCompletionStreamChoice",
    "ChatCompletionStreamChunk",
    # 便捷函数
    "create_message",
    "system",
    "user",
    "assistant",
]
