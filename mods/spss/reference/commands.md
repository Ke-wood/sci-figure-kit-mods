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
| `PROBIT` | **概率单位法 / LC50** | `PROBIT deaths OF total WITH dose /MODEL=PROBIT /PRINT=NONE.`（连续剂量用 `WITH`，别用 `BY`） |
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
- **PROBIT 不进 OXML**：只有备注/警告/数据信息，LC50 数值要从日志或 HTML 里解析。
