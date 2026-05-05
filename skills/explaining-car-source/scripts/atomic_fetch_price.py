import base64
import hashlib
import hmac
import json
import random
import time
import urllib.parse
from datetime import datetime
from typing import Dict, Any, Optional

import requests
from utils import log_http_timing
# ===================== 配置信息 =====================

CONFIG = {
    "apps": {
        "keys": {
            "carlib": ("model_agent", "AFvXYzurlUeSrk0o"),
            "carsource": ("ai_agent", "secAiAgent0228@25OL"),
            "mall_product": ("znkf", "M24cgsND"),
            "checklk": ("nlp", "ca4218cb"),
            "mall_pp": ("large_model", "ec56248fc3719f78c8df520714ea2334"),
            "cs_base": ("ai_agent", "2c2b0389"),
            "sale_cs": ("guazi_ig", "qbf01191895b"),
            "client_re": ("ai_agent", "9a89a824"),
            "nev": ("ai_agent", "824AsudnLs2"),
            "open_data": ("rag__llm-dify-api", "3168608f19"),
            "user_order": ("large_model", "ec56248fc3719f78c8df520714ea2334"),
            "misc_commapi": ("58265588", "fie5uD7oar2P"),
            "kuaizhao": ("lm-xiaogua", "b7c604f7"),
        },
        "urls": {
            "client_rest": "http://client-restful-api.guazi-apps.com",
            "cs_base": "https://car-source-baseinfo.guazi-apps.com",
            "kb": "http://knowledge-base.guazi-apps.com",
            "mall_product": "http://mall-product.guazi-apps.com",
            "carsource": "http://carsource-api.guazi-apps.com",
            "opl_cs": "http://opl-car-source.guazi-apps.com",
            "carlib": "https://carlib-api.guazi-apps.com",
            "im": "https://m.guazi.com",
            "mall_pp": "https://mall-product-price.guazi-apps.com",
            "cars_info": "https://cars-info.guazi-apps.com",
            "appointment": "https://opl-dealer-tool.guazi-apps.com",
            "wechat_guide": "http://znkf-agent-service.guazi-apps.com",
            "act": "https://act.guazi.com",
            "sale_cs": "https://sale-carservice.guazi-apps.com",
            "uc": "https://uc.guazi.com",
            "new_energy": "http://new-energy-server.guazi-apps.com",
            "open_data": "https://open-data-api.guazi-apps.com",
            "user_order": "http://user-order.guazi-apps.com",
            "misc_commapi": "http://misc-commapi.guazi.com",
            "cost_performance": "http://ai-car.guazi-apps.com",
        }
    },
    "pre": {
        "keys": {
            "carlib": ("model_agent", "AFvXYzurlUeSrk0o"),
            "carsource": ("ai_agent", "secAiAgent0228@25OL"),
            "mall_product": ("znkf", "M24cgsND"),
            "checklk": ("nlp", "ca4218cb"),
            "mall_pp": ("large_model", "ec56248fc3719f78c8df520714ea2334"),
            "cs_base": ("ai_agent", "2c2b0389"),
            "sale_cs": ("guazi_ig", "qbf01191895b"),
            "client_re": ("ai_agent", "9a89a824"),
            "nev": ("ai_agent", "824AsudnLs2"),
            "open_data": ("rag__llm-dify-api", "3168608f19"),
            "user_order": ("large_model", "ec56248fc3719f78c8df520714ea2334"),
            "misc_commapi": ("58265588", "fie5uD7oar2P"),
            "kuaizhao": ("lm-xiaogua", "b7c604f7"),
        },
        "urls": {
            "client_rest": "http://client-restful-api.guazi-preview.com",
            "cs_base": "http://car-source-baseinfo-preview.guazi-apps.com",
            "kb": "http://knowledge-base-preview.guazi-apps.com",
            "mall_product": "http://mall-product-preview.guazi-apps.com",
            "carsource": "http://carsource-api-preview.guazi-apps.com",
            "opl_cs": "http://opl-car-source-preview.guazi-apps.com",
            "carlib": "https://carlib-api-preview.guazi-apps.com",
            "im": "https://buy-preview.guazi-apps.com",
            "mall_pp": "https://mall-product-price-preview.guazi-apps.com",
            "cars_info": "https://cars-info.guazi-preview.com",
            "appointment": "https://opl-dealer-tool-preview.guazi-apps.com",
            "wechat_gui": "http://znkf-agent-service.guazi-preview.com",
            "act": "https://act-preview.guazi-apps.com",
            "sale_cs": "https://sale-carservice-preview.guazi-apps.com",
            "uc": "https://muc-preview.guazi-apps.com",
            "new_energy": "http://new-energy-server-preview.guazi-apps.com",
            "open_data": "https://open-data-api-preview.guazi-apps.com",
            "user_order": "http://user-order-preview.guazi-apps.com",
            "misc_commapi": "http://misc-commapi.guazi.com",
            "cost_performance": "http://ai-car.guazi-apps.com",
        }
    }
}

# ===================== API接口常量 =====================
API_CAR_PRICE_COUPON = "clientPrice/carPrice/getByClueIds"
API_QUERY_PRODUCT_STATUS = "api/product/queryProductStatusByClueIds"
API_CAR_PRICE_COST = "clientPriceItem/calculatePriceItemsNoAutoGrant"
API_INTO_CITY = "api/saleCarDeliver/getIntoCities"
API_COST_PERFORMANCE = "price/explain/market_price_for_customer"
API_NEW_CAR_LANDING_FEE = "g3/api/knowledge/car_coupon_info/getNewCarCost"
API_GET_CITY_BY_ID = "misc/area/get_city_by_id"
API_QUERY_CAR_SOURCE = "cars-info/internal/carSource/queryCarSource"

PRODUCT_STATUS_MAP = {5: "待上架", 10: "已上架", 15: "交易中", 20: "售出"}
CAR_BASIC_INFO_COLS = ["title", "tag_name", "car_year", "road_haul", "transfer_num", "car_owner_type", "store_id",
                       "license_full_date"]
CAR_BASIC_INFO_MAP = {
    "title": "车型名称", "tag_name": "车系名称", "car_year": "车款年份", "road_haul": "行驶里程",
    "transfer_num": "过户次数", "car_owner_type": "公户私户类型", "store_id": "车商id"
}
COST_PERFORMANCE_KEY_MAP = {
    "deal_price_min": "历史成交车价格区间下限",
    "deal_price_max": "历史成交车价格区间上限",
    "deal_price_mean": "历史成交车价格平均值",
}


# ===================== 辅助函数 =====================

def get_env_config(env: str) -> Dict[str, Any]:
    """获取指定环境的配置"""
    return CONFIG.get(env, CONFIG["apps"])


def _generate_signature(params: Dict[str, Any], secret: str) -> str:
    """生成签名"""
    try:
        sorted_keys = sorted(params.keys())
        message = "&".join([f"{key}={urllib.parse.quote(str(params[key]))}" for key in sorted_keys])

        hmac_sha256 = hmac.new(secret.encode('utf-8'), message.encode('utf-8'), hashlib.sha256)
        signature = base64.b64encode(hmac_sha256.digest()).decode('utf-8')

        md5_hash = hashlib.md5(signature.encode('utf-8')).hexdigest()
        return md5_hash[5:15]
    except Exception as e:
        print(f"签名生成异常: {e}")
        return ""


def _create_signed_params(params: Dict[str, Any], app_key: str, secret: str) -> Dict[str, Any]:
    """创建带有签名的请求参数"""
    all_params = params.copy()
    all_params["appkey"] = app_key
    all_params["expires"] = str(int(time.time()))
    all_params["nonce"] = ''.join(random.choices("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz", k=4))
    all_params["signature"] = _generate_signature(all_params, secret)
    return all_params


def _make_api_request(method: str, url: str, params: Dict = None, json_data: Dict = None,
                      timeout: int = 10) -> Optional[Dict]:
    """发起API请求并处理通用逻辑"""
    try:
        if method.upper() == 'GET':
            response = requests.get(url, params=params, timeout=timeout)
        elif method.upper() == 'POST':
            response = requests.post(url, params=params, json=json_data, timeout=timeout)
        else:
            raise ValueError("不支持的HTTP方法")

        response.raise_for_status()
        response_json = response.json()

        if response_json.get("code") == 0:
            return response_json.get("data")
        else:
            print(f"API请求失败: url={url}, response={response.text}")
            return None

    except (requests.RequestException, json.JSONDecodeError, ValueError) as e:
        print(f"API请求异常: {e}")
        return None


def validate_clue_id(clue_id: str) -> bool:
    """验证clue_id格式是否正确"""
    return isinstance(clue_id, str) and clue_id.isdigit() and len(clue_id) == 9


def parse_ext(ext_str: str) -> Dict[str, Any]:
    """解析ext参数"""
    if not isinstance(ext_str, str):
        return {}
    try:
        return json.loads(ext_str)
    except json.JSONDecodeError:
        try:
            return eval(ext_str.replace("\n", ""))
        except Exception:
            return {}


def format_price(price: float, unit: str = "元") -> str:
    """格式化价格，返回带单位的整数字符串,原始数据精确到分"""
    if price is None:
        return ""
    return f"{int(price / 100)}{unit}"

def format_price_yuan(price:float,unit:str= "元") -> str:
    """格式化价格，返回带单位的整数字符串，原始数据精确到元"""
    if price is None:
        return ""
    return f"{int(price)}{unit}"


# ===================== 核心业务函数 =====================

def _query_product_status(clue_id: str, config: Dict) -> str:
    """查询产品状态"""
    url = f"{config['urls']['mall_product']}/{API_QUERY_PRODUCT_STATUS}"
    app_key, app_secret = config['keys']['mall_product']
    params = _create_signed_params({"clueIds": clue_id}, app_key, app_secret)
    data = _make_api_request('GET', url, params=params)
    if data and isinstance(data, list) and data:
        return PRODUCT_STATUS_MAP.get(data[0].get("productStatus"), "")
    return ""


def _get_plate_city_info(clue_id: str, plate_city_id: int, config: Dict) -> str:
    """获取迁入城市信息"""
    plate_city_status = ""
    plate_city_name = ""

    # 迁入城市状态
    url_status = f"{config['urls']['sale_cs']}/{API_INTO_CITY}"
    key_status, secret_status = config['keys']['sale_cs']
    params_status = _create_signed_params({"clueId": clue_id, "invoker": "electronic_commerce_online"}, key_status,
                                          secret_status)
    data_status = _make_api_request('GET', url_status, params=params_status, timeout=8)

    if data_status:
        plate_city_status = "允许迁入"
        for item in data_status:
            if item.get("id") == plate_city_id and item.get("verifyImmigration") == 0:
                plate_city_status = "不允许迁入"
                break

    # 迁入城市名称
    url_name = f"{config['urls']['misc_commapi']}/{API_GET_CITY_BY_ID}"
    key_name, secret_name = config['keys']['misc_commapi']
    params_name = _create_signed_params({"id": plate_city_id}, key_name, secret_name)
    data_name = _make_api_request('GET', url_name, params=params_name, timeout=10)

    if data_name:
        plate_city_name = data_name.get("city_name", "")

    return f"{plate_city_name}{plate_city_status}"


def _get_car_price_cost(gz_user_id: str, clue_id: str, plate_city_id: int, selected_city_id: int, guid: str,
                        config: Dict) -> Dict:
    """获取车辆价格成本信息"""
    url = f"{config['urls']['mall_pp']}/{API_CAR_PRICE_COST}"
    app_key, app_secret = config['keys']['mall_pp']

    params = {
        "userId": gz_user_id,
        "clueId": int(clue_id),
        "deviceId": guid or "123",
        "deliveryCityId": selected_city_id,
        "plateCityId": plate_city_id,
        "payType": "fullPayment",
    }
    signed_params = _create_signed_params(params, app_key, app_secret)
    data = _make_api_request('POST', url, json_data=signed_params, timeout=8)

    prices = {}
    if data:
        prices['car_otd_price'] = format_price(data.get("total"))
        for item in data.get("priceItems", []):
            key_map = {
                "car": "car_sell_price",
                "sale_market": "market_sell_price",
                "delivery_deposit": "transfer_deposit",
                "settle_down": "transfer_fee",
                "logistics": "logistics_fee",
            }
            if item.get("key") in key_map:
                prices[key_map[item["key"]]] = format_price(item.get("receivedPrice"))

    return prices


def _get_car_price_coupon(gz_user_id: str, clue_id: str, selected_city_id: int, config: Dict) -> Dict:
    """获取车辆优惠价格信息"""
    url = f"{config['urls']['mall_pp']}/{API_CAR_PRICE_COUPON}"
    app_key, app_secret = config['keys']['mall_pp']
    params = {
        "cluePriceVOs": [{"clueId": clue_id}],
        "selectedCityId": selected_city_id,
        "userId": gz_user_id,
    }
    signed_params = _create_signed_params(params, app_key, app_secret)
    data = _make_api_request('POST', url, json_data=signed_params, timeout=8)

    coupon_info = {}
    if data and isinstance(data, list) and data:
        price_info = data[0]
        coupon_info['butie_info'] = format_price(price_info.get("marketLowestActivitySubsidyPrice"))
        coupon_info['coupon_price'] = format_price(price_info.get("couponPrice"))
        coupon_info['car_orginal_price'] = format_price(price_info.get("clueLinePrice"))
        coupon_info['car_coupon_price'] = format_price(price_info.get("clueCouponPrice"))

        if price_info.get("templateDTO"):
            template = price_info["templateDTO"][0]
            coupon_info['youhui_info'] = json.dumps({
                "优惠券活动使用规则": template.get("usingRule"),
                "优惠券活动开始时间": template.get("templateValidStart"),
                "优惠券活动结束时间": template.get("templateValidEnd"),
                "优惠券活动金额": format_price(template.get("amount")),
            }, ensure_ascii=False)

        if price_info.get("seckillDTO"):
            seckill = price_info["seckillDTO"][0]
            seckill_quota = seckill.get("quota", 0) + seckill.get("dealerReduceAmount", 0)
            coupon_info['xianshimiaosha_info'] = json.dumps({
                "限时秒杀开始时间": seckill.get("startTime"),
                "限时秒杀结束时间": seckill.get("endTime"),
                "限时秒杀优惠额度": format_price(seckill_quota),
            }, ensure_ascii=False)

    return coupon_info


def _get_carsource_info(clue_id: str, config: Dict) -> Dict:
    """获取车源基本信息"""
    url = f"{config['urls']['carsource']}/{API_QUERY_CAR_SOURCE}"
    app_key, app_secret = config['keys']['carsource']
    params = _create_signed_params({"clue_ids": clue_id, "fields": ",".join(CAR_BASIC_INFO_COLS)}, app_key, app_secret)
    data = _make_api_request('GET', url, params=params)

    carsource_info = {}
    if data and str(clue_id) in data:
        info_data = data[str(clue_id)]

        # 计算车龄
        if info_data.get("license_full_date") and info_data["license_full_date"] != "0":
            try:
                date_obj = datetime.strptime(str(info_data["license_full_date"]), "%Y%m%d")
                total_months = (datetime.now().year - date_obj.year) * 12 + (datetime.now().month - date_obj.month) - 1
                years, months = divmod(total_months, 12)
                if years == 0 and months == 0:
                    carsource_info["车龄"] = "不到1个月"
                elif years == 0:
                    carsource_info["车龄"] = f"{months}个月"
                elif months == 0:
                    carsource_info["车龄"] = f"{years}年"
                else:
                    carsource_info["车龄"] = f"{years}年{months}个月"
            except ValueError:
                carsource_info["车龄"] = "未知"
        elif info_data.get("car_year") == str(datetime.now().year + 1): # Heuristic for new cars
             carsource_info["车龄"] = "新车"


        # 字段映射
        for key, value in info_data.items():
            if key in CAR_BASIC_INFO_MAP:
                mapped_key = CAR_BASIC_INFO_MAP[key]
                if key == "road_haul" and value:
                    carsource_info[mapped_key] = f"{value}公里"
                elif key == "car_owner_type" and str(value) in ("1", "2"):
                    carsource_info[mapped_key] = "公户" if str(value) == "1" else "私户"
                elif key == "transfer_num" and value is not None:
                    carsource_info[mapped_key] = "没转过户" if str(value) == "0" else f"{value}次"
                else:
                    carsource_info[mapped_key] = str(value)

    return carsource_info


def get_car_price_comparator(clue_id: str, car_sell_price: int, car_age: str, car_mileage: str, config: Dict) -> Dict:
    """获取车辆价格解释信息"""
    url = f"{config['urls']['cost_performance']}/{API_COST_PERFORMANCE}"
    data = {"clue_id": clue_id, "queried_date": datetime.now().strftime("%Y-%m-%d")}
    response_data = _make_api_request('POST', url, json_data=data)

    comparator = {}
    if not response_data:
        return comparator

    for key, value in response_data.items():
        if key in COST_PERFORMANCE_KEY_MAP:
            comparator[COST_PERFORMANCE_KEY_MAP[key]] = value

    # 市场价格分析
    market_lower = response_data.get('market_price_lower')
    market_upper = response_data.get('market_price_upper')
    if market_lower is not None and market_upper is not None:
        analysis = {"市场价格区间": f"{market_lower}元 - {market_upper}元"}
        if car_sell_price < market_lower:
            analysis['市场价格分析'] = f"售价低于市场价格区间下限，车龄{car_age}，里程{car_mileage}"
        elif car_sell_price > market_upper:
            analysis['市场价格分析'] = f"该车价格高于市场价格区间上限，车龄{car_age}，里程{car_mileage}"
        else:
            analysis['市场价格分析'] = f"该车价格处于合理的市场价格区间内({market_lower}元 - {market_upper}元)，车龄{car_age}，里程{car_mileage}"
        comparator['市场价格分析'] = analysis

    # 历史成交分析
    deal_min = response_data.get('deal_price_min')
    deal_max = response_data.get('deal_price_max')
    deal_mean = response_data.get('deal_price_mean')
    if deal_min is not None and deal_max is not None and deal_mean is not None:
        details = response_data.get('deal_car_details', [])
        min_reason = next((item.get("delta_price_reason_desc", "") for item in details if item.get("deal_price") == deal_min), "")
        max_reason = next((item.get("delta_price_reason_desc", "") for item in details if item.get("deal_price") == deal_max), "")

        if car_sell_price < deal_min:
            comparator['历史成交分析'] = f"售价低于历史成交车价格区间下限，{min_reason}，车龄{car_age}，里程{car_mileage}"
        elif car_sell_price > deal_max:
            comparator['历史成交分析'] = f"该车价格高于历史成交车价格区间上限，{max_reason}，车龄{car_age}，里程{car_mileage}"
        elif car_sell_price < deal_mean:
            comparator['历史成交分析'] = f"该车价格比历史成交车价格平均值低{deal_mean - car_sell_price}元，车龄{car_age}，里程{car_mileage}"
        else:
            comparator['历史成交分析'] = f"该车价格比历史成交车价格平均值高{car_sell_price - deal_mean}元，车龄{car_age}，里程{car_mileage}"

    return comparator


def get_new_car_landing_price(clue_id: str, config: Dict) -> Dict:
    """获取新车落地价"""
    url = f"{config['urls']['kb']}/{API_NEW_CAR_LANDING_FEE}"
    params = {"clueId": clue_id, "cityId": 12}  # cityId 12 for Beijing
    data = _make_api_request('GET', url, params=params)

    new_car_price = {}
    if data:
        new_car_price["新车落地价"] = format_price_yuan(data.get("total_cost"))
        new_car_price["新车裸车价"] = format_price_yuan(data.get("pure_new_car_price"))
        if data.get("necessary_cost"):
            new_car_price["新车必要成本(购置税、交强险、上牌等)"] = format_price_yuan(data["necessary_cost"].get("total_necessary_cost"))
        new_car_price["新车商业保险费"] = format_price_yuan(data.get("commercial_insurance_cost"))

    return new_car_price

@log_http_timing
def get_car_sale_status_by_clue_id(clue_id: str, env: str = 'online') -> str:
    """获取车源销售状态"""
    config = get_env_config("pre" if env in ["preview", "pre"] else "apps")
    return _query_product_status(clue_id, config)


# ===================== 主函数 =====================
@log_http_timing
def get_price_info_by_clue_id_gz_user_id_ext(gz_user_id: str, clue_id: str, ext: str, env: str = 'online') -> Dict[str, str]:
    """
    车价服务综合主函数
    """
    if not validate_clue_id(clue_id):
        #print(f"无效的clue_id: {clue_id}")
        return {"car_price_info": "", "price_analysis_info": "", "new_car_price_info": ""}

    config = get_env_config("pre" if env in ["preview", "pre"] else "apps")
    ext_data = parse_ext(ext)
    plate_city_id = ext_data.get("plate_city_id", 13)
    selected_city_id = ext_data.get("selected_city_id", 13)
    guid = ext_data.get("guid", "123")

    # 1. 获取车源基本信息和价格
    carsource_status = _query_product_status(clue_id, config)
    carsource_info = _get_carsource_info(clue_id, config)

    result = {"车源状态": carsource_status, **carsource_info}

    if carsource_status == "售出":
        result["车辆售价"] = "车辆已售出，可以看看其他车辆"
    elif carsource_status == "待上架":
        result["车辆售价"] = "车辆未上架，暂无法查询价格，可以看看其他车辆"
    else:
        if plate_city_id:
            result["上牌城市信息"] = _get_plate_city_info(clue_id, plate_city_id, config)

        if plate_city_id and selected_city_id and guid:
            price_cost = _get_car_price_cost(gz_user_id, clue_id, plate_city_id, selected_city_id, guid, config)
            result.update({
                "车辆到手价": price_cost.get("car_otd_price"),
                "市场售价": price_cost.get("market_sell_price"),
                "过户押金": price_cost.get("transfer_deposit"),
                "过户上牌费": price_cost.get("transfer_fee"),
                "物流费用": price_cost.get("logistics_fee"),
            })

        if selected_city_id:
            coupon_price_info = _get_car_price_coupon(gz_user_id, clue_id, selected_city_id, config)
            result.update({
                "车辆售价": coupon_price_info.get("car_coupon_price"),
                "车辆原始售价": coupon_price_info.get("car_orginal_price"),
                "已优惠金额": coupon_price_info.get("coupon_price"),
                "已补贴活动信息": coupon_price_info.get("butie_info"),
                "已优惠活动信息": coupon_price_info.get("youhui_info"),
                "已限时秒杀活动信息": coupon_price_info.get("xianshimiaosha_info"),
            })

    car_price_info_json = json.dumps(result, ensure_ascii=False)

    # 2. 获取性价比信息
    price_analysis_info_json = ""
    if carsource_status in ["交易中", "已上架"] and result.get("车辆售价"):
        try:
            car_sell_price_str = result["车辆售价"].replace("元", "")
            if car_sell_price_str.isdigit():
                car_sell_price = int(car_sell_price_str)
                price_analysis_dict = get_car_price_comparator(clue_id, car_sell_price, result.get("车龄", ""),
                                                               result.get("行驶里程", ""), config)
                price_analysis_info_json = json.dumps(price_analysis_dict, ensure_ascii=False)
        except (ValueError, TypeError, AttributeError):
            pass

    # 3. 获取新车落地价
    new_car_price_info_json = json.dumps(get_new_car_landing_price(clue_id, config), ensure_ascii=False)

    return {
        "car_price_info": car_price_info_json,
        "price_analysis_info": price_analysis_info_json,
        "new_car_price_info": new_car_price_info_json
    }


# if __name__ == "__main__":
#     inputs = {
#    "clue_id": "163293875",
#    "gz_user_id": "174132952062000095",
#    "env": "online",
#    "ext": "{\"llm_agent\": 101, \"business_line\": \"\", \"source_from\": null, \"clue_id\": 163293875, \"order_id\": null, \"plate_city\": null, \"plate_city_id\": 55, \"selected_city\": null, \"selected_city_id\": 12, \"location_city\": null, \"location_city_id\": 12, \"credit_valid_status\": 3, \"credit_limit\": 50000000.0, \"finance_user_id\": 1229639920844360737, \"human_service_hours\": 0, \"experiment_status\": {\"car_condition_13202\": \"B\", \"finance_agent_13027\": \"A\", \"finance_agent_12852\": \"B\", \"finance_agent_12940\": \"A\", \"cbsale_c2_online_chat_12989\": \"B\", \"car_condition_12935\": \"B\", \"price_agent_finance_coupon_12979\": \"B\", \"agent_comparison_12699\": \"B\", \"finance_coupon_remind_13111\": \"A\", \"finance_form_filling_12837\": \"B\", \"agent_select_car_12258\": \"A\", \"agent_demands_convergence_12960\": \"A\", \"clue_session_13023\": \"A\", \"finance_12669\": \"B\", \"follow_up_question_13044\": \"B\", \"finance_credit_12936\": \"B\"}, \"finance_form_filling_status\": null, \"finance_contract_sign_status\": null, \"guid\": \"IDFA0b8284784e475b24444d5d369abb567a\", \"pf\": null, \"platform\": \"1\", \"did\": \"IDFA0b8284784e475b24444d5d369abb567a\", \"client\": \"ios\", \"lng\": 0.0, \"lat\": null, \"version_id\": \"12.0.1\", \"ca_s\": \"app_tg\", \"ca_n\": \"chaofantianxiacpa001\", \"entry\": 6, \"scene\": 432, \"scene_detail\": \"【二手车-售车】- [详情页]-[右上角入口]-AI引导\", \"scene_id\": \"d71d0e74fe3b4953911a1ccd5b147280\", \"session_id\": \"e3385cd3-bd98-4d05-b388-a0bd7ae4fb0a\", \"request_time\": \"2026-03-08 22:40:31.374\", \"query_channel\": \"USER_INPUT\", \"query_source_message_id\": null, \"track_key\": null}"
#  }

#     result = get_price_info_by_clue_id_gz_user_id_ext(**inputs)
#     print(result)
#     print("Finished!")

