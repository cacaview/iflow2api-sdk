"""通用数据模型

定义 API 响应中使用的通用数据结构。
"""

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class BaseResponse(BaseModel):
    """响应基类"""

    model_config = ConfigDict(
        extra="allow",  # 允许额外字段
        populate_by_name=True,  # 允许通过字段名填充
    )


class Usage(BaseModel):
    """Token 使用统计"""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    model_config = ConfigDict(extra="allow")


class ModelInfo(BaseModel):
    """模型信息"""

    id: str
    object: str = "model"
    created: int
    owned_by: str = "iflow"
    permission: list[Any] = []
    root: Optional[str] = None
    parent: Optional[str] = None

    model_config = ConfigDict(extra="allow")


class ModelListResponse(BaseResponse):
    """模型列表响应"""

    object: str = "list"
    data: list[ModelInfo] = []
