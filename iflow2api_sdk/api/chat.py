"""Chat Completions API 模块

封装 Chat Completions API，支持流式和非流式响应。
"""

import json
import re
from typing import TYPE_CHECKING, Any, Iterator, Literal, Optional, Union, overload

from ..exceptions import APIError, InvalidRequestError, ModelNotFoundError, ValidationError
from ..models.chat import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatMessage,
)
from ..streaming import AsyncStreamResponse, StreamResponse

if TYPE_CHECKING:
    from ..client import IFlowClient
    from ..client_async import AsyncIFlowClient


def _configure_model_request(request_body: dict, model: str) -> dict:
    """为特定模型配置必要的请求参数

    来源: iFlow CLI 源码中的模型配置 (iflow.js)

    Args:
        request_body: 原始请求体
        model: 模型 ID

    Returns:
        配置后的请求体（副本）
    """
    body = request_body.copy()
    model_lower = model.lower()

    # DeepSeek 模型
    if model_lower.startswith("deepseek"):
        if "thinking_mode" not in body:
            body["thinking_mode"] = True
        if "reasoning" not in body:
            body["reasoning"] = True

    # GLM-5 模型 (特殊配置)
    elif model == "glm-5":
        if "chat_template_kwargs" not in body:
            body["chat_template_kwargs"] = {"enable_thinking": True}
        if "enable_thinking" not in body:
            body["enable_thinking"] = True
        if "thinking" not in body:
            body["thinking"] = {"type": "enabled"}

    # GLM-4.7 模型
    elif model == "glm-4.7":
        if "chat_template_kwargs" not in body:
            body["chat_template_kwargs"] = {"enable_thinking": True}

    # 其他 GLM 模型
    elif model_lower.startswith("glm-"):
        if "chat_template_kwargs" not in body:
            body["chat_template_kwargs"] = {"enable_thinking": True}

    # Kimi-K2.5 模型
    elif model_lower.startswith("kimi-k2.5"):
        if "thinking" not in body:
            body["thinking"] = {"type": "enabled"}

    # 包含 "thinking" 的模型
    elif "thinking" in model_lower:
        if "thinking_mode" not in body:
            body["thinking_mode"] = True

    # mimo- 模型
    elif model_lower.startswith("mimo-"):
        if "thinking" not in body:
            body["thinking"] = {"type": "enabled"}

    # Claude 模型
    elif "claude" in model_lower:
        if "chat_template_kwargs" not in body:
            body["chat_template_kwargs"] = {"enable_thinking": True}

    # sonnet- 模型
    elif "sonnet-" in model_lower:
        if "chat_template_kwargs" not in body:
            body["chat_template_kwargs"] = {"enable_thinking": True}

    # 包含 "reasoning" 的模型
    elif "reasoning" in model_lower:
        if "reasoning" not in body:
            body["reasoning"] = True

    # Qwen 4B 模型 (不支持思考，需要删除相关参数)
    if re.match(r"qwen.*4b", model_lower, re.IGNORECASE):
        for key in ["thinking_mode", "reasoning", "chat_template_kwargs"]:
            if key in body:
                del body[key]

    return body


def _normalize_response(result: dict, preserve_reasoning: bool = False) -> dict:
    """规范化 OpenAI 格式响应

    某些模型（如 GLM-5）使用 reasoning_content 而非 content 返回内容，
    导致 OpenAI 兼容客户端无法读取助手消息。

    Args:
        result: API 响应数据
        preserve_reasoning: 是否保留 reasoning_content 字段
            - False（默认）: 将 reasoning_content 合并到 content，删除 reasoning_content
            - True: 保留 reasoning_content 字段不变
    """
    if preserve_reasoning:
        # 保留 reasoning_content 字段，不做处理
        return result

    choices = result.get("choices", [])
    for choice in choices:
        message = choice.get("message", {})
        content = message.get("content")
        reasoning_content = message.get("reasoning_content")

        if not content and reasoning_content:
            # content 为空但 reasoning_content 有值，将 reasoning_content 移动到 content
            message["content"] = reasoning_content
            del message["reasoning_content"]
        elif content and reasoning_content:
            # 两者都有值，删除 reasoning_content
            del message["reasoning_content"]

    return result


def _check_error_response(response: dict) -> None:
    """检测 API 错误响应

    当 API 返回错误状态时，抛出明确的异常而不是 ValidationError。

    Args:
        response: API 响应数据

    Raises:
        APIError 或其子类
    """
    # 检查是否有错误状态标识
    status = response.get("status")
    if status is not None and str(status) not in ("200", 200):
        message = response.get("msg") or response.get("message") or "Unknown error"
        status_code = int(status) if isinstance(status, (int, str)) else 500
        
        # 根据状态码抛出不同的异常
        if status_code == 404:
            raise ModelNotFoundError(
                message,
                details=response
            )
        elif status_code in (400, 422):
            raise InvalidRequestError(
                message,
                status_code=status_code,
                details=response
            )
        else:
            raise APIError(
                message,
                status_code=status_code,
                details=response
            )
    
    # 检查 OpenAI 格式的错误响应
    if "error" in response and "choices" not in response:
        error = response["error"]
        message = error.get("message", "Unknown error")
        error_type = error.get("type", "api_error")
        status_code = error.get("code", 500)
        
        if isinstance(status_code, str) and status_code.isdigit():
            status_code = int(status_code)
        
        raise APIError(
            message,
            status_code=int(status_code) if isinstance(status_code, (int, str)) else 500,
            error_type=error_type,
            details=response
        )


def _validate_request_params(model: str, messages: list) -> None:
    """验证请求参数

    Args:
        model: 模型 ID
        messages: 消息列表

    Raises:
        ValidationError: 参数验证失败
    """
    if not model or not model.strip():
        raise ValidationError("Model ID cannot be empty", field="model")
    
    if messages is None or len(messages) == 0:
        raise ValidationError("Messages list cannot be empty", field="messages")


class CompletionsAPI:
    """Chat Completions API（同步）"""

    def __init__(self, client: "IFlowClient"):
        self._client = client

    @overload
    def create(
        self,
        *,
        model: str,
        messages: list[Union[ChatMessage, dict]],
        stream: Literal[False] = False,
        preserve_reasoning: bool = False,
        **kwargs,
    ) -> ChatCompletionResponse: ...

    @overload
    def create(
        self,
        *,
        model: str,
        messages: list[Union[ChatMessage, dict]],
        stream: Literal[True],
        preserve_reasoning: bool = False,
        **kwargs,
    ) -> StreamResponse: ...

    def create(
        self,
        *,
        model: str,
        messages: list[Union[ChatMessage, dict]],
        stream: bool = False,
        preserve_reasoning: bool = False,
        **kwargs,
    ) -> Union[ChatCompletionResponse, StreamResponse]:
        """创建 Chat Completion

        Args:
            model: 模型 ID
            messages: 消息列表
            stream: 是否流式响应
            preserve_reasoning: 是否保留 reasoning_content 字段
                - False（默认）: 将 reasoning_content 合并到 content
                - True: 保留 reasoning_content 字段不变
            **kwargs: 其他参数（temperature, max_tokens 等）

        Returns:
            非流式: ChatCompletionResponse
            流式: StreamResponse

        Raises:
            ValidationError: 参数验证失败

        Example:
            >>> # 非流式
            >>> response = client.chat.completions.create(
            ...     model="glm-5",
            ...     messages=[{"role": "user", "content": "你好"}]
            ... )
            >>> print(response.choices[0].message.content)

            >>> # 流式
            >>> for chunk in client.chat.completions.create(
            ...     model="glm-5",
            ...     messages=[{"role": "user", "content": "你好"}],
            ...     stream=True
            ... ):
            ...     if chunk.content:
            ...         print(chunk.content, end="", flush=True)
        """
        # 参数校验
        _validate_request_params(model, messages)
        
        # 构建请求体
        request_body = {
            "model": model,
            "messages": [
                msg.model_dump() if isinstance(msg, ChatMessage) else msg
                for msg in messages
            ],
            "stream": stream,
            **kwargs,
        }

        # 为特定模型配置参数
        request_body = _configure_model_request(request_body, model)

        if stream:
            return self._create_stream(request_body, preserve_reasoning)
        else:
            return self._create_non_stream(request_body, preserve_reasoning)

    def _create_non_stream(self, request_body: dict, preserve_reasoning: bool = False) -> ChatCompletionResponse:
        """非流式请求"""
        response = self._client._request(
            "POST",
            "/chat/completions",
            json=request_body,
        )

        # 检测错误响应
        _check_error_response(response)

        # 规范化响应
        response = _normalize_response(response, preserve_reasoning)

        # 确保 usage 统计信息存在
        if "usage" not in response:
            response["usage"] = {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
            }

        return ChatCompletionResponse(**response)

    def _create_stream(self, request_body: dict, preserve_reasoning: bool = False) -> StreamResponse:
        """流式请求"""
        response_iter = self._client._request_stream(
            "POST",
            "/chat/completions",
            json=request_body,
        )
        return StreamResponse(response_iter, preserve_reasoning=preserve_reasoning)


class ChatAPI:
    """Chat API（同步）"""

    def __init__(self, client: "IFlowClient"):
        self._client = client
        self.completions = CompletionsAPI(client)


class AsyncCompletionsAPI:
    """Chat Completions API（异步）"""

    def __init__(self, client: "AsyncIFlowClient"):
        self._client = client

    @overload
    async def create(
        self,
        *,
        model: str,
        messages: list[Union[ChatMessage, dict]],
        stream: Literal[False] = False,
        preserve_reasoning: bool = False,
        **kwargs,
    ) -> ChatCompletionResponse: ...

    @overload
    async def create(
        self,
        *,
        model: str,
        messages: list[Union[ChatMessage, dict]],
        stream: Literal[True],
        preserve_reasoning: bool = False,
        **kwargs,
    ) -> AsyncStreamResponse: ...

    async def create(
        self,
        *,
        model: str,
        messages: list[Union[ChatMessage, dict]],
        stream: bool = False,
        preserve_reasoning: bool = False,
        **kwargs,
    ) -> Union[ChatCompletionResponse, AsyncStreamResponse]:
        """创建 Chat Completion（异步）

        Args:
            model: 模型 ID
            messages: 消息列表
            stream: 是否流式响应
            preserve_reasoning: 是否保留 reasoning_content 字段
                - False（默认）: 将 reasoning_content 合并到 content
                - True: 保留 reasoning_content 字段不变
            **kwargs: 其他参数

        Returns:
            非流式: ChatCompletionResponse
            流式: AsyncStreamResponse

        Raises:
            ValidationError: 参数验证失败
        """
        # 参数校验
        _validate_request_params(model, messages)
        
        request_body = {
            "model": model,
            "messages": [
                msg.model_dump() if isinstance(msg, ChatMessage) else msg
                for msg in messages
            ],
            "stream": stream,
            **kwargs,
        }

        request_body = _configure_model_request(request_body, model)

        if stream:
            return await self._create_stream(request_body, preserve_reasoning)
        else:
            return await self._create_non_stream(request_body, preserve_reasoning)

    async def _create_non_stream(self, request_body: dict, preserve_reasoning: bool = False) -> ChatCompletionResponse:
        """非流式请求（异步）"""
        response = await self._client._request(
            "POST",
            "/chat/completions",
            json=request_body,
        )

        # 检测错误响应
        _check_error_response(response)

        response = _normalize_response(response, preserve_reasoning)

        if "usage" not in response:
            response["usage"] = {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
            }

        return ChatCompletionResponse(**response)

    async def _create_stream(self, request_body: dict, preserve_reasoning: bool = False) -> AsyncStreamResponse:
        """流式请求（异步）"""
        # 注意：_request_stream 是异步生成器，不能 await
        response_iter = self._client._request_stream(
            "POST",
            "/chat/completions",
            json=request_body,
        )
        return AsyncStreamResponse(response_iter, preserve_reasoning=preserve_reasoning)


class AsyncChatAPI:
    """Chat API（异步）"""

    def __init__(self, client: "AsyncIFlowClient"):
        self._client = client
        self.completions = AsyncCompletionsAPI(client)
