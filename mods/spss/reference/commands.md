# SPSS 命令能力表（Statistics 27）

**权威定义**：本机 `{root}/spss/syntax_xml/<命令>.xml`，共 **328 条命令**的完整语法规格。
下表是常用子集与**语法骨架**（参数大小写不敏感；`/` 开子命令）。以 XSD 为准，骨架仅供起手。

## 描述与探索

| 命令 | 用途 | 骨架 |
|---|---|---|
| `DESCRIPTIVES` | 均值/标准差/极值 | `DESCRIPTIVES VARIABLES=y /STATISTICS=MEAN STDDEV MIN MAX.` |
| `FREQUENCIES` | 频数表、条形图 | `FREQUENCIES VARIABLES=g /BARCHART.` |
| `EXAMINE` | 箱线图、正态性检验、离群值 | `EXAMINE VARIABLES=y BY g /PLOT BOXPLOT NPPLOT /STATISTICS DESCRIPTIVES.` |
| `MEANS` | 分组汇总 | `MEANS TABLES=y BY g /CELLS=MEAN COUNT STDDEV.` |
| `CTABLES` | 自定义表（可多层） | `CTABLES /TABLE y BY g /STATISTICS MEAN.` |
| `CODEBOOK` | 数据字典 | `CODEBOOK y g.` |

## 均值比较 / 方差分析

| 命令 | 用途 | 骨架 |
|---|---|---|
| `T-TEST` | 独立/配对/单样本 t | `T-TEST GROUPS=g(1 2) /VARIABLES=y.`；配对 `T-TEST PAIRS=y1 WITH y2.` |
| `ONEWAY` | 单因素 ANOVA | `ONEWAY y BY g /POSTHOC=TUKEY BONFERRONI /STATISTICS DESCRIPTIVES.` |
| `UNIANOVA` | 一般线性模型（含简单效应） | `UNIANOVA y BY a b /METHOD=SSTYPE(3) /EMMEANS=TABLES(a) COMPARE ADJ(BONFERRONI) /PRINT=DESCRIPTIVE ETASQ.` |
| `GLM` | 含协变量的 GLM | `GLM y BY g WITH cov /METHOD=SSTYPE(3) /PRINT=PARAMETER.` |
| `MIXED` | 线性混合模型 | `MIXED y BY time /FIXED=time \| SSTYPE(3) /RANDOM=INTERCEPT \| SUBJECT(id) COVTYPE(VC) /METHOD=REML.` |
| `GENLIN` | 广义线性模型（非正态） | `GENLIN y BY g /MODEL g DISTRIBUTION=GAMMA LINK=LOG.` |
| `GENLINMIXED` | 广义线性混合模型 | `GENLINMIXED /FIELDS TARGET=y /RANDOM USE_INTERCEPT=TRUE SUBJECTS=id.` |
| `MANOVA` | 多因变量方差 | `MANOVA y1 y2 BY g(1 3) /PRINT=CELLINFO.` |
| `VARCOMP` | 方差成分 | `VARCOMP y BY g /METHOD=REML.` |

## 非参数

| 命令 | 用途 | 骨架 |
|---|---|---|
| `NPAR TESTS` | KW / Mann-Whitney / Wilcoxon | `NPAR TESTS /K-W=y BY g(1 4).`；`/M-W=y BY g(1 2).` |
| `NPTESTS` | 非参数检验（新版对话框） | `NPTESTS /INDEPENDENT TEST (y) GROUP (g) /KRUSKAL_WALLIS.` |
| `ROC` | ROC 曲线与 AUC | `ROC y BY g(1) /PLOT=CURVE /PRINT=COORDINATES.` |
| `WEIGHTED KAPPA` / `FLEISS MULTIRATER KAPPA` | 一致性 | `WEIGHTED KAPPA ...` |

## 相关与回归

| 命令 | 用途 | 骨架 |
|---|---|---|
| `CORRELATIONS` | Pearson/Spearman | `CORRELATIONS /VARIABLES=x y /PRINT=TWOTAIL NOSIG.` |
| `PARTIAL CORR` | 偏相关 | `PARTIAL CORR /VARIABLES=x y BY z.` |
| `REGRESSION` | 线性回归 | `REGRESSION /DEPENDENT=y /METHOD=ENTER x1 x2 /STATISTICS=COEFF OUTS R ANOVA.` |
| `LOGISTIC REGRESSION` | 逻辑回归 | `LOGISTIC REGRESSION VARIABLES=y /METHOD=ENTER x /PRINT=CI(95).` |
| `NOMREG` | 多项/有序 logit | `NOMREG y BY g WITH x /PRINT=FIT PARAMETER.` |
| `PROBIT` | **概率单位法 / LC50** | `PROBIT deaths OF total WITH dose /MODEL=PROBIT /PRINT=CI.`（连续剂量用 `WITH`，别用 `BY`；**`/PRINT=CI` 不能省**，见下方「PROBIT 与 OXML」） |
| `NLR` | 非线性回归（剂量反应） | `NLR y /PRED=… /PARAMETERS=… /CRITERIA=…` |
| `CURVEFIT` | 曲线拟合 | `CURVEFIT /VARIABLES=y WITH x /MODEL=LINEAR QUADRATIC.` |
| `QUANTILE REGRESSION` | 分位数回归 | `QUANTILE REGRESSION y WITH x /QUANTILES=0.5.` |
| `2SLS` / `WLS` / `AREG` | 工具变量/加权/自回归 | `2SLS y WITH x1 /INSTRUMENTS=x2.` |
| `COXREG` | Cox 回归 | `COXREG t /STATUS=c(1) /METHOD=ENTER x.` |
| `KM` | Kaplan-Meier | `KM t BY g /STATUS=c(1) /PRINT=TEST.` |

## 降维与分类

| 命令 | 用途 |
|---|---|
| `FACTOR` | 主成分/因子分析（`/EXTRACTION=PC /ROTATION=VARIMAX`） |
| `CLUSTER` / `QUICK CLUSTER` / `TWOSTEP CLUSTER` | 层次/快速/两步聚类 |
| `DISCRIMINANT` | 判别分析 |
| `CATPCA` / `CATREG` / `MULTIPLE CORRESPONDENCE` / `PROXSCAL` | 分类数据降维 |
| `PROXIMITIES` | 距离矩阵 |

## 信度与一致性

| 命令 | 用途 | 骨架 |
|---|---|---|
| `RELIABILITY` | Cronbach α | `RELIABILITY /VARIABLES=i1 i2 i3 /SCALE('ALL') ALL /MODEL=ALPHA.` |
| `WEIGHTED KAPPA` | 加权 kappa | 见 syntax_xml |

## 数据准备

| 命令 | 用途 |
|---|---|
| `GET DATA` | 读 CSV/Excel/SAS/Stata |
| `SAVE` / `SAVE TRANSLATE` | 存 .sav / 导出 xlsx、csv |
| `AGGREGATE` | 分组汇总成新表 |
| `CASESTOVARS` / `VARSTOCASES` | 宽↔长转换 |
| `COMPUTE` / `RECODE` / `IF` / `SELECT IF` | 变量计算与筛选 |
| `SORT CASES` / `SPLIT FILE` / `WEIGHT` | 排序 / 分组执行 / 加权 |
| `MATCH FILES` / `ADD FILES` | 合并 |
| `MULTIPLE IMPUTATION` | 缺失值多重插补 |
| `BOOTSTRAP` | 自助法 |

## 输出与交付

| 命令 | 用途 | 骨架 |
|---|---|---|
| `OMS` / `OMSEND` | 把表格导成 OXML/HTML/PDF | `OMS /SELECT ALL /DESTINATION FORMAT=OXML OUTFILE='C:/tmp/out.xml'.` … `OMSEND.` |
| `OUTPUT EXPORT` | 导出查看器内容 | `OUTPUT EXPORT /CONTENTS EXPORT=ALL /XLSX DOCUMENTFILE='C:/tmp/o.xlsx'.` |
| `OUTPUT SAVE` | 存 .spv | |
| `SET` / `SHOW` | 会话设置 | |

## 什么时候别用它

- **Tukey / Dunnett / Dunn**：SPSS 27 拿不到（`ADJ()` 只有 Bonferroni/LSD/Šidák），走 `prism` mod。
- **显著性字母（CLD）**：SPSS 没有原生输出，要自己按对比结果算。

## PROBIT 与 OXML（实测更正）

> 旧版本这里写着「PROBIT 不进 OXML，LC50 要从日志或 HTML 解析」。**这是错的**，
> 2026-11-12 用生产作业实测推翻：`PROBIT` 的输出**完整进 OXML**。

实测（`stats.exe -production silent`，`OMS /DESTINATION FORMAT=OXML`）拿到六张 pivotTable：
`Notes` / `Data Information` / `Convergence Information` / `Parameter Estimates` /
`ChiSquareTests` / **`Confidence Limits`**（外加一张概率转换图 `chartTitle`）。

以本机 27.0.1 的一次 5 剂量 / 二项数据实测，LC50 点位：

| 项 | text（显示值） | number（全精度） |
|---|---|---|
| LC50 | 2.626 | `2.6261536612025` |
| 95% 下限 | 1.705 | `1.7050135365051` |
| 95% 上限 | 4.058 | `4.0582517808482` |

同一张表还直出 LC01 = `0.037741234420054`、LC99 = `182.73602223734`，概率档覆盖 .010–.990。
用参数估算值（斜率 1.262601238413、截距 -0.52943412033591）手算 LC50 = 2.626153661203，
与表内 `number` 完全吻合 —— 所以这条路线的数值可信。

对应语法（**`/PRINT=CI` 不能省**）：

```spss
OMS /SELECT ALL /DESTINATION FORMAT=OXML OUTFILE='<ascii 路径>/out.xml'.
PROBIT deaths OF total WITH dose /MODEL=PROBIT /PRINT=CI.
OMSEND.
```

### 三个会让你误判的细节（实测踩到）

1. **`/PRINT=NONE` 不是"零置信区间"。** 它仍会输出 2 处「95% 置信区间 + 下限/上限」，
   那是 `Parameter Estimates` 表里**斜率与截距的 Wald CI**（实测 1.263 [0.991, 1.534]、
   −.529 [−.660, −.398]）。**靠搜「置信」判断 CI 表在不在，结论会完全反过来。**
   要锚定 `pivotTable[@subType="Confidence Limits"]`，或看概率档 `number="0.5"` 是否出现
   （实测：NONE 中 0 次、CI 中 1 次）。
2. **表名随语言/版本变。** 简中版叫「**置信限度**」而不是「置信区间」；判定别锚定显示文本。
3. **`LC50` 字面串在 OXML 里出现 0 次。** 别搜 "LC50"，用概率档 `number="0.5"` 定位。

取数铁律：每格同时有 `number`（全精度）与 `text`（显示值、已舍入），**要数字就读 `number`**。
OXML 可能写一半就断（挂死/超时），解析前先校验 `</outputTree>`，残缺按硬错误处理。

以上都已固化进 `templates/spss_ooxml.py`：`--list` 会标出有没有 Confidence Limits 表，
`--lc 0.5` 直接给点估计与 CI。
