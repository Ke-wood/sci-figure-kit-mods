#!/usr/bin/env python
"""用 Prism 模板做统计分析：Import → RecalcAll → Save → 读 results.json。

**Prism 只出数、不出图**：图的样子是二进制、脚本改不了，出图交给 cnsplots / ggplot2。
这条链只依赖模板里的「一张数据表 + 一个分析」，不需要图。

用法：
  python prism_analyze.py --template oneway.prism --data panel.csv --out results

输入：
  --template  .prism（Prism 10/11 存；一张表、一个分析）
  --data      宽表 CSV（无表头，行=重复，列=组），列数必须等于模板数据表的列数
输出（结果契约）：
  results/anova.csv     主检验（SS/df/MS/F/p）
  results/posthoc.csv   成对比较（均值差、SE、CI、校正 p、是否显著）
  results/letters.csv   紧凑字母显示（如果模板配了全配对比较）
  results/results.json  Prism 原始 results.json（权威，全精度）
  results/stats.json    输入哈希、参数、样本量
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import zipfile

DEFAULT_EXE = "{root}/prism/prism.exe"


def is_ascii(s: str) -> bool:
    try:
        s.encode("ascii")
        return True
    except UnicodeEncodeError:
        return False


def kill_prism() -> None:
    subprocess.run(["taskkill", "/IM", "prism.exe", "/F"], capture_output=True)


def walk_pairs(node, out: list) -> None:
    """results.json 里的成对比较是 uid 套 uid 的嵌套字典，把叶子收集出来。"""
    if isinstance(node, dict):
        if "meansDifference" in node and "pValueAdjusted" in node:
            out.append(node)
            return
        for value in node.values():
            walk_pairs(value, out)
    elif isinstance(node, list):
        for value in node:
            walk_pairs(value, out)


def col_index(sample) -> int | None:
    try:
        return int(sample["id"]["col"]["idx"])
    except Exception:
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--template", required=True)
    ap.add_argument("--data", required=True, help="宽表 CSV：无表头、行=重复、列=组")
    ap.add_argument("--out", default="results")
    ap.add_argument("--exe", default=os.environ.get("PRISM_EXE") or DEFAULT_EXE)
    ap.add_argument("--timeout", type=int, default=180)
    ap.add_argument("--keep-workdir", default=None, help="默认建在 <out>/.prism_work")
    args = ap.parse_args()

    import pandas as pd

    work = args.keep_workdir or os.path.join(args.out, ".prism_work")
    work = os.path.abspath(work)
    work = work.replace("\\", "/")
    if not is_ascii(work):
        print(f"! 工作目录含非 ASCII 字符：{work}", file=sys.stderr)
        return 2
    if not os.path.isfile(args.exe):
        print(f"! 找不到 Prism：{args.exe}", file=sys.stderr)
        return 2

    os.makedirs(work, exist_ok=True)
    os.makedirs(args.out, exist_ok=True)

    data = pd.read_csv(args.data, header=None)
    if data.shape[0] < 2:
        print("! 数据行数太少", file=sys.stderr)
        return 2

    # Prism 的脚本里路径只用正斜杠 —— 混用反斜杠时 Save 会静默失败
    template_local = os.path.join(work, "template.prism").replace("\\", "/")
    shutil.copyfile(args.template, template_local)
    data_path = os.path.join(work, "data.csv").replace("\\", "/")
    data.to_csv(data_path, header=False, index=False)
    saved = os.path.join(work, "out.prism").replace("\\", "/")

    for stale in (saved,):
        if os.path.isfile(stale):
            os.remove(stale)

    script = "\n".join([
        f'Open "{template_local}"',
        "GoTo D 1",
        "ClearTable",
        f'Import "{data_path}", 1, 1',
        "RecalcAll",
        f'Save "{saved}"',
        "Exit",
    ])
    pzc = os.path.join(work, "job.pzc").replace("\\", "/")
    with open(pzc, "w", encoding="mbcs", newline="\r\n") as fh:
        fh.write(script)

    t0 = time.time()
    try:
        # 注意：`@` 后面的**脚本路径**必须是 Windows 原生反斜杠 ——
        # 传正斜杠时 Prism 打不开脚本，弹一下"文件无法打开"然后静默退出（rc=0）。
        # 脚本**里面**的路径反而用正斜杠最稳。
        proc = subprocess.run([args.exe, "@" + os.path.normpath(pzc)], timeout=args.timeout,
                              capture_output=True, text=True)
        rc = proc.returncode
    except subprocess.TimeoutExpired:
        kill_prism()
        print(f"! 超时 {args.timeout}s —— Prism 大概率卡在模态框，已强杀", file=sys.stderr)
        return 3
    elapsed = round(time.time() - t0, 1)

    if not os.path.isfile(saved):
        print(f"! Prism 退出码 {rc}，但没有产出 {saved}", file=sys.stderr)
        return 1

    with zipfile.ZipFile(saved) as zf:
        name = [n for n in zf.namelist() if n.endswith("/results.json")][0]
        raw = zf.read(name).decode("utf-8")
    results = json.loads(raw)
    content = results.get("content", {})
    model = content.get("ordinaryAnovaModel", {})

    with open(os.path.join(args.out, "results.json"), "w", encoding="utf-8") as fh:
        fh.write(raw)

    rows = []
    table = model.get("anovaTable", {})
    for term in ("colFactor", "rowFactor", "interaction", "residual", "total"):
        cell = table.get(term)
        if not isinstance(cell, dict):
            continue
        f_test = cell.get("fTest", {}) or {}
        p = (f_test.get("pValue") or {}).get("value")
        rows.append({
            "term": term, "ss": cell.get("ss"), "df": cell.get("df"), "ms": cell.get("ms"),
            "f": f_test.get("f"), "df_numerator": f_test.get("dfNumerator"),
            "df_denominator": f_test.get("dfDenominator"), "p": p,
        })
    pd.DataFrame(rows).to_csv(os.path.join(args.out, "anova.csv"), index=False)

    tests = []
    walk_pairs(model.get("multipleComparisons", {}), tests)
    post = []
    for t in tests:
        ci = t.get("meansDifferenceCI", {}) or {}
        post.append({
            "group1": col_index(t.get("sample1")),
            "group2": col_index(t.get("sample2")),
            "mean_diff": t.get("meansDifference"),
            "se": t.get("meansDifferenceSE"),
            "ci_low": ci.get("lower"), "ci_high": ci.get("upper"),
            "p_adj": (t.get("pValueAdjusted") or {}).get("value"),
            "significant": (t.get("pValueAdjusted") or {}).get("isSignificant"),
        })
    pd.DataFrame(post).to_csv(os.path.join(args.out, "posthoc.csv"), index=False)

    letters = []
    for _uid, item in (model.get("compactLetterDisplay", {}).get("samples") or {}).items():
        idx = col_index(item)
        if idx is not None:
            letters.append({"group": idx, "letter": item.get("value")})
    pd.DataFrame(sorted(letters, key=lambda r: r["group"])).to_csv(
        os.path.join(args.out, "letters.csv"), index=False)

    stats = {
        "template": os.path.abspath(args.template),
        "data": os.path.abspath(args.data),
        "data_sha256": hashlib.sha256(open(args.data, "rb").read()).hexdigest(),
        "n_rows": int(data.shape[0]),
        "n_groups": int(data.shape[1]),
        "analysis": model.get("status"),
        "comparison_method": model.get("multipleComparisons", {}).get("method"),
        "n_comparisons": model.get("multipleComparisons", {}).get("comparisonCount"),
        "n_significant": model.get("multipleComparisons", {}).get("significantCount"),
        "elapsed_s": elapsed,
        "prism_exit": rc,
    }
    with open(os.path.join(args.out, "stats.json"), "w", encoding="utf-8") as fh:
        json.dump(stats, fh, ensure_ascii=False, indent=2)

    print(json.dumps(stats, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
