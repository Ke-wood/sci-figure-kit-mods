# rms（临床预测模型：nomogram + 校准曲线）

> 临床预测模型可视化 mod。封装 CRAN `rms`（8.2-1，`GPL (>= 2)`）。

## 用途

把多因素回归模型变成临床可用的工具与评估图：

- **nomogram（列线图）**：各变量打分 → 总分 → 预测概率/生存率（临床评分表的图形化）
- **校准曲线（calibration）**：观测 vs 预测，判断模型准不准、有没有过拟合
- **系数 / HR（OR）表**：`cph`（Cox）/ `lrm`（logistic）的规范系数与置信区间

## 实测调用（rms 8.2-1，2026-11-23 本机 R 4.6.1 实跑）

```r
library(rms); library(survival)
dd <- datadist(mydata); options(datadist = "dd")          # 必须先设 datadist
f  <- cph(Surv(time, status) ~ age + sex + ph.ecog + wt.loss,
          data = mydata, x = TRUE, y = TRUE, surv = TRUE, time.inc = 180)

sf  <- Survival(f)                                        # 线性预测子 -> 生存概率
nom <- nomogram(f, fun = list(function(x) sf(180, x)),     # 含"180 天生存率"刻度
                fun.at = c(.95,.9,.8,.7,.5,.3,.1,.05),
                funlabel = "180 天生存率")
plot(nom)

cal <- calibrate(f, u = 180, method = "boot", B = 200)     # 校准曲线
plot(cal)
```

> 两个必踩的坑（实测）：
> 1. 不先 `datadist()` + `options(datadist="dd")`，`nomogram`/`calibrate` 直接报错。
> 2. 生存概率刻度要用 `Survival(f)` 映射：`fun=list(function(x) sf(u, x))`；
>    随便写 lambda 会报 `'x' and 'y' lengths differ`。`calibrate` 要显式给 `u=`。

## 本机实测输出（survival::lung 演示，n=213）

- cph 拟合 n=213
- 列线图含 age/sex/ph.ecog/wt.loss 刻度 + Total Points + 线性预测子 + "180 天生存率"概率刻度
- 校准曲线：`Mean |error| = 0.038`（越接近 0 越准）
- 系数示例：age HR 1.013（每增 1 岁风险 +1.3%）

产物：`nomogram.pdf` / `nomogram.png` / `calibration.pdf` / `calibration.png` / `coef_table.csv`。

## 模板

`templates/nomogram.R`：CSV（time/status/协变量）→ cph → nomogram + calibration + 系数表。

```bash
Rscript templates/nomogram.R --demo --out results
Rscript templates/nomogram.R --data cox.csv --time time --status status \
        --covars age,sex,ph.ecog --u 180 --out results
```

## 注意事项

- **status 约定**：0=删失，1=事件/死亡（survival 也接受 1=删失/2=死亡 的 1/2 编码）。
- 中文标签在默认 `pdf()` 设备上会 `mbcsToSbcs` 转码失败；模板检测 `capabilities("cairo")`，
  有 cairo 就用 `cairo_pdf()` + `png(type="cairo")`，中文正常。
- 纯 R + CRAN 二进制，Windows 无需编译器。
- 校准的 `B`（bootstrap 次数）越大越稳，正式出图建议 ≥200。

## 回退

- 系数表：`survival::coxph` + `broom`。
- 校准：分箱后手算观测 vs 预测。
- KM 曲线美化（风险表）：`survminer`（本机未装，可按需另装）。
