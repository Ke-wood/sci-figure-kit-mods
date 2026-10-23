# khroma

科学配色方案 + **色盲模拟**。35 套出版级色板，函数名是英式拼写 `colour()`。

## 调用

```r
library(khroma)

colour("bright")(5)      # #4477AA #EE6677 #228833 #CCBB44 #66CCEE
colour("okabeito")(8)    # 就是标准的 Okabe-Ito 八色
colour("vibrant")(6)

# 连续 / 发散
colour("batlow")(100)
colour("roma")(100)
```

`colour()` 返回一个函数：`colour("bright")(5)` 取 5 色，`(8)` 取 8 色。

## 色盲检查

```r
# 把图转成各类色盲视角再看一眼
check_colorblind(p, type = "deuteranomaly")
```

支持 protanopia / deuteranopia / tritanopia 等。**配色不能只靠肉眼判断"看起来还行"** ——
红绿在 deuteranopia 下会糊成一片，这是投稿前最常被打回的原因之一。

## 色板清单

```r
names(khroma::colour())   # 列出全部方案名
```

常用：`bright`（高对比、色盲友好）、`okabeito`（Okabe-Ito）、`vibrant`、
`muted`、`light`、`dark`、`contrast`，以及科学色图 `batlow` / `roma` / `vik`。

## 实测（2026-10-24）

```
colour("bright")(5)   → #4477AA #EE6677 #228833 #CCBB44 #66CCEE
colour("okabeito")(8) → #000000 #E69F00 #56B4E9 #009E73 #F0E442 #0072B2 #D55E00 #CC79A7
```

与 `references/palettes.md` 的 Okabe-Ito 逐位一致。

## 坑

- 函数是 `colour()` 不是 `color()`；
- 返回的是**函数**，忘了后面加 `(n)` 会得到一个函数对象；
- 色盲模拟依赖 `colorspace`，装 khroma 时已一并装上。
