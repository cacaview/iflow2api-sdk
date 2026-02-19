"""流式响应处理模块

处理 SSE (Server-Sent Events) 流式响应。
"""

import json
from typing import Iterator, Optional

from .exceptions import StreamError
from .models.chat import ChatCompletionStreamChunk


class StreamChunk:
    """流式响应块

    封装单个流式响应块，提供便捷的属性访问。
    """

    def __init__(self, raw_data: dict):
        self._raw_data = raw_data
        self._chunk: Optional[ChatCompletionStreamChunk] = None

    @property
    def raw(self) -> dict:
        """原始数据字典"""
        return self._raw_data

    @property
    def parsed(self) -> Optional[ChatCompletionStreamChunk]:
        """解析后的 Pydantic 模型"""
        if self._chunk is None:
            try:
                self._chunk = ChatCompletionStreamChunk(**self._raw_data)
            except Exception:
                pass
        return self._chunk

    @property
    def id(self) -> Optional[str]:
        """响应 ID"""
        return self._raw_data.get("id")

    @property
    def model(self) -> Optional[str]:
        """模型名称"""
        return self._raw_data.get("model")

    @property
    def content(self) -> Optional[str]:
        """Delta 内容"""
        choices = self._raw_data.get("choices", [])
        if choices:
            delta = choices[0].get("delta", {})
            return delta.get("content")
        return None

    @property
    def reasoning_content(self) -> Optional[str]:
        """推理内容（思考链）"""
        choices = self._raw_data.get("choices", [])
        if choices:
            delta = choices[0].get("delta", {})
            return delta.get("reasoning_content")
        return None

    @property
    def finish_reason(self) -> Optional[str]:
        """结束原因"""
        choices = self._raw_data.get("choices", [])
        if choices:
            return choices[0].get("finish_reason")
        return None

    @property
    def is_done(self) -> bool:
        """是否为结束标记"""
        return self.finish_reason is not None

    def __repr__(self) -> str:
        content_preview = (self.content or "")[:50]
        if len(content_preview) == 50:
            content_preview += "..."
        return f"StreamChunk(id={self.id}, content={content_preview!r}, finish_reason={self.finish_reason})"


class StreamResponse:
    """流式响应迭代器

    封装 SSE 流式响应，提供便捷的迭代访问。

    Example:
        >>> for chunk in client.chat.completions.create(..., stream=True):
        ...     if chunk.content:
        ...         print(chunk.content, end="", flush=True)
    """

    def __init__(self, response_iter: Iterator[bytes]):
        self._iter = response_iter
        self._buffer = ""
        self._chunk_count = 0

    def _parse_sse_line(self, line: str) -> Optional[StreamChunk]:
        """解析 SSE 数据行

        Args:
            line: SSE 数据行

        Returns:
            StreamChunk 或 None（如果是结束标记或空行）
        """
        line = line.strip()
        if not line:
            return None

        # 处理 data: 前缀
        if line.startswith("data:"):
            data_str = line[5:].strip()

            # 检查结束标记
            if data_str == "[DONE]":
                return None

            try:
                data = json.loads(data_str)
                self._chunk_count += 1
                return StreamChunk(data)
            except json.JSONDecodeError as e:
                raise StreamError(f"Failed to parse SSE data: {e}", details={"line": line})

        return None

    def __iter__(self) -> Iterator[StreamChunk]:
        """迭代流式响应块"""
        for raw_bytes in self._iter:
            # 解码字节
            if isinstance(raw_bytes, bytes):
                chunk_str = raw_bytes.decode("utf-8", errors="replace")
            else:
                chunk_str = str(raw_bytes)

            self._buffer += chunk_str

            # 按行处理
            while "\n" in self._buffer:
                line, self._buffer = self._buffer.split("\n", 1)
                stream_chunk = self._parse_sse_line(line)
                if stream_chunk is not None:
                    yield stream_chunk

        # 处理缓冲区中剩余的数据
        if self._buffer.strip():
            stream_chunk = self._parse_sse_line(self._buffer)
            if stream_chunk is not None:
                yield stream_chunk
            self._buffer = ""

    def iter_content(self) -> Iterator[str]:
        """仅迭代内容文本

        便捷方法，只返回 content 字段，跳过空块。

        Yields:
            内容文本片段
        """
        for chunk in self:
            if chunk.content:
                yield chunk.content

    def collect_content(self) -> str:
        """收集所有内容

        将所有内容块合并为一个字符串。

        Returns:
            完整的内容字符串
        """
        return "".join(self.iter_content())

    @property
    def chunk_count(self) -> int:
        """已处理的块数量"""
        return self._chunk_count


class AsyncStreamResponse:
    """异步流式响应迭代器

    封装异步 SSE 流式响应。
    """

    def __init__(self, response_aiter):
        self._aiter = response_aiter
        self._buffer = ""
        self._chunk_count = 0

    def _parse_sse_line(self, line: str) -> Optional[StreamChunk]:
        """解析 SSE 数据行"""
        line = line.strip()
        if not line:
            return None

        if line.startswith("data:"):
            data_str = line[5:].strip()

            if data_str == "[DONE]":
                return None

            try:
                data = json.loads(data_str)
                self._chunk_count += 1
                return StreamChunk(data)
            except json.JSONDecodeError as e:
                raise StreamError(f"Failed to parse SSE data: {e}", details={"line": line})

        return None

    def __aiter__(self) -> "AsyncStreamResponse":
        return self

    async def __anext__(self) -> StreamChunk:
        """异步获取下一个流式响应块"""
        while True:
            # 先处理缓冲区中的行
            while "\n" in self._buffer:
                line, self._buffer = self._buffer.split("\n", 1)
                stream_chunk = self._parse_sse_line(line)
                if stream_chunk is not None:
                    return stream_chunk

            # 从迭代器获取更多数据
            try:
                raw_bytes = await self._aiter.__anext__()
                if isinstance(raw_bytes, bytes):
                    chunk_str = raw_bytes.decode("utf-8", errors="replace")
                else:
                    chunk_str = str(raw_bytes)
                self._buffer += chunk_str
            except StopAsyncIteration:
                # 处理剩余缓冲区
                if self._buffer.strip():
                    stream_chunk = self._parse_sse_line(self._buffer)
                    self._buffer = ""
                    if stream_chunk is not None:
                        return stream_chunk
                raise

    async def iter_content(self) -> "AsyncContentIterator":
        """仅迭代内容文本"""
        return AsyncContentIterator(self)

    async def collect_content(self) -> str:
        """收集所有内容"""
        content_parts = []
        async for chunk in self:
            if chunk.content:
                content_parts.append(chunk.content)
        return "".join(content_parts)

    @property
    def chunk_count(self) -> int:
        """已处理的块数量"""
        return self._chunk_count


class AsyncContentIterator:
    """异步内容迭代器"""

    def __init__(self, stream: AsyncStreamResponse):
        self._stream = stream

    def __aiter__(self):
        return self

    async def __anext__(self) -> str:
        while True:
            chunk = await self._stream.__anext__()
            if chunk.content:
                return chunk.content
            # 如果没有内容但结束了，停止迭代
            if chunk.is_done:
                raise StopAsyncIteration
