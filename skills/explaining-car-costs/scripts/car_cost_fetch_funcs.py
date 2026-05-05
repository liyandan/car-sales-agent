#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# author: liyandan
# date: 2026-03-23
# version: 1.0.0
# description: 内部 API 签名工具 - 鉴权算法 Python 实现

"""
内部 API 签名工具 - 鉴权算法 Python 实现

API 网关鉴权规则：
1. 参数完整性：appkey、nonce、signature、expires 必须有值不能为空
2. 参数有效性：
   - expires：未过期，默认 600s 有效期内
   - appkey：服务端校验存在性及 expire_at
   - signature：按签名算法生成，与请求中的值一致
"""

import hashlib
import hmac
import random
import string
import time
import urllib.parse
from base64 import b64encode
from typing import Any
import requests

def _md5(value: str) -> str:
    """计算 MD5，返回 32 位小写十六进制字符串"""
    return hashlib.md5(value.encode("utf-8")).hexdigest().lower()


def _sha256_hmac_encode(params: str, secret: str) -> str:
    """
    SHA256 HMAC 后 Base64 编码
    params: 待签名字符串（key1=value1&key2=value2）
    secret: appSecret
    """
    digest = hmac.new(
        secret.encode("utf-8"),
        params.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return b64encode(digest).decode("utf-8")


def _get_encode_string(params: dict[str, Any]) -> str:
    """
    将参数字典按 key 字母升序排序，拼接为 key1=urlencode(value1)&key2=urlencode(value2)
    空值参与计算，转为空字符串。编码方式与 Java URLEncoder.encode 一致
    """
    if not params:
        return ""
    sorted_keys = sorted(params.keys())
    parts = []
    for key in sorted_keys:
        val = params.get(key)
        if val is None:
            val = ""
        else:
            val = str(val)
        # Java URLEncoder.encode 空格为 +，与 quote_plus 一致
        encoded_val = urllib.parse.quote_plus(val)
        parts.append(f"{key}={encoded_val}")
    return "&".join(parts)


def _generate_signature(params_str: str, app_secret: str) -> str:
    """
    对拼接待签名字符串计算签名
    1. HMAC-SHA256 + Base64 得到 str2
    2. MD5(str2) 取第 5-15 位（共 10 位）作为 signature
    """
    str2 = _sha256_hmac_encode(params_str, app_secret)
    md5_result = _md5(str2)
    return md5_result[5:15]


def generate_random_str(length: int = 6) -> str:
    """生成指定长度的随机小写字母字符串"""
    return "".join(random.choices(string.ascii_lowercase, k=length))


# API 网关鉴权要求的参数名（小写）
REQUIRED_PARAMS = ("appkey", "nonce", "signature", "expires")

# 默认 expires 有效期（秒），与网关 600s 一致
DEFAULT_EXPIRES_TTL = 600

def get_current_second(ttl: int = DEFAULT_EXPIRES_TTL) -> str:
    """
    获取 expires 值：当前时间秒数 + ttl。
    网关校验：请求时当前时间须小于 expires，默认 600s 有效。
    """
    return str(int(time.time()) + ttl)


def validate_params_completeness(params: dict[str, Any]) -> tuple[bool, list[str]]:
    """
    校验参数完整性（网关规则 1）。
    appkey、nonce、signature、expires 必须有值不能为空。

    Returns:
        (是否通过, 缺失或为空的参数列表)
    """
    missing = []
    for key in REQUIRED_PARAMS:
        val = params.get(key)
        if val is None or str(val).strip() == "":
            missing.append(key)
    return (len(missing) == 0, missing)


def add_signature(
    app_key: str,
    app_secret: str,
    business_params: dict[str, Any] | None = None,
    expires_ttl: int = DEFAULT_EXPIRES_TTL,
) -> dict[str, Any]:
    """
    生成签名并将签名加入参数表，满足网关鉴权规则。

    Args:
        app_key: 应用 Key（必填，网关会校验存在性）
        app_secret: 应用密钥（用于生成 signature）
        business_params: 业务参数（仅 URL 查询参数参与签名，POST Body 不参与）
        expires_ttl: expires 有效期秒数，默认 600，与网关一致

    Returns:
        包含 appkey、expires、nonce、signature 及业务参数的完整参数字典
        保证四项鉴权参数均有值（满足网关参数完整性要求）
    """
    if not app_key or not str(app_key).strip():
        raise ValueError("appkey 不能为空")
    if not app_secret or not str(app_secret).strip():
        raise ValueError("app_secret 不能为空")

    params = dict(business_params) if business_params else {}
    params["appkey"] = str(app_key).strip()
    params["expires"] = get_current_second(ttl=expires_ttl)
    params["nonce"] = generate_random_str(6)

    params_str = _get_encode_string(params)
    signature = _generate_signature(params_str, app_secret)
    params["signature"] = signature

    # 最终校验：四项鉴权参数完整性
    ok, missing = validate_params_completeness(params)
    if not ok:
        raise ValueError(f"鉴权参数不完整: {missing}")

    return params


def build_signed_url(
    base_url: str,
    app_key: str,
    app_secret: str,
    params: dict[str, Any] | None = None,
    expires_ttl: int = DEFAULT_EXPIRES_TTL,
) -> str:
    """
    构建带签名的 GET 请求 URL。

    Args:
        base_url: 接口基础 URL（不含查询参数）
        app_key: 应用 Key
        app_secret: 应用密钥
        params: URL 查询参数（参与签名）

    Returns:
        完整 URL，包含签名后的查询字符串
    """
    signed = add_signature(app_key, app_secret, params, expires_ttl=expires_ttl)
    qs = urllib.parse.urlencode(signed, safe="", quote_via=urllib.parse.quote_plus)
    sep = "&" if "?" in base_url else "?"
    return f"{base_url}{sep}{qs}"


def parse_car_api_response(response_data: dict) -> dict[str, int] | None:
    """
    解析车辆 API 返回的 JSON，提取并计算年均费用字段。

    计算方式（按用户要求）：
    - 年均保险费 = maintenance_1year_amount，不保留小数，单位：元
    - 年均保养费 = insurance_compulsory_amount + insurance_commercial_amount，不保留小数，单位：元
    - 年均油费 = fuel_cost * 100 * 9，不保留小数，单位：元

    Args:
        response_data: API 返回的完整 JSON，如 {'success': True, 'data': {...}}

    Returns:
        包含 "年均油费"、"年均保险费"、"年均保养费" 的字典，单位：元；解析失败返回 None
    """
    try:
        data = response_data.get("data") or {}
        indicators = data.get("car_content_recommended_indicators") or {}
        items = indicators.get("data") or []
        if not items:
            return {
                "年均保养费": "",
                "年均保险费": "",
                "年均油费": "",
            }
        item = items[0]

        fuel_cost_ministry = float(item.get("fuel_cost_ministry") or 0)
        maintenance_1year = float(item.get("maintenance_1year_amount") or 0)
        insurance_compulsory = float(item.get("insurance_compulsory_amount") or 0)
        insurance_commercial = float(item.get("insurance_commercial_amount") or 0)

        return {
            "年均保养费": f"{int(maintenance_1year)}元",
            "年均保险费": f"{int(insurance_compulsory + insurance_commercial)}元",
            "年均油费": f"{int(fuel_cost_ministry * 100 * 9)}元",
        }
    except (TypeError, ValueError, KeyError):
        return  {
                "年均保养费": "",
                "年均保险费": "",
                "年均油费": "",
            }


def get_signed_params_for_request(
    app_key: str,
    app_secret: str,
    url_params: dict[str, Any] | None = None,
    expires_ttl: int = DEFAULT_EXPIRES_TTL,
) -> dict[str, Any]:
    """
    获取用于请求的完整签名参数（用于 GET 拼接或 POST 表单）。
    生成参数满足网关鉴权规则（完整性、expires 600s、signature 正确）。

    Args:
        app_key: 应用 Key
        app_secret: 应用密钥
        url_params: 附在 URL 上的业务参数（参与签名）
        expires_ttl: expires 有效期秒数，默认 600

    Returns:
        包含 appkey、expires、nonce、signature 及业务参数的字典
    """
    return add_signature(app_key, app_secret, url_params, expires_ttl=expires_ttl)


def get_car_cost_data_by_tag_id(
    url: str,
    tag_id: str,
    app_key: str,
    app_secret: str,    
    timeout: int = 3,
) -> dict[str, Any]:
    """
    根据 tag_id 获取车辆成本数据。失败时自动重试 1 次，仍失败则返回默认空值。

    Args:
        tag_id: 车辆 tag 标识
        app_key: 应用 Key
        app_secret: 应用密钥
        base_url: 接口基础 URL
        timeout: 请求超时秒数

    Returns:
        包含 "年均油费"、"年均保险费"、"年均保养费" 的字典，访问失败时返回空字符串
    """
    sign_params = add_signature(app_key, app_secret)
    body = {
        "page_size": 20,
        "page_num": 1,
        "car_content_recommended_indicators": {
            "@column": "tag_name,maintenance_1year_amount,insurance_compulsory_amount,insurance_commercial_amount,fuel_cost,fuel_cost_ministry",
            "tag_id": f"{tag_id}",
        },
    }
    
    # 访问失败时的默认返回值
    CAR_COST_DEFAULT = {
                "用车成本":{
                            "年均保养费": "",
                            "年均保险费": "",
                            "年均油费": ""
                         }
    }
    last_error: BaseException | None = None
    for attempt in range(2):  # 首次 + 重试 1 次，共 2 次
        try:
            resp = requests.post(url, params=sign_params, json=body, timeout=timeout)
            resp.raise_for_status()  # 4xx/5xx 抛出 HTTPError
            data = resp.json()
            if not data.get("success"):
                last_error = ValueError(f"API 返回失败: {data.get('message', 'unknown')}")
                continue
            result = parse_car_api_response(data)
            if result:
                return {"用车成本":result}
            last_error = ValueError("解析结果为空")
        except requests.RequestException as e:
            last_error = e
        except (ValueError, TypeError, KeyError) as e:
            last_error = e

    return dict(CAR_COST_DEFAULT)


# if __name__ == "__main__":
#     # 使用示例
#     APP_KEY     =  "ai-agent__carexplaining"
#     APP_SECRET  =  "eec5223a75"

#     BASE_URL    =  "https://open-data-api-preview.guazi-apps.com"#"https://open-data-api.guazi-apps.com"

    # 1. 仅基础鉴权（无业务参数）
    # params      =  add_signature(APP_KEY, APP_SECRET)
    # print("签名参数:", params)

    # # 2. 带 URL 业务参数
    # params_with_biz = add_signature(
    #     APP_KEY,
    #     APP_SECRET,
    #     {"name": "abc", "page": 1},
    # )
    # print("带业务参数:", params_with_biz)

    # # 3. 构建完整 GET URL
    # url = build_signed_url(
    #     "https://api.example.com/data",
    #     APP_KEY,
    #     APP_SECRET,
    #     {"id": "123"},
    # )
    # print("签名 URL:", url)


# ============ 使用 requests 发起接口请求示例 ============
#
# import requests
# from sign_utils import add_signature, build_signed_url
#
# APP_KEY = "你的appKey"
# APP_SECRET = "你的appSecret"
# BASE_URL = "https://your-api.example.com"
#
# # GET 请求
# url_params = {"id": "123", "type": "query"}  # URL 上的业务参数（参与签名）
# full_url = build_signed_url(f"{BASE_URL}/api/data", APP_KEY, APP_SECRET, url_params)
# resp = requests.get(full_url)
#
# # GET 请求（手动拼接）
# params = add_signature(APP_KEY, APP_SECRET, url_params)
# resp = requests.get(f"{BASE_URL}/api/data", params=params)
#
# POST 请求（业务参数在 Body，仅 appkey/expires/nonce/signature 参与签名）
# 签名时只含鉴权参数，不含 Body


# result_envelop = get_car_cost_data_by_tag_id(f"{BASE_URL}/v2/api/car",2817,APP_KEY,APP_SECRET)
# print(result_envelop)
# print("====================== 请求结束 ======================")

