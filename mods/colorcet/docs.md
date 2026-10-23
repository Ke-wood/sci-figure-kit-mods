# colorcet

感知均匀色图集合（CET 系列），Python 侧给 matplotlib 用。
**210 个色板 / 420 个 colormap**。

## 调用

```python
import colorcet as cc
import matplotlib.pyplot as plt

ax.imshow(data, cmap=cc.cm["CET_L1"])       # 直接当 cmap
cc.palette["CET_L1"][:5]                     # ['#000000', '#010101', ...] 十六进制
plt.colormaps.register(cc.cm["CET_L1"], name="cet_l1")   # 注册成名字，后面按字符串用
```

命名规律：`CET_L*` 线性、`CET_D*` 发散、`CET_C*` 循环、`CET_R*` 彩虹（不推荐，亮度不单调）。

## 什么时候用它

- 热图要用**亮度单调**的色图（jet/rainbow 在灰度打印时会把高低值糊在一起）；
- 需要**色盲可辨**的连续色标（CET 系列按色觉缺陷设计过）；
- 发散数据（z-score、log2FC）要用发散色图 —— `CET_D1` 这类。

## 实测（2026-10-24）

```
len(cc.palette) = 210,  len(cc.cm) = 420
"rainbow" in cc.cm  → True
"CET_D1" in cc.cm   → True
cc.palette["CET_L1"][:5] → ['#000000', '#010101', '#020202', '#040404', '#050505']
```

## 坑

- **会带 bokeh**（colorcet 原本属于 HoloViz），装的时候体积不小；只用 matplotlib 的话不影响；
- `cc.cm` 的 key 有的是别名（`rainbow`、`fire`），有的是正式名（`CET_L1`），不确定就先 `list(cc.cm)[:10]` 看一眼；
- 循环色图（CET_C*）适合相位/角度，不适合有大小方向的量。

## 和其他色标的关系

| 需求 | 首选 |
|---|---|
| 通用连续量 | `viridis` / `cividis`（matplotlib 内置，不用装） |
| 更细的色图选择 | 本 mod（CET 系列） |
| 正负 / 中心零 | `CET_D*`、`RdBu_r`、`coolwarm` |
| 期刊分类色板 | `palettable` / `paletteer`（R） |
