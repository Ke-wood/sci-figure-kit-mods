#!/usr/bin/env python
"""无人值守跑 SPSS：.sps 语法 → 生产作业 → OXML/文本产物。

SPSS 的两条硬规矩（不遵守就弹 GUI 挂死）：
  1. **不要** `stats.exe foo.sps` —— 那是交互模式，会开窗口等你看结果。
  2. 必须走生产作业：`stats.exe -production silent job.spj`。

用法：
  python spss_run.py --sps analysis.sps --workdir C:/tmp/spss_run --out results

产物：
  <workdir>/job.spj          本次作业定义（可复现）
  <workdir>/job.log          生产作业日志（text-utf8）
  <workdir>/out.xml          .sps 里 OMS 指定的 OXML（若语法里有 OMS）
  <out>/stats.json           本次运行的参数与产物清单

.sps 里要做 OXML 导出，用 OMS：
  OMS /SELECT ALL /DESTINATION FORMAT=OXML OUTFILE='C:/tmp/spss_run/out.xml'.
  ... 你的分析 ...
  OMSEND.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys

DEFAULT_EXE = "{root}/spss/stats.exe"

JOB_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<job xmlns="http://xml.spss.com/spss/production"
     syntaxFormat="batch" syntaxErrorHandling="stop" print="false">
  <output outputPath="{log}" outputFormat="text-utf8"/>
  <syntax syntaxPath="{sps}"/>
</job>
"""


def is_ascii(path: str) -> bool:
    try:
        path.encode("ascii")
        return True
    except UnicodeEncodeError:
        return False


def kill_spss() -> None:
    subprocess.run(["taskkill", "/IM", "stats.exe", "/F"], capture_output=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sps", required=True, help="SPSS 语法文件（.sps）")
    ap.add_argument("--workdir", required=True, help="ASCII 工作目录（中文路径会被 SPSS 拒）")
    ap.add_argument("--out", default=None, help="结果目录，默认 = workdir/results")
    ap.add_argument("--exe", default=os.environ.get("SPSS_EXE") or DEFAULT_EXE)
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--keep", action="store_true", help="保留中间文件（默认也保留，仅供语义清晰）")
    args = ap.parse_args()

    workdir = os.path.abspath(args.workdir).replace("\\", "/")
    outdir = os.path.abspath(args.out or os.path.join(workdir, "results"))
    if not is_ascii(workdir):
        print(f"! 工作目录含非 ASCII 字符，SPSS 可能静默失败：{workdir}", file=sys.stderr)
        return 2
    if not os.path.isfile(args.exe):
        print(f"! 找不到 SPSS：{args.exe}（用 --exe 或环境变量 SPSS_EXE 指定）", file=sys.stderr)
        return 2
    if not os.path.isfile(args.sps):
        print(f"! 找不到语法文件：{args.sps}", file=sys.stderr)
        return 2

    os.makedirs(workdir, exist_ok=True)
    os.makedirs(outdir, exist_ok=True)
    log = f"{workdir}/job.log"
    job = f"{workdir}/job.spj"
    with open(job, "w", encoding="utf-8") as fh:
        fh.write(JOB_TEMPLATE.format(log=log, sps=os.path.abspath(args.sps).replace("\\", "/")))

    print(f"[run] {args.exe} -production silent {job}")
    try:
        proc = subprocess.run(
            [args.exe, "-production", "silent", job],
            timeout=args.timeout, capture_output=True, text=True,
        )
        rc = proc.returncode
        stdout, stderr = proc.stdout or "", proc.stderr or ""
    except subprocess.TimeoutExpired:
        print(f"! 超时 {args.timeout}s，杀掉 stats.exe", file=sys.stderr)
        kill_spss()
        return 3

    produced = sorted(
        os.path.join(dp, f) for dp, _, fs in os.walk(workdir) for f in fs
    )
    # OMS OUTFILE 可以写到 workdir 之外（.sps 里自己指定），所以也扫一遍语法文件所在目录。
    for dp, _, fs in os.walk(os.path.dirname(os.path.abspath(args.sps))):
        for f in fs:
            p = os.path.join(dp, f)
            if p not in produced:
                produced.append(p)
    produced.sort()
    xml = [p for p in produced if p.lower().endswith(".xml")]
    details = {
        "exe": args.exe,
        "sps": os.path.abspath(args.sps),
        "job": job,
        "log": log,
        "returncode": rc,
        "outputs": produced,
        "oXML": xml,
    }
    with open(os.path.join(outdir, "stats.json"), "w", encoding="utf-8") as fh:
        json.dump(details, fh, ensure_ascii=False, indent=2)

    # SPSS 语法错不挂死：退出码仍是 0，错误只在日志里。所以要看日志。
    errors = []
    if os.path.isfile(log):
        text = open(log, encoding="utf-8", errors="replace").read()
        errors = [ln for ln in text.splitlines()
                  if re.search(r"(?i)\berror\b|命令.*错误|无法|失败", ln)]
    if errors:
        print("! 日志里有错误行：", file=sys.stderr)
        for ln in errors[:10]:
            print("   " + ln.strip(), file=sys.stderr)
        return 1

    if not xml:
        print("! 没有产出 OXML —— 检查 .sps 里是否写了 OMS ... OMSEND", file=sys.stderr)
        return 1

    print(json.dumps({"ok": True, "xml": xml, "rc": rc}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
