#!/usr/bin/env Rscript
# 临床预测模型可视化：nomogram（列线图，含生存概率）+ 校准曲线
#
# 用法：
#   Rscript nomogram.R --data cox.csv --time time --status status \
#                      --covars age,sex,ph.ecog --u 180 --out results
#   Rscript nomogram.R --demo --out results        # 用 survival::lung 演示
# 产物：
#   results/nomogram.pdf / .png     列线图（含 u 期生存概率刻度）
#   results/calibration.pdf / .png  校准曲线
#   results/coef_table.csv          系数 / HR / 95%CI / p
#
# 真实 API（rms 8.2-1 实测）：
#   dd <- datadist(data); options(datadist="dd")
#   f  <- cph(Surv(time,status) ~ ..., data=data, x=T,y=T,surv=T,time.inc=u)
#   sf <- Survival(f)                          # 线性预测子 -> 生存概率
#   nom <- nomogram(f, fun=list(function(x) sf(u, x)), funlabel="u期生存率")
#   cal <- calibrate(f, u=u, method="boot", B=200)
#
# status 约定：0=删失，1=事件/死亡。（survival 也支持 1=删失/2=死亡 的 1/2 编码）

suppressMessages({library(rms); library(survival)})

# 中文标签在默认 pdf() 设备上会 'mbcsToSbcs' 转码失败；有 cairo 就用 cairo_pdf。
open_pdf <- function(file, width, height) {
  if (capabilities("cairo")) cairo_pdf(file, width = width, height = height)
  else pdf(file, width = width, height = height)
}
open_png <- function(file, width, height, res = 150) {
  if (capabilities("cairo")) png(file, width = width, height = height, res = res, type = "cairo")
  else png(file, width = width, height = height, res = res)
}

args <- commandArgs(trailingOnly = TRUE)
getarg <- function(name, default = NULL) {
  i <- match(name, args)
  if (is.na(i) || i == length(args)) return(default)
  args[i + 1]
}
out_dir <- getarg("--out", "results")
u_time  <- as.numeric(getarg("--u", "180"))
B_boot  <- as.integer(getarg("--boot", "200"))

if ("--demo" %in% args || is.null(getarg("--data"))) {
  data <- survival::lung
  # lung: status 1=删失 2=死亡，转成 0/1 习惯（0=删失,1=事件）
  data$status <- ifelse(data$status == 2, 1, 0)
  time_col <- "time"; status_col <- "status"
  covars <- c("age", "sex", "ph.ecog", "wt.loss")
  tag <- "lung(demo)"
} else {
  data <- read.csv(getarg("--data"), stringsAsFactors = FALSE)
  time_col <- getarg("--time", "time")
  status_col <- getarg("--status", "status")
  cv <- getarg("--covars")
  if (is.null(cv)) stop("缺少 --covars（逗号分隔的协变量列名）")
  covars <- trimws(strsplit(cv, ",")[[1]])
  tag <- basename(getarg("--data"))
}
miss <- setdiff(c(time_col, status_col, covars), names(data))
if (length(miss)) stop(sprintf("数据缺少列：%s", paste(miss, collapse = ", ")))

dir.create(out_dir, showWarnings = FALSE, recursive = TRUE)

dd <- datadist(data[, c(time_col, status_col, covars), drop = FALSE])
options(datadist = "dd")
fml <- as.formula(sprintf("Surv(%s, %s) ~ %s",
                          time_col, status_col, paste(covars, collapse = " + ")))
f <- cph(fml, data = data, x = TRUE, y = TRUE, surv = TRUE, time.inc = u_time)
cat(sprintf("[%s] cph OK, n=%d\n", tag, f$stats[["Obs"]]))

# 系数 / HR 表（自己从 coef/vcov 构造，不依赖 summary() 的内部结构）
b  <- coef(f)
se <- sqrt(diag(vcov(f)))
z  <- b / se
ct <- data.frame(
  term = names(b), coef = b, se = se,
  HR = exp(b), lower95 = exp(b - 1.96 * se), upper95 = exp(b + 1.96 * se),
  z = z, p = 2 * pnorm(-abs(z)), row.names = NULL, check.names = FALSE
)
write.csv(ct, file.path(out_dir, "coef_table.csv"), row.names = FALSE)

# 列线图（含生存概率刻度）
sf <- Survival(f)
nom <- nomogram(f, fun = list(function(x) sf(u_time, x)),
                fun.at = c(.95, .9, .8, .7, .5, .3, .1, .05),
                funlabel = sprintf("%g 天生存率", u_time))
open_pdf(file.path(out_dir, "nomogram.pdf"), width = 10, height = 7); plot(nom); dev.off()
open_png(file.path(out_dir, "nomogram.png"), width = 1500, height = 1050); plot(nom); dev.off()

# 校准曲线
cal <- calibrate(f, u = u_time, method = "boot", B = B_boot)
open_pdf(file.path(out_dir, "calibration.pdf"), width = 7, height = 7); plot(cal); dev.off()
open_png(file.path(out_dir, "calibration.png"), width = 1050, height = 1050); plot(cal); dev.off()

cat("系数表:\n"); print(ct)
cat("产物目录:", out_dir, "\n")
