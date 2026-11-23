# growthcurver

> 生长曲线拟合 mod。封装 CRAN 包 `growthcurver`（0.3.1，`GPL (>= 2)`，Depends R >= 4.0，Imports minpack.lm）。

## 用途

拟合微生物/细胞的生长曲线（默认 logistic，也支持 Gompertz），一次给出：

- **生长速率** `r`
- **代时** `t_gen`
- **AUC**（`auc_l` = 由拟合曲线算的，`auc_e` = 由实测点算的）
- 拟合参数 `k`（承载量）、`n0`（初始量）、`sigma`（残差）与各自的标准误/显著性

与 `drc` 互补：`drc` 处理剂量-抑制（EC50/ED50），`growthcurver` 处理生长表型（速率/代时）。

## 实测调用（growthcurver 0.3.1，2026-11-23 本机 R 4.6.1 实跑）

真实函数签名：

```r
SummarizeGrowth(data_t, data_n, t_trim = 0, bg_correct = "min", blank = NA)
#   data_t 时间向量；data_n 响应向量
#   返回 list(vals, model, data)；参数在 vals 里，model 是 nls 对象
```

```r
library(growthcurver)

gc <- SummarizeGrowth(time_vec, od_vec)   # 单样本
gc$vals$r          # 生长速率
gc$vals$t_gen      # 代时（小时，取决于你时间列的单位）
gc$vals$auc_l      # AUC（拟合曲线积分）
gc$vals$auc_e      # AUC（实测点梯形积分）
as.data.frame(gc$vals)                     # 全部参数一览

# 绘图：gc$data 是 list(t, N)；gc$model 可直接 predict
plot(gc$data$t, gc$data$N, pch = 19)
lines(gc$data$t, predict(gc$model), col = "red")

# 多样本/整块板批量：
SummarizeGrowthByPlate(plate, t_trim = 0, bg_correct = "min",
                       plot_fit = FALSE, plot_file = "growthcurver.pdf")
```

> 注意：**没有** `growthcurver()` 这个函数，也**没有** `e.col/time.col/rep.col` 这类参数。
> 现存唯一入口是 `SummarizeGrowth`（单曲线）与 `SummarizeGrowthByPlate`（批量）。

## 本机实测输出（合成数据，仅证明接口通）

用两样本合成数据（ctrl 与氮限制 nlim）实跑 `templates/growth_curve.R` 得到：

| sample | k | n0 | r | t_gen | auc_l | auc_e | sigma |
|---|---|---|---|---|---|---|---|
| ctrl | 0.946 | 0.020 | 0.397 | 1.748 | 9.791 | 9.820 | 0.0103 |
| nlim | 0.574 | 0.028 | 0.232 | 2.994 | 4.451 | 4.462 | 0.0055 |

方向与生物学一致：氮限制组承载量更低、生长速率更慢、代时更长。**这些是合成示例数值，不是实验结论。**

## 数据要求

- 长表：每行为一个时间点；多样本用 `sample` 列区分。
- 时间列单调；响应列为连续量（光密度、生物量等）。
- 不同处理分开拟合后，用 `growth_params.csv` 汇总做组间比较。

## 模板

`templates/growth_curve.R`：读 CSV（`time, od[, sample]`）→ 逐样本 `SummarizeGrowth` → 输出
`growth_params.csv` / `growth_curve.png` / `stats.json`。

```bash
Rscript templates/growth_curve.R --data growth.csv --out results
```

## 注意事项

- 本 mod 为 CRAN 直装包；上游源码仓库（sprouffske/growthcurver）停更于 2021-12，以 CRAN 版本为维护入口。
- `bg_correct` 默认按每列最小值做背景校正；若已做空白校正，可设 `bg_correct = "none"`。
- 输出数值均来自输入数据；示例请替换为实测值，勿把虚拟数值当结论。
- 中文出图需显式设置字体（SimHei）+ `axes.unicode_minus = FALSE`（模板用 ggplot2 默认主题，中文依赖系统字体）。

## 回退

后端不可用时，可用 Python `scipy.optimize.curve_fit` 自拟合 logistic，并手动换算代时与 AUC（精度与统计量不如 growthcurver）。
