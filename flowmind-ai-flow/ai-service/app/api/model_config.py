"""
FlowMind 智能流程设计服务 - 模型配置管理 API

本模块提供模型配置管理相关的接口，支持动态添加、删除、管理自定义模型。
"""

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.adapters import ModelFactory
from app.api.deps import require_auth
from app.config.settings import settings
from app.core.exceptions import (
    ConfigurationException,
    ResourceNotFoundException,
    ServiceUnavailableException,
    ValidationException,
)
from app.domain.dto import ResponseVO
from app.infra.logger import logger
from app.utils.auth import TokenUser

router = APIRouter(
    prefix="/models",
    tags=["模型配置"],
)


class ModelConfigInput(BaseModel):
    """模型配置输入模型"""

    model: str = Field(..., description="模型名称")
    base_url: str = Field(..., description="API 基础 URL")
    api_key: str | None = Field(None, description="API Key（可选）")
    temperature: float = Field(0.7, description="温度参数", ge=0.0, le=2.0)
    max_tokens: int = Field(2000, description="最大生成 token 数")
    top_p: float = Field(0.9, description="Top-p 采样参数", ge=0.0, le=1.0)
    timeout: int = Field(60, description="超时时间（秒）")


class ModelConfigResponse(BaseModel):
    """模型配置响应模型"""

    name: str = Field(..., description="模型标识名称")
    model: str = Field(..., description="模型名称")
    base_url: str = Field(..., description="API 基础 URL")
    is_custom: bool = Field(default=False, description="是否为自定义模型")


class PriorityUpdateInput(BaseModel):
    """优先级更新输入"""

    priority: list[str] = Field(..., description="模型优先级列表，按优先级从高到低排列")


class FallbackConfigInput(BaseModel):
    """降级配置输入"""

    enabled: bool | None = Field(None, description="是否启用降级")
    max_retries: int | None = Field(None, description="最大重试次数", ge=0, le=10)
    retry_interval: float | None = Field(
        None, description="重试间隔（秒）", ge=0.0, le=10.0
    )


class AddModelInput(BaseModel):
    """添加模型输入"""

    name: str = Field(..., description="模型标识名称（用于内部引用）")
    config: ModelConfigInput = Field(..., description="模型配置")
    set_as_priority: bool = Field(default=True, description="是否添加到优先级列表末尾")


@router.get("", response_model=ResponseVO[list[ModelConfigResponse]])
async def list_models() -> ResponseVO[list[ModelConfigResponse]]:
    """获取所有模型配置列表"""
    try:
        adapters = ModelFactory.get_all_adapters()
        custom_models = getattr(ModelFactory, "_custom_models", set())

        data = [
            ModelConfigResponse(
                name=name,
                model=adapter.config.model_name,
                base_url=adapter.config.base_url,
                is_custom=name in custom_models,
            )
            for name, adapter in adapters.items()
        ]
        return ResponseVO.success(data)
    except Exception as e:
        logger.error(f"获取模型列表失败：{e}")
        raise ServiceUnavailableException(
            service_name="模型工厂",
            reason=str(e),
        )


@router.get("/priority", response_model=ResponseVO[list[str]])
async def get_priority() -> ResponseVO[list[str]]:
    """获取当前模型优先级"""
    try:
        return ResponseVO.success(settings.get_model_priority())
    except Exception as e:
        logger.error(f"获取优先级失败：{e}")
        raise ConfigurationException(
            message=str(e),
            config_key="model_priority",
        )


@router.post("", response_model=ResponseVO[ModelConfigResponse])
async def add_model(
    input_data: AddModelInput,
    current_user: TokenUser = Depends(require_auth),
) -> ResponseVO[ModelConfigResponse]:
    """添加自定义模型"""
    try:
        adapters = ModelFactory.get_all_adapters()
        if input_data.name in adapters:
            raise ValidationException(
                message=f"模型标识已存在：{input_data.name}",
                field="name",
            )

        config_dict = {
            "model_name": input_data.config.model,
            "base_url": input_data.config.base_url,
            "api_key": input_data.config.api_key,
            "temperature": input_data.config.temperature,
            "max_tokens": input_data.config.max_tokens,
            "top_p": input_data.config.top_p,
            "timeout": input_data.config.timeout,
        }

        adapter = ModelFactory.create_adapter(input_data.name, config_dict)
        ModelFactory.add_adapter(input_data.name, adapter)

        if not hasattr(ModelFactory, "_custom_models"):
            ModelFactory._custom_models = set()
        ModelFactory._custom_models.add(input_data.name)

        if input_data.set_as_priority:
            current_priority = settings.get_model_priority()
            if input_data.name not in current_priority:
                current_priority.append(input_data.name)
                settings.model_priority = ",".join(current_priority)

        logger.info(f"已添加自定义模型：{input_data.name}")

        return ResponseVO.success(
            ModelConfigResponse(
                name=input_data.name,
                model=input_data.config.model,
                base_url=input_data.config.base_url,
                is_custom=True,
            )
        )

    except ValidationException:
        raise
    except Exception as e:
        logger.error(f"添加模型失败：{e}")
        raise ServiceUnavailableException(
            service_name="模型工厂",
            reason=str(e),
        )


@router.delete("/{model_name}", response_model=ResponseVO[dict[str, Any]])
async def remove_model(
    model_name: str,
    current_user: TokenUser = Depends(require_auth),
) -> ResponseVO[dict[str, Any]]:
    """删除自定义模型"""
    try:
        adapters = ModelFactory.get_all_adapters()
        if model_name not in adapters:
            raise ResourceNotFoundException(
                resource_type="模型",
                resource_id=model_name,
            )

        custom_models = getattr(ModelFactory, "_custom_models", set())
        if model_name not in custom_models:
            raise ValidationException(
                message=f"不能删除内置模型：{model_name}",
                field="model_name",
            )

        ModelFactory.remove_adapter(model_name)
        custom_models.discard(model_name)

        current_priority = settings.get_model_priority()
        if model_name in current_priority:
            current_priority.remove(model_name)
            settings.model_priority = ",".join(current_priority)

        logger.info(f"已删除自定义模型：{model_name}")

        return ResponseVO.success(
            {"success": True, "message": f"已删除模型：{model_name}"}
        )

    except (ResourceNotFoundException, ValidationException):
        raise
    except Exception as e:
        logger.error(f"删除模型失败：{e}")
        raise ServiceUnavailableException(
            service_name="模型工厂",
            reason=str(e),
        )


@router.put("/priority", response_model=ResponseVO[dict[str, Any]])
async def update_priority(
    input_data: PriorityUpdateInput,
    current_user: TokenUser = Depends(require_auth),
) -> ResponseVO[dict[str, Any]]:
    """更新模型优先级"""
    try:
        adapters = ModelFactory.get_all_adapters()
        for model in input_data.priority:
            if model not in adapters:
                raise ResourceNotFoundException(
                    resource_type="模型",
                    resource_id=model,
                )

        settings.model_priority = ",".join(input_data.priority)
        ModelFactory.update_priority(input_data.priority)

        logger.info(f"已更新模型优先级：{input_data.priority}")

        return ResponseVO.success(
            {
                "success": True,
                "message": "优先级已更新",
                "priority": input_data.priority,
            }
        )

    except ResourceNotFoundException:
        raise
    except Exception as e:
        logger.error(f"更新优先级失败：{e}")
        raise ConfigurationException(
            message=str(e),
            config_key="model_priority",
        )


@router.put("/fallback", response_model=ResponseVO[dict[str, Any]])
async def update_fallback_config(
    input_data: FallbackConfigInput,
    current_user: TokenUser = Depends(require_auth),
) -> ResponseVO[dict[str, Any]]:
    """更新降级配置"""
    try:
        new_config = settings.update_fallback_config(
            enabled=input_data.enabled,
            max_retries=input_data.max_retries,
            retry_interval=input_data.retry_interval,
        )

        ModelFactory.update_fallback_config(
            enabled=input_data.enabled,
            max_retries=input_data.max_retries,
            retry_interval=input_data.retry_interval,
        )

        logger.info(f"已更新降级配置：enabled={input_data.enabled}")

        return ResponseVO.success(
            {
                "success": True,
                "message": "降级配置已更新",
                "config": new_config,
            }
        )

    except Exception as e:
        logger.error(f"更新降级配置失败：{e}")
        raise ConfigurationException(
            message=str(e),
            config_key="fallback",
        )
