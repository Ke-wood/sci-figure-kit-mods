# enrichment-gseapy

本地富集分析：把一列基因（或一张排序表）变成富集结果表 + 统计量 + 摘要。
`gseapy` 1.3.1 已随 figkit 装好，**这个 mod 不需要安装任何东西**，装的是方法与模板。

## 什么时候用它

- 已经有一列差异基因（或任意感兴趣的基因），想问「它们富集在哪些通路/功能上」；
- 想按 log2FC 排序做 GSEA，而不是先切一个阈值（切阈值会引入选择偏倚）；
- 不想依赖联网的 Enrichr API，也不想装 R 注释库。

## 两种模式

| 模式 | 函数 | 输入 | 什么时候用 |
|---|---|---|---|
| **ORA** | `gseapy.enrich` | 基因列表 + 背景大小 | 已有明确阈值筛出的基因 |
| **GSEA** | `gseapy.prerank` | 全基因排序表（`gene`,`score`） | 不想切阈值 / 要看整体趋势 |

`gseapy.enrichr` 是联网版（走 Enrichr 网站），**离线环境别用**。

## 调用块（实测，gseapy 1.3.1）

```python
import gseapy as gp

gene_sets = gp.read_gmt("h.all.v2023.2.Hs.symbols.gmt")   # 本地 GMT
res = gp.enrich(
    gene_list=genes,             # list[str]
    gene_sets=gene_sets,         # dict 或 GMT 路径
    background=20000,            # 背景基因数，或背景基因 list
    outdir=None,                 # 不落盘，自己接管输出
)
df = res.results                 # 列见下
```

输出列：`Gene_set` / `Term` / `Overlap` / `P-value` / `Adjusted P-value` / `Odds Ratio` / `Combined Score` / `Genes`。

## 三个必须注意的点

1. **背景一定要显式给**。不给就默认用基因集大小当背景，p 值会系统性偏小，
   这是富集分析里最常见的假显著来源。
2. **基因 ID 必须与基因集同一种**。GMT 是 symbol 就用 symbol，是 Ensembl 就先转，
   混用会得到「零富集」而不是报错 —— 静默错误最难查。
3. **FDR 不是 p 值**。报告里写 `Adjusted P-value`，并且说清用的是哪个阈值。

## 模板：`templates/ora.py`

```bash
{root}/envs/figkit/Scripts/python.exe templates/ora.py \
  --genes sig_genes.txt \
  --sets h.all.v2023.2.Hs.symbols.gmt \
  --background 20000 \
  --out results
```

产出（结果契约三件套）：`results/enrichment.tsv`、`results/stats.json`、`results/analysis.md`。

## 已验证

`gp.enrich` 离线跑通（1.3.1），返回上述 8 列；模板在同一环境实跑通过。
未验证：`prerank` 的 GSEA 曲线（需要真实排序表，逻辑同上，先读结果表再谈图）。
