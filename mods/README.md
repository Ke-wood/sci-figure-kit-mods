# mods —— 本仓库的全部 mod

每个子目录是一个 mod，最小集合 `mod.json` + `docs.md`。
它们**不能自带安装命令**：真正装什么由核心仓库的 `mod.py` 按 `type` / `env` 决定。

```
mods/
├── _catalog.json     已知 mod 目录（含只登记未装的候选）
├── _template/        新建 mod 的骨架
└── <id>/
    ├── mod.json      清单
    ├── docs.md       实测调用方式与坑
    ├── templates/    可直接跑的脚本（可选）
    └── reference/    命令表等长文档（可选）
```

## 怎么用

把要的目录拷进核心仓库的 `mods/`，然后在核心仓库里 `mod.py install <id> --yes`。
装完 `mod.py index` 会自动把这些 mod 压成一页 `mods/INDEX.md`，供模型按需展开。

## 新增须知

- `summary` 要能独立成句（它直接进索引）；
- `routes[].intent` 写成用户会说的话（它进路由表）；
- `docs.md` 的调用块必须实测过，写清版本与坑；
- 提交前跑 `python scripts/check_mods.py`。
