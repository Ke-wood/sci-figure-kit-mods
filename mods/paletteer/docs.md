# paletteer

R 的配色聚合器：**2545 个离散色板**，来自几十个包（ggsci、RColorBrewer、viridis、
colorBlindness、fishualize、awtools、dutchmasters…），统一用 `包名::色板名` 调。

## 调用

```r
library(paletteer)

paletteer_d("ggsci::default_nejm")          # 离散：返回十六进制向量
paletteer_d("RColorBrewer::Set2", 8)
paletteer_c("viridis::viridis", n = 100)    # 连续：返回 n 个渐变点

# 直接进 ggplot
scale_color_paletteer_d("ggsci::default_nejm")
scale_fill_paletteer_c("viridis::viridis")
```

## 先查名字，别猜

```r
d <- palettes_d_names          # 2545 行：package / palette / length
subset(d, package == "ggsci")
```

**命名坑（实测）**：ggsci 的色板在 paletteer 里带前缀，不是 ggsci 文档里的名字：

| 你以为 | 实际 |
|---|---|
| `ggsci::npg` | `ggsci::nrc_npg` |
| `ggsci::lancet` | `ggsci::lanonc_lancet` |
| `ggsci::nejm` | `ggsci::default_nejm` |
| `ggsci::jco` | `ggsci::default_jco` |
| `ggsci::aaas` | `ggsci::default_aaas` |

写错会报 `Palette "ggsci::npg" not found`，不会静默给错色。

## 实测（2026-10-24）

```
paletteer_d("ggsci::default_nejm")
#BC3C29 #0072B5 #E18727 #20854E #7876B1 #6F99AD #FFDC91 #EE4C97
```

与本 skill `references/palettes.md` 里的 NEJM 色板逐位一致。

## 什么时候用它

- 想用某篇论文/某个包的官方色板，但不想去找属于哪个包；
- 要在 R 里快速拿到一批十六进制，粘到 Python 或文档里；
- 需要色板长度不同的版本（3/4/5…色）——`paletteer_d(name, n)` 会取前 n 个。

不适合：精确控制单个颜色（那就手写十六进制）。
