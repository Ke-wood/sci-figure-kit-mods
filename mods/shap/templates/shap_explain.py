#!/usr/bin/env python3
"""用 SHAP 解释一个黑盒模型：全局重要性 + 单样本归因 + 依赖图。

真实 API（shap 0.54.1 实测）：
    explainer = shap.TreeExplainer(model)      # 树模型；其他模型用 shap.Explainer(model, X)
    expl = explainer(X)                        # 返回 Explanation 对象（.values 形状 n×features）
    shap.plots.beeswarm(expl)                  # 蜂群（全局重要性 + 方向）
    shap.plots.bar(expl)                       # 平均 |SHAP|
    shap.plots.waterfall(expl[i])              # 第 i 个样本的归因瀑布
    shap.plots.scatter(expl[:, "feat"])        # 单特征依赖

分类模型注意：二分类的 expl.values 是 3 维 (n, features, 2)，要取正类
    expl = expl[:, :, 1]  # 再画，否则 beeswarm 会报维度错。

用法：
    python shap_explain.py --data data.csv --target y --out shap_out
    python shap_explain.py --demo --out shap_out      # 用 sklearn diabetes 演示
"""
from __future__ import annotations

import argparse
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402


def load_data(args):
    if args.demo or not args.data:
        from sklearn.datasets import load_diabetes

        d = load_diabetes(as_frame=True)
        X = d.data
        y = d.target
        return X, y, "diabetes(demo, 回归)"
    df = pd.read_csv(args.data)
    if args.target not in df.columns:
        raise SystemExit(f"CSV 里没有目标列 {args.target!r}")
    y = df[args.target]
    X = df.drop(columns=[args.target])
    X = X.select_dtypes(include=[np.number])  # SHAP 只吃数值特征
    return X, y, os.path.basename(args.data)


def build_model(y):
    from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor

    # 目标是否近似整数且取值很少 → 当分类
    uniq = np.unique(np.asarray(y))
    if len(uniq) <= 10 and np.allclose(uniq, np.round(uniq)):
        return RandomForestClassifier(n_estimators=200, random_state=0), "classification"
    return RandomForestRegressor(n_estimators=200, random_state=0), "regression"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="SHAP 模型解释")
    ap.add_argument("--data", help="CSV 路径；省略或 --demo 则用内置演示数据")
    ap.add_argument("--target", default="y", help="目标列名（默认 y）")
    ap.add_argument("--out", default="shap_out")
    ap.add_argument("--demo", action="store_true")
    args = ap.parse_args(argv)

    import shap

    X, y, tag = load_data(args)
    os.makedirs(args.out, exist_ok=True)
    model, task = build_model(y)
    model.fit(X, y)

    explainer = shap.TreeExplainer(model)
    expl = explainer(X)
    # 分类：取正类切片
    if expl.values.ndim == 3:
        expl = expl[:, :, 1]

    # 全局重要性表
    imp = pd.DataFrame({
        "feature": list(X.columns),
        "mean_abs_shap": np.abs(expl.values).mean(axis=0),
    }).sort_values("mean_abs_shap", ascending=False)
    imp.to_csv(os.path.join(args.out, "shap_importance.csv"), index=False)

    def save(fn):
        plt.tight_layout()
        plt.savefig(os.path.join(args.out, fn), dpi=200, bbox_inches="tight")
        plt.close("all")

    shap.plots.beeswarm(expl, max_display=15, show=False)
    save("shap_beeswarm.png")

    shap.plots.bar(expl, max_display=15, show=False)
    save("shap_bar.png")

    shap.plots.waterfall(expl[0], max_display=12, show=False)
    save("shap_waterfall.png")

    top_feat = imp.iloc[0]["feature"]
    shap.plots.scatter(expl[:, top_feat], show=False)
    save(f"shap_dependence_{top_feat}.png")

    print(f"[{tag}] 任务={task} 样本={len(X)} 特征={X.shape[1]}")
    print("Top-5 特征（平均 |SHAP|）:")
    print(imp.head(5).to_string(index=False))
    print("产物目录:", args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
