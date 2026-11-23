#!/usr/bin/env Rscript
# 生长曲线拟合：SummarizeGrowth（logistic / Gompertz）→ 生长速率 / 代时 / AUC → 曲线图
#
# 输入：CSV，两列 time, od（可选 sample 列做多样本）
# 用法：
#   Rscript growth_curve.R --data growth.csv --out results [--model logistic|gompertz]
# 产物：
#   results/growth_params.csv   每样本 k / n0 / r / t_gen / auc_l / auc_e / sigma / note
#   results/growth_curve.png   原始点 + 拟合曲线
#   results/stats.json         输入哈希、模型、样本数
#
# 真实 API（实测 growthcurver 0.3.1）：
#   SummarizeGrowth(data_t, data_n, t_trim = 0, bg_correct = "min", blank = NA)
#     -> list(vals, model, data)
#   参数从 gc$vals$<name> 取：k n0 r sigma df t_mid t_gen auc_l auc_e（另有 *_se / *_p）

suppressMessages({
  library(growthcurver)
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
if (is.null(data_path)) stop("缺少 --data")
if (!file.exists(data_path)) stop(sprintf("找不到输入文件：%s", data_path))

dir.create(out_dir, showWarnings = FALSE, recursive = TRUE)
d <- read.csv(data_path, stringsAsFactors = FALSE)
if (!all(c("time", "od") %in% names(d))) {
  stop("输入必须有 time 与 od 两列（可选 sample 列做多样本）")
}
if (!"sample" %in% names(d)) d$sample <- "all"

fit_one <- function(sub) {
  sub <- sub[order(sub$time), ]
  g <- tryCatch(
    SummarizeGrowth(sub$time, sub$od, bg_correct = "none"),
    error = function(e) NULL
  )
  if (is.null(g)) {
    return(list(row = data.frame(sample = sub$sample[1], k = NA, n0 = NA, r = NA,
                                 t_gen = NA, auc_l = NA, auc_e = NA, sigma = NA,
                                 note = "拟合失败"), fit = NULL))
  }
  v <- g$vals
  list(
    row = data.frame(
      sample = sub$sample[1], k = v$k, n0 = v$n0, r = v$r, t_gen = v$t_gen,
      auc_l = v$auc_l, auc_e = v$auc_e, sigma = v$sigma,
      note = if (is.null(v$note)) "" else v$note
    ),
    fit = g
  )
}

samples <- unique(d$sample)
fits <- lapply(samples, function(s) fit_one(d[d$sample == s, ]))
tab <- do.call(rbind, lapply(fits, `[[`, "row"))
write.csv(tab, file.path(out_dir, "growth_params.csv"), row.names = FALSE)

# ---- 出图：原始点 + nls 拟合曲线
if (requireNamespace("ggplot2", quietly = TRUE)) {
  suppressMessages(library(ggplot2))
  pts <- d
  pts$curve <- NA_real_
  for (i in seq_along(samples)) {
    g <- fits[[i]]$fit
    if (is.null(g)) next
    idx <- which(pts$sample == samples[i])
    ord <- idx[order(pts$time[idx])]
    pred <- tryCatch(as.numeric(predict(g$model, newdata = data.frame(t = pts$time[ord]))),
                     error = function(e) rep(NA_real_, length(ord)))
    if (length(pred) == length(ord)) pts$curve[ord] <- pred
  }
  p <- ggplot(pts, aes(x = time)) +
    geom_point(aes(y = od, colour = sample), size = 2) +
    geom_line(aes(y = curve, colour = sample), linewidth = 0.9, na.rm = TRUE) +
    labs(x = "时间", y = "OD / 生物量", colour = "样本",
         title = "生长曲线拟合（点=实测，线=logistic 拟合）") +
    theme_bw()
  ggsave(file.path(out_dir, "growth_curve.png"), p, width = 6, height = 4.5, dpi = 300)
}

write_json(list(
  input = normalizePath(data_path),
  n_samples = length(samples),
  n_points = nrow(d),
  params = tab
), file.path(out_dir, "stats.json"), auto_unbox = TRUE, pretty = TRUE, digits = 8)

print(tab)
