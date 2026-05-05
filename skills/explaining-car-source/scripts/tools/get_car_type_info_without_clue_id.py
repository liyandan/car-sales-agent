#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取无车源ID的车型配置信息 - 内部工具
"""
import argparse
import json
import sys
from pathlib import Path

_SCRIPTS_ROOT = Path(__file__).resolve().parent.parent
if str(_SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_ROOT))

from car_condition_tools import get_car_general_knowledge_without_clue_id_


def main():
    parser = argparse.ArgumentParser(
        description="根据用户问题获取无车源ID场景下的车型配置信息"
    )
    parser.add_argument("--question", required=True, help="用户提问内容，如：卡罗拉1.2T 2022款轮毂型号")
    parser.add_argument("--env", default="online", help="环境: online, test, preview, pre")
    args = parser.parse_args()

    query_result = f"查询{args.question}的车型配置信息为 xxxxx"
    result = {"car_type_info":{
        "query_result":query_result
        }}#get_car_general_knowledge_without_clue_id_(args.question,  args.env)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

