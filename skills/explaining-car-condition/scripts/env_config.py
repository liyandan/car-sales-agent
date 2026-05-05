#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Author   : liyandan
# @Date     : 2026-03-06
# @Description: 车况接口环境配置(Test/Preview/Online)

"""
车况接口环境配置模块
支持根据请求中的 env 参数动态选择不同环境的配置
"""

from typing import Dict
from dataclasses import dataclass


@dataclass
class CarConditionEnvConfig:
    """车况接口环境配置"""
    # URL配置
    url_client_rest: str
    url_cs_base: str
    url_kb: str
    url_mall_prd: str
    url_carsource: str
    url_opl_cs: str
    url_carlib: str
    url_im: str
    url_mall_pp: str
    url_cars_info: str
    url_appointment: str
    url_wechat_guide: str
    url_act: str
    url_sale_cs: str
    url_uc: str
    url_new_energy: str
    url_mall_report: str
    url_open_data: str
    url_user_order: str
    url_city_name: str
    url_kuaizhao: str
    url_cost_performance: str
    url_car_source_highlight: str
    url_car_reputation: str
    url_car_general_knowledge: str

    
    # 密钥配置
    key_carlib: str
    secret_carlib: str
    key_carsource: str
    secret_carsource: str
    key_mall_prd: str
    secret_mall_prd: str
    key_checklk: str
    secret_checklk: str
    key_mall_pp: str
    secret_mall_pp: str
    key_cs_base: str
    secret_cs_base: str
    key_sale_cs: str
    secret_sale_cs: str
    key_client_re: str
    secret_client_re: str
    key_nev: str
    key_mall_report: str
    secret_nev: str
    key_open_data: str
    secret_open_data: str
    key_user_order: str
    secret_user_order: str
    key_city_name: str
    secret_city_name: str
    key_kuaizhao: str
    secret_kuaizhao: str
    key_car_source_highlight: str
    key_car_reputation: str
    key_car_general_knowledge: str

# 测试环境配置
TEST_CONFIG = CarConditionEnvConfig(
    # URL配置
    url_client_rest     =   "http://client-restful-api.guazi-cloud.com",
    url_cs_base         =   "http://mall-car-baseinfo.guazi-cloud.com",
    url_kb              =   "http://knowledge-base.guazi-cloud.com",
    url_mall_prd        =   "http://mall-product.guazi-cloud.com",
    url_carsource       =   "http://carsource-api.guazi-cloud.com",
    url_opl_cs          =   "http://opl-car-source.guazi-cloud.com",
    url_carlib          =   "http://carlib-api.guazi-cloud.com",
    url_im              =   "http://buy.guazi-cloud.com",
    url_mall_pp         =   "http://mall-product-price.guazi-cloud.com",
    url_cars_info       =   "http://cars-info.guazi-cloud.com",
    url_appointment     =   "http://opl-dealer-tool.guazi-cloud.com",
    url_wechat_guide    =   "http://znkf-agent-service.guazi-cloud.com",
    url_act             =   "http://act.guazi-cloud.com",
    url_sale_cs         =   "",
    url_uc              =   "http://uc.guazi-cloud.com",
    url_new_energy      =   "http://new-energy.guazi-cloud.com",
    url_mall_report     =   "http://mall-report.guazi-cloud.com",
    url_open_data       =   "http://open-data-api.guazi-cloud.com",
    url_user_order      =   "http://user-order.guazi-cloud.com",
    url_city_name       =   "http://misc-commapi.guazi.com/misc/area/get_city_by_id",
    url_kuaizhao                =   "http://mall-product.guazi-cloud.com",
    url_cost_performance        =   "http://ai-car.guazi-cloud.com",
    url_car_source_highlight    =   "https://ai-agent.guazi-cloud.com/api/internal/car-analysis/interpretation",
    url_car_reputation          =   "https://llm-dify-api-preview.guazi-apps.com/v1/workflows/run",
    url_car_general_knowledge   =   "https://llm-dify-api-preview.guazi-apps.com/v1/workflows/run",

    # 密钥配置
    key_carlib          =   "model_agent",
    secret_carlib       =   "AFvXYzurlUeSrk0o",
    key_carsource       =   "ai_agent",
    secret_carsource    =   "secAiAgent02@25Dev",
    key_mall_prd        =   "dataset-external-apis",
    secret_mall_prd     =   "123456",
    key_checklk         =   "nlp",
    secret_checklk      =   "ca4218cb",
    key_mall_pp         =   "large_model",
    secret_mall_pp      =   "ec56248fc3719f78c8df520714ea2334",
    key_cs_base         =   "ai_agent",
    secret_cs_base      =   "2c2b0389",
    key_sale_cs         =   "guazi_ig",
    secret_sale_cs      =   "qbf01191895b",
    key_client_re       =   "",
    secret_client_re    =   "",
    key_nev             =   "ai_agent",
    key_mall_report     =   "ai_agent_energy",
    secret_nev          =   "824AsudnLs2",
    key_open_data       =   "rag__llm-dify-api",
    secret_open_data    =   "3168608f19",
    key_user_order      =   "large_model",
    secret_user_order   =   "ec56248fc3719f78c8df520714ea2334",
    key_city_name       =   "58265588",
    secret_city_name    =   "fie5uD7oar2P",
    key_kuaizhao        =   "lm-xiaogua",
    secret_kuaizhao     =   "b7c604f7",
    key_car_source_highlight  =   "",
    key_car_reputation        =   "app-lfZEruv4nvWDvDBqv2xYvLvm",
    key_car_general_knowledge =   "app-lfZEruv4nvWDvDBqv2xYvLvm"
)

# 预发环境配置
PREVIEW_CONFIG = CarConditionEnvConfig(
    url_client_rest     =   "http://client-restful-api.guazi-preview.com",
    url_cs_base         =   "http://car-source-baseinfo-preview.guazi-apps.com",
    url_kb              =   "http://knowledge-base-preview.guazi-apps.com",
    url_mall_prd        =   "http://mall-product-preview.guazi-apps.com",
    url_carsource       =   "http://carsource-api-preview.guazi-apps.com",
    url_opl_cs          =   "http://opl-car-source-preview.guazi-apps.com",
    url_carlib          =   "http://carlib-api-preview.guazi-apps.com",
    url_im              =   "http://buy-preview.guazi-apps.com",
    url_mall_pp         =   "http://mall-product-price-preview.guazi-apps.com",
    url_cars_info       =   "http://cars-info.guazi-preview.com",
    url_appointment     =   "http://opl-dealer-tool-preview.guazi-apps.com",
    url_wechat_guide    =   "http://znkf-agent-service.guazi-preview.com",
    url_act             =   "http://act-preview.guazi-apps.com",
    url_sale_cs         =   "http://sale-carservice-preview.guazi-apps.com",
    url_uc              =   "http://muc-preview.guazi-apps.com",
    url_new_energy      =   "http://new-energy-server-preview.guazi-apps.com",
    url_mall_report     =   "http://mall-report-preview.guazi-apps.com",
    url_open_data       =   "http://open-data-api-preview.guazi-apps.com",
    url_user_order      =   "http://user-order-preview.guazi-apps.com",
    url_city_name       =   "http://misc-commapi.guazi.com/misc/area/get_city_by_id",
    url_kuaizhao        =   "http://mall-product-preview.guazi-apps.com",
    url_cost_performance=   "http://ai-car.guazi-apps.com",
    url_car_source_highlight    =   "https://ai-agent-preview.guazi-apps.com/api/internal/car-analysis/interpretation",
    url_car_reputation          =   "https://llm-dify-api-preview.guazi-apps.com/v1/workflows/run",
    url_car_general_knowledge   =   "https://llm-dify-api-preview.guazi-apps.com/v1/workflows/run",
    
    # 密钥配置
    key_carlib          =   "model_agent",
    secret_carlib       =   "AFvXYzurlUeSrk0o",
    key_carsource       =   "ai_agent",
    secret_carsource    =   "secAiAgent0228@25OL",
    key_mall_prd        =   "znkf",
    secret_mall_prd     =   "M24cgsND",
    key_checklk         =   "nlp",
    secret_checklk      =   "ca4218cb",
    key_mall_pp         =   "large_model",
    secret_mall_pp      =   "ec56248fc3719f78c8df520714ea2334",
    key_cs_base         =   "ai_agent",
    secret_cs_base      =   "2c2b0389",
    key_sale_cs         =   "guazi_ig",
    secret_sale_cs      =   "qbf01191895b",
    key_client_re       =   "ai_agent",
    secret_client_re    =   "9a89a824",
    key_nev             =   "ai_agent",
    key_mall_report     =   "ai_agent_energy",
    secret_nev          =   "824AsudnLs2",
    key_open_data       =   "rag__llm-dify-api",
    secret_open_data    =   "3168608f19",
    key_user_order      =   "large_model",
    secret_user_order   =   "ec56248fc3719f78c8df520714ea2334",
    key_city_name       =   "58265588",
    secret_city_name    =   "fie5uD7oar2P",
    key_kuaizhao        =   "lm-xiaogua",
    secret_kuaizhao     =   "b7c604f7",
    key_car_source_highlight  =   "",
    key_car_reputation        =   "app-lfZEruv4nvWDvDBqv2xYvLvm",
    key_car_general_knowledge =   "app-lfZEruv4nvWDvDBqv2xYvLvm"
)

# 生产环境配置
PROD_CONFIG = CarConditionEnvConfig(
    # URL配置
    url_client_rest     =   "http://client-restful-api.guazi-apps.com",
    url_cs_base         =   "http://car-source-baseinfo.guazi-apps.com",
    url_kb              =   "http://knowledge-base.guazi-apps.com",
    url_mall_prd        =   "http://mall-product.guazi-apps.com",
    url_carsource       =   "http://carsource-api.guazi-apps.com",
    url_opl_cs          =   "http://opl-car-source.guazi-apps.com",
    url_carlib          =   "http://carlib-api.guazi-apps.com",
    url_im              =   "http://m.guazi.com",
    url_mall_pp         =   "http://mall-product-price.guazi-apps.com",
    url_cars_info       =   "http://cars-info.guazi-apps.com",
    url_appointment     =   "http://opl-dealer-tool.guazi-apps.com",
    url_wechat_guide    =   "http://znkf-agent-service.guazi-apps.com",
    url_act             =   "http://act.guazi.com",
    url_sale_cs         =   "http://sale-carservice.guazi-apps.com",
    url_uc              =   "http://uc.guazi.com",
    url_new_energy      =   "http://new-energy-server.guazi-apps.com",
    url_mall_report     =   "http://mall-report.guazi-apps.com",
    url_open_data       =   "http://open-data-api.guazi-apps.com",
    url_user_order      =   "http://user-order.guazi-apps.com",
    url_city_name       =   "http://misc-commapi.guazi.com/misc/area/get_city_by_id",
    url_kuaizhao        =   "http://mall-product.guazi-apps.com",
    url_cost_performance=   "http://ai-car.guazi-apps.com",
    url_car_source_highlight    =   "https://ai-agent.guazi-apps.com/api/internal/car-analysis/interpretation",
    url_car_reputation          =   "https://llm-dify-api.guazi-apps.com/v1/workflows/run",
    url_car_general_knowledge   =   "https://llm-dify-api.guazi-apps.com/v1/workflows/run",
    
    # 密钥配置
    key_carlib          =   "model_agent",
    secret_carlib       =   "AFvXYzurlUeSrk0o",
    key_carsource       =   "ai_agent",
    secret_carsource    =   "secAiAgent0228@25OL",
    key_mall_prd        =   "znkf",
    secret_mall_prd     =   "M24cgsND",
    key_checklk         =   "nlp",
    secret_checklk      =   "ca4218cb",
    key_mall_pp         =   "large_model",
    secret_mall_pp      =   "ec56248fc3719f78c8df520714ea2334",
    key_cs_base         =   "ai_agent",
    secret_cs_base      =   "2c2b0389",
    key_sale_cs         =   "guazi_ig",
    secret_sale_cs      =   "qbf01191895b",
    key_client_re       =   "ai_agent",
    secret_client_re    =   "9a89a824",
    key_nev             =   "ai_agent",
    key_mall_report     =   "ai_agent_energy",
    secret_nev          =   "824AsudnLs2",
    key_open_data       =   "rag__llm-dify-api",
    secret_open_data    =   "3168608f19",
    key_user_order      =   "large_model",
    secret_user_order   =   "ec56248fc3719f78c8df520714ea2334",
    key_city_name       =   "58265588",
    secret_city_name    =   "fie5uD7oar2P",
    key_kuaizhao        =   "lm-xiaogua",
    secret_kuaizhao     =   "b7c604f7",
    key_car_source_highlight  =   "",
    key_car_reputation        =   "app-lfZEruv4nvWDvDBqv2xYvLvm",
    key_car_general_knowledge =   "app-lfZEruv4nvWDvDBqv2xYvLvm"
)


def get_env_config(env: str) -> CarConditionEnvConfig:
    if env == "test":
        return TEST_CONFIG
    elif env == "preview" or env == "pre":
        return PREVIEW_CONFIG
    else:
        return PROD_CONFIG

