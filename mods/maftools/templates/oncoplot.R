#!/usr/bin/env Rscript
# 突变景观：MAF -> oncoplot（突变瀑布）+ 基因突变汇总表
#
# 输入：MAF 文件（Mutation Annotation Format）
# 用法：
#   Rscript oncoplot.R --maf mutations.maf --out results [--top 20]
# 产物：
#   results/oncoplot.pdf / .png     突变瀑布图
#   results/gene_summary.csv        各基因突变样本数与突变类型
#   results/sample_summary.csv      各样本突变数（突变负荷）
#
# 真实 API（maftools 2.28.0 实测）：
#   maf <- read.maf(maf = "x.maf")            # 也可 clinicalData=
#   oncoplot(maf, top = 20)                   # 突变瀑布
#   getGeneSummary(maf) / getSampleSummary(maf)

suppressMessages(library(maftools))

args <- commandArgs(trailingOnly = TRUE)
getarg <- function(name, default = NULL) {
  i <- match(name, args)
  if (is.na(i) || i == length(args)) return(default)
  args[i + 1]
}
maf_path <- getarg("--maf")
out_dir <- getarg("--out", "results")
top_n <- as.integer(getarg("--top", "20"))
if (is.null(maf_path)) stop("缺少 --maf")
if (!file.exists(maf_path)) stop(sprintf("找不到 MAF：%s", maf_path))

dir.create(out_dir, showWarnings = FALSE, recursive = TRUE)

# read.maf 读 .gz 需要有 R.utils；这里用 base R 分块解压，避免额外依赖。
maf_read <- maf_path
if (grepl("\\.gz$", maf_path, ignore.case = TRUE)) {
  tmp <- tempfile(fileext = ".maf")
  ci <- gzfile(maf_path, "rb"); co <- file(tmp, "wb")
  repeat {
    chunk <- readBin(ci, "raw", 65536L)
    if (length(chunk) == 0L) break
    writeBin(chunk, co)
  }
  close(ci); close(co)
  maf_read <- tmp
}

maf <- read.maf(maf = maf_read, verbose = FALSE)
cat(sprintf("样本数=%d  基因数(有突变)=%d\n", length(unique(maf@data$Tumor_Sample_Barcode)),
            length(unique(maf@data$Hugo_Symbol))))

# 基因与样本汇总
gs <- getGeneSummary(maf)
ss <- getSampleSummary(maf)
write.csv(gs, file.path(out_dir, "gene_summary.csv"), row.names = FALSE)
write.csv(ss, file.path(out_dir, "sample_summary.csv"), row.names = FALSE)

# oncoplot（突变瀑布）
pdf(file.path(out_dir, "oncoplot.pdf"), width = 12, height = 8)
oncoplot(maf = maf, top = top_n)
dev.off()
png(file.path(out_dir, "oncoplot.png"), width = 1800, height = 1200, res = 150)
oncoplot(maf = maf, top = top_n)
dev.off()

cat("Top 突变基因:\n")
print(head(gs[, c("Hugo_Symbol", "MutatedSamples")], top_n))
cat("产物目录:", out_dir, "\n")
