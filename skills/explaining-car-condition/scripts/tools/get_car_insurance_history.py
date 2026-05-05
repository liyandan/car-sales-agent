#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通过车源ID获取出险记录内容 - 内部工具
"""
import argparse
import json
import sys
from pathlib import Path

_SCRIPTS_ROOT = Path(__file__).resolve().parent.parent
if str(_SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_ROOT))

from car_condition_tools import get_car_insurance_history_by_clue_id


def main():
    parser = argparse.ArgumentParser(description="通过车源ID(clue_id)获取车辆的出险记录内容")
    parser.add_argument("--clue_id", required=True, help="车源ID")
    parser.add_argument("--env", default="online", help="环境: online, test, preview, pre")
    args = parser.parse_args()

    result = get_car_insurance_history_by_clue_id(args.clue_id, args.env)
    if isinstance(result, dict):
        payload = result
    elif isinstance(result, list):
        payload = {"raw": result}
    else:
        payload = {"car_insurance_history_text": "" if result is None else str(result)}
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
