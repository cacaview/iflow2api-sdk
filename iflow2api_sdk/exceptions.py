"""异常定义模块

定义 SDK 中使用的所有异常类型。
"""

from typing import Optional


class IFlowError(Exception):
    """SDK 基础异常类"""

    def __init__(self, message: str, details: Optional[dict] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} - {self.details}"
        return self.message


class AuthenticationError(IFlowError):
    """认证错误

    当 API 密钥无效或签名失败时抛出。
    """
    pass


class ConfigurationError(IFlowError):
    """配置错误

    当配置缺失或无效时抛出。
    """
    pass


class APIError(IFlowError):
    """API 错误

    当 API 请求失败时抛出。

    Attributes:
        status_code: HTTP 状态码
        error_type: 错误类型
        request_id: 请求 ID（如果有）
    """

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        error_type: Optional[str] = None,
        request_id: Optional[str] = None,
        details: Optional[dict] = None,
    ):
        self.status_code = status_code
        self.error_type = error_type
        self.request_id = request_id
        super().__init__(message, details)

    def __str__(self) -> str:
        parts = [self.message]
        if self.status_code:
            parts.append(f"status_code={self.status_code}")
        if self.error_type:
            parts.append(f"type={self.error_type}")
        if self.request_id:
            parts.append(f"request_id={self.request_id}")
        if self.details:
            parts.append(f"details={self.details}")
        return " | ".join(parts)


class RateLimitError(APIError):
    """速率限制错误

    当请求超过速率限制时抛出。
    """

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        **kwargs,
    ):
        self.retry_after = retry_after
        super().__init__(message, status_code=429, error_type="rate_limit_error", **kwargs)

    def __str__(self) -> str:
        base = super().__str__()
        if self.retry_after:
            return f"{base} | retry_after={self.retry_after}s"
        return base


class StreamError(IFlowError):
    """流式响应错误

    当处理流式响应时发生错误时抛出。
    """
    pass


class TimeoutError(IFlowError):
    """超时错误

    当请求超时时抛出。
    """
    pass


class ConnectionError(IFlowError):
    """连接错误

    当无法连接到服务器时抛出。
    """
    pass


class ModelNotFoundError(APIError):
    """模型不存在错误

    当请求的模型不存在时抛出。
    """

    def __init__(self, message: str = "Model not found", model_id: Optional[str] = None, **kwargs):
        self.model_id = model_id
        if model_id:
            message = f"{message}: {model_id}"
        super().__init__(message, status_code=404, error_type="model_not_found", **kwargs)


class InvalidRequestError(APIError):
    """无效请求错误

    当请求参数无效时抛出。
    """

    def __init__(self, message: str = "Invalid request", **kwargs):
        super().__init__(message, error_type="invalid_request_error", **kwargs)


class ValidationError(IFlowError):
    """验证错误

    当请求参数验证失败时抛出。
    """

    def __init__(self, message: str, field: Optional[str] = None, details: Optional[dict] = None):
        self.field = field
        super().__init__(message, details)

    def __str__(self) -> str:
        if self.field:
            return f"Validation error on field '{self.field}': {self.message}"
        return f"Validation error: {self.message}"
