"""同步客户端模块

提供同步的 IFlow API 客户端。
"""

from typing import Any, Iterator, Optional

import httpx

from .api.chat import ChatAPI
from .api.models import ModelsAPI
from .auth import AuthConfig, build_headers
from .config import ClientConfig, RequestOptions
from .exceptions import (
    APIError,
    AuthenticationError,
    ConnectionError,
    RateLimitError,
    TimeoutError,
)


class IFlowClient:
    """IFlow API 同步客户端

    提供对 iFlow API 的同步访问。

    Example:
        >>> from iflow2api_sdk import IFlowClient
        >>> 
        >>> # 使用 API Key 初始化
        >>> client = IFlowClient(api_key="your-api-key")
        >>> 
        >>> # 或使用本地代理
        >>> client = IFlowClient(
        ...     api_key="not-needed",
        ...     base_url="http://localhost:28000/v1"
        ... )
        >>> 
        >>> # 获取模型列表
        >>> models = client.models.list()
        >>> print([m.id for m in models.data])
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
        self._client: Optional[httpx.Client] = None

        # 初始化 API 模块
        self._models = ModelsAPI(self)
        self._chat = ChatAPI(self)

    @property
    def models(self) -> ModelsAPI:
        """Models API"""
        return self._models

    @property
    def chat(self) -> ChatAPI:
        """Chat API"""
        return self._chat

    def _get_client(self) -> httpx.Client:
        """获取或创建 HTTP 客户端"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.Client(
                timeout=httpx.Timeout(
                    self._config.timeout,
                    connect=self._config.connect_timeout,
                ),
                follow_redirects=True,
            )
        return self._client

    def _request(
        self,
        method: str,
        path: str,
        json: Optional[dict] = None,
        options: Optional[RequestOptions] = None,
    ) -> dict:
        """发送 HTTP 请求

        Args:
            method: HTTP 方法
            path: API 路径
            json: JSON 请求体
            options: 请求选项

        Returns:
            响应 JSON 数据

        Raises:
            APIError: API 错误
            ConnectionError: 连接错误
            TimeoutError: 超时错误
        """
        client = self._get_client()
        url = f"{self._config.base_url}{path}"

        # 构建请求头
        stream = path == "/chat/completions" and json and json.get("stream", False)
        headers = build_headers(self._auth_config, stream=stream)

        # 合并额外请求头
        if options and options.headers:
            headers.update(options.headers)

        # 获取超时设置
        timeout = options.timeout if options and options.timeout else self._config.timeout

        try:
            response = client.request(
                method,
                url,
                headers=headers,
                json=json,
                timeout=timeout,
            )

            # 检查状态码
            if response.status_code >= 400:
                self._handle_error_response(response)

            return response.json()

        except httpx.TimeoutException as e:
            raise TimeoutError(f"Request timed out: {e}")
        except httpx.ConnectError as e:
            raise ConnectionError(f"Failed to connect to server: {e}")
        except httpx.HTTPStatusError as e:
            self._handle_error_response(e.response)
        except Exception as e:
            if isinstance(e, (APIError, TimeoutError, ConnectionError)):
                raise
            raise APIError(f"Request failed: {e}")

    def _request_stream(
        self,
        method: str,
        path: str,
        json: Optional[dict] = None,
        options: Optional[RequestOptions] = None,
    ) -> Iterator[bytes]:
        """发送流式 HTTP 请求

        Args:
            method: HTTP 方法
            path: API 路径
            json: JSON 请求体
            options: 请求选项

        Yields:
            响应字节流
        """
        client = self._get_client()
        url = f"{self._config.base_url}{path}"

        # 构建请求头（流式）
        headers = build_headers(self._auth_config, stream=True)

        if options and options.headers:
            headers.update(options.headers)

        timeout = options.timeout if options and options.timeout else self._config.timeout

        try:
            with client.stream(
                method,
                url,
                headers=headers,
                json=json,
                timeout=timeout,
            ) as response:
                if response.status_code >= 400:
                    # 尝试读取错误响应
                    try:
                        error_data = response.json()
                        self._handle_error_response(response, error_data)
                    except Exception:
                        self._handle_error_response(response)

                for chunk in response.iter_bytes():
                    yield chunk

        except httpx.TimeoutException as e:
            raise TimeoutError(f"Stream request timed out: {e}")
        except httpx.ConnectError as e:
            raise ConnectionError(f"Failed to connect to server: {e}")
        except Exception as e:
            if isinstance(e, (APIError, TimeoutError, ConnectionError)):
                raise
            raise APIError(f"Stream request failed: {e}")

    def _handle_error_response(
        self,
        response: httpx.Response,
        error_data: Optional[dict] = None,
    ) -> None:
        """处理错误响应

        Args:
            response: HTTP 响应
            error_data: 已解析的错误数据（可选）

        Raises:
            APIError 或其子类
        """
        status_code = response.status_code

        if error_data is None:
            try:
                error_data = response.json()
            except Exception:
                error_data = {}

        # 提取错误信息
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

        # 特殊状态码处理
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

    def close(self) -> None:
        """关闭客户端"""
        if self._client and not self._client.is_closed:
            self._client.close()
            self._client = None

    def __enter__(self) -> "IFlowClient":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def __repr__(self) -> str:
        return f"IFlowClient(base_url={self._config.base_url!r})"
