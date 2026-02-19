"""Models API 模块

封装模型列表 API。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..models.common import ModelInfo, ModelListResponse

if TYPE_CHECKING:
    from ..client import IFlowClient
    from ..client_async import AsyncIFlowClient


class ModelsAPI:
    """Models API（同步）"""

    def __init__(self, client: "IFlowClient"):
        self._client = client

    def list(self) -> ModelListResponse:
        """获取可用模型列表

        Returns:
            ModelListResponse: 模型列表响应

        Example:
            >>> models = client.models.list()
            >>> for model in models.data:
            ...     print(model.id)
        """
        response = self._client._request("GET", "/models")
        return ModelListResponse(**response)

    def get_model_ids(self) -> list[str]:
        """获取模型 ID 列表

        便捷方法，返回所有模型的 ID。

        Returns:
            模型 ID 列表
        """
        models = self.list()
        return [m.id for m in models.data]


class AsyncModelsAPI:
    """Models API（异步）"""

    def __init__(self, client: "AsyncIFlowClient"):
        self._client = client

    async def list(self) -> ModelListResponse:
        """获取可用模型列表

        Returns:
            ModelListResponse: 模型列表响应
        """
        response = await self._client._request("GET", "/models")
        return ModelListResponse(**response)

    async def get_model_ids(self) -> list[str]:
        """获取模型 ID 列表

        Returns:
            模型 ID 列表
        """
        models = await self.list()
        return [m.id for m in models.data]
