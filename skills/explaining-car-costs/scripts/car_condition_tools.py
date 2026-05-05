#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Author   : liyandan  
# @Date     : 2026-03-07
# @Description: 车况工具函数封装
import os
import json
from logger import get_logger
from env_config import get_env_config
from tool_common import validate_clue_id
from tool_common import validate_tag_id
from tool_common import CAR_BASIC_INFO_COLS
from concurrent.futures import ThreadPoolExecutor, as_completed

# 获取车源基础信息原子函数
# 1. 获取车源id关联的车型信息
from atomic_fetch_fucs import get_car_basic_info_by_clue_id
from atomic_fetch_fucs import get_get_car_type_info_by_car_id
from atomic_fetch_fucs import get_optional_features
# 首任车主权益删除
from tool_common import remove_owner_info
from tool_common import car_type_info_parser

# 2. 获取车源id关联的车辆检测报告信息
from atomic_fetch_fucs import get_check_report_defects
from tool_common import parse_check_report_defects

# 3. 获取车源id关联的车辆检测报告链接
from atomic_fetch_fucs import get_car_check_report_link_by_clue_id

# 4. 获取车源id关联的出险记录
from atomic_fetch_fucs import get_product_info_by_clue_id
from atomic_fetch_fucs import get_insurance_report
from tool_common import insurance_report_parser

# 7.
from tool_common import car_basic_info_parser
from atomic_fetch_fucs import get_battery_report_by_clue_id

# 8 
from atomic_fetch_fucs import get_car_hand_picked_by_clue_id

# 9
from atomic_fetch_fucs import get_car_images_http

# 15 
from atomic_fetch_fucs import get_car_source_city_by_clue_id

# 16
from atomic_fetch_fucs import get_car_condition_level_by_clue_id

logger = get_logger(__name__)

# 17 
from atomic_fetch_price import get_price_info_by_clue_id_gz_user_id_ext

# 18
from atomic_fetch_fucs import get_car_reputation_by_clue_id

# 19 
from atomic_fetch_fucs import get_car_general_knowledge_without_clue_id

# 20 
from tool_common import car_source_other_info_parser
from atomic_fetch_fucs import get_car_source_highlight_by_clue_id

# 21
from atomic_fetch_fucs import get_car_cost_by_tag_id_

# 样例工具函数，通过城市名称获取天气信息
# @tool("weather_search")
# def search(city: str) -> str:
#     """Search the weachter information for the input city"""
#     return f"The weather information for: {city} is sunny."

# 第1个封装的工具
# 通过车源id获取对应的车型配置信息，目前暂时没有更新选装配置的信息
def get_car_type_info_by_clue_id(clue_id: str,env:str="online") -> str:
    """ 通过车源ID(clue_id)获取车辆的车型配置信息 """
    # 默认线上环境，如果传入的环境不合法，则使用线上环境
    # 统一返回JSON字典
    result          =    {}

    loca_env        =    "online"
    if env is None or env == "" or env not in ( "online","test","preview","pre"):
        local_env   =    "online"
    else:
        local_env   =     env
    
    # 不合法的clue_id 返回空字典
    if clue_id is None or clue_id == "" or not validate_clue_id(clue_id):
        return {}

    # 拿到环境配置
    env_config              =   get_env_config(local_env)

    # 为车型配置数据获取接口查询url、key、secret信息
    url_carlib              =   env_config.url_carlib
    key_carlib              =   env_config.key_carlib
    secret_carlib           =   env_config.secret_carlib

    # 获取车源接口url网址
    url_carsource           =   env_config.url_carsource
    url_query_car_source    =   os.path.join(url_carsource, "cars-info/internal/carSource/queryCarSource")
   
    # 获取车源接口key
    key_carsource           =   env_config.key_carsource
    # 获取车源接口密钥
    secret_carsource        =   env_config.secret_carsource

    if clue_id != "-1" and clue_id and validate_clue_id(clue_id):
        fields = CAR_BASIC_INFO_COLS
    else:
        fields = []
    # 获取车源基本信息
    car_basic_info_multi_clue_id = get_car_basic_info_by_clue_id(clue_id, CAR_BASIC_INFO_COLS, url_query_car_source, key_carsource, secret_carsource)

    if car_basic_info_multi_clue_id:
        car_type_id = car_basic_info_multi_clue_id.get(clue_id, {}).get("car_id", "")
        if car_type_id:
            # 获取车型信息（依赖car_type_id）
            car_type_info_result = get_get_car_type_info_by_car_id(car_type_id, url_carlib, key_carlib, secret_carlib)
            if car_type_info_result:
                car_type_info_parser_result = car_type_info_parser(car_type_info_result)

                # 获取选装配置项
                car_type_optional = ""
                if car_type_info_parser_result.get("选装配置项", -1) != -1:
                    ids_ = car_type_info_parser_result.get("选装配置项")
                    optionalfeattures = get_optional_features(car_type_id, str(ids_), url_carlib, key_carlib,
                                                              secret_carlib)
                    car_type_optional = str(optionalfeattures)
                    car_type_info_parser_result["选装配置项"] = ""

                # 获取充电配置项
                charging_info_parser_result = {}
                charging_info_map_dict = ["快充时间", "慢充时间", "快充功能", "电池充电时间", "充电桩价格", "快充电量",
                                          "电池快充电量范围", "高压快充", "快充接口位置", "充电站", "充电桩",
                                          "电池类型",
                                          "电池组质保", "电池组质保年限", "电池组质保里程", "电芯品牌", "电池冷却方式",
                                          "电池能量密度", "电池容量", "三电系统质保", "三电系统质保里程",
                                          "三电系统质保年限",
                                          "三电首任车主质保政策"]

                for key in charging_info_map_dict:
                    if key not in car_type_info_parser_result:
                        continue
                    value = car_type_info_parser_result.get(key, "")
                    if value in [None, "", "null", "-"]:
                        continue
                    charging_info_parser_result[key] = value

                filtered_charging_info = remove_owner_info(charging_info_parser_result)

                # 获取燃油消耗配置项
                fuelconsump_info_parser_result = {}
                fuelconsump_info_map_dict = ["工信部综合油耗", "实测油耗", "WLTC综合油耗", "百公里耗电量"]
                for key in fuelconsump_info_map_dict:
                    if key not in car_type_info_parser_result:
                        continue
                    value = car_type_info_parser_result.get(key, "")
                    if value in [None, "", "null", "-"]:
                        continue
                    fuelconsump_info_parser_result[key] = value

                # 获取续航里程配置项
                rangeperf_info_parser_result = {}
                rangeperf_info_map_dict = ["纯电续航里程", "WLTC纯电续航里程", "CLTC综合续航", "NEDC纯电续航里程",
                                           "WLTP纯电续航里程", "CLTC纯电续航里程", "EPA纯电续航里程", "NEDC综合续航",
                                           "WLTC综合续航", "工信部续航里程", "油箱容积"]
                for key in rangeperf_info_map_dict:
                    if key not in car_type_info_parser_result:
                        continue
                    value = car_type_info_parser_result.get(key, "")
                    if value in [None, "", "null", "-"]:
                        continue
                    rangeperf_info_parser_result[key] = value
                return car_type_info_parser_result


    return {}


# 第2个封装的工具
# 通过车源id获取对应车辆的检测报告异常内容 （有优化空间，可以去掉检测报告中的url链接）
def get_car_checkreport_content_by_clue_id(clue_id: str,env:str="online") -> str:
    """ 通过车源ID(clue_id)获取车辆的检测报告完整内容 """
    # 默认线上环境，如果传入的环境不合法，则使用线上环境
    # 统一返回JSON字典
    loca_env      =    "online"
    if env is None or env == "" or env not in ( "online","test","preview","pre"):
        local_env =    "online"
    else:
        local_env =     env
    
    if clue_id is None or clue_id == "" or not validate_clue_id(clue_id):
        return {}
    # 拿到环境配置
    env_config      = get_env_config(local_env)

    url_cs_base     = env_config.url_cs_base
    key_cs_base     = env_config.key_cs_base
    secret_cs_base  = env_config.secret_cs_base

    content_list = get_check_report_defects(clue_id, url_cs_base, key_cs_base, secret_cs_base)

    # 解析检测报告缺陷数据
    parsed_defects = parse_check_report_defects(content_list) if content_list else []
    
    return parsed_defects

# 第3个封装工具
# 通过车源id获取对应的车辆检测报告URL链接
def get_car_checkreport_link_by_clue_id(clue_id: str,env:str="online") -> str:
    """ 通过车源ID(clue_id)获取车辆的检测报告链接网址 """
    loca_env        =    "online"
    if env is None or env == "" or env not in ( "online","test","preview","pre"):
        local_env   =    "online"
    else:
        local_env   =     env
    
    if clue_id is None or clue_id == "" or not validate_clue_id(clue_id):
        logger.info("车源id不合法，无法返回有效的车辆检测报告链接")
        return "" # clue_id 不合法直接返回空链接
    # 拿到环境配置
    env_config      =     get_env_config(local_env)
    url_cs_base     =     env_config.url_cs_base
    key_cs_base     =     env_config.key_cs_base
    secret_cs_base  =     env_config.secret_cs_base

    url_query_car_check_report =  os.path.join(url_cs_base, "internal/checkReport/getShowReportUrl")
    
    car_check_report_link      =  get_car_check_report_link_by_clue_id(clue_id, url_query_car_check_report, key_cs_base, secret_cs_base)
    
    return car_check_report_link

# 第4个封装工具
# 通过车源id获取对应的车辆出险记录
def get_car_insurance_history_by_clue_id(clue_id: str,env:str="online") -> str:
    """ 通过车源ID(clue_id)获取车辆的出险记录内容 """
    loca_env         =    "online"
    if env is None or env == "" or env not in ( "online","test","preview","pre"):
        local_env    =    "online"
    else:
        local_env    =     env
    
    if clue_id is None or clue_id == "" or not validate_clue_id(clue_id):
        logger.info("车源id不合法，无法返回有效的车辆出险记录")
        return {} # clue_id 不合法直接返回空链接
    # 拿到环境配置
    env_config       =      get_env_config(local_env)
    
    # 获取车源id关联的出险记录id、vin加密id，首先获取产品信息中的url,key和 secret
    url_mall_prd     =      env_config.url_mall_prd
    key_mall_prd     =      env_config.key_mall_prd
    secret_mall_prd  =      env_config.secret_mall_prd

    url_carsource    =      env_config.url_carsource
    key_carsource    =      env_config.key_carsource
    secret_carsource =      env_config.secret_carsource

    url_im           =      env_config.url_im

    product_info     =      get_product_info_by_clue_id(clue_id, url_mall_prd, key_mall_prd, secret_mall_prd)
    if not product_info or "carSourceBaseInfo" not in product_info:
        logger.info("车源id相关的产品信息获取失败")
        return {} # product_info 不合法直接返回空链接
    else:
        carSourceBaseInfo = product_info["carSourceBaseInfo"]
        vin_encrypt = carSourceBaseInfo.get("vinEncrypt", "")
        g3_order_id = carSourceBaseInfo.get("attrCarSourceInsuranceRecordId", "")

        # 第2步：获取出险报告（依赖第1步获取产品信息的结果进行处理）
        if vin_encrypt and g3_order_id:
            insurance_report = get_insurance_report(vin_encrypt, g3_order_id, url_carsource, key_carsource, secret_carsource)
            insurance_car_source_info, insurance_report_content, car_age = insurance_report_parser(insurance_report)
            return insurance_report_content
    return {}


# 第5个封装工具
# 通过车源id获取对应的车辆出险记录链接(url)
def get_car_insurance_history_link_by_clue_id(clue_id: str,env:str="online") -> str:
    """ 通过车源ID(clue_id)获取车辆的出险记录链接 """
    loca_env      =    "online"
    if env is None or env == "" or env not in ( "online","test","preview","pre"):
        local_env =    "online"
    else:
        local_env =     env
    
    if clue_id is None or clue_id == "" or not validate_clue_id(clue_id):
        logger.info("车源id不合法，无法返回有效的车辆出险记录")
        return {} # clue_id 不合法直接返回空链接
    # 拿到环境配置
    env_config       =      get_env_config(local_env)
    
    # 获取车源id关联的出险记录id、vin加密id，首先获取产品信息中的url,key和 secret
    url_mall_prd     =      env_config.url_mall_prd
    key_mall_prd     =      env_config.key_mall_prd
    secret_mall_prd  =      env_config.secret_mall_prd

    url_carsource    =      env_config.url_carsource
    key_carsource    =      env_config.key_carsource
    secret_carsource =      env_config.secret_carsource

    url_im           =      env_config.url_im

    product_info    =       get_product_info_by_clue_id(clue_id, url_mall_prd, key_mall_prd, secret_mall_prd)
    if not product_info or "carSourceBaseInfo" not in product_info:
        logger.info("车源id相关的产品信息获取失败")
        return {}    # product_info 不合法直接返回空链接
    else:
        carSourceBaseInfo = product_info["carSourceBaseInfo"]
        vin_encrypt = carSourceBaseInfo.get("vinEncrypt", "")
        g3_order_id = carSourceBaseInfo.get("attrCarSourceInsuranceRecordId", "")

        # 第2步：获取出险报告（依赖第1步获取产品信息的结果进行处理）
        if vin_encrypt and g3_order_id:
            insurance_report_link = os.path.join(url_im, "insurance-record?clueId={}&hideTitlebar=1".format(clue_id))
            return {"car_insurance_history_link": insurance_report_link}
    return {}

# 第6个工具
# 获取车源基本信息，需要优化，将相关的信息转换为有效的业务字段返回
def get_carsource_basic_info(clue_id: str,env:str="online") -> str:
    """ Get the car insurance record link(url) by the given clue id """
    loca_env      =    "online"
    if env is None or env == "" or env not in ( "online","test","preview","pre"):
        local_env =    "online"
    else:
        local_env =     env
    
    if clue_id is None or clue_id == "" or not validate_clue_id(clue_id):
        logger.info("车源id不合法，无法返回有效的车辆出险记录")
        return {} # clue_id 不合法直接返回空链接
    # 拿到环境配置
    env_config       =      get_env_config(local_env)
    
    # 获取车源id关联的出险记录id、vin加密id，首先获取产品信息中的url,key和 secret
    url_mall_prd     =      env_config.url_mall_prd
    key_mall_prd     =      env_config.key_mall_prd
    secret_mall_prd  =      env_config.secret_mall_prd

    product_info    =       get_product_info_by_clue_id(clue_id, url_mall_prd, key_mall_prd, secret_mall_prd)
    if not product_info or "carSourceBaseInfo" not in product_info:
        logger.info("车源id相关的产品信息获取失败")
        return {}    # product_info 不合法直接返回空链接
    else:
        carSourceBaseInfo = product_info.get("carSourceBaseInfo",{})
        car_source_filterd_result = car_source_other_info_parser(carSourceBaseInfo)
        return car_source_filterd_result
    return {}

# 第7个工具
# 获取车源对应车辆的基本信息
def get_car_basic_info_by_clue_id_(clue_id: str,env:str="online") -> str:
    """通过车源ID(clue_id)获取车辆的基本信息,能够获取到的信息包括：车款年份、车型名称、上牌日期、车系名称、行驶里程、过户次数、电池租用状态、年检到期日、公户私户类型、车身颜色、车钥匙、内饰颜色、电池检测报告、车龄、所在门店id 等"""
    # 默认线上环境，如果传入的环境不合法，则使用线上环境
    # 统一返回JSON字典
    loca_env        =    "online"
    if env is None or env == "" or env not in ( "online","test","preview","pre"):
        local_env   =    "online"
    else:
        local_env   =     env
    
    # 不合法的clue_id 返回空字典
    if clue_id is None or clue_id == "" or not validate_clue_id(clue_id):
        return {}

    # 拿到环境配置
    env_config      =     get_env_config(local_env)

    # 为车型配置数据获取接口查询url、key、secret信息
    url_carlib      =     env_config.url_carlib
    key_carlib      =     env_config.key_carlib
    secret_carlib   =     env_config.secret_carlib

    # 获取车源接口url网址
    url_carsource           =   env_config.url_carsource
    
   
    # 获取车源接口key
    key_carsource           =   env_config.key_carsource
    # 获取车源接口密钥
    secret_carsource        =   env_config.secret_carsource
    # 为电池报告提取基础链接
    url_mall_report         =   env_config.url_mall_report
    key_mall_report         =   env_config.key_mall_report
    secret_nev              =   env_config.secret_nev
    # 

    if clue_id != "-1" and clue_id and validate_clue_id(clue_id):
        fields = CAR_BASIC_INFO_COLS
    else:
        fields = []
    # Step1. 获取车源基本信息
    
    task_list = []
    if clue_id != "-1" and clue_id and validate_clue_id(clue_id):
        url_query_car_source    =   os.path.join(url_carsource, "cars-info/internal/carSource/queryCarSource")
        url_battery_report      =  f"{url_mall_report.rstrip('/')}/api/server/getBatteryReportInfo"
        
        task_list.extend([
                {
                    "func": get_battery_report_by_clue_id,
                    "args": (clue_id, url_battery_report, key_mall_report, secret_nev),
                    "name": "获取电池报告"
                },
                {
                    "func": get_car_basic_info_by_clue_id,
                    "args": (clue_id, CAR_BASIC_INFO_COLS, url_query_car_source, key_carsource, secret_carsource),
                    "name": "获取车源基本信息"
                },
            ])

        # 使用线程池并行执行所有HTTP数据获取的请求
        task_results = {}
        with ThreadPoolExecutor() as executor:
            future_to_task = {
                executor.submit(task["func"], *task.get("args", ())): task["name"]
                for task in task_list
            }

            for future in as_completed(future_to_task):
                task_name = future_to_task[future]
                try:
                    task_results[task_name] = future.result()
                except Exception as e:
                    print(f"{task_name} 异常: {e}")
                    task_results[task_name] = None
        car_basic_info_multi_clue_id    =   task_results.get("获取车源基本信息", {})
        battery_report                  =   task_results.get("获取电池报告", {})
    else:
        # 车源id不合法，无法拿到有效信息，返回空字典
        return {}
    # Step2. 解析车辆基本信息
    car_basic_info, _, _, store_id = car_basic_info_parser(car_basic_info_multi_clue_id, clue_id,battery_report)
    """
       返回结果示例:
       '{"车款年份": "2013", "车型名称": "丰田 花冠 2013款 1.6L 自动豪华版", "上牌日期": "20150906", "车系名称": "花冠", "行驶里程": "152200公里", "过户次数": "0", "电池租用状态": "查询不到", "年检到期日": "20260930", "公户私户类型": "公户", "车身颜色": "黑色", "车钥匙": "1", "内饰颜色": "米色", "电池检测报告": {}}'
       包括字段：车款年份、车型名称、上牌日期、车系名称、行驶里程、过户次数、电池租用状态、年检到期日、公户私户类型、车身颜色、车钥匙、内饰颜色、电池检测报告、车龄、所在门店id
    """
    return car_basic_info

# 第8个工具
# 获取车源对应车辆的基本信息
def get_car_sourcechannel_by_clue_id(clue_id: str,env:str="online") -> str:
    """通过车源ID(clue_id)获取车源渠道信息（如：车商车、个人车等）"""
    loca_env        =    "online"
    if env is None or env == "" or env not in ( "online","test","preview","pre"):
        local_env   =    "online"
    else:
        local_env   =     env
    
    # 不合法的clue_id 返回空字典
    if clue_id is None or clue_id == "" or not validate_clue_id(clue_id):
        return {"车源渠道":"无法提供车源渠道信息"}

    # 拿到环境配置
    env_config            =     get_env_config(local_env)

    url_kb                =     env_config.url_kb

    url_car_hand          =     os.path.join(url_kb, "g3/api/knowledge/car_hand_picked/verify_hand_picked")
    result = get_car_hand_picked_by_clue_id(clue_id,url_car_hand)

    return {"车源渠道":result}

# 第9个工具
# 获取车源对应车辆商品详情页链接网址
def get_car_product_detail_page_by_clue_id(clue_id: str,env:str="online") -> str:
    """通过车源ID(clue_id)获取该车源对应二手车商品详情页的链接网址"""
    loca_env        =    "online"
    if env is None or env == "" or env not in ( "online","test","preview","pre"):
        local_env   =    "online"
    else:
        local_env   =     env
    
    # 不合法的clue_id 返回空字典
    if clue_id is None or clue_id == "" or not validate_clue_id(clue_id):
        return {"car_product_detail_page_url":""}
    
    # 拿到环境配置
    env_config            =     get_env_config(local_env)
    url_im                =     env_config.url_im

    product_details_page_link = os.path.join(url_im,"detail?clueId={}&hideTitlebar=1&h5Ready=1&isPageView=1".format(clue_id))

    return {"car_product_detail_page_url":product_details_page_link}

# 第10个工具
# 获取车源对应车辆外观、内饰、机舱工况等的图片链接地址
def get_car_pictures_links_by_clue_id(clue_id: str,env:str="online") -> str:
    """通过车源ID(clue_id)获取该车源对应车辆的外观图片、内饰图片、机舱工况等的图片链接地址"""
    loca_env        =    "online"
    if env is None or env == "" or env not in ( "online","test","preview","pre"):
        local_env   =    "online"
    else:
        local_env   =     env
    
    # 不合法的clue_id 返回空字典
    if clue_id is None or clue_id == "" or not validate_clue_id(clue_id):
        return {"car_appearance_images_url":"",
                "control_interior_images_url":"",
                "engine_room_images_url":""}
    
    result = {"car_appearance_images_url":"",
                "control_interior_images_url":"",
                "engine_room_images_url":""}
    # 拿到环境配置
    env_config            =     get_env_config(local_env)
    url_mall_prd          =     env_config.url_mall_prd
    key_mall_prd          =     env_config.key_mall_prd
    secret_mall_prd       =     env_config.secret_mall_prd
    url_im                =     env_config.url_im

    image_response        =     get_car_images_http(clue_id, url_mall_prd, key_mall_prd, secret_mall_prd)
    if image_response and image_response.status_code == 200:
            try:
                response_json = image_response.json()
                if response_json.get("code") == 0:
                    image_result = response_json.get("data")
                    if image_result:
                        carsource_images = image_result.get("carSourceImages", [])
                        if len(carsource_images) > 0:
                            # 解析图片数据
                            car_appearance_inds = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 34, 35, 36, 37, 38, 39, 40, 43, 46, 48,
                                                50, 51, 52, 53, 54, 55, 56, 57]
                            control_interior_inds = [11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 41, 42, 44, 45, 47,
                                                    49]
                            engine_room_chassis_inds = [24, 25, 26, 27, 28, 29, 30]

                            car_appearance_links = []
                            control_interior_links = []
                            engine_room_links = []
                            track_key = json.dumps({"agent_type": "agent_clue_database"}, ensure_ascii=False)

                            for carsource_image in carsource_images:
                                ind = carsource_image.get("ind")
                                category_id = carsource_image.get("categoryId")
                                if ((ind in car_appearance_inds or category_id in [1, 2]) and carsource_image.get(
                                        "fullImageUrl")):
                                    car_appearance_links.append(carsource_image.get("fullImageUrl"))
                                elif ((ind in control_interior_inds or category_id in [3, 6]) and carsource_image.get(
                                        "fullImageUrl")):
                                    control_interior_links.append(carsource_image.get("fullImageUrl"))
                                elif (ind in engine_room_chassis_inds and carsource_image.get("fullImageUrl")):
                                    engine_room_links.append(carsource_image.get("fullImageUrl"))
                            result["car_appearance_images_url"]          =       car_appearance_links
                            result["control_interior_images_url"]          =       control_interior_links
                            result["engine_room_images_url"]       =       engine_room_links
            except Exception as e:
                logger.error(f"解析车源图片数据异常: {e}")
                return result 
    return result

# 第11个工具
# 获取车源对应车辆外观、内饰、机舱工况等的图片链接地址
def get_car_pictures_cards_by_clue_id(clue_id: str,env:str="online") -> str:
    """通过车源ID(clue_id)获取该车源对应车辆的外观图片卡片、内饰图片卡片、机舱工况图片卡片等卡片信息"""
    loca_env        =    "online"
    if env is None or env == "" or env not in ( "online","test","preview","pre"):
        local_env   =    "online"
    else:
        local_env   =     env
    
    # 不合法的clue_id 返回空字典
    if clue_id is None or clue_id == "" or not validate_clue_id(clue_id):
        return {"car_appearance_images_card":"",
                "control_interior_images_card":"",
                "engine_room_images_card":""}
    
    result = {"car_appearance_images_card":"",
                "control_interior_images_card":"",
                "engine_room_images_card":""}
    # 拿到环境配置
    env_config            =     get_env_config(local_env)
    url_mall_prd          =     env_config.url_mall_prd
    key_mall_prd          =     env_config.key_mall_prd
    secret_mall_prd       =     env_config.secret_mall_prd
    url_im                =     env_config.url_im

    image_response        =     get_car_images_http(clue_id, url_mall_prd, key_mall_prd, secret_mall_prd)
    if image_response and image_response.status_code == 200:
            try:
                response_json = image_response.json()
                if response_json.get("code") == 0:
                    image_result = response_json.get("data")
                    if image_result:
                        carsource_images = image_result.get("carSourceImages", [])
                        if len(carsource_images) > 0:
                            # 解析图片数据
                            car_appearance_inds = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 34, 35, 36, 37, 38, 39, 40, 43, 46, 48,
                                                50, 51, 52, 53, 54, 55, 56, 57]
                            control_interior_inds = [11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 41, 42, 44, 45, 47,
                                                    49]
                            engine_room_chassis_inds = [24, 25, 26, 27, 28, 29, 30]

                            car_appearance_links = []
                            control_interior_links = []
                            engine_room_links = []
                            track_key = json.dumps({"agent_type": "agent_clue_database"}, ensure_ascii=False)

                            for carsource_image in carsource_images:
                                ind = carsource_image.get("ind")
                                category_id = carsource_image.get("categoryId")
                                if ((ind in car_appearance_inds or category_id in [1, 2]) and carsource_image.get(
                                        "fullImageUrl")):
                                    car_appearance_links.append(carsource_image.get("fullImageUrl"))
                                elif ((ind in control_interior_inds or category_id in [3, 6]) and carsource_image.get(
                                        "fullImageUrl")):
                                    control_interior_links.append(carsource_image.get("fullImageUrl"))
                                elif (ind in engine_room_chassis_inds and carsource_image.get("fullImageUrl")):
                                    engine_room_links.append(carsource_image.get("fullImageUrl"))

                            product_details_page_link = os.path.join(url_im,
                                                                    "detail?clueId={}&hideTitlebar=1&h5Ready=1&isPageView=1".format(
                                                                        clue_id))
                            car_appearance_image_url = {
                                "message_type": "PICTURE",
                                "content": {
                                    "type": 21,
                                    "info": {
                                        "links": car_appearance_links,
                                        "more_info_url": product_details_page_link,
                                        "clue_id": clue_id
                                    },
                                    "track_key": track_key
                                }
                            }
                            control_interior_image_url = {
                                "message_type": "PICTURE",
                                "content": {
                                    "type": 21,
                                    "info": {
                                        "links": control_interior_links,
                                        "more_info_url": product_details_page_link,
                                        "clue_id": clue_id
                                    },
                                    "track_key": track_key
                                }
                            }
                            engine_room_image_url = {
                                "message_type": "PICTURE",
                                "content": {
                                    "type": 21,
                                    "info": {
                                        "links": engine_room_links,
                                        "more_info_url": product_details_page_link,
                                        "clue_id": clue_id
                                    },
                                    "track_key": track_key
                                }
                            }
                            result.update({
                            "car_appearance_images_card": json.dumps(car_appearance_image_url, ensure_ascii=False),
                            "control_interior_images_card": json.dumps(control_interior_image_url, ensure_ascii=False),
                            "engine_room_images_card": json.dumps(engine_room_image_url, ensure_ascii=False)
                        })
            except Exception as e:
                logger.error(f"解析车源图片数据异常: {e}")
                return result 
    return result

# 第12个工具
# 获取车源对应车辆选装配置卡片信息
def get_optional_features_by_clue_id(clue_id: str,env:str="online") -> str:
    """通过车源ID(clue_id)获取对应车辆的选装配置信息"""
    result          =    {"optional_features":{}}

    optional_features_key_name = 'attrCarSourceOptionalComponents'
    optional_features_ids      = ""
    car_type_id                = ""

    loca_env      =    "online"
    if env is None or env == "" or env not in ( "online","test","preview","pre"):
        local_env =    "online"
    else:
        local_env =     env
    
    if clue_id is None or clue_id == "" or not validate_clue_id(clue_id):
        logger.info("车源id不合法，无法返回有效的车辆出险记录")
        return result # clue_id 不合法直接返回空链接
    # 拿到环境配置
    env_config       =      get_env_config(local_env)
    
    # 获取车源id关联的出险记录id、vin加密id，首先获取产品信息中的url,key和 secret
    url_mall_prd     =      env_config.url_mall_prd
    key_mall_prd     =      env_config.key_mall_prd
    secret_mall_prd  =      env_config.secret_mall_prd

    url_carlib       =      env_config.url_carlib
    key_carlib       =      env_config.key_carlib
    secret_carlib    =      env_config.secret_carlib

    product_info    =       get_product_info_by_clue_id(clue_id, url_mall_prd, key_mall_prd, secret_mall_prd)
    if not product_info or "carSourceBaseInfo" not in product_info:
        logger.info("车源id相关的产品信息获取失败")
        return result    # product_info 不合法直接返回空链接
    else:
        carSourceBaseInfo = product_info.get("carSourceBaseInfo",{})
        optional_features_ids = carSourceBaseInfo.get(optional_features_key_name, "")
        car_type_id = carSourceBaseInfo.get("carId", "")
        if len(optional_features_ids) == 0 or len(str(car_type_id)) == 0:
            return result

    try:
       optionalfeattures = get_optional_features(car_type_id, str(optional_features_ids), url_carlib, key_carlib,
                                                                secret_carlib)
       result["optional_features"] = optionalfeattures               
       return result
    except Exception as e:
       return result
    return result 

# 第13个工具
# 获取车源对应车辆的选装配置
def get_charging_info_by_clue_id(clue_id: str,env:str="online") -> str:
    """通过车源ID(clue_id)获取对应车辆的充电相关信息"""
    result          =    {"charging_info":{}}

    loca_env        =    "online"
    if env is None or env == "" or env not in ( "online","test","preview","pre"):
        local_env   =    "online"
    else:
        local_env   =     env
    
    # 不合法的clue_id 返回空字典
    if clue_id is None or clue_id == "" or not validate_clue_id(clue_id):
        return result

    # 拿到环境配置
    env_config      =     get_env_config(local_env)

    # 为车型配置数据获取接口查询url、key、secret信息
    url_carlib      =     env_config.url_carlib
    key_carlib      =     env_config.key_carlib
    secret_carlib   =     env_config.secret_carlib

    # 获取车源接口url网址
    url_carsource           =   env_config.url_carsource
    url_query_car_source    =   os.path.join(url_carsource, "cars-info/internal/carSource/queryCarSource")
   
    # 获取车源接口key
    key_carsource           =   env_config.key_carsource
    # 获取车源接口密钥
    secret_carsource        =   env_config.secret_carsource

    if clue_id != "-1" and clue_id and validate_clue_id(clue_id):
        fields = CAR_BASIC_INFO_COLS
    else:
        fields = []
    # 获取车源基本信息
    car_basic_info_multi_clue_id = get_car_basic_info_by_clue_id(clue_id, CAR_BASIC_INFO_COLS, url_query_car_source, key_carsource, secret_carsource)

    if car_basic_info_multi_clue_id:
        car_type_id = car_basic_info_multi_clue_id.get(clue_id, {}).get("car_id", "")
        if car_type_id:
            # 获取车型信息（依赖car_type_id）
            car_type_info_result = get_get_car_type_info_by_car_id(car_type_id, url_carlib, key_carlib, secret_carlib)
            if car_type_info_result:
                car_type_info_parser_result = car_type_info_parser(car_type_info_result)

                # 获取充电配置项
                charging_info_parser_result = {}
                charging_info_map_dict = ["快充时间", "慢充时间", "快充功能", "电池充电时间", "充电桩价格", "快充电量",
                                          "电池快充电量范围", "高压快充", "快充接口位置", "充电站", "充电桩",
                                          "电池类型",
                                          "电池组质保", "电池组质保年限", "电池组质保里程", "电芯品牌", "电池冷却方式",
                                          "电池能量密度", "电池容量", "三电系统质保", "三电系统质保里程",
                                          "三电系统质保年限",
                                          "三电首任车主质保政策"]

                for key in charging_info_map_dict:
                    if key not in car_type_info_parser_result:
                        continue
                    value = car_type_info_parser_result.get(key, "")
                    if value in [None, "", "null", "-"]:
                        continue
                    charging_info_parser_result[key] = value

                filtered_charging_info = remove_owner_info(charging_info_parser_result)

                result["charging_info"] = filtered_charging_info
                return result
    return result


# 第14个工具
# 获取车源对应车辆油耗、电耗及满电续航配置信息
def get_energyconfig_by_clue_id(clue_id: str,env:str="online") -> str:
    """通过车源ID(clue_id)获取车辆的燃油类型、油耗、电耗、及满电续航配置信息"""
    result          =    { }

    loca_env        =    "online"
    if env is None or env == "" or env not in ( "online","test","preview","pre"):
        local_env   =    "online"
    else:
        local_env   =     env
    
    # 不合法的clue_id 返回空字典
    if clue_id is None or clue_id == "" or not validate_clue_id(clue_id):
        return {}

    # 拿到环境配置
    env_config      =     get_env_config(local_env)

    # 为车型配置数据获取接口查询url、key、secret信息
    url_carlib      =     env_config.url_carlib
    key_carlib      =     env_config.key_carlib
    secret_carlib   =     env_config.secret_carlib

    # 获取车源接口url网址
    url_carsource           =   env_config.url_carsource
    url_query_car_source    =   os.path.join(url_carsource, "cars-info/internal/carSource/queryCarSource")
   
    # 获取车源接口key
    key_carsource           =   env_config.key_carsource
    # 获取车源接口密钥
    secret_carsource        =   env_config.secret_carsource

    if clue_id != "-1" and clue_id and validate_clue_id(clue_id):
        fields = CAR_BASIC_INFO_COLS
    else:
        fields = []
    # 获取车源基本信息
    car_basic_info_multi_clue_id = get_car_basic_info_by_clue_id(clue_id, CAR_BASIC_INFO_COLS, url_query_car_source, key_carsource, secret_carsource)

    if car_basic_info_multi_clue_id:
        car_type_id = car_basic_info_multi_clue_id.get(clue_id, {}).get("car_id", "")
        if car_type_id:
            # 获取车型信息（依赖car_type_id）
            car_type_info_result = get_get_car_type_info_by_car_id(car_type_id, url_carlib, key_carlib, secret_carlib)
            if car_type_info_result:
                car_type_info_parser_result = car_type_info_parser(car_type_info_result)

                result["动力类型"] = car_type_info_parser_result.get("燃油类型", "")

                # 获取燃油消耗配置项
                fuelconsump_info_parser_result = {}
                fuelconsump_info_map_dict = ["工信部综合油耗", "实测油耗", "WLTC综合油耗", "百公里耗电量"]
                for key in fuelconsump_info_map_dict:
                    if key not in car_type_info_parser_result:
                        continue
                    value = car_type_info_parser_result.get(key, "")
                    if value in [None, "", "null", "-"]:
                        continue
                    fuelconsump_info_parser_result[key] = value
                result["能耗信息"] = fuelconsump_info_parser_result

                # 获取续航里程配置项
                rangeperf_info_parser_result = {}
                rangeperf_info_map_dict = ["纯电续航里程", "WLTC纯电续航里程", "CLTC综合续航", "NEDC纯电续航里程",
                                           "WLTP纯电续航里程", "CLTC纯电续航里程", "EPA纯电续航里程", "NEDC综合续航",
                                           "WLTC综合续航", "工信部续航里程", "油箱容积"]
                for key in rangeperf_info_map_dict:
                    if key not in car_type_info_parser_result:
                        continue
                    value = car_type_info_parser_result.get(key, "")
                    if value in [None, "", "null", "-"]:
                        continue
                    rangeperf_info_parser_result[key] = value
                result["续航里程信息"] =  rangeperf_info_parser_result
                return result


    return {}


# 第15个工具
# 获取车源所在城市
def get_car_source_city_by_clue_id_(clue_id: str,ext:str, env:str="online") -> str:
    """通过车源ID(clue_id)和附加信息(ext)获取车源所在城市"""
    result          =    {"car_source_city":{}}
    loca_env        =    "online"
    if env is None or env == "" or env not in ( "online","test","preview","pre"):
        local_env   =    "online"
    else:
        local_env   =     env
    
    # 不合法的clue_id 返回空字典
    if clue_id is None or clue_id == "" or not validate_clue_id(clue_id):
        return result

    # 拿到环境配置
    env_config      =     get_env_config(local_env)
    url_cs_base = env_config.url_cs_base
    key_cs_base = env_config.key_cs_base
    secret_cs_base = env_config.secret_cs_base

    url_uniform_query          =  os.path.join(url_cs_base, "productPresentation/v2/uniformQuery")

    car_sourc_city = get_car_source_city_by_clue_id(clue_id, ext, url_uniform_query, key_cs_base, secret_cs_base)
    result["car_source_city"] = car_sourc_city
    return result

# 第16个工具
# 获取车源对应车辆的车况等级
def get_car_condition_level_by_clue_id_(clue_id: str,env:str="online") -> str:
    """通过车源ID(clue_id)获取车源对应车辆的车况等级"""
    result          =    { "car_condition_level":""}

    loca_env        =    "online"
    if env is None or env == "" or env not in ( "online","test","preview","pre"):
        local_env   =    "online"
    else:
        local_env   =     env
    
    # 不合法的clue_id 返回空字典
    if clue_id is None or clue_id == "" or not validate_clue_id(clue_id):
        return  { "car_condition_level":""}

    # 拿到环境配置
    env_config          =     get_env_config(local_env)
    url_cs_base         =     env_config.url_cs_base
    key_cs_base         =     env_config.key_cs_base
    secret_cs_base      =     env_config.secret_cs_base

    url_car_condition_level    =  os.path.join(url_cs_base, "internal/checkReport/userPerspectiveReportEvaluation")
    car_condition_level = get_car_condition_level_by_clue_id(clue_id,url_car_condition_level, key_cs_base, secret_cs_base)

    result["car_condition_level"] = car_condition_level
    return result

# 第17个工具
# 获取车源对应车辆的车况等级
def get_car_price_info_by_clue_id_gz_user_id_ext(clue_id: str,gz_user_id:str,ext:str,env:str="online") -> str:
    """通过车源ID(clue_id)和用户ID(gz_user_id)以及扩展参数(ext)获取车源对应车辆的所有价格信息（含优惠、优惠后价格、优惠信息等）"""
    result = {"car_price_info": "", "price_analysis_info": "", "new_car_price_info": ""}
    try:
        price_info = get_price_info_by_clue_id_gz_user_id_ext(gz_user_id, clue_id, ext, env)
        result["car_price_info"] = price_info.get("car_price_info","")
        result["price_analysis_info"] = price_info.get("price_analysis_info","")
        result["new_car_price_info"] = price_info.get("new_car_price_info","")
    except Exception as e:
        logger.error(f"get_car_price_info_by_clue_id_gz_user_id_ext error: {e}")
        return result
    return result

# 第18个工具
# 获取带车源ID的相关车型口碑知识（可能会存在没有的情况，但是对于热门车型的口碑都是有的）
def get_car_reputation_by_clue_id_(clue_id: str, env:str="online") -> str:
    """通过车源ID(clue_id)获取车源对应车辆某一口碑维度(车型、车系、品牌等)的车主评价口碑知识，其中口碑的维度包括："""
    result = {}
    loca_env        =    "online"
    if env is None or env == "" or env not in ( "online","test","preview","pre"):
        local_env   =    "online"
    else:
        local_env   =     env
    
    # 不合法的clue_id 返回空字典
    if clue_id is None or clue_id == "" or not validate_clue_id(clue_id):
        return  { "car_condition_level":""}

    # 拿到环境配置
    env_config                  =   get_env_config(local_env)
    
    try:
        car_reputation           =   get_car_reputation_by_clue_id( clue_id )
        result["car_reputation"] =   car_reputation
        return result
    except Exception as e:
        logger.error(f"get_car_reputation_by_clue_id_ error: {e}")
        return result
    return result

# 第19个工具
# 获取无车源用户问题的汽车通用知识（包括口碑和车型配置查询）
def get_car_general_knowledge_without_clue_id_(question:str,env:str="online") -> str:
    """通过车源ID(clue_id)获取车源对应车辆车型、车系、品牌等口碑知识"""
    result                       =    {"car_knowledge":{}}
    loca_env                     =    "online"
    if env is None or env == "" or env not in ( "online","test","preview","pre"):
        local_env                =    "online"
    else:
        local_env                =     env

    # 拿到环境配置
    env_config                   =     get_env_config(local_env)
    url_car_general_knowledge    =     env_config.url_car_general_knowledge
    key_car_general_knowledge    =     env_config.key_car_general_knowledge

    try:
        car_knowledge = get_car_general_knowledge_without_clue_id( question )
        result["car_knowledge"] = car_knowledge
        return result
    except Exception as e:
        logger.error(f"get_car_general_knowledge_by_clue_id error: {e}")
        return result
    return result

def get_car_cost_by_clue_id_(clue_id ,env:str="online") -> str:
    """通过车源ID(clue_id)获取车源对应车辆的用车成本信息（年均保养费、年均保险费、年均油费）"""
    result = {
        "用车成本":{
                    "年均保养费": "",
                    "年均保险费": "",
                    "年均油费": ""
                }
        }
    loca_env = "online"
    if env is None or env == "" or env not in ( "online","test","preview","pre"):
        local_env = "online"
    elif env == "preview" or env == "pre" or env == "test":
        local_env = "preview"
    else:
        local_env = env

    # 拿到环境配置
    env_config = get_env_config(local_env)
    url_car_cost = env_config.url_car_cost

    url_car_cost_api = os.path.join(url_car_cost, "v2/api/car")
    key_car_cost = env_config.key_car_cost
    secret_car_cost = env_config.secret_car_cost


    # 获取车源接口url网址
    url_carsource           =   env_config.url_carsource
    url_query_car_source    =   os.path.join(url_carsource, "cars-info/internal/carSource/queryCarSource")
   
    # 获取车源接口key和密钥
    key_carsource           =   env_config.key_carsource
    secret_carsource        =   env_config.secret_carsource


    CAR_TAG_ID_COLS = ["tag_id"]
    if clue_id != "-1" and clue_id and validate_clue_id(clue_id):
        fields = CAR_TAG_ID_COLS
    else:
        fields = []

    try:
        # Step 1. 通过clue_id 获取tag_id 
        tag_id = ""
        
        # 通过 clue_id 获取 车系id
        car_basic_info_ = get_car_basic_info_by_clue_id(clue_id, CAR_TAG_ID_COLS, url_query_car_source, key_carsource, secret_carsource)
        
        if car_basic_info_ is None :
            return {
                "用车成本":{
                    "年均保养费": "",
                    "年均保险费": "",
                    "年均油费": ""
                }
            }
        else:
            if isinstance(car_basic_info_, dict):
                tag_id = car_basic_info_.get(f"{clue_id}", {}).get("tag_id", "")
                if tag_id is None or tag_id == "" or not validate_tag_id(str(tag_id)):
                    return {
                        "用车成本":{
                            "年均保养费": "",
                            "年均保险费": "",
                            "年均油费": ""
                        }
                    }
            else:
                return {
                    "用车成本":{
                        "年均保养费": "",
                        "年均保险费": "",
                        "年均油费": ""
                    }
                }
        
        # Step 2. 通过 tag_id 获取用车成本信息 （注意，目前只有油车有数据，新能源车没有数据）

        car_cost = get_car_cost_by_tag_id_(tag_id, url_car_cost_api, key_car_cost, secret_car_cost)
        result = car_cost
        return result
    except Exception as e:
        logger.error(f"get_car_cost_by_clue_id error: {e}")
        return result
    return result

# 第20个工具
# 获取车源亮点小作文文案
def get_car_source_highlight_by_clue_id_(clue_id: str,env:str="online") -> str:
    """通过车源ID(clue_id)获取车源对应车辆车型、车系、品牌等口碑知识"""
    result                 =    {"car_source_highlight":""}
    loca_env               =    "online"
    if env is None or env == "" or env not in ( "online","test","preview","pre"):
        local_env          =    "online"
    else:
        local_env          =    env

    # 目前无法提供这部分的数据，需要后端对小作文的数据进行封装
    # # 不合法的clue_id 返回空字典
    # if clue_id is None or clue_id == "" or not validate_clue_id(clue_id):
    #     return  { "car_condition_level":""}

    # # 拿到环境配置
    # env_config                         =     get_env_config(local_env)
    # url_car_source_highlight           =     env_config.url_car_source_highlight

    # try:
    #     car_knowledge                  =     get_car_source_highlight_by_clue_id( clue_id, url_car_source_highlight )
    #     result["car_source_highlight"] =     car_knowledge
    #     return result
    # except Exception as e:
    #     logger.error(f"get_car_reputation_by_clue_id error: {e}")
    #     return result
    
    return result

# if __name__ == "__main__":
    # 业务逻辑已拆分为独立可执行脚本，参见 scripts/tools/ 目录
    # 例如: python scripts/tools/get_car_type_info.py <clue_id> [--env online]
    # 下面为 get_car_reputation_by_clue_id_ 的多组测试示例，便于快速本地验证

    # 示例1：整体评价（期望：返回包含 car_reputation 字段的非空结果）
    # result = get_car_reputation_by_clue_id_("160179652", "这车怎么样？", "174132952062000095","test")
    # print("示例1-整体评价-期望 car_reputation 非空:", result)

    # # # 示例2：空间表现（期望：能正常返回，与空间相关的口碑内容）
    # result = get_car_reputation_by_clue_id_("160179652", "车主普遍反馈空间怎么样？", "174132952062000095""online")
    # print("示例2-空间表现-期望 car_reputation 正常返回:", result)

    # # # 示例3：油耗表现（期望：能正常返回，与油耗/费油相关的口碑内容）
    # result = get_car_reputation_by_clue_id_("160179652", "油耗表现怎么样？费油吗？", "174132952062000095""online")
    # print("示例3-油耗表现-期望 car_reputation 正常返回:", result)

    # # # 示例4：舒适性与噪音（期望：能正常返回，与舒适性/噪音相关的口碑内容）
    # result = get_car_reputation_by_clue_id_("160179652", "车主对舒适性和噪音的评价如何？","174132952062000095" "online")
    # print("示例4-舒适性与噪音-期望 car_reputation 正常返回:", result)

    # # # 示例5：非法 env 兜底验证（期望：env 无效时按 online 兜底，依然返回 car_reputation）
    # result = get_car_reputation_by_clue_id_("160179652", "底盘质感如何？", "174132952062000095""dev")
    # print("示例5-env非法兜底-期望 car_reputation 依然可用:", result)

    # # # 示例6：非法 clue_id（空字符串，期望：直接返回 {\"car_condition_level\": \"\"}）
    # result = get_car_reputation_by_clue_id_("", "这车怎么样？", "174132952062000095""online")
    # print("示例6-clue_id为空-期望 {'car_condition_level': ''}:", result)

    # # # 示例7：非法 clue_id（格式不合法，期望：同样返回 {\"car_condition_level\": \"\"}）
    #result = get_car_reputation_by_clue_id_("160179652","online")
    #print("示例7-clue_id不合法-期望 {'car_condition_level': ''}:", result)

    # result = get_car_general_knowledge_by_clue_id_("这车怎么样？", "174132952062000095","preview")
    # print("示例8-get_car_general_knowledge_by_clue_id_ -期望 car_knowledge 非空:", result)

    # result = get_car_general_knowledge_by_clue_id_("宝马X3怎么样？", "174132952062000095","preview")
    # print("示例9-get_car_general_knowledge_by_clue_id_ -期望 car_knowledge 非空:", result)

    #result = get_car_source_highlight_by_clue_id_("160179652","preview")
    #print("示例10-get_car_source_highlight_by_clue_id_ -期望 car_source_highlight 非空:", result)
    # result = get_car_cost_by_clue_id_("164477550","online")
    # print(result)

    # result = get_car_cost_by_clue_id_("164357273","preview")
    # print(result)

    # result = get_car_cost_by_clue_id_("164568446","online")
    # print(result)

    # result = get_car_cost_by_clue_id_("164552211","test")
    # print(result)

    # result = get_car_cost_by_clue_id_("164375404","online")
    # print(result)
    # print("Finished!")

    
   