"""Models API 模块

封装模型列表 API。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..models.common import ModelInfo, ModelListResponse

if TYPE_CHECKING:
    from ..client import IFlowClient
    from ..client_async import AsyncIFlowClient


class VisionModelInfo(ModelInfo):
    """视觉模型信息"""

    supports_vision: bool = True
    max_images: int = 10


class VisionModelListResponse(ModelListResponse):
    """视觉模型列表响应"""

    data: list[VisionModelInfo]


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

    def list_vision(self) -> VisionModelListResponse:
        """获取支持视觉功能的模型列表

        Returns:
            VisionModelListResponse: 视觉模型列表响应

        Example:
            >>> vision_models = client.models.list_vision()
            >>> for model in vision_models.data:
            ...     print(f"{model.id}: max_images={model.max_images}")
        """
        response = self._client._request("GET", "/vision-models")
        return VisionModelListResponse(**response)

    def get_model_ids(self) -> list[str]:
        """获取模型 ID 列表

        便捷方法，返回所有模型的 ID。

        Returns:
            模型 ID 列表
        """
        models = self.list()
        return [m.id for m in models.data]

    def get_vision_model_ids(self) -> list[str]:
        """获取视觉模型 ID 列表

        便捷方法，返回所有支持视觉功能的模型 ID。

        Returns:
            视觉模型 ID 列表
        """
        models = self.list_vision()
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

    async def list_vision(self) -> VisionModelListResponse:
        """获取支持视觉功能的模型列表

        Returns:
            VisionModelListResponse: 视觉模型列表响应
        """
        response = await self._client._request("GET", "/vision-models")
        return VisionModelListResponse(**response)

    async def get_model_ids(self) -> list[str]:
        """获取模型 ID 列表

        Returns:
            模型 ID 列表
        """
        models = await self.list()
        return [m.id for m in models.data]

    async def get_vision_model_ids(self) -> list[str]:
        """获取视觉模型 ID 列表

        便捷方法，返回所有支持视觉功能的模型 ID。

        Returns:
            视觉模型 ID 列表
        """
        models = await self.list_vision()
        return [m.id for m in models.data]
