"""Chat 相关数据模型

定义 Chat Completions API 的请求和响应模型。
"""

from typing import Any, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

from .common import BaseResponse, Usage


# 消息角色类型
Role = Literal["system", "user", "assistant", "tool"]


class ChatMessage(BaseModel):
    """聊天消息"""

    role: Role
    content: Optional[str] = None
    name: Optional[str] = None
    tool_calls: Optional[list[dict]] = None
    tool_call_id: Optional[str] = None

    model_config = ConfigDict(extra="allow")


class ChatCompletionRequest(BaseModel):
    """Chat Completions API 请求"""

    model: str
    messages: list[ChatMessage]
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    max_tokens: Optional[int] = None
    stream: bool = False
    stop: Optional[Union[str, list[str]]] = None
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None
    user: Optional[str] = None
    tools: Optional[list[dict]] = None
    tool_choice: Optional[Union[str, dict]] = None

    model_config = ConfigDict(extra="allow")


class ChatCompletionMessage(BaseModel):
    """Chat Completion 响应消息"""

    role: Literal["assistant"] = "assistant"
    content: Optional[str] = None
    reasoning_content: Optional[str] = None
    tool_calls: Optional[list[dict]] = None

    model_config = ConfigDict(extra="allow")


class ChatCompletionChoice(BaseModel):
    """Chat Completion 选择项"""

    index: int = 0
    message: ChatCompletionMessage
    finish_reason: Optional[str] = None

    model_config = ConfigDict(extra="allow")


class ChatCompletionResponse(BaseResponse):
    """Chat Completion 响应"""

    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[ChatCompletionChoice]
    usage: Usage = Field(default_factory=Usage)


# ============ 流式响应模型 ============


class ChatCompletionStreamDelta(BaseModel):
    """流式响应 Delta"""

    role: Optional[Literal["assistant"]] = None
    content: Optional[str] = None
    reasoning_content: Optional[str] = None
    tool_calls: Optional[list[dict]] = None

    model_config = ConfigDict(extra="allow")


class ChatCompletionStreamChoice(BaseModel):
    """流式响应选择项"""

    index: int = 0
    delta: ChatCompletionStreamDelta
    finish_reason: Optional[str] = None

    model_config = ConfigDict(extra="allow")


class ChatCompletionStreamChunk(BaseResponse):
    """流式响应 Chunk"""

    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: list[ChatCompletionStreamChoice]
    usage: Optional[Usage] = None


# ============ 便捷类型 ============


def create_message(
    role: Role,
    content: Optional[str] = None,
    **kwargs,
) -> dict:
    """创建消息字典

    便捷函数，用于快速创建消息。

    Args:
        role: 消息角色
        content: 消息内容
        **kwargs: 其他字段

    Returns:
        消息字典

    Example:
        >>> msg = create_message("user", "你好")
        >>> msg
        {"role": "user", "content": "你好"}
    """
    msg = {"role": role}
    if content is not None:
        msg["content"] = content
    msg.update(kwargs)
    return msg


def system(content: str) -> dict:
    """创建系统消息"""
    return create_message("system", content)


def user(content: str) -> dict:
    """创建用户消息"""
    return create_message("user", content)


def assistant(content: str) -> dict:
    """创建助手消息"""
    return create_message("assistant", content)
