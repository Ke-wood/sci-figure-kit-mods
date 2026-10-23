# limma

线性模型差异表达。微阵列与 RNA-seq 都能用：RNA-seq 走 `voom`，
芯片走 `lmFit` 直接吃 log 表达。

## 什么时候用它

- 数据是**芯片**（已归一化 log 表达）或需要**自定义对比**（多组、配对、协变量）；
- 样本很少（n < 6/组），需要 `eBayes` 的方差收缩来稳住；
- 想用同一套 `design` 矩阵同时回答多个问题（`makeContrasts`）。

**和 pydeseq2 的分工**：原始 counts + 两组比较 → pydeseq2（负二项更合适）；
芯片/已归一化/复杂设计 → limma。别用 limma 跑原始 counts 而不 voom。

## 调用块

```r
suppressMessages(library(limma))

# 芯片：expr 是 log 表达矩阵（行=基因，列=样本）
design <- model.matrix(~ 0 + group, data = meta)
colnames(design) <- levels(factor(meta$group))
fit <- lmFit(expr, design)
contr <- makeContrasts(B - A, levels = design)
fit2 <- eBayes(contrasts.fit(fit, contr))
tt <- topTable(fit2, number = Inf, sort.by = "P")
write.table(tt, "results/de.tsv", sep = "\t", quote = FALSE, col.names = NA)

# RNA-seq counts：v 是 DGEList
v <- voom(dge, design, plot = FALSE)
fit <- lmFit(v, design)
```

## 坑

| 坑 | 现象 | 正解 |
|---|---|---|
| 设计矩阵列名与对比对不上 | `makeContrasts` 报 `non-conformable` | `colnames(design)` 必须是合法变量名，别留 `groupB` 这种默认名 |
| 用了 `topTable` 默认 `number=10` | 结果表只有 10 行 | 显式 `number = Inf` |
| counts 直接 `lmFit` | log2FC 有量纲问题 | 先 `voom`，或换 pydeseq2 |
| 多组比较没设 `ref` | 对比方向反了 | `factor(group, levels = c("A","B"))` 或显式 `makeContrasts` |

## 输出

`topTable` 列：`logFC` / `AveExpr` / `t` / `P.Value` / `adj.P.Val` / `B`。
结果契约：`results/de.tsv` + `results/stats.json`（design 公式、对比、样本量、显著数、输入哈希）+ `results/analysis.md`。

## 安装

Bioconductor 包（CRAN 没有）。`mod.py install limma --yes` 会先试 CRAN，
失败自动转 `BiocManager::install`，装到 `{root}/R/library`。

**状态**：本机尚未安装（清单与调用块已按官方 API 写）。首次安装建议先 `--dry-run` 看计划。
