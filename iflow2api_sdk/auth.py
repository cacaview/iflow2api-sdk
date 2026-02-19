"""认证签名模块

实现 iFlow API 的 HMAC-SHA256 签名认证。
"""

import hashlib
import hmac
import time
import uuid
from dataclasses import dataclass
from typing import Optional

from .exceptions import AuthenticationError


# iFlow CLI 特殊 User-Agent，用于解锁更多模型
IFLOW_CLI_USER_AGENT = "iFlow-Cli"


@dataclass
class AuthConfig:
    """认证配置

    Attributes:
        api_key: API 密钥
        session_id: 会话 ID（可选，默认自动生成）
        conversation_id: 对话 ID（可选，默认自动生成）
    """

    api_key: str
    session_id: Optional[str] = None
    conversation_id: Optional[str] = None

    def __post_init__(self):
        if not self.api_key:
            raise AuthenticationError("API key is required")
        if not self.session_id:
            self.session_id = str(uuid.uuid4())
        if not self.conversation_id:
            self.conversation_id = str(uuid.uuid4())


def generate_signature(
    user_agent: str,
    session_id: str,
    timestamp: int,
    api_key: str,
) -> str:
    """生成 iFlow API 签名 (HMAC-SHA256)

    签名算法来源于 iflow-cli 源码:
    - 算法: HMAC-SHA256
    - 密钥: apiKey
    - 签名内容: `{user_agent}:{session_id}:{timestamp}`
    - 输出: 十六进制字符串

    Args:
        user_agent: User-Agent 字符串
        session_id: 会话 ID
        timestamp: 时间戳（毫秒）
        api_key: API 密钥

    Returns:
        HMAC-SHA256 签名的十六进制字符串

    Raises:
        AuthenticationError: 签名生成失败
    """
    if not api_key:
        raise AuthenticationError("API key is required for signature generation")

    message = f"{user_agent}:{session_id}:{timestamp}"
    try:
        return hmac.new(
            api_key.encode("utf-8"),
            message.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
    except Exception as e:
        raise AuthenticationError(f"Failed to generate signature: {e}")


def build_headers(
    auth_config: AuthConfig,
    stream: bool = False,
) -> dict:
    """构建请求头

    模仿 iFlow CLI 的请求头设置:
    - user-agent: iFlow-Cli
    - session-id: 会话ID
    - conversation-id: 对话ID
    - x-iflow-signature: HMAC-SHA256 签名
    - x-iflow-timestamp: 时间戳(毫秒)

    Args:
        auth_config: 认证配置
        stream: 是否流式请求，流式请求时不设置 Accept 头

    Returns:
        请求头字典
    """
    timestamp = int(time.time() * 1000)  # 毫秒时间戳

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_config.api_key}",
        "User-Agent": IFLOW_CLI_USER_AGENT,
        "session-id": auth_config.session_id,
        "conversation-id": auth_config.conversation_id,
    }

    # 非流式请求设置 Accept 头，流式请求不设置以让上游返回 SSE
    if not stream:
        headers["Accept"] = "application/json"

    # 添加签名
    signature = generate_signature(
        IFLOW_CLI_USER_AGENT,
        auth_config.session_id,
        timestamp,
        auth_config.api_key,
    )
    headers["x-iflow-signature"] = signature
    headers["x-iflow-timestamp"] = str(timestamp)

    return headers
