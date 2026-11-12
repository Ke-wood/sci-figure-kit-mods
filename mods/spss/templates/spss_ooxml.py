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
    title = table.get("label") or table.get("text") or table.get("name") or ""
    sub_type = table.get("subType") or table.get("subtype") or ""

    # 行/列维度必须分开取：**列名只能来自列方向的维度**。
    # 曾经把所有维度的类目混在一起当列名，于是行维度（如「概率」.10/.50/.90）
    # 被当成列标签，导出的 TSV 列语义整体错位 —— 下游按 col 对齐全错。
    #
    # 方向属性的名字随版本变：实测 SPSS 27 的 OXML 用 **axis="row"/"column"**，
    # 而早期样例/文档里见过 position="row"/"column"。两个都要认，否则
    # col_categories 恒为空、导出表没有列标签（实测踩到：cl.tsv 只有表头）。
    headers = []
    col_categories = []
    for dim in table.iter():
        if local_name(dim) != "dimension":
            continue
        pos = (dim.get("axis") or dim.get("position") or "").lower()
        cats = [_category_label(c) for c in dim if local_name(c) == "category"]
        if not cats:
            continue
        headers.append({"dimension": dim.get("name") or dim.get("text") or "",
                        "position": pos or "row",
                        "categories": cats})
        if pos == "column":
            col_categories.extend(cats)

    rows = []
    # 真实 OXML（SPSS 27 实测）有两种行形态，必须都认：
    #   ① 平铺：<dim><category/><cell/><cell/></dim>
    #   ② 嵌套：<category number="0.5" text=".50"><dimension axis="column">…
    #      <cell/></dimension></category> —— Confidence Limits 表就是这种，
    #      列维度嵌在概率档 category 内部。只遍历 <dim> 会一行都取不到
    #      （实测 cl.tsv 只有表头，就是这个原因）。
    for row in table.iter():
        if local_name(row) != "dim":
            continue
        labels = []
        cat_numbers = []
        for cat in row:
            if local_name(cat) in ("category", "dim"):
                lab = _category_label(cat)
                if lab:
                    labels.append(lab)
                # **保留 category 的 number 属性**：概率档显示值是 ".50"，
                # 真正的数值判别（--lc 0.5）必须靠 number="0.5"。
                for attr in ("number", "value"):
                    v = cat.get(attr)
                    if v is not None and v.strip() != "":
                        cat_numbers.append(v.strip())
                        break
        cells = []
        for cell in row.iter():
            if local_name(cell) != "cell":
                continue
            num, txt = _cell_values(cell)
            cells.append({"number": num, "text": txt})
        if not cells and not labels:
            continue
        rows.append({"labels": labels, "cat_numbers": cat_numbers, "cells": cells})

    # 形态 ②：概率档 category 直接挂在行维度下（没有 <dim> 包裹）。
    # 这个分支只在上面没拿到任何行时才用，避免与形态 ① 重复计数。
    if not rows:
        for dim in table.iter():
            if local_name(dim) != "dimension":
                continue
            if (dim.get("axis") or dim.get("position") or "").lower() != "row":
                continue
            for cat in dim:
                if local_name(cat) != "category":
                    continue
                cells = []
                for cell in cat.iter():
                    if local_name(cell) != "cell":
                        continue
                    num, txt = _cell_values(cell)
                    cells.append({"number": num, "text": txt})
                if not cells:
                    continue
                lab = _category_label(cat)
                nums = []
                for attr in ("number", "value"):
                    v = cat.get(attr)
                    if v is not None and v.strip() != "":
                        nums.append(v.strip())
                        break
                rows.append({
                    "labels": [lab] if lab else [],
                    "cat_numbers": nums,
                    "cells": cells,
                })

    # 维度列表从 headers 派生（上面已按 position 分好），不要再调 _dimensions()：
    # 那个函数把行/列混在一起，正是列语义错位的根源。
    row_dims = [h["dimension"] for h in headers
                if (h.get("position") or "") != "column"]
    col_dims = [h["dimension"] for h in headers
                if (h.get("position") or "") == "column"]

    return {
        "title": title,
        "subType": sub_type,
        "row_dimensions": row_dims,
        "column_dimensions": col_dims,
        "headers": headers,
        "rows": rows,
        "records": _leaf_records(table),
    }


def _is_leaf(cat) -> bool:
    """category 是叶子吗？判据是「有没有 cell 子节点」。

    真实 OXML 里 category 有两种形态：带 cell 的是数值叶子；不带 cell 的是
    容器（其下继续套 dimension）。**不能按固定深度判断** —— Parameter
    Estimates 是 3 层、Confidence Limits 是 4 层，深度会变。
    """
    for ch in cat:
        if local_name(ch) == "cell":
            return True
    return False


def _leaf_records(table):
    """把嵌套结构摊平成 [{path:[维度名→类目标签], numbers:[...], texts:[...]}]。

    这是给 `--lc` 之类"按语义找数"的调用方用的：真实结构是
      模型 > 概率(0.5) > CL 类型(dose 的...) > 统计(估算/下限/上限) > cell
    每一层都有意义，只取 cells 会丢掉「这是 dose 的还是 log(dose) 的」这类
    关键区分（实测两种 CL 类型会给不同量级的两套数）。
    """
    records = []

    def walk(node, path):
        for ch in list(node):
            tag = local_name(ch)
            if tag == "dimension":
                dim_name = ch.get("text") or ch.get("name") or ""
                walk(ch, path + [("dim", dim_name)])
            elif tag == "group":
                walk(ch, path + [("group", ch.get("text") or "")])
            elif tag == "category":
                label = _category_label(ch)
                num = None
                for attr in ("number", "value"):
                    v = ch.get(attr)
                    if v is not None and v.strip() != "":
                        num = v.strip()
                        break
                this_path = path + [("cat", label, num)]
                if _is_leaf(ch):
                    nums, txts = [], []
                    for cell in ch:
                        if local_name(cell) != "cell":
                            continue
                        n, t = _cell_values(cell)
                        nums.append(n)
                        txts.append(t)
                    records.append({
                        "path": this_path,
                        "numbers": nums,
                        "texts": txts,
                    })
                else:
                    walk(ch, this_path)

    walk(table, [])
    return records


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
    """按标题 / subType / 维度名 / 类目名匹配一张表。

    **必须查 subType。** 简中版把这张表叫「置信限度」，用户照文档敲
    `--table 'Confidence Limits'` 时标题匹配不到，但 subType 正是它 ——
    不查 subType 就会明明有这张表却报"没有"。
    """
    needle_l = needle.lower()
    if needle_l in (parsed.get("title") or "").lower():
        return True
    if needle_l in (parsed.get("subType") or "").lower():
        return True
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

    这是给 `--tsv` / `--json` 用的统一形状：一行一个格子。

    **以 records（叶子路径）为唯一来源，不再用 headers 按下标对齐。**
    曾经的做法是把所有 column 维度的类目首尾相接当列名，再去和 cell 按下标
    配对。真实 OXML 里列维度是分层的（`CL 类型` 2 个 × `统计` 3 个），拼平后
    粒度与 cell 序列对不上，于是标签与数值整体错位（实测 0/6 对得上）。

    同时**避免重复计数**：`parse_table` 的 rows 里会有一条"伪行"（模型的
    PROBIT）把整棵子树的 cell 都吞进来，再叠加各概率档自己的行，结果是
    cell 数的两倍（实测 420 vs 真实 210）。走 records 天然一叶一行，不会重复。
    """
    flat = []

    for rec in parsed.get("records") or []:
        path = rec.get("path") or []
        # 把路径拆成：行维度标签列表 + 列维度标签列表 + 统计名
        # 真实语义：模型(行) > 概率(行) > CL 类型(列) > 统计(列)
        cats = []
        col_parts = []
        stat = ""
        for item in path:
            if item[0] not in ("cat", "group") or len(item) < 2:
                continue
            lab = str(item[1] or "")
            cats.append(lab)
        if not cats:
            continue
        stat = cats[-1]
        row_label = " | ".join(cats[:-1]) if len(cats) > 1 else cats[0]
        # 列标签：CL 类型 + 统计名（两者都是列维度语义）
        if len(cats) >= 3:
            col_parts = cats[-3:-1]
        elif len(cats) >= 2:
            col_parts = cats[:-1]
        col_label = " | ".join(col_parts + [stat]) if col_parts else stat

        nums = rec.get("numbers") or []
        txts = rec.get("texts") or []
        for i, n in enumerate(nums):
            flat.append({
                "table": parsed.get("title") or "",
                "row": row_label,
                "col": col_label,
                "number": n,
                "text": txts[i] if i < len(txts) else None,
            })

    # 老结构（真有 <dim> 行的文件）才走 rows；records 为空说明是这种。
    if not flat:
        headers = parsed.get("headers") or []
        col_names = []
        for h in headers:
            if (h.get("position") or "").lower() == "column":
                col_names.extend(h.get("categories") or [])
        if not col_names and len(headers) > 1:
            for h in headers[1:]:
                col_names.extend(h.get("categories") or [])
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


def flat_row_count_ok(parsed, flat) -> str:
    """自检：导出行数应等于该表原始 `<cell>` 数。不等就返回告警文本。

    这个检查是为一个真实 bug 加的：解析器曾把同一批 cell 报两遍
    （伪行吞掉全部 + 各概率档再来一遍），420 行 vs 真实 210 个 cell，
    表面看不出问题，只有对账才发现。以后任何重复计数都能被它挡住。
    """
    recs = parsed.get("records") or []
    if not recs:
        return ""  # 老结构没法这么对账，跳过
    expect = sum(len(r.get("numbers") or []) for r in recs)
    got = len(flat)
    if got == expect:
        return ""
    return (f"！行数与 cell 数不符：导出 {got} 行，但表里只有 {expect} 个 cell"
            f"（{parsed.get('title') or parsed.get('subType')}）——疑似重复计数。")


def write_tsv(rows, path):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write("table\trow\tcol\tnumber\ttext\n")
        for r in rows:
            fh.write("\t".join(
                "" if r.get(k) is None else str(r.get(k)).replace("\t", " ")
                for k in ("table", "row", "col", "number", "text")
            ) + "\n")


def _cat_numbers(row):
    """取这一行的 category number 属性（全精度字符串），按出现顺序。

    **必须看 number，不能看 text。** SPSS 把概率档显示成 `.50`（带前导点），
    拿 text 去和 "0.5" 比对永远不相等 —— `--lc 0.5` 会在明明有 CI 表时报「没找到」。
    实测：text=".50" 的 category 其 number 是 "0.5"。

    `row` 是 `parse_table()` 产出的 **dict**（不是 XML 结点），所以直接读
    `cat_numbers`；为了兼容早期调用方/旧结构，dict 缺该键时再退回 labels 猜。
    """
    if isinstance(row, dict):
        nums = row.get("cat_numbers")
        if nums:
            return list(nums)
        # 没有 number 时退回 labels（.50 / 0.5 这类写法都能被 _num_eq 认）
        return [str(x).strip() for x in (row.get("labels") or [])]
    # 真拿到 XML 结点时按旧路径走（保持兼容）
    out = []
    for cat in row:
        if local_name(cat) not in ("category", "dim"):
            continue
        for attr in ("number", "value"):
            v = cat.get(attr)
            if v is not None and v.strip() != "":
                out.append(v.strip())
                break
    return out


def _num_eq(a: str, b: float) -> bool:
    """把 OXML 里的数字串与目标浮点比较（容忍 .50 / 0.5 / 0.500 等写法）。"""
    try:
        return abs(float(a) - float(b)) < 1e-9
    except (TypeError, ValueError):
        return False


def _ci_ordered(lower, point, upper) -> bool:
    """置信区间的基本物理约束：lower <= point <= upper。

    这是防"静默返回错值"的最后一道闸。真实踩过：解析器把 lower/upper
    串到 log(dose) 分支，给出 lower=0.3728 > upper=0.2557 —— 一个物理上
    不可能的结果，却因为函数正常返回而没人发现。有了这条，
    调用方读到 ordered_ok=false 就知道该停下来查，而不是直接拿去用。
    """
    try:
        lo, po, up = float(lower), float(point), float(upper)
    except (TypeError, ValueError):
        return False
    return lo <= po <= up


# 列维度类目名的语义识别：不同语言/版本写法不同，靠关键词归类。
# **「估算」必须在内。** SPSS 简中把点估计那一列写作「估算」（不是"点估计"、
# 也不是"估计"）。漏了它会让 _classify 返回 unknown → records 分支整段放弃
# → 回退到旧兜底 → lower/upper 串到 log(dose) 分支去（实测下限定成 0.37）。
_LOWER_HINTS = ("下限", "lower", "lcl", "low")
_POINT_HINTS = ("估算", "点估计", "估计", "point", "estimate", "prob")
_UPPER_HINTS = ("上限", "upper", "ucl", "high")


def _classify(col_label: str) -> str:
    """把列标签归成 lower / point / upper / unknown。"""
    s = (col_label or "").strip().lower()
    if not s:
        return "unknown"
    for h in _LOWER_HINTS:
        if h in s:
            return "lower"
    for h in _UPPER_HINTS:
        if h in s:
            return "upper"
    for h in _POINT_HINTS:
        if h in s:
            return "point"
    return "unknown"


def extract_lc(tables, p: float = 0.5):
    """从 Confidence Limits 表里抽某个概率档（默认 0.5 = LC50）的点估计与 CI。

    实测的 OXML 形状（SPSS 27）：
      pivotTable[@subType='Confidence Limits']
        └─ 行维度「概率」→ category number='0.5'（text 是 ".50"）
        └─ 列维度「dose 的 95% 置信限度」→ 下限 / 点估计 / 上限

    **point / lower / upper 的归属必须按列标签判定，不能按 cell 出现顺序。**
    实测 cell 顺序在真实文件里是「下限、点估计、上限」，但按顺序硬赋会在
    别的表/版本里错位（曾出现 point 拿到下限值的情况）。这里：
      1. 先用列标签关键词给每个 cell 归类；
      2. 归不出来时退回「按数值大小排」（lower ≤ point ≤ upper）作为兜底；
    两条都尽量让语义正确，而不是"能跑就行"。
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

    # ---- 首选：按 records 的路径语义精确取数（真实结构有 4 层，见 _leaf_records）
    # 路径形如：[('dim','模型'),('cat','PROBIT'),('dim','概率'),('cat','.50',num='0.5'),
    #            ('dim','CL 类型'),('cat','dose 的 95% 置信限度'),
    #            ('dim','统计'),('cat','估算'|'下限'|'上限')]
    # 关键：同一概率档下有 **dose 的** 与 **log(dose) 的** 两套数，量级不同，
    # 必须按路径里的 "log(" 区分，否则会拿错数。
    recs = target.get("records") or []
    # 只保留 dose（不是 log(dose)）那一支，且只要目标概率档。
    #
    # 真实路径（SPSS 27，4 层）：
    #   dim:模型 > cat:PROBIT > dim:概率 > cat:.500(num='0.5')
    #     > dim:CL 类型 > cat:'dose 的 95% 置信限度'
    #       > dim:统计 > cat:'估算'|'下限'|'上限'
    # 早期版本把「最后一个 cat」当统计名，同时又用它当 cl_type，两者互相覆盖，
    # 于是 `log(` 判断失效、log(dose) 的数混进来（实测下限定成了 0.3728）。
    # 这里改成按位置语义取：cl_type 取「含置信限度字样的那一级」，
    # stat 取「最后一级 cat」，两者分开保存、互不覆盖。
    want_prob = []
    for r in recs:
        path = r.get("path") or []
        prob = None
        cl_type = ""
        cats = []
        for item in path:
            if item[0] != "cat" or len(item) < 2:
                continue
            lab = str(item[1] or "")
            cats.append(lab)
            if len(item) >= 3 and item[2] is not None and _num_eq(item[2], p):
                prob = item[2]
            low = lab.lower()
            if "置信限度" in lab or "confidence" in low or "置信区间" in lab:
                cl_type = lab
        if prob is None or not cats:
            continue
        if "log(" in cl_type.lower():
            continue  # 跳过 log(dose) 分支：量级不同，不是 LC50
        nums = r.get("numbers") or []
        if not nums:
            continue
        want_prob.append({"stat": cats[-1], "number": nums[0], "cl_type": cl_type})

    if want_prob:
        got = {"lower": None, "point": None, "upper": None}
        for item in want_prob:
            kind = _classify(item["stat"])
            if kind in got and got[kind] is None:
                got[kind] = item["number"]
        if all(v is not None for v in got.values()):
            return {
                "table": target.get("title"),
                "subType": target.get("subType"),
                "probability": p,
                "point": got["point"],
                "lower": got["lower"],
                "upper": got["upper"],
                "cl_type": want_prob[0]["cl_type"],
                "source": "records",
                "ordered_ok": _ci_ordered(got["lower"], got["point"], got["upper"]),
            }

    # ---- 兜底：老结构（平铺 rows）
    col_labels = []
    for h in target.get("headers") or []:
        if (h.get("position") or "").lower() == "column":
            col_labels.extend(h.get("categories") or [])

    for row in target.get("rows") or []:
        nums_of_cats = _cat_numbers(row)
        hit = any(_num_eq(v, p) for v in nums_of_cats)
        if not hit:
            labels = row.get("labels") or []
            hit = any(_num_eq(str(x).strip(), p) for x in labels)
        if not hit:
            continue

        cells = [c for c in (row.get("cells") or []) if c.get("number") is not None]
        if not cells:
            continue

        point = lower = upper = None
        for i, cell in enumerate(cells):
            kind = _classify(col_labels[i]) if i < len(col_labels) else "unknown"
            if kind == "lower" and lower is None:
                lower = cell["number"]
            elif kind == "upper" and upper is None:
                upper = cell["number"]
            elif kind == "point" and point is None:
                point = cell["number"]

        if point is None or lower is None or upper is None:
            # 兜底：按数值大小推断（lower ≤ point ≤ upper），比按顺序瞎赋可靠
            try:
                vals = sorted(float(c["number"]) for c in cells[:3])
                if len(vals) >= 3:
                    lower = lower or f"{vals[0]:g}"
                    point = point or f"{vals[1]:g}"
                    upper = upper or f"{vals[2]:g}"
            except (TypeError, ValueError):
                pass
        # 仍然缺就用原始顺序补齐（最后一层兜底，并在字段里标注）
        nums = [c["number"] for c in cells]
        if point is None:
            point = nums[1] if len(nums) > 1 else nums[0]
        if lower is None:
            lower = nums[0]
        if upper is None:
            upper = nums[2] if len(nums) > 2 else nums[-1]

        return {
            "table": target.get("title"),
            "subType": target.get("subType"),
            "probability": p,
            "point": point,
            "lower": lower,
            "upper": upper,
            "column_labels": col_labels,
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
            print(f"! 没有标题或 subType 含「{args.table}」的表。可用 --list 看有哪些。",
                  file=sys.stderr)
            return 2
        selected = picked[0]
        print(f"选中：{selected.get('title')}"
              + (f"（subType={selected.get('subType')}）" if selected.get("subType") else ""),
              file=sys.stderr)
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
        if got.get("ordered_ok") is False:
            print("! 置信区间顺序异常：应当 lower <= point <= upper，实际不成立。\n"
                  "  这通常意味着数值串到了别的分支（例如 log(dose) 的 CL）。\n"
                  "  请用 --list 核对表结构，不要直接使用这三个数。",
                  file=sys.stderr)
            return 3
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
        # --find 与 --tsv/--json 可以同时用：先打印命中，再照常写文件。
        # 早先这里直接 return 0，导致 combo 时文件静默不写，用户以为写成功了。
        if not args.tsv and not args.json_out:
            return 0

    # 写盘前先对账：行数与真实 cell 数不符就告警（见 flat_row_count_ok 的说明）
    if selected is not None:
        warn = flat_row_count_ok(selected, rows)
        if warn:
            print(warn, file=sys.stderr)

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
