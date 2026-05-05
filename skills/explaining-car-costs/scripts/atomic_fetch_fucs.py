#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Author   : liyandan 
# @Date     : 2026-03-07
# @Description: 车况工具原子函数(聚合各大数据平台的通用接口，获取最终数据)

import json
import os,random
import requests
import datetime as dt
from logger import get_logger
from utils import create_params, parse_input_data_with_json_eval,log_http_timing
from tool_common import parse_response_data
# 通用验证签名信息导入
from tool_common import compute_sign_carsource

from tool_common import convert_keys_to_chinese
from tool_common import car_type_reputation_info_parser
from get_reputation_data import get_reputation_data
from car_knowledge_base_search import get_car_knowledge_base_search_result_main
from car_cost_fetch_funcs import get_car_cost_data_by_tag_id

logger = get_logger(__name__)

@log_http_timing
def get_car_basic_info_by_clue_id(clue_id, fields, url_query_car_source, CARSOURCE_APP_KEY, CARSOURCE_APP_SECRET):
    """根据车源id，获取车源基本信息"""
    fields = ",".join(fields)
    params = {"clue_ids": clue_id, "fields": fields}
    all_params = create_params(params, CARSOURCE_APP_KEY, CARSOURCE_APP_SECRET)
    try:
        result = requests.get(url_query_car_source, params=all_params).json()
        return result.get("data", {})
    except Exception as e:
        logger.error(f"get_car_basic_info_by_clue_id error: {e}")
        return {}

@log_http_timing
def get_get_car_type_info_by_car_id(car_id, URL_CARLIB, CARLIB_APP_KEY, CARLIB_APP_SECRET):
    """根据车型id，获取车型库配置项"""
    if car_id == "" or car_id is None or car_id == 0:
        return {}
    params = {"id": car_id}
    all_params = create_params(params, CARLIB_APP_KEY, CARLIB_APP_SECRET)
    url_model_type = os.path.join(URL_CARLIB, "api/cars/getCarById")
    try:
        response = requests.get(url_model_type, params=all_params, timeout=10)
        if response.status_code != 200:
            return {}
        result = response.json()
        if result.get("code") != 0:
            return {}
        if result.get("data", {}) == "":
            return {}
        return result.get("data", {})
    except Exception as e:
        logger.error(f"get_get_car_type_info_by_car_id error: {e}")
        return {}

@log_http_timing
def get_optional_features(carTypeId, ids, URL_CARLIB, CARLIB_APP_KEY, CARLIB_APP_SECRET):
    """获取选装配置"""
    data = []
    try:
        params = {"ids": ids, "carId": int(carTypeId)}
        all_params = create_params(params, CARLIB_APP_KEY, CARLIB_APP_SECRET)
        url_model_type = os.path.join(URL_CARLIB, "api/cars/config/getByIds")
        result = requests.get(url_model_type, params=all_params).json()
        data = result["data"]
    except Exception as e:
        logger.error(f"get_optional_features error: {e}")
        return []
    return data

@log_http_timing
def get_check_report_defects(clue_id: str, base_url: str, app_key: str = None, app_secret: str = None) -> dict:
    """
    获取检测报告内的异常(缺陷)数据

    Args:
        clue_id: 车源ID
        env: 环境类型 (test/pre/prod)
        app_key: 应用密钥
        app_secret: 应用秘钥

    Returns:
        dict: 检测报告缺陷数据
    """

    # 构建请求参数
    params = {
        "clueId": clue_id
    }

    url_check_report = f"{base_url}/internal/checkReport/getToCDefects"
    # 如果提供了app_key和app_secret，则添加签名
    if app_key and app_secret:
        params = create_params(params, app_key, app_secret)

    try:
        response = requests.get(url_check_report, params=params, timeout=30)
        response.raise_for_status()

        result = response.json()
        data = result.get("data", {})
        # check_report_data = data.get("check_report_data", {})
        report_type = data.get("reportType", -1)
        content_list = data.get("contentList", []) if report_type == 3 else []
        return content_list
    except Exception as e:
        logger.error(f"get_check_report_defects,{e}")
        return {}


@log_http_timing
def get_car_check_report_link_by_clue_id(clue_id, url, CARSOURCE_BASE_APP_KEY, CARSOURCE_BASE_APP_SECRET):
    """根据车源id，获取检测报告链接"""
    params = {'showScene': 'intelligent_customer_service_report', 'clueId': f"{clue_id}"}
    all_params = create_params(params, CARSOURCE_BASE_APP_KEY, CARSOURCE_BASE_APP_SECRET)
    try:
        response              = requests.get(url, params=all_params)
        car_check_report_link = parse_response_data(response).get("showReportUrl", "")
        if not car_check_report_link:
            return ""
        return car_check_report_link
    except Exception as e:
        logger.error(f"get_car_check_report_link_by_clue_id error: {e}")
        return ""

# ======================= 出险记录相关 =======================
@log_http_timing
def get_product_info_by_clue_id(clue_id, URL_MALL_PRODUCT, MALL_PRODUCT_APP_KEY, MALL_PRODUCT_APP_SECRET):
    """根据车源id，获取出险记录id、vin加密id"""
    if not clue_id or clue_id == "-1" or clue_id == "":
        return {}
    try:
        params = {"clueId": clue_id}
        all_params = create_params(params, MALL_PRODUCT_APP_KEY, MALL_PRODUCT_APP_SECRET)
        url_product_info = os.path.join(URL_MALL_PRODUCT, "api/product/getProductInfo")
        response = requests.get(url_product_info, params=all_params, timeout=10)
        product_info = parse_response_data(response)
        if not product_info:
            return {}
        return product_info
    except Exception as e:
        logger.error("get_product_info_by_clue_id error: {e}")
        return {}

@log_http_timing
def get_insurance_report(vin_encrypt, g3_order_id, URL_CARSOURCE, CARSOURCE_APP_KEY, CARSOURCE_APP_SECRET):
    """根据vin_encrypt，g3_order_id，获取车辆出险记录"""
    if vin_encrypt == "" or not vin_encrypt or g3_order_id == "" or not g3_order_id:
        return {}

    params = {"g3OrderId": g3_order_id, "vinEncrypt": vin_encrypt}
    now_ts = int(dt.datetime.now().timestamp())
    delay_s = 60
    all_params = {
        'appkey': CARSOURCE_APP_KEY,
        'expires': str(now_ts + delay_s),
        'nonce': str(random.randint(100000000, 100000000 * 10)),
    }
    if isinstance(params, dict):
        all_params.update(params)

    signature = compute_sign_carsource(all_params, CARSOURCE_APP_SECRET)
    all_params['signature'] = signature
    url_insurance_report = os.path.join(URL_CARSOURCE, "cars-report/internal/insurance/explanation/report")
    try:
        response = requests.get(url_insurance_report, params=all_params, timeout=10)
        insurance_report_info = parse_response_data(response)
        if not insurance_report_info:
            return {}
        return insurance_report_info
    except Exception as e:
        print("get_insurance_report error: %s", str(e))
        return {}

@log_http_timing
def get_battery_report_by_clue_id(clue_id, url_battery_report, nev_app_key, nev_app_secret):
    """获取电池报告"""
    headers = {"Content-Type": "application/json"}
    params = {
        "clueId": clue_id,
        "did": "did",  # 后续可能替换
        "deviceId": "deviceId",  # 设备id
        "sourceFrom": "app",  # 渠道来源
        # "tagId":1242,
        "selectedCity": 1  # 给固定值，暂时不影响
    }
    all_params = create_params(params, nev_app_key, nev_app_secret)
    try:
        response = requests.post(url_battery_report, params=all_params, headers=headers, data=json.dumps(params),
                                 timeout=10)
        result = parse_response_data(response)
        if not isinstance(result, dict):
            return {}
        return convert_keys_to_chinese(result)
    except Exception as e:
        logger.error( f"get_battery_report_by_clue_id error: {e}" )
        return {}

@log_http_timing
def get_battery_report_by_clue_id(clue_id, url_battery_report, nev_app_key, nev_app_secret):
    """获取电池报告"""
    headers = {"Content-Type": "application/json"}
    params = {
        "clueId": clue_id,
        "did": "did",  # 后续可能替换
        "deviceId": "deviceId",  # 设备id
        "sourceFrom": "app",  # 渠道来源
        # "tagId":1242,
        "selectedCity": 1  # 给固定值，暂时不影响
    }
    all_params = create_params(params, nev_app_key, nev_app_secret)
    try:
        response = requests.post(url_battery_report, params=all_params, headers=headers, data=json.dumps(params),
                                 timeout=10)
        result = parse_response_data(response)
        if not isinstance(result, dict):
            return {}
        return convert_keys_to_chinese(result)
    except Exception as e:
        logger.error( f"get_battery_report_by_clue_id error: {e}" )
        return {}

@log_http_timing
def get_car_hand_picked_by_clue_id(clue_id, url):
    """获取车源渠道"""
    params = {"clueId": clue_id}
    try:
        response = requests.get(url, params=params, timeout=10)
        result = parse_response_data(response)
        if type(result) is int:
            if result == 0:
                return "车商车"
            else:
                return "自营车"
        else:
            return "无法提供车源渠道信息"
    except Exception as e:
        logger.error( f"get_car_sourcechannel_by_clue_id error: {e}" )
        return "无法提供车源渠道信息"

@log_http_timing
def get_car_images_http(clue_id, url_mall_prd, key_mall_prd, secret_mall_prd):
    params = {"clueId": clue_id, "imageType": "1", "snapshotType": "1"}
    all_params = create_params(params, key_mall_prd, secret_mall_prd)
    url_image_api = os.path.join(url_mall_prd, "api/product/getImages")
    return requests.get(url_image_api, params=all_params, headers={"accept": "*/*"}, timeout=10)

@log_http_timing
def get_car_source_city_by_clue_id(clue_id, ext, url, CARSOURCE_BASE_APP_KEY, CARSOURCE_BASE_APP_SECRET):
    """根据车源id，获取车源城市"""
    ext = parse_input_data_with_json_eval(ext, default_value={})

    params = {
        "cityId": ext.get("plate_city_id", 13), "selectedCity": ext.get("selected_city_id", 13),
        "locationCity": ext.get("location_city_id", 13),
        "versionId": ext.get("version_id", "1"), "sourceFrom": "", "deviceId": "", "client": "", "chdUserId": "",
        "skuList": clue_id, "queryProgrammeId": 192}
    all_params = create_params(params, CARSOURCE_BASE_APP_KEY, CARSOURCE_BASE_APP_SECRET)
    try:
        response = requests.get(url, params=all_params)
        car_source_city = parse_response_data(response).get("carList", [])[0].get("skuBasicArea", {}).get(
            "carSourceCityDesc", "")
        if not car_source_city:
            return ""
        return car_source_city
    except Exception as e:
        logger.error(f"get_car_source_city_by_clue_id error: {e}")
        return ""
@log_http_timing
def get_car_condition_level_by_clue_id(clue_id, url, CARSOURCE_BASE_APP_KEY, CARSOURCE_BASE_APP_SECRET):
    """根据车源id，获取车况等级"""
    params = {"clueId": clue_id}
    all_params = create_params(params, CARSOURCE_BASE_APP_KEY, CARSOURCE_BASE_APP_SECRET)
    try:
        response = requests.get(url, params=all_params)
        return parse_response_data(response).get("evaluationResult", {}).get("resultSummary", "")
    except Exception as e:
        logger.error(f"get_car_condition_level_by_clue_id error: {e}")
        return ""

@log_http_timing
def get_car_general_knowledge_without_clue_id(question):
    """用户提问的通用汽车知识，获取检索结果"""

    try:
        result_dict = get_car_knowledge_base_search_result_main(question)
        retrieval_results = result_dict.get("data", {})
        retrieval_type = result_dict.get("retrieve_type", "")
        result = {}
        result["通用知识库检索结果"] = retrieval_results
        result["通用知识库检索类型"] = retrieval_type

        return result
    except Exception as e:
        logger.error(f"用户提问的通用汽车知识，获取检索结果失败{str(e)}")
        return {}

@log_http_timing
def get_car_reputation_by_clue_id(clue_id):
    """根据车源id，获取车源相关车辆的口碑知识"""
    try:
        result_json       = get_reputation_data("koubei",clue_id,"JSON")
        retrieval_results = result_json.get( "koubei_knowledge", {} )
        result            = {}
        if isinstance(retrieval_results, str):
            result = json.loads(retrieval_results)
        elif isinstance(retrieval_results, dict):
            result = retrieval_results  
        else:
            result      = {}
        filtered_result = {}
        if isinstance(result, list):
            first_item = result[0]
            filtered_result.update(car_type_reputation_info_parser(first_item))
        else:
            filtered_result = {}
        return filtered_result
    except requests.exceptions.RequestException as e:
        logger.error(f"车型口碑知识库检索失败{str(e)}")
        return {}


@log_http_timing
def get_car_cost_by_tag_id_(tag_id, url, key_car_cost, secret_car_cost):
    """根据车源id，获取车源对应车辆的用车成本信息（年均保养费、年均保险费、年均油费）"""
    # 首先根据clue_id 获取 tag_id 然后再根据 tag_id 获取用车成本信息
    try:
        result = get_car_cost_data_by_tag_id(url, tag_id, key_car_cost, secret_car_cost)
    except Exception as e:
        return {
                    "用车成本":{
                                "年均保养费": "",
                                "年均保险费": "",
                                "年均油费": ""
                            }
               }
    return result

@log_http_timing
def get_car_source_highlight_by_clue_id(clue_id, url):
    """根据车源id，获取车源亮点小作文文案"""


    return {}