# palettable

ColorBrewer / CartoColors / 手动作家色板的 Python 实现，纯 Python、无编译。

## 调用

```python
from palettable.colorbrewer.qualitative import Set2_8, Paired_12
from palettable.cartocolors.qualitative import Bold_5
from palettable.colorbrewer.sequential import Blues_9
from palettable.colorbrewer.diverging import RdBu_11

Set2_8.hex_colors        # ['#66C2A5', '#FC8D62', ...]
Set2_8.mpl_colormap      # 直接给 matplotlib 用
Set2_8.mpl_colors        # RGB 元组
```

命名是 `<色板>_<色数>`：`Set2_8` 是 8 色，`Set2_4` 是 4 色。色数是固定的，
不是任意取 —— 想要别的长度就换一个色板。

## 什么时候用它

- 要 **ColorBrewer** 的经典定性/顺序/发散色板，又不想装 R；
- 要 `CartoColors`（`Bold_5`、`Sunset_7` 这类）；
- 想把色板直接变成 matplotlib colormap（`.mpl_colormap`）。

## 实测（2026-10-24）

```
Set2_8   → ['#66C2A5', '#FC8D62', '#8DA0CB', '#E78AC3', '#A6D854', '#FFD92F', '#E5C494', '#B3B3B3']
Paired_12→ ['#A6CEE3', '#1F78B4', '#B2DF8A', '#33A02C', ...]
Bold_5   → ['#7F3C8D', '#11A579', '#3969AC', '#F2B701', '#E73F74']
```

`Set2_8` 与 R 的 `RColorBrewer::brewer.pal(8, "Set2")` 完全一致。

## 坑

- **定性色板最多 12 色**（ColorBrewer 的设计上限），超过 12 组要合并类别或分面；
- 名字里的数字是色数，写错就 `ImportError`（例如 `Set2_7` 不存在）；
- 发散色板（`RdBu_11`）要配 `vmin=-1, vmax=1` 之类的对称范围，否则零点会漂。

## 与其他配色 mod 的分工

| 场景 | 用哪个 |
|---|---|
| ColorBrewer / Carto 经典色板（Python） | 本 mod |
| 上千个色板、含 ggsci 期刊色（R） | `paletteer` |
| 色盲模拟 + 科学色图（R） | `khroma` |
| 感知均匀连续色图（Python） | `colorcet` |
