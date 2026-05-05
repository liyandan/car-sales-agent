#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通过车源ID和ext获取车源所在城市 - 内部工具
"""
import argparse
import json
import sys
from pathlib import Path

_SCRIPTS_ROOT = Path(__file__).resolve().parent.parent
if str(_SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_ROOT))

from car_condition_tools import get_car_source_city_by_clue_id_


def main():
    parser = argparse.ArgumentParser(description="通过车源ID(clue_id)和附加信息(ext)获取车源所在城市")
    parser.add_argument("--clue_id", required=True, help="车源ID")
    parser.add_argument("--plate_city_id", required=False, default="", help="上牌城市ID")
    parser.add_argument("--selected_city_id", required=False, default="", help="选择城市ID")
    parser.add_argument("--location_city_id", required=False, default="", help="定位城市ID")
    parser.add_argument("--env", default="online", help="环境: online, test, preview, pre")
    args = parser.parse_args()

    result = get_car_source_city_by_clue_id_(args.clue_id, args.plate_city_id, args.selected_city_id, args.location_city_id, args.env)
    print(json.dumps(result, ensure_ascii=False, indent=2))



if __name__ == "__main__":
    main()
