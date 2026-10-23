#!/usr/bin/env python
"""ORA 富集：基因列表 + 基因集 → 富集表 + 统计量 + 人读摘要。

用法（figkit 环境）：
  {root}/envs/figkit/Scripts/python.exe ora.py \
      --genes sig_genes.txt \
      --sets  msigdb_hallmark.gmt \
      --background 20000 \
      --out   results

输入：
  --genes      每行一个基因（也接受单列 TSV/CSV，或用 --gene-col 指定列名）
  --sets       .gmt 文件，或 gseapy 能读的库名（离线跑请给文件）
  --background 背景基因数（整数），或一个基因列表文件；强烈建议显式给，
               否则富集 p 值会系统性偏小
输出（结果契约）：
  results/enrichment.tsv   富集结果表
  results/stats.json       参数、显著条数、输入哈希
  results/analysis.md      人读摘要
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys


def read_genes(path: str, column: str | None) -> list[str]:
    if column:
        import pandas as pd

        df = pd.read_csv(path, sep=None, engine="python")
        if column not in df.columns:
            raise SystemExit(f"列 {column!r} 不在 {path} 里：{list(df.columns)}")
        values = df[column].astype(str).tolist()
    else:
        values = []
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                values.append(line.split("\t")[0].split(",")[0].strip())
    seen, out = set(), []
    for v in values:
        if v and v not in seen:
            seen.add(v)
            out.append(v)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--genes", required=True)
    ap.add_argument("--gene-col", default=None)
    ap.add_argument("--sets", required=True, help="GMT 文件路径")
    ap.add_argument("--background", required=True, help="背景基因数（整数）或基因列表文件")
    ap.add_argument("--out", default="results")
    ap.add_argument("--cutoff", type=float, default=0.05)
    args = ap.parse_args()

    import gseapy as gp

    genes = read_genes(args.genes, args.gene_col)
    if not genes:
        raise SystemExit("基因列表是空的")

    if os.path.isfile(args.background):
        background = read_genes(args.background, None)
    else:
        background = int(args.background)

    gene_sets = gp.read_gmt(args.sets)
    res = gp.enrich(gene_list=genes, gene_sets=gene_sets, background=background, outdir=None)
    table = res.results.copy()

    os.makedirs(args.out, exist_ok=True)
    tsv = os.path.join(args.out, "enrichment.tsv")
    table.to_csv(tsv, sep="\t", index=False)

    padj = table["Adjusted P-value"] if "Adjusted P-value" in table else table["P-value"]
    sig = table[padj < args.cutoff]

    digest = hashlib.sha256("\n".join(genes).encode()).hexdigest()
    stats = {
        "method": "ORA (hypergeometric, gseapy.enrich)",
        "gseapy_version": getattr(gp, "__version__", "unknown"),
        "gene_sets_file": os.path.abspath(args.sets),
        "n_gene_sets": int(len(gene_sets)),
        "n_genes": len(genes),
        "background": background if isinstance(background, int) else len(background),
        "cutoff_padj": args.cutoff,
        "n_significant": int(sig.shape[0]),
        "input_sha256": digest,
    }
    with open(os.path.join(args.out, "stats.json"), "w", encoding="utf-8") as fh:
        json.dump(stats, fh, ensure_ascii=False, indent=2)

    top = sig.sort_values(padj.name if hasattr(padj, "name") else "Adjusted P-value").head(10)
    lines = [
        "# 富集分析摘要",
        "",
        f"- 方法：{stats['method']}（gseapy {stats['gseapy_version']}）",
        f"- 输入基因：{stats['n_genes']} 个；背景：{stats['background']}；基因集：{stats['n_gene_sets']} 组",
        f"- 显著（FDR < {args.cutoff}）：{stats['n_significant']} 条",
        "",
        "## 显著条目（前 10）",
        "",
    ]
    if top.empty:
        lines.append("（没有条目通过 FDR 阈值）")
    else:
        for _, row in top.iterrows():
            lines.append(
                f"- **{row['Term']}**：{row['Overlap']}，"
                f"P = {row['P-value']:.3g}，FDR = {row['Adjusted P-value']:.3g}"
            )
    lines += [
        "",
        "## 复核",
        "",
        "```bash",
        f"python ora.py --genes {os.path.abspath(args.genes)} --sets {os.path.abspath(args.sets)} "
        f"--background {stats['background']} --out {os.path.abspath(args.out)}",
        "```",
        "",
        f"输入哈希：`{digest}`",
    ]
    with open(os.path.join(args.out, "analysis.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")

    print(json.dumps(stats, ensure_ascii=False, indent=2))
    print(f"写入：{tsv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
