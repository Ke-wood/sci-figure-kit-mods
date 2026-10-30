# sci-figure-kit-mods

[`sci-figure-kit`](https://github.com/Ke-wood/sci-figure-kit-core) 的 mod 仓库。
每个 mod 是一个目录：清单 + 文档 + 可选模板。**不含任何可执行安装命令** ——
命令由核心仓库的 `mod.py` 按 `type` / `env` 拼绝对路径。

## 用

```bash
# 把要的 mod 拷进核心仓库的 mods/
cp -r mods/pydeseq2 ../sci-figure-kit/mods/

# 在核心仓库里装
cd ../sci-figure-kit
python scripts/mod.py install pydeseq2 --yes    # 装完自动刷新 mods/INDEX.md
python scripts/mod.py update --check            # 之后随时查上游更新
```

## 有哪些

| 类别 | mod |
|---|---|
| 绘图风格 | `ggpubfigs`（色盲色板 + 期刊主题）、`icarus-figures`（paperfig，约 50 个图型）、`sci-figure`（8 个脚本骨架 + QA 清单） |
| 配色 | `paletteer`（2545 个色板）、`khroma`（科学色板 + 色盲模拟）、`colorcet`（感知均匀色图）、`palettable`（ColorBrewer） |
| 统计 | `pydeseq2`（bulk DE）、`limma`（线性模型）、`clusterprofiler`（GO/KEGG）、`wgcna`（共表达网络）、`drc`（剂量反应）、`ssdtools`（SSD/HC5/PNEC）、`mixture-tox`（CA/IA + TU） |
| 软件桥 | `prism`（只做统计，读 results.json）、`spss`（生产作业 / 进程内 Python） |
| 网络毒理 | `network-tox`（STRING PPI + hub 基因） |
| 方法与模板 | `enrichment-gseapy`（离线 ORA/GSEA + 结果契约） |

## 一个 mod 长什么样

```
mods/<id>/
├── mod.json     清单：type / env / purpose / summary / routes
├── docs.md      什么时候用、实测调用块、坑、产物
├── templates/   可选，可直接跑的脚本
└── reference/   可选，命令表等长文档
```

`mod.json` 的关键字段：

```jsonc
{
  "type": "rpkg",        // pypkg | pysrc | rpkg | rgh | mplstyle | rstyle | snippets
  "env": "r",            // figkit | omicverse | r（snippets 为 null）
  "purpose": "analysis", // plot | analysis | both
  "summary": "一句话：解决什么问题",
  "routes": [
    { "intent": "用户会怎么问", "backend": "用哪个库", "why": "为什么", "fallback": "挂了用什么" }
  ],
  "source": { "kind": "cran", "url": "…" }
}
```

**`summary` 进索引，`routes[].intent` 进路由表** —— 这两处写清楚，模型才选得中。
`kind: "local"` 表示方法是我们自己写的、没有上游可更新（`update` 会跳过）。

## 加一个 mod

1. 复制 `mods/_template/` 改名；
2. 填 `mod.json`，写 `docs.md`（**调用块要实测过**，别凭记忆写 API）；
3. 在核心仓库里 `install` + `verify`，确认能跑通；
4. 提 PR。

CI 会检查：清单是合法 JSON、必填字段齐全、`docs.md` 存在、没有本机路径。

## 许可

各 mod 的 `license` 字段记录上游许可；本仓库自身 MIT。
