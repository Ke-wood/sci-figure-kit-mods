#!/usr/bin/env python
"""用 SPSS 自带的 Python 直接跑语法、取回数据 —— 不走生产作业、不解析 OXML。

**必须用 SPSS 的 Python**：
  {root}/spss/Python3/python.exe

它自带 `spss / spssaux / spssdata / SpssClient` 四个模块，是 SPSS 官方的进程内接口：
  spss.Submit(语法)        直接执行（等价于在语法窗口里 Run）
  spssdata.Spssdata()      把当前数据集读成游标（全精度）
  SpssClient               访问输出文档里的表格对象

对比生产作业（stats.exe -production）：
  + 快（进程内，无启动开销）、能直接拿数据、能读输出对象
  - 依赖 SPSS 的 Python 3.8；语法错误会抛 Python 异常（比 exit 0 更诚实）

用法：
  {root}/spss/Python3/python.exe spss_py.py --sps analysis.sps --table out.csv --out results
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sps", required=True, help="SPSS 语法文件")
    ap.add_argument("--out", default="results", help="结果目录")
    ap.add_argument("--table", default=None, help="把当前数据集导出成这个 CSV 文件名")
    ap.add_argument("--oXML", default=None, help="把输出导出成 OXML（等价于 OMS 包裹）")
    args = ap.parse_args()

    try:
        import spss
        import spssdata
    except ImportError as exc:
        print(f"! 这个 Python 没有 spss 模块：{exc}\n"
              f"  请用 {root}/spss/Python3/python.exe 运行本脚本", file=sys.stderr)
        return 2

    os.makedirs(args.out, exist_ok=True)
    syntax = open(args.sps, encoding="utf-8").read()

    if args.oXML:
        spss.Submit(f"OMS /SELECT ALL /DESTINATION FORMAT=OXML OUTFILE='{args.oXML}'.")
    try:
        spss.Submit(syntax.splitlines())
    except Exception as exc:            # 语法错会在这里抛出来
        print(f"! SPSS 语法失败：{exc}", file=sys.stderr)
        return 1
    finally:
        if args.oXML:
            try:
                spss.Submit("OMSEND.")
            except Exception:
                pass

    summary = {"sps": os.path.abspath(args.sps), "oXML": args.oXML, "rows": 0}
    if args.table:
        path = os.path.join(args.out, args.table)
        with spssdata.Spssdata() as data, open(path, "w", encoding="utf-8", newline="") as fh:
            writer = csv.writer(fh)
            names = getattr(data, "varnames", None)
            names = names() if callable(names) else names
            writer.writerow(names)
            n = 0
            for case in data:
                writer.writerow(case)
                n += 1
        summary["table"] = os.path.abspath(path)
        summary["rows"] = n

    with open(os.path.join(args.out, "stats.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=2)
    print(json.dumps({"ok": True, **summary}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
