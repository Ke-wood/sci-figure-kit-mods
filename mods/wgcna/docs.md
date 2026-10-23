# WGCNA

加权基因共表达网络分析：把基因按表达相关性聚成模块，再看模块与性状的关系。

## 什么时候用它

- 有 **≥ 15 个样本**的表达矩阵，想找协同变化的基因群（模块）；
- 想问「哪个模块与我的临床性状/处理相关」，并从中挑枢纽基因；
- 作为差异表达的补充：DE 看单个基因，WGCNA 看基因群。

样本太少（< 15）时模块划分很不稳，结论别当真。

## 调用块

```r
suppressMessages(library(WGCNA))
options(stringsAsFactors = FALSE)

# 输入：行 = 样本，列 = 基因（建议先 vst / log 归一化，别用原始 counts）
datExpr <- as.data.frame(t(expr_matrix))

# 1 离群样本（先看，别急着删）
gsg <- goodSamplesGenes(datExpr, verbose = 0)
if (!gsg$allOK) datExpr <- datExpr[gsg$goodSamples, gsg$goodGenes]

# 2 软阈值
sft <- pickSoftThreshold(datExpr, powerVector = c(1:10, 12, 14), networkType = "signed")
power <- sft$powerEstimate

# 3 模块
net <- blockwiseModules(datExpr, power = power, networkType = "signed",
                        TOMType = "signed", minModuleSize = 30,
                        mergeCutHeight = 0.25, numericLabels = TRUE,
                        saveTOMs = FALSE, verbose = 0)

# 4 模块-性状关联
MEs <- moduleEigengenes(datExpr, net$colors)$eigengenes
cor <- cor(MEs, traits, use = "p")
p <- corPvalueStudent(cor, nSamples = nrow(datExpr))
write.table(cor, "results/module_trait_cor.tsv", sep = "\t")
write.table(p,   "results/module_trait_p.tsv",   sep = "\t")
```

## 坑

| 坑 | 现象 | 正解 |
|---|---|---|
| 用原始 counts | 模块被文库大小主导 | 先 vst / logCPM |
| `powerEstimate` 是 NA | 样本/基因太少，无标度拓扑没达成 | 手动指定（如 12）并在报告里写明 |
| 未过滤低表达基因 | 内存爆、模块噪声大 | 先保留表达 > 阈值的基因（常留 5000–15000） |
| 直接删离群样本 | 结果不可复现 | 先记录、再决定，样本处理写进 `analysis.md` |

## 输出

`net$colors`（基因→模块）、`MEs`（模块特征值）、模块-性状相关矩阵与 p 值。
结果契约：`results/modules.tsv`、`results/module_trait_cor.tsv`、`stats.json`、`analysis.md`。

## 安装

CRAN 包：`mod.py install wgcna --yes`（走 `install.packages`，Windows 二进制）。
**状态**：本机尚未安装；清单与调用块按官方 API 写。
