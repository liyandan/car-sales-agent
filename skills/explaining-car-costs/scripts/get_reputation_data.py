import json
import requests
import time
import random
import hmac
import hashlib
import urllib.parse
import base64
import binascii
import os

# --- Constants ---
CAR_BASIC_INFO_COLS = [
    "has_shelf", "create_time", "title", "minor_category_name", "tag_name", "car_id",
    "car_year", "license_full_date", "road_haul", "transfer_num", "fuel_type",
    "car_keys", "evaluate_score", "evaluate_level", "vin_encrypt",
    "attr_carsource_insurance_record_id", "emission_standard",
    "attr_carsource_battery_owner_type", "attr_carsource_battery_inspection_health",
    "attr_carsource_battery_inspection_report", "attr_carsource_battery_inspection_commit_time",
    "audit_full_date", "strong_insurance_full_date", "business_insurance_full_date", "car_color",
]

# API endpoints and credentials
API_QUERY_CARSOURCE = 'cars-info/internal/carSource/queryCarSource'
URL_CARSOURCE = "http://carsource-api.guazi-apps.com"
CARSOURCE_APP_KEY = "ai_agent"
CARSOURCE_APP_SECRET = "secAiAgent0228@25OL"

ES_API_ENDPOINT = "http://10.16.10.74:9200/cartypes_koubei_chexing/_search"
ES_HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Basic ZWxhc3RpYzplczhwd2Q="
}

# --- Reusable Sessions ---
# Use Session objects to leverage connection pooling for performance
session_carsource = requests.Session()
session_es = requests.Session()


# --- Helper Functions (moved to global scope) ---

def _random_string(length):
    """Generates a random string of a given length."""
    AB = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    return ''.join(random.choice(AB) for _ in range(length))


def _md5(message):
    """Computes the MD5 hash of a string."""
    md5_hash = hashlib.md5()
    md5_hash.update(message.encode('utf-8'))
    return binascii.hexlify(md5_hash.digest()).decode('utf-8')


def _sign_by_hmac_sha256(message, secret):
    """Signs a message using HMAC-SHA256."""
    key = secret.encode('utf-8')
    message_encoded = message.encode('utf-8')
    signature = hmac.new(key, message_encoded, hashlib.sha256)
    return base64.b64encode(signature.digest()).decode('utf-8')


def _sign(param_map, secret):
    """Generates a signature for the given parameters."""
    try:
        keys = sorted(param_map.keys())
        params = [f"{key}={urllib.parse.quote(str(param_map[key]))}" for key in keys]
        message = "&".join(params)
        signature = _sign_by_hmac_sha256(message, secret)
        signature_md5 = _md5(signature)
        return signature_md5[5:15]
    except Exception as e:
        print(f"Sign exception: param_map={param_map}, error={str(e)}")
        return None


def create_params(car_params, app_key, secret):
    """为 API 请求创建签名的参数映射。"""
    car_params["appkey"] = app_key
    car_params["expires"] = str(int(time.time()))
    car_params["nonce"] = _random_string(4)
    car_params["signature"] = _sign(car_params, secret)
    return car_params


def get_car_basic_info_by_clue_id(clue_id: str, fields: list) -> dict:
    """使用 clue ID 获取车辆的基本信息。"""
    url_query_car_source = os.path.join(URL_CARSOURCE, API_QUERY_CARSOURCE)
    params = {"clue_ids": clue_id, "fields": ",".join(fields)}
    all_params = create_params(params, CARSOURCE_APP_KEY, CARSOURCE_APP_SECRET)
    try:
        response = session_carsource.get(url_query_car_source, params=all_params, timeout=5)
        response.raise_for_status()  # Raise an exception for bad status codes
        result = response.json()
        if result.get("code") != 0:
            print(f"Car source API error: {result.get('code')} - {result.get('msg')}")
            return {}
        return result.get("data") or {}
    except requests.exceptions.RequestException as e:
        print(f"Car source API request failed: {e}")
        return {}


def get_car_id(clue_id: str) -> dict:
    """检索给定 clue_id 对应的 car_id。"""
    if not clue_id or clue_id in ["-1", "0"]:
        return {"car_id": ""}

    car_basic_info = get_car_basic_info_by_clue_id(clue_id, CAR_BASIC_INFO_COLS)
    
    # car_basic_info is a dict with clue_id as key, e.g. {'295655780': {'car_id': 123}}
    car_info = car_basic_info.get(clue_id, {})
    car_type_id = car_info.get("car_id")
    
    if car_type_id and car_type_id != -1:
        return {"car_id": str(car_type_id)}
    
    return {"car_id": ""}


def retrieve_koubei_es(car_id: str):
    """Retrieves koubei data from Elasticsearch for a given car_id."""
    json_data = {
        "query": {"term": {"car_id": car_id}},
        "track_total_hits": True
    }
    try:
        response = session_es.post(
            ES_API_ENDPOINT,
            headers=ES_HEADERS,
            json=json_data, # Use json parameter to automatically handle serialization and headers
            timeout=5
        )
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        print(f"ES retrieval failed: {e}")
        return None

def get_reputation_data(koubei_item_name: str, clue_id: str, koubei_format: str) -> dict:
    """
    根据 clue_id 检索口碑知识的主要函数。
    """
    car_id_result = get_car_id(clue_id)
    car_id = car_id_result.get("car_id", "")
    
    base_response = {
        "koubei_knowledge": "[]",
        "retrieve_type": "车型口碑知识库检索",
        "few_shot": "[]",
        "car_id": car_id
    }

    if not koubei_item_name or not car_id:
        base_response["retrieve_type"] = "无需汽车知识库检索"
        return base_response

    result = retrieve_koubei_es(car_id)
    if result is None:
        return base_response
    
    try:
        hits = result.json().get("hits", {}).get("hits", [])
        if not hits:
            return base_response

        source = hits[0].get("_source", {})
        value = ""
        if koubei_format == "JSON":
            value = source
        else:
            value = source.get(koubei_item_name, "")
        
        if value:
            value_list = [value]
            base_response["koubei_knowledge"] = json.dumps(value_list, ensure_ascii=False)
        
        return base_response

    except (json.JSONDecodeError, KeyError) as e:
        print(f"处理 ES 响应时出错： {e}")
        return base_response
