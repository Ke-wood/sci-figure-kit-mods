# spss

无人值守跑 **IBM SPSS Statistics**（`{root}/spss/stats.exe`，27.0.1）。
这个 mod 不含 SPSS 本体，只给调用方式与纪律。

**完整命令能力表见 `reference/commands.md`**（常用 60 条；SPSS 共 328 条命令，
逐条规格在本机 `{root}/spss/syntax_xml/<命令>.xml`）。

## 什么时候用它

| 场景 | 为什么是 SPSS |
|---|---|
| **LC50 / EC50（概率单位法）** | Prism 9/10 都不做；SPSS `PROBIT` 是标准实现 |
| **线性混合模型**（MIXED） | SPSS 的强项；Prism 到 11 才补混合模型 |
| **Kruskal-Wallis** | `NPAR TESTS /K-W`，H 与 scipy 逐位一致，不会像 Prism 那样挂死 |
| **双因素 + 简单效应** | `UNIANOVA /EMMEANS` 一次出 8 张表 |

**不该用它**：Tukey / Dunnett / Dunn 事后（SPSS 27 拿不到）—— 这些走 `prism` mod。

## 四种调用接口（2026-10-24 实测）

| 接口 | 入口 | 适合 | 状态 |
|---|---|---|---|
| **生产作业** | `stats.exe -production silent job.spj` | 无人值守、批量、结果落 OXML | ✅ 实测跑通 |
| **进程内 Python** | `{root}/spss/Python3/python.exe` + `spss.Submit` | 要直接读数据、要快、要读输出对象 | ✅ 实测（Submit + `spssdata` 取数） |
| **COM** | ProgID `SPSS.Application16` | Excel/VBA 驱动 | ⚠️ 已注册，但本机 Python 没装 `pywin32` |
| **R 集成** | `RConsole.exe` / `rcommute.exe` | SPSS 调 R 或 R 调 SPSS | 未验 |

SPSS 自带 Python 3.8 与四个模块：`spss`（Submit）、`spssdata`（游标读全精度）、
`spssaux`（辅助）、`SpssClient`（输出文档里的表格对象）。**这比 OXML 好用**：
不用解析 pivot、不用等文件落盘。

## 调用方式：两条路

### A 生产作业（稳、可留证据）

```powershell
& '{root}/spss/stats.exe' -production silent 'C:/tmp/spss_run/job.spj'
```

**绝对不要** `stats.exe foo.sps` —— 那是交互模式，会弹 SPSS 窗口等你看结果（挂死）。

### job.spj（有官方 XSD：`{root}/spss/production-1.2.xsd`）

```xml
<?xml version="1.0" encoding="UTF-8"?>
<job xmlns="http://xml.spss.com/spss/production"
     syntaxFormat="batch" syntaxErrorHandling="stop" print="false">
  <output outputPath="C:/tmp/spss_run/job.log" outputFormat="text-utf8"/>
  <syntax syntaxPath="C:/tmp/spss_run/analysis.sps"/>
</job>
```

顺序不能反：`output` 必须在 `syntax` 前；`syntax` 用的是 **`syntaxPath` 属性**，
不是元素文本（写成 `<syntax>C:/...</syntax>` 会被静默忽略，作业照样"成功"但什么都没跑）。

### analysis.sps

```spss
GET DATA /TYPE=TXT
  /FILE='C:/tmp/spss_run/data.csv'
  /DELIMITERS=","
  /QUALIFIER='"'
  /ARRANGEMENT=DELIMITED
  /FIRSTCASE=2
  /VARIABLES=group A8 value F8.2.

OMS /SELECT ALL /DESTINATION FORMAT=OXML OUTFILE='C:/tmp/spss_run/out.xml'.
DESCRIPTIVES VARIABLES=value /STATISTICS=MEAN STDDEV MIN MAX.
OMSEND.
```

### B 进程内 Python（快、能直接取数）

```powershell
& '{root}/spss/Python3/python.exe' '<skill>/mods/spss/templates/spss_py.py' `
    --sps analysis.sps --table agg.csv --out results
```

```python
import spss, spssdata
spss.Submit(open("analysis.sps").read().splitlines())   # 语法错会抛异常，不是 exit 0
with spssdata.Spssdata() as data:
    names = data.varnames
    for case in data: ...                               # case 是全精度元组
```

实测：`AGGREGATE` 后读回 `A=12.466666666666669`、`B=15.2`，与源表一致。

> 坑：字符串变量按声明宽度补齐（`A8` 读出来是 `'A       '`），落 CSV 前 `.strip()`。

## 四条硬约束

1. **产物路径全用纯 ASCII。** 中文目录下 SPSS 会"正常退出"但 OXML 不生成。
2. **看日志，不看退出码。** 语法错时 SPSS 仍是 exit 0，错误只写在日志里
   （`syntaxErrorHandling="stop"` 会停在出错那条）。
3. **OXML 可能只写一半。** 挂死时会留下几 KB 的残文件 —— 解析前先校验
   `</outputTree>` 是否存在，残缺就当硬错误。
4. **PROBIT 的结果不进 OXML**（只有备注/警告/数据信息），LC50 要从日志/HTML 解析，
   或者改用能进 OXML 的 `UNIANOVA`/`DESCRIPTIVES` 路线。

## 读 OXML 的三个要点

- 每格同时有 `number`（**全精度**）与 `text`（显示值、带舍入）：**要数字就读 `number`**。
- 表是 `pivotTable`，行/列是 `dimension`/`category`，不是规整 CSV；脚注在 `footnote` 里。
- 输出 UTF-8，中文表名直接可读（控制台显示乱码只是控制台的事）。

## 用这个 mod 的脚本

`templates/spss_run.py`：生成 `.spj` → 跑生产作业 → 超时 `taskkill` → 收集 OXML。

```powershell
python templates/spss_run.py --sps analysis.sps --workdir C:/tmp/spss_run --timeout 300
```

## 已验证（2026-10-23，本机 27.0.1 @ {root}/spss）

- 生产作业跑通：`DESCRIPTIVES` 产出 OXML，`number="13.833333333333"` 与
  `text="13.8333"` 都在，6 行数据、均值 13.8333 与源表一致；
- `syntaxPath` 写错的坑实测复现（元素文本写法 → 作业"成功"但零产物）；
- 超时强杀路径已实现（未触发）。
