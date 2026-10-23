# ggpubfigs

色盲友好配色 + ggplot2 期刊主题扩展（133★，MIT，不在 CRAN）。

来源：https://github.com/JLSteenwyk/ggpubfigs

## 什么时候用它

- 图要在 R 里用 ggplot2 画，且**配色必须色盲安全**（投稿常见要求）
- 想要一个现成的「干净期刊主题」，不想自己一条条写 `theme()` 参数
- 它只覆盖配色与主题，**不提供新图型** —— 要新图型走 paperfig（mod）或 cnsplots

## 用法

```r
library(ggplot2); library(ggpubfigs)

ggplot(df, aes(x, y, colour = grp)) + geom_point() +
  scale_colour_manual(values = friendly_pal("wong_eight", n = 3)) +
  theme_simple()
```

### ⚠️ `friendly_pal()` 返回的是**色值向量，不是 ggplot2 的 scale**

实测：它返回一个 `palette` 类的十六进制色值向量（`friendly_pal("wong_eight", 2)`
→ `#E69F00 #56B4E9`）。所以**不能**直接 `+ friendly_pal(...)` —— 那样会报
`Can't add <palette> to a <ggplot> object`。必须包进 `scale_*_manual(values = )`：

```r
scale_colour_manual(values = friendly_pal("wong_eight", 3))
scale_fill_manual(values  = friendly_pal("wong_eight", 3))
```

签名：`friendly_pal(name, n, type = c("discrete", "continuous"))`。
`type="continuous"` 时返回 `n` 个插值色，可喂给 `scale_*_gradientn(colours = )`。

可选的 `name`（实测 `names(friendly_pals)`）：

```
bright_seven  contrast_three  vibrant_seven  muted_nine   nickel_five
ito_seven     ibm_five        wong_eight     tol_eight    zesty_four
retro_four    tableau_ten     glasbey_twelve viridis_eight cividis_eight
```

投稿常用 `wong_eight` / `ito_seven` / `tol_eight` —— 都是色盲安全的标准色板。

## 实测 API

**R 包导出对象（实测 ls("package:...")）**（2026-10-06T00:38:18+08:00 由 `mod.py verify --write-docs` 实测写入，非凭记忆）

```
friendly_pal
friendly_pals
theme_big_grid
theme_big_simple
theme_black
theme_blue
theme_grey
theme_grid
theme_red
theme_simple
```
