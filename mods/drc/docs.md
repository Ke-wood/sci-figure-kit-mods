# drc

剂量-反应曲线拟合：4 参数/3 参数 logistic、hormesis（Brian-Cousens）、
ED10/50/90 与置信区间、多条曲线参数比较。

## 什么时候用它

- 急性毒性要 **LC50/EC50 的置信区间**（比 probit 更常用 log-logistic）；
- 低剂量刺激（hormesis）——U 形或双相曲线；
- 同一物质不同处理组（温度、pH、物种）的 EC50 是否有差异。

## 模型选择

| 函数 | 形状 | 什么时候用 |
|---|---|---|
| `LL.4()` | 4 参数 log-logistic（上下渐近线） | 默认，响应有明确上下限 |
| `LL.3()` | 3 参数（下渐近线固定 0） | 抑制率从 0 起 |
| `BC.5()` | Brian-Cousens | 有 hormesis（低剂量低于对照） |
| `W1.4()` | Weibull | 不对称曲线 |

**选模型看 AIC，不看 R²**；R² 对非线性模型没有可比性。

## 调用

```r
library(drc)
m  <- drm(resp ~ conc, data = d, fct = LL.4())
ED(m, c(10, 50, 90), interval = "delta", type = "relative")
```

`interval = "delta"` 是 delta 法置信区间（快、常用）；要 profile 似然就写 `"fls"`。

## 模板：`templates/dose_response.R`

```powershell
& '{root}/R/bin/Rscript.exe' "<skill>/mods/drc/templates/dose_response.R" `
    --data dose.csv --out results --model LL.4
```

产物：`ed50.csv`、`params.csv`、`dose_response.png`、`stats.json`。

## 实测（2026-10-24）

5 个浓度 × 3 重复，LL.4：

```
ED10 = 0.111  (0.052 – 0.170)
ED50 = 1.216  (0.955 – 1.476)
ED90 = 13.27  (5.48 – 21.06)
```

## 坑

| 坑 | 现象 | 正解 |
|---|---|---|
| 数据不是"每浓度一组重复" | `Convergence failed` | 长表：每个浓度多行，别把所有响应混在一起 |
| 响应是原始 OD 而不是抑制率 | 上下渐近线不成立 | 先换算成相对抑制率/死亡率（%） |
| 只看 R² 选模型 | 4 参数模型过拟合 | 比 AIC；参数不可解释就退回 LL.3 |
| 浓度跨 0 | log 轴报错 | 浓度 > 0；0 剂量当对照单独处理 |

## 与 ssdtools 的分工

单个物种、单个物质的 EC50 → 本 mod；多个物种的毒性值分布 → `ssdtools`（HC5/PNEC）。
