#!/usr/bin/env python
"""把 Prism 的 results.json 倒成扁平表 —— 不绑定某一种分析。

`prism_analyze.py` 只认单因素 ANOVA 的字段（`ordinaryAnovaModel` 等），
换个分析（剂量反应、t 检验、双因素）就得改代码。这个脚本走另一条路：
**递归遍历 results.json 的整棵树**，把所有"带数值叶子"的节点连同它的
路径一起倒出来。路径就是语义标签，所以不必预先知道分析类型。

## 用法

    # 1) 看这个 results.json 里有哪些字段路径（先摸结构）
    python prism_results.py --list results.json

    # 2) 全量倒成 TSV（path / key / value）
    python prism_results.py --results results.json --tsv numbers.tsv

    # 3) 按路径子串筛（例如只要置信区间）
    python prism_results.py --results results.json --grep "confiden" --json picked.json

    # 4) 直接找某个值（例如 EC50 / pValue）
    python prism_results.py --results results.json --find "ec50"

## 从 .prism 文件里拿 results.json

.prism 是个 zip。可以手工解：

    python -c "import zipfile;zipfile.ZipFile('x.prism').extractall('unz')"
    # results.json 通常在 unz/ 根或 data/ 下

`prism_analyze.py` 已经会自动做这一步。
"""
from __future__ import annotations

import argparse
import json
import sys

# 这些 key 一旦出现就当作"一个可报告的量"，不必再往下钻
VALUE_KEYS = (
    "value", "meansDifference", "pValue", "pValueAdjusted", "f", "fTest",
    "ss", "df", "ms", "ci", "ci95", "lower", "upper", "estimate", "stdError",
    "r2", "rSquared", "a", "b", "c", "d", "ec50", "ec90", "ED50", "ED90",
    "n", "mean", "median", "sd", "sem", "t", "r", "rho", "chiSquare",
)


def is_scalar(v) -> bool:
    return isinstance(v, (int, float, str, bool)) or v is None


def walk(node, path: str, out: list) -> None:
    """递归收集 (path, key, value)。

    把数值叶子按路径记下来：路径本身说明它是哪张表的哪个量，
    所以换分析类型也不用改代码 —— 这是与 prism_analyze.py 的分工差异。
    """
    if isinstance(node, dict):
        for k, v in node.items():
            child = f"{path}.{k}" if path else str(k)
            if is_scalar(v):
                # 叶子：记下来
                out.append({"path": child, "key": str(k), "value": v})
            else:
                walk(v, child, out)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            child = f"{path}[{i}]"
            if is_scalar(v):
                out.append({"path": child, "key": f"[{i}]", "value": v})
            else:
                walk(v, child, out)


def load_results(path: str):
    with open(path, encoding="utf-8", errors="replace") as fh:
        raw = fh.read()
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(
            f"! {path} 不是合法 JSON（{exc}）。\n"
            "  results.json 是 Prism 存盘时写进 .prism 包里的，"
            "确认你解的是 Save 之后的 .prism，而不是模板本身。"
        )


def main() -> int:
    ap = argparse.ArgumentParser(description="把 Prism results.json 倒成扁平表")
    ap.add_argument("--results", help="results.json 路径")
    ap.add_argument("--list", metavar="JSON", help="只列字段路径（给路径即可）")
    ap.add_argument("--tsv", help="写成 TSV（path / key / value）")
    ap.add_argument("--json", dest="json_out", help="写成 JSON 列表")
    ap.add_argument("--grep", help="只保留 path 含该子串的行")
    ap.add_argument("--find", help="只打印 path 含该子串的行")
    args = ap.parse_args()

    src = args.results or args.list
    if not src:
        ap.error("需要 --results 或 --list <file>")
    data = load_results(src)

    flat: list = []
    walk(data, "", flat)

    if args.list:
        print(f"{len(flat)} 个数值叶子。前 60 条路径：")
        for row in flat[:60]:
            print(f"  {row['path']} = {row['value']!r}")
        if len(flat) > 60:
            print(f"  … 还有 {len(flat) - 60} 条，用 --tsv 全量导出")
        return 0

    needle = args.find or args.grep
    if needle:
        needle_l = needle.lower()
        picked = [r for r in flat if needle_l in r["path"].lower()]
        if not picked:
            print(f"! 「{needle}」没有命中任何路径。用 --list 看看有哪些字段。",
                  file=sys.stderr)
            return 2
        if args.find:
            for r in picked:
                print(f"{r['path']} = {r['value']!r}")
            return 0
        flat = picked

    if args.tsv:
        with open(args.tsv, "w", encoding="utf-8", newline="") as fh:
            fh.write("path\tkey\tvalue\n")
            for r in flat:
                v = "" if r["value"] is None else str(r["value"]).replace("\t", " ")
                fh.write(f"{r['path']}\t{r['key']}\t{v}\n")
        print(f"已写 {args.tsv}（{len(flat)} 行）")

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as fh:
            json.dump({"source": src, "count": len(flat), "values": flat},
                      fh, ensure_ascii=False, indent=2)
        print(f"已写 {args.json_out}（{len(flat)} 行）")

    if not args.tsv and not args.json_out and not needle:
        print(f"{len(flat)} 个数值叶子；用 --tsv / --json 导出，或 --list 看路径。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
