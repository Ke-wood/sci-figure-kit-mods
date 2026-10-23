#!/usr/bin/env python
"""静默跑 Prism 脚本：`prism.exe @script.pzc` —— 带超时与强杀兜底。

Prism 的脚本是**没有沙箱**的：任何一条命令写错，它会弹一个模态框并**永久挂死**，
既不退出也没有错误码。所以这里的纪律是：

  1. 脚本必须以 `Exit` 结尾（Exit 会关掉所有文件、不保存、不询问、直接退出）。
  2. 路径必须**纯 ASCII**；`.pzc` 按系统 ANSI 码页（中文 Windows 是 GBK）落盘。
  3. 完成判定看**进程退出**，不看产物文件出现（哨兵可能在挂起前就写好了）。
  4. 超时 `taskkill /IM prism.exe /F` —— 这是唯一兜底。

用法：
  python prism_run.py --script job.pzc --workdir C:/tmp/prism_run --timeout 180

产物：workdir 下本次脚本写出的所有文件（OpenOutput / ExportSVG / Save 等）。
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

DEFAULT_EXE = "{root}/prism/prism.exe"


def is_ascii(s: str) -> bool:
    try:
        s.encode("ascii")
        return True
    except UnicodeEncodeError:
        return False


def kill_prism() -> None:
    subprocess.run(["taskkill", "/IM", "prism.exe", "/F"], capture_output=True)


def check_script(text: str) -> list[str]:
    """启动前先做静态检查 —— 比挂了再杀省事得多。"""
    problems = []
    body = [ln.strip() for ln in text.splitlines()]
    body = [ln for ln in body if ln and not ln.startswith("//") and not ln.startswith("/*")]
    if not body:
        problems.append("脚本是空的")
    elif body[-1].lower() != "exit":
        problems.append("脚本最后一行必须是 Exit（否则退出时可能弹「是否保存」并挂死）")
    for bad, why in (("SaveAs", "没有 SaveAs 这条命令，真命令是 Save \"<filename>\"") ,
                     ("GoTo R", "GoTo R n 的编号推不出来，某些 view 会报 No such sheet! 并挂死")):
        if any(bad.lower() in ln.lower() for ln in body):
            problems.append(f"{bad}：{why}")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--script", help="已有 .pzc 路径；与 --code 二选一")
    ap.add_argument("--code", help="直接给脚本文本（会落到 workdir/job.pzc）")
    ap.add_argument("--workdir", required=True, help="ASCII 工作目录")
    ap.add_argument("--exe", default=os.environ.get("PRISM_EXE") or DEFAULT_EXE)
    ap.add_argument("--timeout", type=int, default=180)
    ap.add_argument("--force", action="store_true", help="跳过静态检查（不建议）")
    args = ap.parse_args()

    workdir = os.path.abspath(args.workdir).replace("\\", "/")
    if not is_ascii(workdir):
        print(f"! 工作目录含非 ASCII 字符：{workdir}", file=sys.stderr)
        return 2
    if not os.path.isfile(args.exe):
        print(f"! 找不到 Prism：{args.exe}（用 --exe 或 PRISM_EXE 指定）", file=sys.stderr)
        return 2
    if not (args.script or args.code):
        print("! 需要 --script 或 --code", file=sys.stderr)
        return 2

    os.makedirs(workdir, exist_ok=True)
    if args.script:
        src = os.path.abspath(args.script)
        if not is_ascii(src):
            print(f"! 脚本路径含非 ASCII 字符：{src}", file=sys.stderr)
            return 2
        text = open(src, encoding="mbcs", errors="replace").read()
        script = src
    else:
        text = args.code
        # .pzc 按系统 ANSI 码页写；中文必须走 mbcs，否则 Prism 里是乱码
        script = os.path.join(workdir, "job.pzc")
        with open(script, "w", encoding="mbcs", newline="\r\n") as fh:
            fh.write(text)

    problems = check_script(text)
    if problems and not args.force:
        print("! 静态检查没过：", file=sys.stderr)
        for p in problems:
            print("   - " + p, file=sys.stderr)
        return 2

    print(f"[run] {args.exe} @{script}")
    try:
        # `@` 后的脚本路径必须是原生反斜杠：正斜杠会让 Prism 打不开脚本，
        # 弹一下"文件无法打开"就退出（rc 仍是 0，看起来像成功）。
        proc = subprocess.run([args.exe, "@" + os.path.normpath(script)], timeout=args.timeout,
                              capture_output=True, text=True)
        rc = proc.returncode
    except subprocess.TimeoutExpired:
        print(f"! 超时 {args.timeout}s —— Prism 大概率卡在模态框，强杀", file=sys.stderr)
        kill_prism()
        return 3

    produced = sorted(os.path.join(dp, f) for dp, _, fs in os.walk(workdir) for f in fs)
    print(json.dumps({"ok": rc == 0, "rc": rc, "script": script, "outputs": produced},
                     ensure_ascii=False, indent=2))
    return 0 if rc == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
