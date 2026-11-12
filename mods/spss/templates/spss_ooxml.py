#!/usr/bin/env python
"""把 SPSS 的 OXML 解析成 tidy 表 / 扁平 JSON —— 不用再手抠 pivotTable。

## 为什么需要它

`spss_run.py` 只负责"让 SPSS 跑起来并产出 OXML"，但 OXML 本身不是规整表格：
它是 `pivotTable` 套 `dimension` 套 `category` 的树，每格同时有 `number`
（全精度）与 `text`（显示值、已舍入）。每次都现写解析，就等于每次都要
重新踩下面这几个坑：

  1. 要数字必须读 `number`；读 `text` 会拿到 "13.8333" 这种被舍入的值。
  2. 缺失值是 `number=""` 且 `text` 可能是 "." 或空 —— 必须落成 None，不能当 0。
  3. 表名/维度名走 `<dimension>` 的 `name` 属性，不是行标签文字。
  4. 文件可能只写一半（SPSS 挂死/超时），**解析前必须校验 `</outputTree>`**；
     残缺文件当硬错误，不要返回一张看似正常的空表。

## 用法

    # 1) 先列一下这个 OXML 里有哪些表
    python spss_ooxml.py --list out.xml

    # 2) 把某张表导成 TSV（按表标题匹配，子串即可）
    python spss_ooxml.py --xml out.xml --table "Confidence Limits" --tsv lc50.tsv

    # 3) 全部表倒成扁平 JSON（每行一个观测：table / row / col / value）
    python spss_ooxml.py --xml out.xml --json all.json

    # 4) 只要某张表里的一个数（例如 LC50）
    python spss_ooxml.py --xml out.xml --table "Confidence Limits" --find LC50
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import xml.etree.ElementTree as ET

# OXML 的根名在不同 SPSS 版本里可能是 outputTree / output；两个都认。
ROOT_TAGS = ("outputTree", "output")


class OxmlIncomplete(Exception):
    """OXML 被截断（典型原因：SPSS 挂死或超时）。"""


def strip_ns(tag: str) -> str:
    """'ns:pivotTable' / '{uri}pivotTable' → 'pivotTable'。"""
    if "}" in tag:
        tag = tag.split("}", 1)[1]
    if ":" in tag:
        tag = tag.split(":", 1)[1]
    return tag


def local_name(elem) -> str:
    return strip_ns(elem.tag)


def load_ooxml(path: str):
    """读 OXML，先做完整性校验再解析。

    不先校验就会踩坑：截断的文件常常仍能被 ET 解析（只要断在合法位置），
    于是你拿到一张"哪里都不对但也不报错"的空表。
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(f"OXML 不存在：{path}")
    raw = open(path, "rb").read()
    if not raw.strip():
        raise OxmlIncomplete(f"OXML 是空文件：{path}")

    # 完整性：正常结束必须是 </outputTree> 或 </output>。
    tail = raw[-4096:].decode("utf-8", errors="replace").lower()
    if "</outputtree>" not in tail and "</output>" not in tail:
        raise OxmlIncomplete(
            f"OXML 不完整（找不到结束标签，文件 {len(raw)} 字节）：{path}\n"
            "常见原因：SPSS 超时被强杀、或 OMS ... OMSEND 没有成对。"
        )
    try:
        return ET.fromstring(raw)
    except ET.ParseError as exc:
        raise OxmlIncomplete(f"OXML 解析失败（{exc}），文件 {len(raw)} 字节：{path}") from exc


# ---------------------------------------------------------------- 表结构

def _dimensions(table):
    """pivotTable → (行维度名列表, 列维度名列表)。"""
    row_dims, col_dims = [], []
    for dim in table.iter():
        if local_name(dim) != "dimension":
            continue
        name = dim.get("name") or dim.get("label") or ""
        pos = (dim.get("position") or "").lower()
        if pos == "column":
            col_dims.append(name)
        else:
            # OXML 里没有 position 或缺省时，按行维度处理（最常见）。
            row_dims.append(name)
    return row_dims, col_dims


def _category_label(cat) -> str:
    """取 category / dim 的显示标签：label 属性 > 文本 > ''。"""
    for attr in ("label", "text", "name"):
        v = cat.get(attr)
        if v:
            return v.strip()
    return (cat.text or "").strip()


def _cell_values(cell):
    """取一格: 返回 (number, text)。

    `number` 是**全精度**值（"13.833333333333"），`text` 是显示值（"13.8333"）。
    缺失时 number 可能是 "" 或 "NaN"，一律给 None。
    """
    num = cell.get("number")
    txt = cell.get("text")
    if num is not None:
        num = num.strip()
        if num == "" or num.lower() in ("nan", "none", "."):
            num = None
    if txt is not None:
        txt = txt.strip()
        if txt in ("", "."):
            txt = None
    return num, txt


def parse_table(table):
    """把一张 pivotTable 解成 {title, subType, rows:[{labels, cells}], headers}。

    OXML 的行结构是 `<dimension>` 里若干 `<category>`，再跟一组 `<dim>` 行，
    每行含若干 `<cell>`。这里按「category 数量」与「cell 数量」对齐，
    不做任何假设性的行列重排 —— 宁可如实给出，也不猜。

    **subType 是最可靠的表标识，优先用它而不是标题文本。** 原因（实测）：
    简体中文版把剂量反应那张表叫「置信限度」，而 `Parameter Estimates` 表里
    也有「95% 置信区间 / 下限 / 上限」字样 —— 靠搜「置信」判断 CI 表是否存在，
    会在 `/PRINT=NONE` 时得出**完全相反**的结论。见 `has_lc_confidence()`。
    """
    title = table.get("label") or table.get("name") or ""
    sub_type = table.get("subType") or table.get("subtype") or ""
    row_dims, col_dims = _dimensions(table)

    # 顶部维度（列标题）：取每个 dimension 下的 category 标签
    headers = []
    for dim in table.iter():
        if local_name(dim) != "dimension":
            continue
        cats = [_category_label(c) for c in dim if local_name(c) == "category"]
        if cats:
            headers.append({"dimension": dim.get("name") or "",
                            "categories": cats})

    rows = []
    for row in table.iter():
        if local_name(row) != "dim":
            continue
        # 该行的行维度标签
        labels = []
        for cat in row:
            if local_name(cat) in ("category", "dim"):
                lab = _category_label(cat)
                if lab:
                    labels.append(lab)
        cells = []
        for cell in row.iter():
            if local_name(cell) != "cell":
                continue
            num, txt = _cell_values(cell)
            cells.append({"number": num, "text": txt})
        if not cells and not labels:
            continue
        # 前 len(labels) 个当行标签，其余当值（OXML 里 often 混在一起，
        # 这里保留两类信息，交给调用方按 headers 对齐）
        rows.append({"labels": labels, "cells": cells})

    return {
        "title": title,
        "subType": sub_type,
        "row_dimensions": row_dims,
        "column_dimensions": col_dims,
        "headers": headers,
        "rows": rows,
    }


def has_lc_confidence(tables) -> bool:
    """是否存在真正的 LC50/EC50 置信限度表。

    **判据只能用 subType，不能用标题文本、也不能搜 "LC50"。** 实测教训：
      - 简体中文版把这张表叫「置信限度」，不是「置信区间」；
      - `Parameter Estimates` 表里也有「95% 置信区间 / 下限 / 上限」，
        那是斜率与截距的 Wald CI，`/PRINT=NONE` 时同样存在；
      - `LC50` 字面串在 OXML 里出现 0 次（值靠概率档 number="0.5" 定位）。
    所以搜「置信」会把 NONE 误判成有 CI，搜 "LC50" 永远搜不到。
    """
    for t in tables:
        if (t.get("subType") or "").strip().lower() == "confidence limits":
            return True
        if "confidence limits" in (t.get("title") or "").lower():
            return True
    return False


def all_tables(root):
    out = []
    for elem in root.iter():
        if local_name(elem) == "pivotTable":
            out.append(parse_table(elem))
    return out


def _matches(parsed, needle: str) -> bool:
    needle_l = needle.lower()
    if needle_l in (parsed.get("title") or "").lower():
        return True
    # 也匹配维度名，方便按 "Confidence" / "Parameter" 这种词找
    for h in parsed.get("headers") or []:
        if needle_l in (h.get("dimension") or "").lower():
            return True
        for c in h.get("categories") or []:
            if needle_l in (c or "").lower():
                return True
    return False


# ---------------------------------------------------------------- 输出

def table_to_rows(parsed):
    """一张表 → 扁平 (row_label, col_label, number, text) 列表。

    这是给 `--tsv` 与 `--json` 用的统一形状：一行一个格子，
    row_label 取该行的行标签拼接，col_label 取表头里对应位置。
    """
    flat = []
    headers = parsed.get("headers") or []
    # 把每个维度的类目标签拉平成一个列名列表（按出现顺序）
    col_names = []
    for h in headers:
        for c in h.get("categories") or []:
            col_names.append(c)
    for r in parsed.get("rows") or []:
        row_label = " | ".join(r.get("labels") or [])
        for i, cell in enumerate(r.get("cells") or []):
            col_label = col_names[i] if i < len(col_names) else f"c{i}"
            flat.append({
                "table": parsed.get("title") or "",
                "row": row_label,
                "col": col_label,
                "number": cell.get("number"),
                "text": cell.get("text"),
            })
    return flat


def write_tsv(rows, path):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write("table\trow\tcol\tnumber\ttext\n")
        for r in rows:
            fh.write("\t".join(
                "" if r.get(k) is None else str(r.get(k)).replace("\t", " ")
                for k in ("table", "row", "col", "number", "text")
            ) + "\n")


def extract_lc(tables, p: float = 0.5):
    """从 Confidence Limits 表里抽某个概率档（默认 0.5 = LC50）的点估计与 CI。

    实测的 OXML 形状：
      pivotTable[@subType='Confidence Limits']
        └─ 行维度「概率」→ category[@number='0.5']
        └─ 列「<剂量变量的> 95% 置信限度」→「统计」组三个 cell
           （依次是点估计、下限、上限；带 number 属性的是全精度值）

    这里不硬编码 cell 顺序（不同 SPSS 版本可能不同），而是按行里出现的
    category 的 number 属性找目标概率档，再取该行所有带 number 的 cell。
    """
    target = None
    for t in tables:
        if (t.get("subType") or "").strip().lower() == "confidence limits":
            target = t
            break
    if target is None:
        for t in tables:
            if "confidence limits" in (t.get("title") or "").lower():
                target = t
                break
    if target is None:
        return None

    want = str(p)
    for row in target.get("rows") or []:
        labels = row.get("labels") or []
        # 概率档出现在行标签里（要么是 "0.5"，要么带 number 属性的 category）
        if not any(str(x).strip() in (want, f"{p:g}", f"{p:.3f}") for x in labels):
            continue
        nums = [c.get("number") for c in (row.get("cells") or [])
                if c.get("number") is not None]
        if not nums:
            continue
        return {
            "table": target.get("title"),
            "subType": target.get("subType"),
            "probability": p,
            "point": nums[0] if len(nums) > 0 else None,
            "lower": nums[1] if len(nums) > 1 else None,
            "upper": nums[2] if len(nums) > 2 else None,
            "all_numbers": nums,
        }
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description="解析 SPSS OXML：列结构 / 导 TSV / 倒 JSON / 取单值")
    ap.add_argument("--xml", help="OXML 文件路径")
    ap.add_argument("--list", metavar="XML", help="只列 OXML 里有哪些表（给路径即可）")
    ap.add_argument("--table", help="按标题子串挑一张表")
    ap.add_argument("--tsv", help="把选中的表写成 TSV")
    ap.add_argument("--json", dest="json_out", help="把选中的表（或全部）写成扁平 JSON")
    ap.add_argument("--find", help="在选中表里找含该关键词的行，只打印命中的数字")
    ap.add_argument("--lc", nargs="?", const="0.5",
                    help="直接抽 LC/EC 点估计与 CI；可带概率（默认 0.5 = LC50）")
    args = ap.parse_args()

    xml_path = args.xml or args.list
    if not xml_path:
        ap.error("需要 --xml 或 --list <file>")

    try:
        root = load_ooxml(xml_path)
    except OxmlIncomplete as exc:
        print(f"! {exc}", file=sys.stderr)
        return 2
    except FileNotFoundError as exc:
        print(f"! {exc}", file=sys.stderr)
        return 2

    tables = all_tables(root)

    if args.list:
        print(f"{len(tables)} 张表：")
        for i, t in enumerate(tables):
            n = len(t.get("rows") or [])
            st = t.get("subType") or ""
            print(f"  [{i}] {t.get('title') or '(无标题)'}"
                  + (f"  subType={st}" if st else "")
                  + f"  ({n} 行)")
            for h in t.get("headers") or []:
                cats = h.get("categories") or []
                if cats:
                    print(f"        {h.get('dimension') or '?'}: "
                          + ", ".join(cats[:8]) + (" …" if len(cats) > 8 else ""))
        if has_lc_confidence(tables):
            print("\n含 LC/EC 置信限度表（subType=Confidence Limits）—— 可以抽 LC50。")
        else:
            print("\n**没有 Confidence Limits 表** —— 若你期望 LC50/EC50，"
                  "检查 .sps 里的 PROBIT 是否写了 /PRINT=CI（写 NONE 会把这张表关掉）。")
        return 0

    if args.table:
        picked = [t for t in tables if _matches(t, args.table)]
        if not picked:
            print(f"! 没有标题含「{args.table}」的表。可用 --list 看有哪些。", file=sys.stderr)
            return 2
        selected = picked[0]
        print(f"选中：{selected.get('title')}", file=sys.stderr)
    else:
        selected = None

    rows = []
    if selected is not None:
        rows = table_to_rows(selected)
    else:
        for t in tables:
            rows.extend(table_to_rows(t))

    if args.lc:
        try:
            p = float(args.lc)
        except ValueError:
            print(f"! --lc 的概率要是数字：{args.lc}", file=sys.stderr)
            return 2
        got = extract_lc(tables, p)
        if got is None:
            print("! 没找到 Confidence Limits 表里的该概率档。\n"
                  "  先跑 --list 看有没有 Confidence Limits 表；"
                  "若没有，检查 .sps 的 PROBIT 是否写了 /PRINT=CI。",
                  file=sys.stderr)
            return 2
        print(json.dumps(got, ensure_ascii=False, indent=2))
        return 0

    if args.find:
        needle = args.find.lower()
        hits = [r for r in rows if needle in (r.get("row") or "").lower()
                or needle in (r.get("col") or "").lower()]
        if not hits:
            print(f"! 「{args.find}」没有命中任何行", file=sys.stderr)
            return 2
        for h in hits:
            print(f"{h.get('row')} | {h.get('col')} | number={h.get('number')} | text={h.get('text')}")
        return 0

    if args.tsv:
        write_tsv(rows, args.tsv)
        print(f"已写 {args.tsv}（{len(rows)} 行）")

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as fh:
            json.dump({"source": os.path.abspath(xml_path),
                       "tables": [t.get("title") for t in tables],
                       "rows": rows}, fh, ensure_ascii=False, indent=2)
        print(f"已写 {args.json_out}（{len(rows)} 行）")

    if not args.tsv and not args.json_out:
        # 没指定输出就把表结构打到 stdout，方便肉眼确认
        print(json.dumps({"tables": [t.get("title") for t in tables],
                          "row_count": len(rows)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
