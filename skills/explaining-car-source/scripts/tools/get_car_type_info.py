#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通过车源ID获取车型配置信息 - 内部工具
"""
import argparse
import json
import sys
from pathlib import Path

_SCRIPTS_ROOT = Path(__file__).resolve().parent.parent
if str(_SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_ROOT))

from car_condition_tools import get_car_type_info_by_clue_id


def main():
    parser = argparse.ArgumentParser( description="通过车源ID(clue_id)获取车辆的车型配置信息" )
    parser.add_argument( "--clue_id", required=True, help="车源ID" )
    parser.add_argument( "--env", default="online", help="环境: online, test, preview, pre" )
    args = parser.parse_args()

    result = get_car_type_info_by_clue_id(args.clue_id, args.env)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
