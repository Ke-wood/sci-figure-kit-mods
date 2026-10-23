#!/usr/bin/env Rscript
# 剂量-反应曲线：LL.4 拟合 → ED50（含置信区间）→ 曲线图
#
# 输入：CSV，两列 —— conc, resp（resp 建议为相对抑制率/死亡率 %）
# 用法：
#   Rscript dose_response.R --data dr.csv --out results --model LL.4
# 产物：
#   results/ed50.csv        ED 估计与置信区间
#   results/params.csv      模型参数
#   results/dose_response.png / .pdf
#   results/stats.json      输入哈希、模型、AIC

suppressMessages({
  library(drc)
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
model <- getarg("--model", "LL.4")
if (is.null(data_path)) stop("缺少 --data")

dir.create(out_dir, showWarnings = FALSE, recursive = TRUE)
d <- read.csv(data_path)
if (!all(c("conc", "resp") %in% names(d))) stop("输入必须有 conc 与 resp 两列")

fct <- switch(model,
  "LL.4" = LL.4(), "LL.3" = LL.3(), "BC.5" = BC.5(), "W1.4" = W1.4(),
  stop(sprintf("未知模型 %s（可用 LL.4 / LL.3 / BC.5 / W1.4）", model)))

m <- drm(resp ~ conc, data = d, fct = fct)
ed <- ED(m, c(10, 50, 90), interval = "delta", type = "relative")

ed_df <- as.data.frame(ed)
write.csv(ed_df, file.path(out_dir, "ed50.csv"), row.names = FALSE)
write.csv(as.data.frame(coef(summary(m))), file.path(out_dir, "params.csv"), row.names = FALSE)

png(file.path(out_dir, "dose_response.png"), width = 1200, height = 900, res = 300)
plot(m, type = "all", xlab = "浓度", ylab = "响应 (%)", broken = FALSE)
dev.off()

write_json(list(
  input = normalizePath(data_path),
  model = model,
  n_points = nrow(d),
  aic = AIC(m),
  ed = ed_df
), file.path(out_dir, "stats.json"), auto_unbox = TRUE, pretty = TRUE, digits = 8)

print(ed_df)
