#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Author       : liyandan
# @Date         : 2026-03-06
# @Description  : 车况接口工具类

import re
import json
import time
import random
import hmac
import hashlib
import urllib.parse
import base64
import binascii
from datetime import datetime
from functools import wraps
from typing import Callable, Any

from settings import get_settings

def log_http_timing(func: Callable) -> Callable:
    """
    HTTP请求耗时日志装饰器
    根据配置参数决定是否打印接口耗时
    
    使用方式:
        @log_http_timing
        def your_http_function():
            response = requests.get(...)
            return response
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        settings = get_settings()
        
        # 如果未启用HTTP耗时日志，直接执行原函数
        if not settings.enable_http_timing_log:
            return func(*args, **kwargs)
        
        # 记录开始时间
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            elapsed_time = (time.time() - start_time) * 1000  # 转换为毫秒
            print(f"[HTTP耗时] {func.__name__} 耗时: {elapsed_time:.2f}ms")
            return result
        except Exception as e:
            elapsed_time = (time.time() - start_time) * 1000
            print(f"[HTTP耗时] {func.__name__} 耗时: {elapsed_time:.2f}ms (异常: {str(e)})")
            raise
    
    return wrapper


def parse_input_data_with_json_eval(input_data, default_value=None):
    """
    尝试通过多种方式解析输入数据

    Args:
        input_data: 待解析的输入数据
        default_value: 解析失败时返回的默认值

    Returns:
        解析后的数据，或原数据，或默认值
    """
    # 如果输入已经不是字符串，直接返回
    if not isinstance(input_data, str):
        return input_data

    # 尝试使用 json.loads 解析
    try:
        return json.loads(input_data)
    except (json.JSONDecodeError, TypeError):
        print(f"input_data不是json字符串: {input_data}")

    # 尝试使用 eval 解析（注意：eval有安全风险，仅在可信环境使用）
    try:
        input_data_cleaned = input_data.replace('\n', r'\n')
        return eval(input_data_cleaned)
    except (SyntaxError, NameError, TypeError, ValueError):
        print("input_data不是eval字符串")

    # 如果都解析失败，根据情况返回原数据或默认值
    if default_value is not None:
        print(f"input_data返回默认值：{default_value}" )
        return default_value
    else:
        print("input_data返回初始值")
        return input_data


def create_params(car_params, app_key, secret):
    """创建包含签名的参数Map（通用版本）"""
    # 当前时间戳（秒）
    expires = str(int(time.time()))

    # 添加必要参数
    car_params["appkey"] = app_key
    car_params["expires"] = expires

    def random_string(length):
        """生成指定长度的随机字符串"""
        AB = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        return ''.join(random.choice(AB) for _ in range(length))

    car_params["nonce"] = random_string(4)

    # 计md5
    def md5(message):
        """计算字符串的MD5值"""
        md5_hash = hashlib.md5()
        md5_hash.update(message.encode('utf-8'))
        return binascii.hexlify(md5_hash.digest()).decode('utf-8')

    def sign_by_hmac_sha256(message, secret):
        """使用HMAC-SHA256算法对消息进行签名"""
        key = secret.encode('utf-8')
        message = message.encode('utf-8')
        signature = hmac.new(key, message, hashlib.sha256)
        return base64.b64encode(signature.digest()).decode('utf-8')

    # 计算签名
    def sign(param_map, secret):
        """生成签名"""
        try:
            # 按键名排序
            keys = sorted(param_map.keys())

            # 构建要签名的字符串
            params = []
            for key in keys:
                value = str(param_map[key])
                params.append(f"{key}={urllib.parse.quote(value)}")

            message = "&".join(params)

            # 签名并截取子串
            signature = sign_by_hmac_sha256(message, secret)
            signature_md5 = md5(signature)
            return signature_md5[5:15]
        except Exception as e:
            print(f"Sign exception: param_map={param_map}, error={str(e)}")
            return None

    signature = sign(car_params, secret)
    car_params["signature"] = signature

    return car_params


def is_integer_regex(s) -> bool:
    """检查字符串是否为正整数"""
    s = str(s)
    return bool(re.fullmatch(r'^[1-9]\d*$', s))


# 计算两个datetime的时间差
def calc_interval_months(date1_str, date2_str, date_format="%Y-%m-%d"):
    date1 = datetime.strptime(date1_str, date_format)
    date2 = datetime.strptime(date2_str, date_format)
    if date1 > date2:
        date1, date2 = date2, date1
    total_months = (date2.year - date1.year) * 12 + (date2.month - date1.month)
    return total_months


# 车源基本信息解析
def car_basic_info_parser(car_basic_info_multi_clue_id: dict, clue_id: int):
    car_basic_info = {}
    car_data = car_basic_info_multi_clue_id.get(str(clue_id), {})
    for key in car_data:
        # 根据上牌日期更新车龄和上牌日期
        if key == "license_full_date":
            if car_data["license_full_date"]:
                today_date = datetime.strftime(datetime.now(), "%Y-%m-%d")
                # 将整数转换为字符串并解析为日期对象
                date_obj = datetime.strptime(str(car_data["license_full_date"]), "%Y%m%d")
                # 将日期对象格式化为字符串
                plate_date = date_obj.strftime("%Y-%m-%d")
                total_months = calc_interval_months(plate_date, today_date)
                car_basic_info.update({
                    "total_months": total_months,
                    "license_full_date": plate_date
                })
            else:
                car_basic_info.update({
                    "total_months": "",
                    "license_full_date": ""
                })

        # 处理行驶里程
        if key == "road_haul":
            if car_data.get("road_haul", "") != "":
                car_basic_info.update({"road_haul": car_data.get("road_haul", "")})
            else:
                car_basic_info.update({"road_haul": ""})

    return car_basic_info