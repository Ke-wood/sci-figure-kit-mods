#!/usr/bin/env Rscript
# 物种敏感度分布（SSD）→ HC5 → PNEC
#
# 输入：CSV，两列 —— species, Conc（列名必须是 Conc，ssdtools 强制）
# 用法：
#   Rscript ssd_hc5.R --data toxicity.csv --out results --af 10
# 产物：
#   results/hc5.csv      各分布的 HC5 与模型加权结果
#   results/pnec.csv     PNEC = HC5 / 评估因子
#   results/ssd.png      SSD 曲线（叠加 HC5）
#   results/stats.json   输入哈希、分布集、样本量

suppressMessages({
  library(ssdtools)
  library(ggplot2)
  library(jsonlite)
})

args <- commandArgs(trailingOnly = TRUE)
getarg <- function(name, default = NULL) {
  i <- match(name, args)
  if (is.na(i) || i == length(args)) return(default)
  args[i + 1]
}

data_path <- getarg("--data")
out_dir <- getarg("--out", "results")
af <- as.numeric(getarg("--af", "10"))
dists <- strsplit(getarg("--dists", "lnorm,llogis,gamma,burrIII3"), ",")[[1]]
if (is.null(data_path)) stop("缺少 --data")

dir.create(out_dir, showWarnings = FALSE, recursive = TRUE)
d <- read.csv(data_path)
if (!"Conc" %in% names(d)) stop("输入必须有 Conc 列（大小写敏感）")

fit <- ssd_fit_dists(d, dists = dists)
hc <- ssd_hc(fit, proportion = 0.05, ci = TRUE, nboot = 1000)

hc_df <- as.data.frame(hc)
hc_df <- hc_df[, !vapply(hc_df, is.list, logical(1)), drop = FALSE]  # dists/samples 是 list 列
write.csv(hc_df, file.path(out_dir, "hc5.csv"), row.names = FALSE)

hc5 <- hc$est[hc$dist == "average"][1]
pnec <- hc5 / af
write.csv(data.frame(hc5 = hc5, af = af, pnec = pnec),
          file.path(out_dir, "pnec.csv"), row.names = FALSE)

p <- autoplot(fit) +
  labs(title = NULL, x = "浓度 (mg/L)", y = "受影响物种比例") +
  theme_classic(base_size = 8) +
  theme(legend.position = "right")
ggsave(file.path(out_dir, "ssd.png"), p, width = 120, height = 80,
       units = "mm", dpi = 300, device = ragg::agg_png)

write_json(list(
  input = normalizePath(data_path),
  n_species = nrow(d),
  dists = dists,
  hc5 = hc5,
  pnec = pnec,
  assessment_factor = af,
  ci = list(lcl = hc$lcl[hc$dist == "average"][1],
            ucl = hc$ucl[hc$dist == "average"][1])
), file.path(out_dir, "stats.json"), auto_unbox = TRUE, pretty = TRUE)

cat(sprintf("HC5 = %.4f mg/L  (95%% CI %.4f - %.4f)\nPNEC = %.4f mg/L (AF=%g)\n",
            hc5, hc$lcl[hc$dist == "average"][1], hc$ucl[hc$dist == "average"][1], pnec, af))
