# prism

用本机 **GraphPad Prism**（`{root}/prism/prism.exe`，10.6.1）做统计分析。
**只出数，不出图** —— 图的样子是二进制、脚本改不了，出图交给 cnsplots / ggplot2 更舒服。

这个 mod 不含 Prism 本体，只给调用方式与纪律。

## 什么时候用它

| 场景 | 为什么是 Prism |
|---|---|
| 单因素 ANOVA + **Tukey / Dunnett / Dunn** | SPSS 27 拿不到这三个（`ADJ()` 只有 Bonferroni/LSD/Šidák） |
| 要**显著性字母**（CLD） | 全配对设计下 Prism 直接给每组字母，Python 侧要自己实现 Piepho |
| t 检验 / 线性回归 / 剂量反应（EC50） | 曲线拟合与参数置信区间是 Prism 的强项 |
| 已有 `.prism` 模板，换数据重跑 | 参数锁在模板 JSON 里，换行数不用改 |

**不该用它**：LC50/probit（Prism 不做）、混合模型（11 之前没有）→ 走 `spss` mod。

## 接口盘点（2026-10-24 实测）

| 接口 | 结论 |
|---|---|
| **`.pzc` 脚本** | ✅ 唯一可用：`prism.exe @job.pzc` |
| **工程文件** | ✅ `.prism` = zip + JSON（数据表、参数、`results.json` 全可读） |
| **COM / OLE** | ❌ 没有 `IDispatch` / TypeLib，`Prism.Command` 的 `LocalServer32` 是空的 |
| **命令行** | 只认 `@脚本`，没有 `--script` 之类 |

## 调用链（已实测）

```
.prism 模板 ──prism_analyze.py──> Import CSV → RecalcAll → Save
                                          └─> 解包 out.prism → results.json
                                              └─> anova.csv / posthoc.csv / letters.csv
```

```powershell
python "<skill>/mods/prism/templates/prism_analyze.py" `
    --template oneway.prism --data panel.csv --out results
```

- `--data` 是**宽表 CSV，不要表头**：行 = 重复，列 = 组，列数必须等于模板数据表的列数；
- 产物：`anova.csv`、`posthoc.csv`、`letters.csv`、`results.json`（原始权威）、`stats.json`（输入哈希）；
- 一次约 4 秒。

## 模板怎么做（1 分钟）

1. Prism → New Project → **Column**（回归用 XY）
2. 把数据表减到**正好**要用的列数（Prism 默认给 12 列），填占位值 `11.11 / 22.22 / 33.33…`
3. **Analyze** → 选分析（如 One-way ANOVA → Multiple comparisons → Dunnett）
4. **Save As → `.prism`**

**不需要建图。** 一张表 + 一个分析就够——这正是"Prism 只负责分析"之后省下的那步。

## results.json 长什么样

```
content.ordinaryAnovaModel
├── anovaTable.colFactor.{ss, df, ms, fTest{f, dfNumerator, dfDenominator, pValue}}
├── multipleComparisons.{method, comparisonCount, significantCount, tests{uid→uid→{meansDifference, CI, pValueAdjusted}}}
├── compactLetterDisplay.{letterCount, samples{uid→{id.col.idx, value:"A B"}}}
└── descriptiveStatistics{uid→...}
```

`tests` 是 uid 套 uid 的嵌套字典，按 `sample1/sample2.id.col.idx` 还原组号 ——
`prism_analyze.py` 里的 `walk_pairs()` 就是干这个的。

## 实测结论（2026-10-24）

模板 `Project1.prism`（7 组 one-way ANOVA + Tukey），喂 6×7 的已知数据：

| 项 | Prism | scipy / statsmodels |
|---|---|---|
| F | 69.9999999999999 | 70.000000 |
| p | 4.9722743225397346e-18 | 4.97227e-18 |
| df | 6 / 35 | 6 / 35 |
| A–B 均值差 | -2.0 | -2.0 |
| A–B 校正 p | 7.2236e-05 | 0.0001 |
| A–B 95% CI | [-3.1414, -0.8586] | [-3.1414, -0.8586] |
| CLD 字母 | F, D E, B C, A, E F, C D, A B | — |

显著性计数 15/21 与 statsmodels 的 `reject` 数一致。

## 坑（都踩过）

| 坑 | 现象 | 正解 |
|---|---|---|
| **`@` 后的脚本路径用正斜杠** | Prism 弹「文件无法打开」，随后**静默退出 rc=0**，什么都没做 | 传 `os.path.normpath(script)`（反斜杠） |
| 脚本里有错命令 | 模态框 → 永久挂死 | 先静态检查（Exit / SaveAs / GoTo R），超时 `taskkill` |
| 脚本改数据后不保存就退出 | 弹「是否保存」→ 挂死 | 以 `Exit` 结尾 |
| 路径含中文 | 启动即失败 | 工作目录与脚本路径全 ASCII；`.pzc` 按 GBK 写 |
| `GoTo R n` | 编号推不出来，某些 view 报 `No such sheet!` 并挂死 | 不碰结果视图，直接读 `results.json` |

## 其他脚本

`templates/prism_run.py`：只跑一个现成的 `.pzc`（带静态检查、GBK 落盘、超时强杀、产物清单）。
需要"脚本里干别的事"（批量、导出数据表）时用它。
