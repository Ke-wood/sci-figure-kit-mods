# pydeseq2

DESeq2 的 Python 实现：bulk RNA-seq 差异表达分析（负二项 GLM + Wald 检验 + LFC 收缩）。
装在 `{root}/envs/omicverse`，与 omicverse 共用一套 anndata/numpy/scipy。
来源：https://github.com/scverse/PyDESeq2

## 什么时候用它

- 有 **counts 矩阵**（原始整数计数，不是 TPM/FPKM）与样本分组，要做差异表达；
- 要 `log2FoldChange` / `pvalue` / `padj` 三列，后续自己画火山图、MA 图、热图；
- 本机没装 R 的 limma / DESeq2，这个 mod 就是补「bulk DE」这个空。

上游归一化后的连续值（TPM、log 表达）不适合它 —— DESeq2 的模型假设是计数。

## 调用块（实测可跑，2026-10-18，v0.5.4）

```python
import pandas as pd
from pydeseq2.dds import DeseqDataSet
from pydeseq2.ds import DeseqStats

# counts: 行 = 样本，列 = 基因；必须是整数计数
counts = pd.read_csv("counts.tsv", sep="\t", index_col=0)
# metadata: 行 = 样本（与 counts 同索引），列 = 分组等协变量
meta = pd.read_csv("samples.tsv", sep="\t", index_col=0)

dds = DeseqDataSet(counts=counts, metadata=meta, design="~condition", n_cpus=2)
dds.deseq2()

stat = DeseqStats(dds, contrast=["condition", "B", "A"], n_cpus=2)
stat.summary()
res = stat.results_df            # 索引是基因，列见下
res.to_csv("results/de.tsv", sep="\t")
```

协变量直接写进公式：`design="~condition + batch"`。

## 实测踩到的坑

| 坑 | 现象 | 正解 |
|---|---|---|
| 矩阵方向反了 | `ValueError: obs must have as many rows as X has rows (200), but has 6 rows` | **行=样本、列=基因**；必要时空 `counts.T` |
| 顶层没有导出 | `dir(pydeseq2)` 是空的，`from pydeseq2 import ...` 拿不到东西 | 从子模块进：`pydeseq2.dds.DeseqDataSet`、`pydeseq2.ds.DeseqStats` |
| 设计式参数改名 | 老教程写 `design_factors=` | 0.5.x 用 `design="~condition"`；两者都试，捕 `TypeError` 回退 |

## 输出

`stat.results_df` 的列：
`baseMean` / `log2FoldChange` / `lfcSE` / `stat` / `pvalue` / `padj`。

结果契约（本 skill 通用）：`results/de.tsv` + `results/stats.json`（样本量、设计式、
对比、显著数、输入哈希）+ 需要时 `results/analysis.md`。图从同一份 `de.tsv` 出，
不要另算一遍。

## 已验证

合成数据 200 基因 × 6 样本（前 40 个在 B 组上调 4 倍），实测
`padj<0.05 且 |log2FC|>1` 命中 **40 个，真阳性 40 个**，无假阳性。
验证脚本：`D:\workspace\DSH\杂活\_verify_pydeseq2\smoke.py`。
