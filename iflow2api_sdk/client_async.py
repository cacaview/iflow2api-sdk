"""异步客户端模块

提供异步的 IFlow API 客户端。
"""

from typing import Any, AsyncIterator, Optional

import httpx

from .api.chat import AsyncChatAPI
from .api.models import AsyncModelsAPI
from .auth import AuthConfig, build_headers
from .config import ClientConfig, RequestOptions
from .exceptions import (
    APIError,
    AuthenticationError,
    ConnectionError,
    RateLimitError,
    TimeoutError,
)


class AsyncIFlowClient:
    """IFlow API 异步客户端

    提供对 iFlow API 的异步访问。

    Example:
        >>> import asyncio
        >>> from iflow2api_sdk import AsyncIFlowClient
        >>> 
        >>> async def main():
        ...     async with AsyncIFlowClient(api_key="your-api-key") as client:
        ...         # 获取模型列表
        ...         models = await client.models.list()
        ...         print([m.id for m in models.data])
        ...         
        ...         # Chat Completions
        ...         response = await client.chat.completions.create(
        ...             model="glm-5",
        ...             messages=[{"role": "user", "content": "你好！"}]
        ...         )
        ...         print(response.choices[0].message.content)
        ...         
        ...         # 流式响应
        ...         stream = await client.chat.completions.create(
        ...             model="glm-5",
        ...             messages=[{"role": "user", "content": "写一首诗"}],
        ...             stream=True
        ...         )
        ...         async for chunk in stream:
        ...             if chunk.content:
        ...                 print(chunk.content, end="", flush=True)
        >>> 
        >>> asyncio.run(main())
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 300.0,
        connect_timeout: float = 10.0,
        **kwargs,
    ):
        """初始化客户端

        Args:
            api_key: API 密钥（必需，除非使用本地代理）
            base_url: API 基础 URL（默认: https://apis.iflow.cn/v1）
            timeout: 请求超时时间（秒）
            connect_timeout: 连接超时时间（秒）
            **kwargs: 其他配置参数
        """
        # 如果未提供 api_key，尝试从环境变量获取
        if api_key is None:
            import os
            api_key = os.environ.get("IFLOW_API_KEY")
        
        if not api_key:
            raise AuthenticationError(
                "API key is required. Pass it as argument or set IFLOW_API_KEY environment variable."
            )

        self._config = ClientConfig(
            api_key=api_key,
            base_url=base_url or "https://apis.iflow.cn/v1",
            timeout=timeout,
            connect_timeout=connect_timeout,
            **kwargs,
        )

        self._auth_config = self._config.to_auth_config()
        self._client: Optional[httpx.AsyncClient] = None

        # 初始化 API 模块
        self._models = AsyncModelsAPI(self)
        self._chat = AsyncChatAPI(self)

    @property
    def models(self) -> AsyncModelsAPI:
        """Models API"""
        return self._models

    @property
    def chat(self) -> AsyncChatAPI:
        """Chat API"""
        return self._chat

    async def _get_client(self) -> httpx.AsyncClient:
        """获取或创建 HTTP 客户端"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(
                    self._config.timeout,
                    connect=self._config.connect_timeout,
                ),
                follow_redirects=True,
            )
        return self._client

    async def _request(
        self,
        method: str,
        path: str,
        json: Optional[dict] = None,
        options: Optional[RequestOptions] = None,
    ) -> dict:
        """发送 HTTP 请求（异步）

        Args:
            method: HTTP 方法
            path: API 路径
            json: JSON 请求体
            options: 请求选项

        Returns:
            响应 JSON 数据
        """
        client = await self._get_client()
        url = f"{self._config.base_url}{path}"

        # 构建请求头
        stream = path == "/chat/completions" and json and json.get("stream", False)
        headers = build_headers(self._auth_config, stream=stream)

        if options and options.headers:
            headers.update(options.headers)

        timeout = options.timeout if options and options.timeout else self._config.timeout

        try:
            response = await client.request(
                method,
                url,
                headers=headers,
                json=json,
                timeout=timeout,
            )

            if response.status_code >= 400:
                await self._handle_error_response(response)

            return response.json()

        except httpx.TimeoutException as e:
            raise TimeoutError(f"Request timed out: {e}")
        except httpx.ConnectError as e:
            raise ConnectionError(f"Failed to connect to server: {e}")
        except httpx.HTTPStatusError as e:
            await self._handle_error_response(e.response)
        except Exception as e:
            if isinstance(e, (APIError, TimeoutError, ConnectionError)):
                raise
            raise APIError(f"Request failed: {e}")

    async def _request_stream(
        self,
        method: str,
        path: str,
        json: Optional[dict] = None,
        options: Optional[RequestOptions] = None,
    ) -> AsyncIterator[bytes]:
        """发送流式 HTTP 请求（异步）

        Args:
            method: HTTP 方法
            path: API 路径
            json: JSON 请求体
            options: 请求选项

        Yields:
            响应字节流
        """
        client = await self._get_client()
        url = f"{self._config.base_url}{path}"

        headers = build_headers(self._auth_config, stream=True)

        if options and options.headers:
            headers.update(options.headers)

        timeout = options.timeout if options and options.timeout else self._config.timeout

        try:
            async with client.stream(
                method,
                url,
                headers=headers,
                json=json,
                timeout=timeout,
            ) as response:
                if response.status_code >= 400:
                    try:
                        error_data = await response.json()
                        await self._handle_error_response(response, error_data)
                    except Exception:
                        await self._handle_error_response(response)

                async for chunk in response.aiter_bytes():
                    yield chunk

        except httpx.TimeoutException as e:
            raise TimeoutError(f"Stream request timed out: {e}")
        except httpx.ConnectError as e:
            raise ConnectionError(f"Failed to connect to server: {e}")
        except Exception as e:
            if isinstance(e, (APIError, TimeoutError, ConnectionError)):
                raise
            raise APIError(f"Stream request failed: {e}")

    async def _handle_error_response(
        self,
        response: httpx.Response,
        error_data: Optional[dict] = None,
    ) -> None:
        """处理错误响应"""
        status_code = response.status_code

        if error_data is None:
            try:
                error_data = await response.json()
            except Exception:
                error_data = {}

        message = (
            error_data.get("error", {}).get("message")
            or error_data.get("msg")
            or error_data.get("message")
            or f"HTTP {status_code}"
        )

        error_type = (
            error_data.get("error", {}).get("type")
            or error_data.get("type")
            or "api_error"
        )

        request_id = response.headers.get("x-request-id")

        if status_code == 401:
            raise AuthenticationError(
                message,
                details={"status_code": status_code, "error_type": error_type},
            )
        elif status_code == 429:
            retry_after = response.headers.get("retry-after")
            raise RateLimitError(
                message,
                retry_after=int(retry_after) if retry_after else None,
                request_id=request_id,
                details=error_data,
            )
        else:
            raise APIError(
                message,
                status_code=status_code,
                error_type=error_type,
                request_id=request_id,
                details=error_data,
            )

    async def close(self) -> None:
        """关闭客户端"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> "AsyncIFlowClient":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    def __repr__(self) -> str:
        return f"AsyncIFlowClient(base_url={self._config.base_url!r})"
