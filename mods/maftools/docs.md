# maftools

> 突变景观分析 mod。封装 Bioconductor `maftools`（2.28.0，MIT）。

## 用途

读 MAF（Mutation Annotation Format），出肿瘤/基因组方向的专用图：

- **oncoplot（突变瀑布图）**：各样本 × 基因的突变矩阵 + 顶部突变负荷（TMB）+ 突变类型色块
- **coOncoplot**：分组并排对比两个队列
- **lollipopPlot**：把突变标在蛋白结构域上（驱动基因常用）
- **rainfallPlot**：突变谱雨点图
- **TiTv / 突变负荷 / 突变谱**：`titv` / `mafSummary` / `trinucleotideMatrix`

## 实测调用（maftools 2.28.0，2026-11-23 本机 R 4.6.1 实跑）

```r
library(maftools)
maf <- read.maf(maf = "mutations.maf")        # 可加 clinicalData=
oncoplot(maf, top = 20)                        # 突变瀑布
lollipopPlot(maf, gene = "TP53")               # 蛋白域突变
getGeneSummary(maf)                            # 各基因突变样本数
getSampleSummary(maf)                          # 各样本突变数（突变负荷）
```

> 坑：`read.maf` 直接读 **.gz** 需要 `R.utils` 包（本机未装）。模板用 base R 分块解压后再读，
> 不依赖 R.utils；你自己写脚本时要么先解压，要么装 R.utils。

## 本机实测输出（maftools 自带 tcga_laml.maf.gz）

- 样本 192，有突变基因 1241
- Top 突变基因（`MutatedSamples`）：FLT3 52、DNMT3A 48、NPM1 33、IDH2 20、IDH1 18、TET2 17、RUNX1 16、TP53 15…
- 与 TCGA-LAML 已知突变格局一致 → 证明接口通

产物：`oncoplot.pdf` / `oncoplot.png` / `gene_summary.csv` / `sample_summary.csv`。

## 模板

`templates/oncoplot.R`：MAF → oncoplot + 基因/样本汇总表。

```bash
Rscript templates/oncoplot.R --maf mutations.maf --out results --top 20
```

## 注意事项

- 输入必须是 **MAF**；VCF 要先转 MAF（`maftools` 的 vcf2maf 或外部工具）。
- 基因太多 oncoplot 会糊，`--top` 控制行数。
- 纯 R + Bioc 二进制，Windows 无需编译器。
- 与 ComplexHeatmap `oncoPrint()` 的分工：oncoPrint 只画矩阵，maftools 会解析 MAF（突变类型、临床注释、TMB 全带）。

## 回退

`ComplexHeatmap::oncoPrint()`（需自己把 MAF 整理成矩阵）。
