#!/usr/bin/env python
"""mods 仓库检查：清单合法、必填字段齐全、docs 存在、无本机路径。"""
from __future__ import annotations

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODS = os.path.join(ROOT, "mods")

TEXT_EXT = {".md", ".json", ".py", ".R", ".sh"}
FORBIDDEN = [
    re.compile(r"[A-Za-z]:[\\/]+Users[\\/]+[A-Za-z0-9_.-]+"),
    re.compile(r"/home/[A-Za-z0-9_.-]+/"),
]
REQUIRED = ("id", "type", "env", "purpose", "summary", "routes", "source")
TYPES = {"pypkg", "pysrc", "rpkg", "rgh", "mplstyle", "rstyle", "snippets"}
PURPOSES = {"plot", "analysis", "both"}


def main() -> int:
    problems: list[str] = []
    ids: list[str] = []

    for name in sorted(os.listdir(MODS)):
        d = os.path.join(MODS, name)
        if not os.path.isdir(d) or name.startswith("_"):
            continue
        mj = os.path.join(d, "mod.json")
        if not os.path.isfile(mj):
            problems.append(f"mods/{name}/ 缺 mod.json")
            continue
        try:
            mod = json.load(open(mj, encoding="utf-8"))
        except Exception as exc:
            problems.append(f"mods/{name}/mod.json 非法 JSON：{exc}")
            continue
        ids.append(mod.get("id", name))
        for key in REQUIRED:
            if key not in mod:
                problems.append(f"{name}: 缺字段 {key}")
        if mod.get("type") not in TYPES:
            problems.append(f"{name}: type={mod.get('type')!r} 不在闭集内")
        if mod.get("purpose") not in PURPOSES:
            problems.append(f"{name}: purpose={mod.get('purpose')!r} 必须是 plot/analysis/both")
        if not os.path.isfile(os.path.join(d, "docs.md")):
            problems.append(f"{name}: 缺 docs.md")
        for route in mod.get("routes") or []:
            if not isinstance(route, dict) or not route.get("intent"):
                problems.append(f"{name}: routes 里有缺 intent 的条目")

    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [x for x in dirnames if x not in {"__pycache__", ".git"}]
        for fn in filenames:
            if os.path.splitext(fn)[1].lower() not in TEXT_EXT:
                continue
            p = os.path.join(dirpath, fn)
            rel = os.path.relpath(p, ROOT)
            text = open(p, encoding="utf-8", errors="replace").read()
            for pat in FORBIDDEN:
                for m in pat.finditer(text):
                    line = text[: m.start()].count("\n") + 1
                    problems.append(f"{rel}:{line} 含本机路径 {m.group(0)!r}")

    if problems:
        print(f"FAIL：{len(problems)} 处问题")
        for p in problems[:40]:
            print("  - " + p)
        return 1
    print(f"OK：{len(ids)} 个 mod 清单合法（{', '.join(ids[:6])}…）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
