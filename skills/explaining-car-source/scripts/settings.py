#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Author   : liyandan 
# @Date     : 2026-03-06
# @Description: 应用配置

from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置类"""

    # 基础配置
    app_name: str = Field(default="flowforge", description="应用名称")
    app_port: int = Field(default=8000, description="应用端口")

    # 日志配置
    log_level: str = Field(default="INFO", description="日志级别")
    log_json: bool = Field(default=False, description="是否使用JSON格式日志")
    log_file_path: str = Field(default="logs/app.log", description="日志文件路径")
    log_file_max_size: int = Field(default=10485760, description="日志文件最大大小(字节)，默认10MB")
    log_file_backup_count: int = Field(default=5, description="日志文件备份数量")
    log_format: str = Field(default="%(asctime)s [%(levelname)s] %(app)s %(module)s %(filter)s %(request_id)s %(message)s", description="日志格式")
    log_datefmt: str = Field(default="%Y-%m-%dT%H:%M:%S.000%z", description="日志时间格式")

    # 小瓜Redis配置
    xiaogua_redis_use_sentinel: bool = Field(default=False, description="是否使用哨兵模式")
    xiaogua_redis_password: Optional[str] = Field(default=None, description="Redis密码")
    xiaogua_redis_username: Optional[str] = Field(default=None, description="Redis用户名")
    xiaogua_redis_db: int = Field(default=0, description="Redis数据库")
    xiaogua_redis_host: str = Field(default="localhost", description="Redis地址")
    xiaogua_redis_port: int = Field(default="6379", description="Redis端口")

    xiaogua_redis_sentinel_hosts: str = Field(default="localhost:26379", description="哨兵主机列表")
    xiaogua_redis_sentinel_service_name: str = Field(default="mymaster", description="哨兵服务名")

    # LLM配置
    llm_provider: str = Field(default="openai", description="LLM提供商")
    llm_model: str = Field(default="gpt-4o-mini", description="LLM模型")
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API密钥")

    # 本地模型配置
    qwen3_4b_2507_base_url: str = Field(default="http://119.255.238.69:8002/v1", description="qwen3_4b_2507 Base URL")
    qwen3_4b_2507_api_key: str = Field(default="qwen3_4b_2507", description="qwen3_4b_2507 API Key")
    qwen3_4b_2507_model: str = Field(default="qwen3_4b_2507", description="qwen3_4b_2507 模型名称")
    qwen3_4b_2507_max_tokens: int = Field(default=512, description="qwen3_4b_2507 最大输出token数")

    # 火山引擎模型配置
    kimi_k2_250905_base_url: str = Field(default="https://ark.cn-beijing.volces.com/api/v3", description="火山引擎 Kimi-k2-250905 Base URL")
    kimi_k2_250905_api_key: Optional[str] = Field(default=None, description="火山引擎 Kimi-k2-250905 API Key")
    kimi_k2_250905_model: str = Field(default="kimi-k2-250905", description="火山引擎 Kimi-k2-250905 模型名称")
    kimi_k2_250905_max_tokens: int = Field(default=512, description="火山引擎 Kimi-k2-250905 最大输出token数")

    # 风控接口配置
    risk_control_base_url: str = Field(default="http://content-audit.guazi-apps.com/riskcontrol/text", description="风控接口URL")
    risk_control_app_key: str = Field(default="llm_agent_to_c", description="风控接口AppKey")
    risk_control_app_secret: str = Field(default="gre32klkgers35Q5QvE", description="风控接口AppSecret")
    risk_control_app_id: str = Field(default="llm_agent_to_c", description="风控接口AppId")
    risk_control_event_id: str = Field(default="llm_agent_to_c_text", description="风控接口EventId")

    # 会话历史接口配置
    history_prod_base_url: str = Field(default="http://ai-agent.guazi-apps.com/api/internal/agent/get_conversation_history_v2", description="会话历史接口URL")
    history_preview_base_url: str = Field(default="http://ai-agent-preview.guazi-apps.com/api/internal/agent/get_conversation_history_v2", description="预发环境会话历史接口URL")
    history_test_base_url: str = Field(default="http://ai-agent.guazi-cloud.com/api/internal/agent/get_conversation_history_v2", description="测试环境会话历史接口URL")
    history_app_key: str = Field(default="dify-platform-api", description="会话历史接口AppKey")
    history_app_secret: str = Field(default="KY2DpyRQ", description="会话历史接口AppSecret")

    # 售后CRM会话历史接口配置
    history_after_sales_crm_prod_base_url: str = Field(default="http://eim-plt-customer.guazi.com/api/aiagent/convert/im-history", description="售后CRM会话历史接口URL")
    history_after_sales_crm_preview_base_url: str = Field(default="http://eim-plt-customer-preview.guazi-apps.com/api/aiagent/convert/im-history",description="预发环境售后CRM会话历史接口URL")
    history_after_sales_crm_test_base_url: str = Field(default="http://eim-plt-customer-beta.guazi-cloud.com/api/aiagent/convert/im-history",description="测试环境售后CRM会话历史接口URL")

    # 订单接口配置
    order_base_url: str = Field(default="http://order-search.guazi-apps.com/order/query/getOrderByConditionFromEs", description="订单接口URL")
    order_app_key: str = Field(default="ig-action-server", description="订单接口AppKey")
    order_app_secret: str = Field(default="77d22ef518a1", description="订单接口AppSecret")

    # 车源接口配置
    car_basic_info_base_url: str = Field(default="http://carsource-api.guazi-apps.com/cars-info/internal/carSource/queryCarSource", description="车源基础信息接口URL")
    car_basic_info_app_key: str = Field(default="ai_agent", description="车源基础信息接口AppKey")
    car_basic_info_app_secret: str = Field(default="secAiAgent0228@25OL", description="车源基础信息接口AppSecret")

    # 收藏接口配置
    collection_base_url: str = Field(default="http://mlp-api-feature.guazi-apps.com/api/feature/batch_get_features_new", description="收藏接口URL")
    collection_app_key: str = Field(default="ai_platform", description="收藏接口AppKey")
    collection_app_secret: str = Field(default="26858F09E0CDA9F7", description="收藏接口AppSecret")

    # HTTP请求日志配置
    enable_http_timing_log: bool = Field(default=False, description="是否启用第三方HTTP接口耗时日志")

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "allow"  # 允许额外的字段


# 全局配置实例
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """获取配置单例"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """重新加载配置"""
    global _settings
    _settings = Settings()
    return _settings