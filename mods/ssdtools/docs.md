# ssdtools

物种敏感度分布（Species Sensitivity Distribution, SSD）：用一组物种的毒性值拟合分布，
取第 5 百分位 **HC5**，除以评估因子得到 **PNEC**。生态风险评估的标准交付物。

## 什么时候用它

- 有 ≥ 5 个物种的急性/慢性毒性值（LC50 / EC50 / NOEC），要给"保护 95% 物种"的浓度；
- 写风险评估章节，需要 HC5 的置信区间；
- 要一张 SSD 曲线图（物种累积概率 vs 浓度）。

输入是**同一物质、同一终点、同一单位**的毒性值。混急性与慢性、混 mg/L 与 μg/L 是最常见的错。

## 调用

```r
library(ssdtools)

d <- read.csv("toxicity.csv")          # 必须有 Conc 列（大写 C）
fit <- ssd_fit_dists(d, dists = c("lnorm", "llogis", "gamma", "burrIII3"))
hc  <- ssd_hc(fit, proportion = 0.05, ci = TRUE, nboot = 1000)
```

`dists` 用多个分布时 `ssd_hc` 给的是 **AIC 加权平均**（`dist = "average"`），
这也是推荐做法；只给一个分布就是单模型估计。

## 模板：`templates/ssd_hc5.R`

```powershell
& '{root}/R/bin/Rscript.exe' "<skill>/mods/ssdtools/templates/ssd_hc5.R" `
    --data toxicity.csv --out results --af 10
```

产物：`hc5.csv`（各分布 + 加权）、`pnec.csv`、`ssd.png`、`stats.json`。

## 实测（2026-10-24）

8 个物种、4 个分布加权：

```
HC5  = 0.5237 mg/L  (95% CI 0.1724 – 1.3619)
PNEC = 0.0524 mg/L  (AF = 10)
```

## 坑

| 坑 | 现象 | 正解 |
|---|---|---|
| 列名写成 `conc` | `names(data) must include 'Conc'` | 第一列必须是 `Conc` |
| 直接把 `ssd_hc()` 结果 `write.csv` | `unimplemented type 'list'` | 结果是 tibble，含 `dists` / `samples` 两个 list 列，先剔除 |
| 物种太少 | HC5 的 CI 极宽甚至算不出 | ≥ 5 个物种仅能作探索；正式评估建议 ≥ 10 |
| 单位不统一 | HC5 差 1000 倍 | 全部换算成 mg/L 再进模型 |
| 评估因子乱取 | PNEC 不可比 | 按法规：急性 AF=1000、慢性 AF=10–100，写进报告 |

## 与别的 mod 的分工

- 单个物种的 LC50/EC50 与置信区间 → `drc` 或 `spss`（probit）；
- 多物种分布 → 本 mod；
- 混合物毒性（CA/IA）→ 用 `drc` 拟合各组后自己算 TU 和（见 docs 的说明）。
