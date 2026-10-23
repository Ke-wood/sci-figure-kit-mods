# clusterProfiler

R 生态的富集标准件：GO / KEGG 的 ORA 与 GSEA，配 `enrichplot` 直接出图。

## 什么时候用它

- 已经用 limma / pydeseq2 拿到了基因列表或排序表，要在 R 里做富集；
- 需要 **GO 三个本体分开**（BP/CC/MF）或 KEGG 通路编号；
- 想要 `dotplot` / `ridgeplot` / `cnetplot` 这类现成图。

只用 Python 的话，`enrichment-gseapy` 更轻，不用装注释库。

## 前置：注释库（必须先装）

`enrichGO` 本身不含基因-本体映射，必须有物种注释库：

| 物种 | 包 |
|---|---|
| 人 | `org.Hs.eg.db` |
| 鼠 | `org.Mm.eg.db` |
| 其他 | `AnnotationHub` 或对应 `org.*.eg.db` |

它们也是 R 包，用同一套 mod 机制装：`type=rpkg, env=r, install.pkg=org.Hs.eg.db`。
没装就调用会报 `there is no package called 'org.Hs.eg.db'`。

## 调用块

```r
suppressMessages({library(clusterProfiler); library(org.Hs.eg.db)})

# ORA：基因列表 + 背景（universe）
ego <- enrichGO(gene = genes, OrgDb = org.Hs.eg.db, keyType = "SYMBOL",
                ont = "BP", pAdjustMethod = "BH",
                pvalueCutoff = 0.05, qvalueCutoff = 0.2,
                universe = background_genes, readable = TRUE)

# KEGG（需要联网取通路定义，或预存 KEGG 数据）
ekk <- enrichKEGG(gene = entrez_ids, organism = "hsa", universe = background_entrez)

# GSEA：排序表（不要切阈值）
gse <- gseGO(geneList = sorted_named_vector, OrgDb = org.Hs.eg.db,
             ont = "BP", minGSSize = 10, pvalueCutoff = 0.05)

write.table(as.data.frame(ego), "results/go_bp.tsv", sep = "\t", quote = FALSE)
```

## 坑

| 坑 | 现象 | 正解 |
|---|---|---|
| 没装注释库 | `there is no package called 'org.Hs.eg.db'` | 先装注释库 mod |
| ID 类型不匹配 | 结果为空但不报错 | `keyType` 与输入一致；SYMBOL 转 ENTREZ 用 `bitr()` |
| KEGG 联网失败 | `enrichKEGG` 卡住/报错 | 用 `download_KEGG` 预存，或改走 gseapy |
| 没给 universe | 结果偏乐观 | 显式传背景基因集 |

## 输出

`enrichResult` 转 `data.frame` 后有 `ID` / `Description` / `GeneRatio` / `BgRatio` /
`pvalue` / `p.adjust` / `qvalue` / `geneID` / `Count`。结果契约照旧：
`results/*.tsv` + `stats.json` + `analysis.md`。

## 安装

Bioconductor 包，依赖较重（AnnotationDbi / DOSE / GOSemSim / enrichplot），
首次安装 5–10 分钟。`mod.py install clusterprofiler --yes` 会自动转 BiocManager。

**状态**：本机尚未安装；清单与调用块按官方 API 写。
