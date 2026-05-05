#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Author   : liyandan 
# @Date     : 2026-03-07
# @Description: 车况工具原子函数(聚合各大数据平台的通用接口，获取最终数据)

import json
from math import log
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
def get_car_general_knowledge_without_clue_id(question,gz_user_id, url, api_key):
    """用户提问的通用汽车知识，获取检索结果"""
    headers_retrieval = {
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json"
       }
    payload = {
        "inputs": {
            "question"              :   question,
            "rephrased_question"    :   question, 
            "clue_id"               :   "",
            "koubei_format"         :   "",
            "search_type"           :   ""
        },
        "user": f"{gz_user_id}" if gz_user_id else "get_car_general_knowledge_tool_user"
    }
    try:
        response                    =  requests.post(url, headers=headers_retrieval, data=json.dumps(payload))
        result_json                 =  response.json()
        retrieval_results           =  result_json.get("data",{}).get("outputs",{}).get("data",{})
        retrieval_type           =  result_json.get("data",{}).get("outputs",{}).get("retrieve_type",{})
        result = {}
        result["通用知识库检索结果"] = retrieval_results
        result["通用知识库检索类型"] = retrieval_type

        return result
    except requests.exceptions.RequestException as e:
        logger.error(f"用户提问的通用汽车知识，获取检索结果失败{str(e)}")
        return {}

@log_http_timing
def get_car_reputation_by_clue_id(clue_id, question,gz_user_id,url, api_key):
    """根据车源id，获取车源相关车辆的口碑知识"""
    headers_retrieval = {
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json"
                        }

    try:
        # 准备请求体
        payload = {
            "inputs": {
                         "question"             :    f"{question}",
                         "rephrased_question"   :    f"{question}",
                         "clue_id"              :    f"{clue_id}",
                         "koubei_format"        :    "JSON",
                         "search_type"          :    "车型口碑知识库检索"
            },
            "user": f"{gz_user_id}" if gz_user_id else "get_car_reputation_tool_user"
        }

        # 发送POST请求
        response = requests.post(
            url,
            headers    =  headers_retrieval,
            data=json.dumps(payload)
        )
        result_json       = response.json()
        retrieval_results = result_json.get("data",{}).get("outputs",{}).get("data",{})
        result = {}
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
def get_car_paint_tag_by_clue_id(clue_id,url,api_key ,secret):
    """根据车源id，获取车源漆面状态：原版原漆 or 非原版原漆"""
    params = {"clue_id":str(clue_id),"tag":"1021"}
    tags = []
    try:
        all_params = create_params(params, api_key, secret)
        response = requests.get(url, params=all_params, timeout=10) 
        result = response.json()
        if result.get("code") == 0:
           data = result.get("data", {})
           if data.get("exsit"):
              return "原版原漆"
           else:
              return "非原版原漆"
        else:
            return ""
    except Exception as e:
        return ""
    
    return ""

@log_http_timing
def get_car_source_highlight_by_clue_id(clue_id, url):
    """根据车源id，获取车源亮点小作文文案"""
    # #Step1: 获取车源亮点小作文需要的基础参数信息
    # params_get_url = f"http://mall-report.guazi-apps.com/tools/llmCopy/getRequestParam?chdUserId=162986983611200045&clueId={clue_id}&ignoreSign=11ce234b"

    # response = requests.get(params_get_url)
    # result = response.json()
    # if result.get("code") != 0:
    #     return {}
    # params = result.get("data",{})

    # print(params)

    # {
    #     'key': {
    #             'carSourceInfo': {
    #                         'clueId': 160179652, 
    #                         'carName': '丰田 花冠 2013款 1.6L 自动豪华版', 
    #                         'carAge': '10年6个月', 
    #                         'roadHaul': '15.22万公里', 
    #                         'transferNum': '0次', 
    #                         'fuelType': '汽油'
    #              }, 
    #             'carModelId': 30540, 
    #             'vinEncrypt': 'C015Q3920267700487585794', 
    #             'g3OrderId': '5ba9296e133148c694effff4eaba76b3', 
    #             'taskId': 6417181, 
    #             'gzUserId': 162986983611200045, 
    #             'onMallShelfStatus': True
    #             }, 
    #     'value': {
    #         'carSourceInfo': {
    #             'clueId': 160179652, 
    #             'carName': '丰田 花冠 2013款 1.6L 自动豪华版', 
    #             'carAge': '10年6个月', 
    #             'roadHaul': '15.22万公里', 
    #             'transferNum': '0次', 
    #             'fuelType': '汽油'
    #             }, 
    #             'vinEncrypt': 'C015Q3920267700487585794', 
    #             'g3OrderId': '5ba9296e133148c694effff4eaba76b3',
    #              'taskId': 6417181}
    #              }


    #----------------------------------------------------
    # carSourceInfo = params.get("key",{}).get("carSourceInfo",{})

    # carsourceinfo_carName = carSourceInfo.get("carName","")
    # carsourceinfo_carAge = carSourceInfo.get("carAge","")
    # carsourceinfo_roadHaul = carSourceInfo.get("roadHaul","")
    # carsourceinfo_transferNum = carSourceInfo.get("transferNum","")
    # carsourceinfo_fuelType = carSourceInfo.get("fuelType","")

    
    # key_info = params.get("key",{})
    # taskId = key_info.get("taskId",0)
    # carModelId = key_info.get("carModelId","")
    # vinEncrypt = key_info.get("vinEncrypt","")
    # g3OrderId = key_info.get("g3OrderId","")
    # gzUserId = key_info.get("gzUserId",174132952062000099)
    # onMallShelfStatus = key_info.get("onMallShelfStatus","false")
    # if isinstance(onMallShelfStatus, bool):
    #     if onMallShelfStatus:
    #         onMallShelfStatus = "true"
    #     else:
    #         onMallShelfStatus = "false"
    

    # payload = {
    #     "carSourceInfo": {
    #         "clueId": int(clue_id),
    #         "carName": carsourceinfo_carName,
    #         "carAge": carsourceinfo_carAge,
    #         "roadHaul": carsourceinfo_roadHaul,
    #         "transferNum": carsourceinfo_transferNum,
    #         "fuelType": carsourceinfo_fuelType,
    #     },
    #     "taskId": taskId,
    #     "carModelId": f"{carModelId}",
    #     "vinEncrypt": vinEncrypt,
    #     "g3OrderId": g3OrderId,
    #     "gzUserId": gzUserId,
    #     "onMallShelfStatus": onMallShelfStatus
    # }
    #---------------------------------------------------- 

    # Content-Type: application/json
    # {
    # carSourceInfo: {
    # "carName": "丰田卡罗拉 2020款 1.2T S-CVT GL-i精英版",
    # "carAge": "3年2个月",
    # "roadHaul": "4.2w公里",
    # "transferNum": "1次",
    # "fuelType": "汽油",
    # "clueId": 198765432111
        
    # },
    # "taskId": 1987654,
    # "carModelId": "MODEL002",
    # "vinEncrypt": "encrypted_vin_67890",
    # "g3OrderId": "G3ORDER002",
    # "gzUserId": 100869527000,  //20251208新增gzUserId用于查询用户分组情况，gzUserId为空则默认为对照组
    # "onMallShelfStatus": "true"  //是否已经在商品中心上架
    # }
    # header = { "Content-Type": "application/json" }
    #Step2: 获取车源亮点小作文需要的车况卖点信息



    return {}