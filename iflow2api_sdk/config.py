"""配置管理模块

管理 SDK 的配置，包括默认值和环境变量支持。
"""

import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from .auth import AuthConfig
from .exceptions import ConfigurationError


# 默认配置
DEFAULT_BASE_URL = "https://apis.iflow.cn/v1"
DEFAULT_TIMEOUT = 300.0
DEFAULT_CONNECT_TIMEOUT = 10.0
DEFAULT_MAX_RETRIES = 3


@dataclass
class ClientConfig:
    """客户端配置

    Attributes:
        api_key: API 密钥（必需）
        base_url: API 基础 URL
        timeout: 请求超时时间（秒）
        connect_timeout: 连接超时时间（秒）
        max_retries: 最大重试次数
        session_id: 会话 ID（可选）
        conversation_id: 对话 ID（可选）
        api_key_expires_at: API Key 过期时间（OAuth 模式下与 token 同步）
    """

    api_key: str
    base_url: str = DEFAULT_BASE_URL
    timeout: float = DEFAULT_TIMEOUT
    connect_timeout: float = DEFAULT_CONNECT_TIMEOUT
    max_retries: int = DEFAULT_MAX_RETRIES
    session_id: Optional[str] = None
    conversation_id: Optional[str] = None
    api_key_expires_at: Optional[datetime] = None

    def __post_init__(self):
        if not self.api_key:
            raise ConfigurationError("API key is required")

        # 移除 base_url 末尾的斜杠
        self.base_url = self.base_url.rstrip("/")

    def to_auth_config(self) -> AuthConfig:
        """转换为认证配置"""
        return AuthConfig(
            api_key=self.api_key,
            session_id=self.session_id,
            conversation_id=self.conversation_id,
        )

    def is_api_key_expired(self) -> bool:
        """检查 API Key 是否已过期

        Returns:
            True 如果已过期或即将过期（5分钟内），False 如果未过期或未设置过期时间
        """
        if self.api_key_expires_at is None:
            return False
        # 提前 5 分钟认为过期，避免临界情况
        from datetime import timedelta
        return datetime.now() >= self.api_key_expires_at - timedelta(minutes=5)

    @classmethod
    def from_env(cls) -> "ClientConfig":
        """从环境变量创建配置

        环境变量:
            IFLOW_API_KEY: API 密钥（必需）
            IFLOW_BASE_URL: API 基础 URL（可选）
            IFLOW_TIMEOUT: 请求超时时间（可选）
            IFLOW_CONNECT_TIMEOUT: 连接超时时间（可选）
            IFLOW_MAX_RETRIES: 最大重试次数（可选）
            IFLOW_API_KEY_EXPIRES_AT: API Key 过期时间（ISO 格式，可选）

        Returns:
            ClientConfig 实例

        Raises:
            ConfigurationError: 缺少必需的环境变量
        """
        api_key = os.environ.get("IFLOW_API_KEY")
        if not api_key:
            raise ConfigurationError(
                "API key not found. Set IFLOW_API_KEY environment variable."
            )

        # 解析过期时间
        expires_at = None
        expires_at_str = os.environ.get("IFLOW_API_KEY_EXPIRES_AT")
        if expires_at_str:
            try:
                expires_at = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
            except ValueError:
                pass  # 忽略无效的日期格式

        return cls(
            api_key=api_key,
            base_url=os.environ.get("IFLOW_BASE_URL", DEFAULT_BASE_URL),
            timeout=float(os.environ.get("IFLOW_TIMEOUT", DEFAULT_TIMEOUT)),
            connect_timeout=float(os.environ.get("IFLOW_CONNECT_TIMEOUT", DEFAULT_CONNECT_TIMEOUT)),
            max_retries=int(os.environ.get("IFLOW_MAX_RETRIES", DEFAULT_MAX_RETRIES)),
            api_key_expires_at=expires_at,
        )


@dataclass
class RequestOptions:
    """请求选项

    用于单个请求的额外配置。

    Attributes:
        timeout: 请求超时时间（秒），None 表示使用客户端默认值
        headers: 额外的请求头
        extra: 其他额外参数
    """

    timeout: Optional[float] = None
    headers: dict = field(default_factory=dict)
    extra: dict = field(default_factory=dict)
