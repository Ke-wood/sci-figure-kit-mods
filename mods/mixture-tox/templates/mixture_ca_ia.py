#!/usr/bin/env python
"""混合物毒性：浓度加和（CA）与独立作用（IA）预测，外加 TU 判定。

用法（figkit 环境）：
  {root}/envs/figkit/Scripts/python.exe mixture_ca_ia.py \
      --singles singles.csv --mixtures mixtures.csv --out results [--observed obs.csv]

输入：
  singles.csv    compound, conc, response     ← 单组分剂量-反应（response 0–1，随浓度下降）
  mixtures.csv   mixture, compound, fraction  ← 每个混合物的组分比例（每组和为 1）
  obs.csv（可选）mixture, ec50_observed       ← 实测混合物 EC50，用来算 TU 与偏差比

输出：
  results/ec50.csv       各混合物的 CA / IA 预测 EC50（可选：实测值与偏差比）
  results/curves.csv     两个模型的完整预测曲线（effect, concentration）
  results/params.csv     各单组分的 4PL 参数
  results/stats.json     输入哈希、样本量、判读
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

import numpy as np
import pandas as pd


def four_pl(c, bottom, top, ec50, hill):
    return bottom + (top - bottom) / (1.0 + (c / ec50) ** hill)


def fit_single(conc: np.ndarray, resp: np.ndarray):
    from scipy.optimize import curve_fit

    p0 = [max(0.0, resp.min()), min(1.0, resp.max()), float(np.median(conc)), 1.0]
    bounds = ([0.0, 0.0, conc.min() / 100, 0.1], [1.0, 1.0, conc.max() * 100, 10.0])
    popt, _ = curve_fit(four_pl, conc, resp, p0=p0, bounds=bounds, maxfev=50000)
    return popt


def ecx(p, effect: float) -> float:
    """单组分达到给定效应所需的浓度（反解 4PL）。"""
    bottom, top, ec50, hill = p
    ratio = (top - bottom) / (effect - bottom) - 1.0
    if ratio <= 0:
        return float("nan")
    return float(ec50 * ratio ** (1.0 / hill))


def ca_curve(params: dict, fractions: dict, effects: np.ndarray) -> np.ndarray:
    """CA：Σ fi / ECxi(E) = 1/C  →  C(E)。"""
    out = []
    for e in effects:
        inv = 0.0
        for name, fi in fractions.items():
            c = ecx(params[name], e)
            if not np.isfinite(c) or c <= 0:
                inv = np.nan
                break
            inv += fi / c
        out.append(1.0 / inv if inv and np.isfinite(inv) else np.nan)
    return np.array(out)


def ia_effect(params: dict, fractions: dict, conc: float) -> float:
    """IA：E = 1 - Π(1 - Ei(C))。"""
    survive = 1.0
    for name, _ in fractions.items():
        survive *= 1.0 - four_pl(conc, *params[name])
    return 1.0 - survive


def ia_ec(effect: float, params: dict, fractions: dict) -> float:
    from scipy.optimize import brentq

    lo, hi = 1e-6, 1e6
    f = lambda c: ia_effect(params, fractions, c) - effect
    if f(lo) * f(hi) > 0:
        return float("nan")
    return float(brentq(f, lo, hi, maxiter=200))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--singles", required=True)
    ap.add_argument("--mixtures", required=True)
    ap.add_argument("--observed", default=None)
    ap.add_argument("--out", default="results")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    singles = pd.read_csv(args.singles)
    mixtures = pd.read_csv(args.mixtures)
    need = {"compound", "conc", "response"}
    if not need.issubset(singles.columns):
        print(f"! singles.csv 需要 {sorted(need)}", file=sys.stderr)
        return 2

    params = {}
    rows = []
    for name, sub in singles.groupby("compound"):
        p = fit_single(sub["conc"].to_numpy(float), sub["response"].to_numpy(float))
        params[name] = p
        rows.append({"compound": name, "bottom": p[0], "top": p[1], "ec50": p[2], "hill": p[3]})
    pd.DataFrame(rows).to_csv(os.path.join(args.out, "params.csv"), index=False)

    effects = np.round(np.arange(0.05, 0.96, 0.05), 2)
    curves, summary = [], []
    observed = {}
    if args.observed and os.path.isfile(args.observed):
        obs = pd.read_csv(args.observed)
        observed = dict(zip(obs["mixture"], obs["ec50_observed"]))

    for mid, sub in mixtures.groupby("mixture"):
        fractions = {r.compound: float(r.fraction) for r in sub.itertuples()}
        missing = [c for c in fractions if c not in params]
        if missing:
            print(f"! {mid} 引用了没有单组分数据的化合物：{missing}", file=sys.stderr)
            return 2
        total = sum(fractions.values())
        if abs(total - 1.0) > 0.01:
            print(f"! {mid} 的比例和是 {total:.3f}，应为 1", file=sys.stderr)
            return 2

        ca = ca_curve(params, fractions, effects)
        ia = np.array([ia_ec(e, params, fractions) for e in effects])
        for e, c_ca, c_ia in zip(effects, ca, ia):
            curves.append({"mixture": mid, "effect": e, "ca_conc": c_ca, "ia_conc": c_ia})

        ca50 = ca_curve(params, fractions, np.array([0.5]))[0]
        ia50 = ia_ec(0.5, params, fractions)
        row = {"mixture": mid, "ca_ec50": ca50, "ia_ec50": ia50}
        if mid in observed:
            obs50 = float(observed[mid])
            row["ec50_observed"] = obs50
            row["mdr_ca"] = obs50 / ca50 if ca50 else None
            row["mdr_ia"] = obs50 / ia50 if ia50 else None
            row["tu_ca"] = sum(f * obs50 / params[c][2] for c, f in fractions.items())
        summary.append(row)

    pd.DataFrame(summary).to_csv(os.path.join(args.out, "ec50.csv"), index=False)
    pd.DataFrame(curves).to_csv(os.path.join(args.out, "curves.csv"), index=False)

    stats = {
        "singles": os.path.abspath(args.singles),
        "mixtures": os.path.abspath(args.mixtures),
        "n_compounds": len(params),
        "n_mixtures": len(summary),
        "input_sha256": hashlib.sha256(
            open(args.singles, "rb").read() + open(args.mixtures, "rb").read()).hexdigest(),
        "reading": {
            "ca_ec50": "浓度加和预测（作用位点相同）",
            "ia_ec50": "独立作用预测（作用模式独立）",
            "mdr_<model>": "实测/预测，<1 协同、>1 拮抗（同一数量级内视为无偏差）",
            "tu_ca": "Σ(fi·C_obs/EC50i)：≈1 浓度加和，<1 协同，>1 拮抗",
        },
    }
    with open(os.path.join(args.out, "stats.json"), "w", encoding="utf-8") as fh:
        json.dump(stats, fh, ensure_ascii=False, indent=2)

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
