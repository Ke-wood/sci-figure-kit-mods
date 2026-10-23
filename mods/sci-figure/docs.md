# sci-figure（模板库）

一套 SCI / Elsevier 风格的绘图脚本模板与参考文档（MIT）。

来源：https://github.com/xiao-yuling/sci-figure

## 什么时候用它

- 想**照着一个完整可跑的脚本改**，而不是从零写
- 需要一份「投稿前该检查什么」的清单

## 里面有什么

- `examples/python/` —— 8 个图型的完整脚本：bar / errorbar / heatmap /
  histogram / line / multipanel / scatter / violin_box
- `references/` —— `style-guide.md`（期刊 rcParams 配方）、
  `chart-patterns.md`、`backend-selection.md`、`qa-checklist.md`
- `examples/gallery/` —— 对应的成品预览 PNG

**这些是模板，不是库** —— 读它、抄它、按本项目数据改写，不要 import。
读之前先看下面的实测文件清单确认路径。注意 `examples/gallery/*.png`
在稀疏拉取时被跳过了（省流量），需要预览图就 `--full-fetch` 重装。

## 注意

这个仓库原本是一个 Claude skill。本 mod 只取它的 `examples/` 与
`references/` 当模板用，不装载它自带的 skill。

## 实测 API

**代码在位（实测列目录，相对 vendor/src）**（2026-10-06T00:20:37+08:00 由 `mod.py verify --write-docs` 实测写入，非凭记忆）

```
LICENSE
README.md
examples/python/bar_example.py
examples/python/errorbar_example.py
examples/python/heatmap_example.py
examples/python/histogram_example.py
examples/python/line_example.py
examples/python/multipanel_example.py
examples/python/scatter_example.py
examples/python/violin_box_example.py
references/backend-selection.md
references/chart-patterns.md
references/qa-checklist.md
references/style-guide.md
```
