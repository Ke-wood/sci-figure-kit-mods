# SHAP

> 模型可解释性 mod。封装 PyPI `shap`（0.54.1，MIT）。

## 用途

解释任意黑盒模型的预测（不限于线性模型）：

- **全局特征重要性**：`beeswarm`（蜂群，含方向与分布）/ `bar`（平均 |SHAP|）
- **单样本归因**：`waterfall`（把预测从基准值逐特征推到结果）/ `force`
- **特征依赖 / 交互**：`scatter`（非线性与交互效应）

## 实测调用（shap 0.54.1，2026-11-23 本机 figkit py3.14 实跑）

真实 API：

```python
import shap
explainer = shap.TreeExplainer(model)   # 树模型用 TreeExplainer（快）；其他模型用 shap.Explainer(model, X)
expl = explainer(X)                     # 返回 Explanation 对象，.values 形状 n × features
shap.plots.beeswarm(expl)               # 蜂群
shap.plots.bar(expl)                    # 平均 |SHAP|
shap.plots.waterfall(expl[0])           # 第 0 个样本的归因瀑布
shap.plots.scatter(expl[:, "feat"])     # 单特征依赖
```

> **分类模型注意**：二分类时 `expl.values` 是 3 维 `(n, features, 2)`，要取正类切片
> `expl = expl[:, :, 1]` 再画，否则 beeswarm 报维度错。

## 本机实测输出（sklearn diabetes 演示，442 样本 × 10 特征）

Top-5 特征（平均 |SHAP|）：

| 特征 | mean_abs_shap |
|---|---|
| s5 | 27.52 |
| bmi | 26.36 |
| bp | 8.24 |
| s6 | 4.82 |
| s3 | 4.38 |

方向与临床常识一致（bmi、bp 是糖尿病强预测因子）。**这是 sklearn 自带数据集的演示数值，非实验结论。**

产物：`shap_beeswarm.png` / `shap_bar.png` / `shap_waterfall.png` /
`shap_dependence_<top特征>.png` / `shap_importance.csv`。

## 模板

`templates/shap_explain.py`：CSV（特征列 + 目标列）→ 训练随机森林 → SHAP 四图 + 重要性表。

```bash
python templates/shap_explain.py --demo --out shap_out
python templates/shap_explain.py --data data.csv --target y --out shap_out
```

## 注意事项

- 本机依赖已齐（numpy 2.4.6 / scipy 1.18.1 / scikit-learn 1.9.1 / pandas），装它**只新增 shap + slicer 两个纯 Python 包**，不顶动核心依赖。
- SHAP 只吃**数值特征**；类别特征请先 one-hot / 编码。
- 本 mod 是分析库，也可只导出 SHAP 值 CSV 交给下游绘图。

## 回退

`sklearn.inspection.permutation_importance`，或线性/GLM 模型的标准化系数大小。
