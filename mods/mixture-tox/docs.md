# mixture-tox

联合暴露的毒性预测：**浓度加和（CA）** 与 **独立作用（IA）**，外加 TU / MDR 判读。

## 什么时候用它

- 两种以上污染物同时暴露，要回答"混合物比各自单独作用更强还是更弱"；
- 只有单组分的剂量-反应曲线，想知道等比例（或任意比例）混合后的 EC50；
- 要判断协同 / 拮抗，但不想靠"看起来更低"这种主观判断。

## 两个模型怎么选

| 模型 | 假设 | 预测式 |
|---|---|---|
| **CA** 浓度加和 | 各组分作用位点相同、只是效力不同 | `Σ fi / ECxi(E) = 1 / C` |
| **IA** 独立作用 | 各组分作用机制独立、效应可相乘 | `E = 1 − Π(1 − Ei(C))` |

**不要二选一**：同一份数据两个都算。实测 EC50 落在 CA 与 IA 之间 → 无额外交互；
低于两者 → 协同；高于两者 → 拮抗。这是比单看 TU 更稳的判读方式。

## 调用

```powershell
{root}/envs/figkit/Scripts/python.exe "<skill>/mods/mixture-tox/templates/mixture_ca_ia.py" `
    --singles singles.csv --mixtures mixtures.csv --out results [--observed obs.csv]
```

```
singles.csv    compound, conc, response      效应 0–1，随浓度下降
mixtures.csv   mixture, compound, fraction   每个混合物的比例，和为 1
obs.csv        mixture, ec50_observed        可选，用来算 MDR 与 TU
```

产物：`ec50.csv`（CA/IA 预测、MDR、TU）、`curves.csv`（两条预测曲线）、
`params.csv`（单组分 4PL 参数）、`stats.json`。

## 判读

| 指标 | 含义 |
|---|---|
| `mdr_ca` / `mdr_ia` | 实测 EC50 ÷ 预测 EC50。< 1 协同，> 1 拮抗；同一数量级内视为无偏差 |
| `tu_ca` | `Σ(fi·C_obs/EC50i)`：≈1 浓度加和，<1 协同，>1 拮抗 |

写结论时说清用的是哪一个模型判的，别只写"有协同作用"。

## 实测（2026-10-24，解析解对照）

A（EC50=1，hill=1）+ B（EC50=4，hill=1），50:50：

| | 理论值 | 程序输出 |
|---|---|---|
| CA 预测 EC50 | 1.6000（= 2/(1/1+1/4)） | 1.600016 |
| IA 预测 EC50 | 5.7016（解 C²−5C−4=0） | 5.701587 |

误差来自 4PL 拟合，量级 1e-5，可忽略。

## 坑

| 坑 | 现象 | 正解 |
|---|---|---|
| 比例和不为 1 | 预测整体偏移 | 模板会直接报错；先归一化 |
| 单组分曲线外推 | EC50 落在实测浓度范围外 | 拟合区间要覆盖 EC50；否则标"外推" |
| 用不同终点/单位混合 | 预测无意义 | 同一终点（死亡率/抑制率）、同一单位 |
| 机制不同却只用 CA | 高估或低估 | 两个模型都算，看实测落在哪 |
| 低剂量 hormesis | 4PL 拟不上 | 单组分先用 `drc` 的 BC.5，或截掉刺激段 |

## 与其他 mod 的关系

- 单组分曲线拟合（尤其 hormesis）→ `drc`；
- 单物种多化合物 → 本 mod；
- 多物种分布（同一化合物）→ `ssdtools`。
