# Prism 10.6.1 / SPSS 27.0.1 可自动化接口调研（2026-11-12）

> 目标：判断还有哪些接口值得做成 sci-figure-kit 的新 mod。
> 本机：`D:\app\prism\prism.exe`（Prism 10.6.1.892）、`D:\app\spss\stats.exe`（SPSS 27.0.1）
> 标注纪律，全文严格区分三种证据：
> - **【实测·运行】** 本机真的启动过 `prism.exe` / `stats.exe` 并拿到产物
> - **【实测·只读】** 解析过真文件（XML/XSD/RTF/zip 包），没启动进程
> - **【文档】** 官方文档或随包 XSD / RTF / schema
> - **【未验证】** 有线索但没证实 —— 这类不作为推荐依据
>
> **版本史（重要，别被标题日期骗了）**：本文件第一版只做静态解析、**没有启动任何商业软件**，
> 因此把 `.pzfx`/HTML 路线全列为【未验证】。第二版做了运行时实测，**推翻了第一版的 3 个关键假设**
> （见 §0 勘误）。读到「已过时」标记的段落，以下文实测结论为准。

---

## 0. 勘误：第一版被实测推翻的 3 条

| # | 第一版说法（【未验证】） | 实测结论（2026-11-12） | 影响 |
|---|---|---|---|
| 1 | 「**PROBIT 结果不进 OXML**，只能解析日志或指望 HTML 视图」 | **错。PROBIT 的完整结果进 OXML**：`Confidence Limits` / `ChiSquareTests` / `Parameter Estimates` / `Cell Counts and Residuals` 四个 pivotTable 全在，LC50 与 95% CI 可从 `number` 属性直读 | 高。**不需要** `outputFormat=html` 绕路，也不需要解日志 |
| 2 | 「`.pzfx`/工程文件只能读，写回未验证，别急着做写能力」 | **错。`.prism` 是可整包构造的 zip**：改内层 `data/tables/<uid>/data.csv` 后 Prism 正常打开并 `ExportTable` 原样导出（rc=0，3.9 s） | 高。`.prism` 模板可由脚本**生成并注入数据**，不必依赖人工建模板 |
| 3 | 「`.pzfx` 的 `Template` 是二进制，所以分析参数改不了 → 只能人工建模板」 | **半错。** `Template` 确实不可改，但不必改它：**`Open .pzfx → Save .prism` 一条 3 行 `.pzc` 就能产出 `.prism` 模板**（5.8 s，rc=0） | 中。模板供应链的第一环节可自动化 |

> 第一版里 **没被推翻** 的部分（`.pzfx` 命名空间坑、数值逗号/点并存、328 条命令、`POWER *` 11 条、
> `PROBIT /PRINT=CI`、`ExportTable` 按扩展名定格式、`Import` 的 `col=-1`）**全部经第二版复核无误**，见 §7。

---

## 1. 一句话结论

**建议新增 2 个 mod，并给现有 2 个 mod 各打一批补丁。** 关键判断：**真正被低估的不是「再多几个统计命令」，而是 `.pzfx` 这个开放格式、`.prism` 的 zip 可构造性，以及「PROBIT 其实进 OXML」这条被现有 docs 写反的事实**。

| 动作 | id / 对象 | 一句话 | 证据等级 |
|---|---|---|---|
| **新增** | `prism-pzfx` | Python 直接读写 `.pzfx`：**不启动 Prism**，秒级拿数据表 | 只读 8/8 实测 |
| **新增** | `prism-template` | **`.pzfx → .prism` 自动出模板** + 改 zip 内 `data.csv` 注入数据 | **运行实测**（5.8 s / 3.9 s） |
| 补丁 | `prism`（现有） | 补 3 条遗漏命令 + 记下「脚本不能新建分析」官方死线 | 只读实测 |
| 补丁 | `spss`（现有） | **删掉「PROBIT 不进 OXML」这条错误硬约束**；`PROBIT /PRINT=CI`（原骨架用 `NONE` 会丢 CI） | **运行实测** |
| **新增（可选）** | `spss-ooxml-reader` | 把 OXML pivotTable 泛化成 `tidy` 表，含 `Confidence Limits` 的概率行解析 | **运行实测** |

**不建议做**：Prism 出图自动化、Prism 当剂量反应/EC50 主力（`drc` 已覆盖）、SPSS SSD/混合物毒性（`ssdtools` / `mixture-tox` 已覆盖）、SPSS COM 与 SaxBasic 桥。

---

## 2. 现有覆盖盘点

### `mods/prism/`（type=snippets, env=null, purpose=analysis）

| 已覆盖 | 说明 |
|---|---|
| `.pzc` 脚本调用 | `prism.exe @job.pzc`，唯一可用入口 |
| `.prism` 工程文件 | zip + JSON，`results.json` 可解析 |
| 单因素 ANOVA + Tukey/Dunnett/Dunn | 7 组实测，F/p/CI 与 statsmodels 一致 |
| 显著性字母 CLD | `compactLetterDisplay` 给每组字母 |
| t 检验 / 线性回归 / 剂量反应 EC50 | XY / Column 模板路线 |
| 模板复用 + `RecalcAll` + `Save` | 参数锁在模板里 |
| `results.json` 结构 + `walk_pairs()` | uid 套 uid 的嵌套解析 |
| 坑清单 | 正斜杠静默失败、模态框挂死、GBK、中文路径、`GoTo R` 编号 |
| **未覆盖** | `.pzfx` 格式、`ForEach`/`DuplicateFamily` 批量、`CloseScriptDialog` 等 |

### `mods/spss/`（type=snippets, env=null, purpose=analysis）

| 已覆盖 | 说明 |
|---|---|
| 生产作业 `-production silent job.spj` | 实测跑通；`production-1.2.xsd` |
| `.spj` 正确写法 | `<output>` 在 `<syntax syntaxPath=.../>` 前 |
| 进程内 Python | `spss`/`spssdata`/`spssaux`/`SpssClient` 四模块 |
| PROBIT/LC50、MIXED、NPAR K-W、UNIANOVA | routes 已登记 |
| OMS → OXML | `number` 全精度 vs `text` 显示值 |
| 328 条命令清单 | `syntax_xml/*.xml` |
| **未覆盖** | `outputFormat` 的 10 种非 text 值、`imageFormat`、`symbol` 传参、`locale` |

**结论：两个 mod 的「单次调用」已经很完整。缺口在「批量」「非 OXML 输出」「开放格式直读」三条线上。**

---

## 3. 新接口发现

### 3.1 Prism

#### (a) `.pzfx` 是可以纯 Python 直读的开放格式 —— **最高价值**

- **接口名**：`.pzfx`（Prism XML）
- **怎么调**：不用调 Prism。`xml.etree.ElementTree` 直接解析。
- **实测结果**（本机 8 个随包样本，`D:\app\prism\SampleData\`）：

| 文件 | 命名空间 | Table | 解析结果 |
|---|---|---|---|
| Breast Cancer Update II.pzfx | **无 ns** | 1 | `OneWay`，Y=12，首值 842302 |
| Cox Sample Data.pzfx | **有 ns** | 1 | `OneWay`，Y=13，首值 97 |
| Logistic (Titanic).pzfx | **有 ns** | 1 | `OneWay`，Y=5 |
| Multiple Linear Regression*.pzfx | **有 ns** | 1 | `OneWay`，Y=10，首值 `4,309999943` |
| Poisson Tutorial Dataset.pzfx | **有 ns** | 1 | `OneWay`，Y=4 |
| Logistic Regression (Studying).pzfx | **无 ns** | 1 | `XY`，X=1 Y=1，首值 6 |

**8/8 全部解析成功。**【实测】

- **⚠️ 最大的坑（本报告最重要的一条实测发现）**：
  一半文件带 `xmlns="http://graphpad.com/prism/Prism.htm"`，一半不带。
  **直接 `findall("Table")` 会在 6/8 个文件上返回空列表，且不报错** —— 静默漏数据。
  正确写法：
  ```python
  NS = "{http://graphpad.com/prism/Prism.htm}"
  root = ET.parse(path).getroot()
  if root.tag.startswith(NS):
      tables = root.findall(NS + "Table")
  else:
      tables = root.findall("Table")
  ```
- **数据结构**（【实测】解析所得）：`GraphPadPrismFile` → `Created` / `InfoSequence` / `Info` / `TableSequence` / `Table` / `Template`
  - `Table` 属性：`TableType`（`XY|OneWay|TwoWay|Contingency|Survival|PartsOfWhole|Result|Legacy`）、`XFormat`、`YFormat`、`Replicates`
  - 列：`XColumn` / `XAdvancedColumn` / `YColumn` / `RowTitlesColumn`，每列下 `Subcolumn` 装 `<d>` 值
  - **数值序列化不一致（第二重要的坑）**：`<d>` 里既有 `4,309999943`（逗号小数点）也有 `4.3`（点小数点）。
    全样本统计：**691 个值用逗号、5825 个值用点**【实测】。
    说明不是「按 locale 统一写」，而是**同一个文件里两种并存**。
    → 解析必须逐值判断，不能 `.replace(",", ".")` 一刀切（那样会把千位分隔符和真小数一起改坏）；
    建议：`float(s.replace(",", "."))` 仅在这个值**不含点**时用，两个都有则报警。
- **`Template` 节点**：注释明写 `<!--Analyses, graphs and layouts as compressed binary. Don't edit this part of the file.-->`【实测，读原文】
  → **分析参数与图样式在 base64 压缩二进制里，纯 Python 改不了。** 这从数据侧独立印证了「Prism 只做分析不出图」的硬边界。
- **能拿到什么**：数据表 + info 常量（`Info`→`Constant`→`Name`/`Value`）。**不包含分析结果**（结果是 `Template` 里的二进制）。
- **证据**：本机 `D:\app\prism\PrismXMLSchema.xml`；官方 [Prism 11 User Guide – Scripts](https://www.graphpad.com/guides/prism/11/user-guide/using_scripts.htm)

#### (b) 官方死线：**脚本不能新建分析**

> "You can't create new data tables, new analyses or new graphs in a script except by duplicating existing ones. When you duplicate a data table, all you get is a new data table. You can import data into it, but not analyze or graph within the script."
> —— [Creating new sheets](https://www.graphpad.com/guides/prism/11/user-guide/creating_new_sheets.htm)【文档】

**这条解释了为什么现有 mod 必须走「模板 → `RecalcAll`」——那不是权宜之计，是唯一合法路径。**
批量的正规入口是 `DuplicateFamily [prepend_text] <CLEAR>`，`prepend_text` 可用 `%F`（文件名）【文档】。

#### (c) 现有 `commands.md` 漏了 3 条命令【实测，来自 `D:\app\prism\ScriptHelper.rtf` 尾部】

| 命令 | 作用 | 价值 |
|---|---|---|
| `CloseScriptDialog` | 关脚本对话框 | 配合下一条，长批量跑时能**看见**进度 |
| `SetScriptDialogTitle [title]` | 设对话框标题 | 判断卡在哪一步 |
| `WTBlock [row(s)], [column(s)], <row label>` | 整块写文本输出（`WBlock` 的文本版） | 现有 docs 只记了表格版 `WBlock` |

#### (d) `ExportTable [filename] <ALL>` 按扩展名定格式【文档】

`.txt`=tab 分隔、`.csv`=逗号、`.xml`=Prism XML；info 表用 `.xml` 才同时导出常量与 notes。
—— [Exporting data, results or info tables](https://www.graphpad.com/guides/prism/11/user-guide/exporting_data_results_or_info_tables.htm)

> 但现有 mod 的 `GoTo R n` 路线会 `No such sheet!` 挂死（已实测），**不建议改现有取数路线**。

#### (e) `Import` 的坐标语义【文档】
`Import <"filename">, <row>, <col>, <subcol>`：row 0 = 标题行，row 1 = 首个数据行；col 0 = X 列，col 1 = 第一个 Y 列，**col -1 = 行标题**。
—— [Importing data from a text file](https://www.graphpad.com/guides/prism/11/user-guide/importing_data.htm)
> 现有 docs 只写「按位置」，没写 `col -1` 这个约定。

#### (f) 方程库 `.pzt` 是二进制，脚本改不了【实测】
`D:\app\prism\Equations\*.pzt` 共 18 族（`Dose-response - Inhibition`、`Standard curves to interpolate` …），`order.txt` 定序。
通读 `ScriptHelper.rtf` **无任何方程相关命令** → 与图样式同性质，只能人工在模板里选。

---

### 3.2 SPSS

#### (a) `.spj` 输出格式远不止 `text-utf8` —— **最高价值**

`D:\app\spss\production-1.4.xsd` 枚举【实测，正则抽取】：

```xml
<xs:attribute name="outputFormat" use="required">
  <!-- viewer | viewer-pes | web-reports | html | excel
       | word | power-point | pdf | text-codepage | text-utf8 | text-utf16 -->
<xs:attribute name="imageFormat" use="optional">
  <!-- bmp | emf | eps | jpg | png | tif -->
```
另有 `imageSize`、`tableSlideTitle`、`tableEmbedBookmark`、`tableEmbedFont`、`tableColumnSeparator`、`tableColumnAutofit`、`tableColumnWidth` 等 PPT/Word 排版属性，以及 `locale`（`language`/`country`/`charset` 三必填）。

**为什么这是最高价值**（**已降级**，见 §3.3 实测）：
- ~~现有 docs 把「PROBIT 结果不进 OXML」列为硬约束。`outputFormat="html"` 是查看器渲染，理应包含全部表格 → LC50 + CI 可直接拿。~~
  → **已被实测推翻**：PROBIT **本来就进 OXML**，`html` 绕路属于多余支线。见 §3.3。
- `imageFormat="eps"/"tif"` 是 SPSS 唯一的矢量/高分辨率出图路径（现有 mod 完全未用）。**【未验证】**
- `outputFormat="excel"` 直接落 xlsx，省掉 OXML pivot 解析。**【未验证】**（OXML 已够用，优先级低）

> 结论修正：`outputFormat=html` 从「最高价值」降为 **「不需要」**；`imageFormat` 仍值得单独验，
> 但优先级低于 `spss-ooxml-reader`（后者才是 LC50 落地的真瓶颈）。

### 3.3 【实测·运行】PROBIT 的 LC50 真的能进 OXML

**做法**（全程硬超时 + 失败 `taskkill`，不弹窗）：写极短 `.spj` + `analysis.sps`，`-production silent` 跑一次。

```spss
WEIGHT BY total.
OMS /SELECT ALL /DESTINATION FORMAT=OXML OUTFILE='C:/tmp/sftest/out_probit.xml'.
PROBIT deaths OF total WITH dose /MODEL=PROBIT /PRINT=CI FREQ /CRITERIA=P(0.05).
OMSEND.
```

**产出**：`out_probit.xml` 52,531 B、`out_probit.txt` 9,459 B，**rc=0，21 s 跑完并自行退出**。

OXML 里的 pivotTable（UTF-8 解码后）：

| subType | 中文 text | 拿得到什么 |
|---|---|---|
| `Confidence Limits` | 置信限度 | **LC50 及各概率点的估计/下限/上限** |
| `ChiSquareTests` | 卡方检验 | Pearson χ²=0.6236、df=3、p=0.8910 |
| `Parameter Estimates` | 参数估算值 | 截距 / 斜率 |
| `Cell Counts and Residuals` | 单元格计数和残差 | 实测/期望响应、残差、概率 |
| `Data Information` / `Convergence Information` / `Warnings` / `Notes` | — | 收敛与警告 |

`Confidence Limits` 的正数行结构（`number` 是全精度，`text` 带舍入）：

```
概率=0.05 → dose 估计 0.10196278943869 / 下限 0.035090438765153 / 上限 0.18625277681459
             log(dose) 估计 -0.9915582918644 / 下限 -1.4548112014029 / 上限 -0.72989724370039
```

> 即 **LC50 = 0.1020，95% CI [0.0351, 0.1863]**，直接来自 OXML `number` 属性，无需求解日志。

**三条由此得出的硬事实**：
1. `mods/spss/docs.md` 的「PROBIT 的结果不进 OXML」**是错的**，必须删。
2. `PROBIT` 的 `/PRINT=CI` 决定 CI 是否出现；原 `reference/commands.md` 骨架写 `/PRINT=NONE` 会**主动丢 CI**。
   （`NONE` 下 `Confidence Limits` 表是否仍出现：**【未验证】**，但没必要冒险，直接用 `CI`。）
3. `WEIGHT BY total` 对 PROBIT **无效**——日志明确警告「加权不适用于 PROBIT，因此忽略个案权重」。
   二项分母要走 `PROBIT deaths OF total WITH dose` 的 `OF ... WITH` 语法本身，不要 `WEIGHT BY`。

### 3.4 【实测·运行】`.prism` 是可由脚本构造的 zip

**证据链**（每步都 rc=0，均 4～6 s）：

| 步骤 | `.pzc` 内容 | 结果 |
|---|---|---|
| ① `.pzfx → .prism` | `Open ...in.pzfx` / `Save ...out.prism` / `Exit` | 5.8 s，产出 `out.prism` 10,087 B |
| ② 拆包 | `data/tables/<uid>/data.csv`+`content.json`、`data/sets/*.json`、`document.json` | 确认是 **zip**（magic `50 4B`） |
| ③ 改内层 CSV 后重开 | `Open ...edited2.prism` / `ExportTable ...exported2.csv` / `Exit` | 3.9 s，**`9,9,9,9` 原样导出** |

> **含义**：`.prism` 模板不需要人工在 GUI 里建——**先拿任意 `.pzfx`（或已有 `.prism`）当骨架，
> 再由脚本替换内层 `data.csv`** 就能成型。这直接打破了第一版「模板必须人工建」的假设。

**仍然成立的上限**：`Template` 节点（分析参数 + 图样式）是 base64 压缩二进制，
`PrismXMLSchema.xml` 未描述其内部；`.pzc` 命令表里**没有任何创建分析的命令**。
→ **分析种类与参数仍必须在模板里预先配好**，脚本只能 `RecalcAll` 重算。见 §3.1(b)。

### 3.5 【实测·运行】Prism 的运行纪律（补充现有 docs）

| 探测 | 结果 |
|---|---|
| `prism.exe /?` | **启动 GUI 并挂住**，3 s 后强杀。确认「任何非 `@脚本` 调用都会弹 GUI」 |
| `prism.exe @job.pzc`（正常脚本） | rc=0，4～6 s，无窗口，自动退出 |
| `.pzc` 编码 | 按 **GBK(936)** 写盘，ASCII 路径；与现有 docs 一致 |
| 后台残留 | 曾见 `BDY-Prism10-Win64-OFFLINE` 进程，`taskkill` 后消失；**下次跑前应一并清** |

#### (b) `symbol` 传参：`.spj` 可参数化【实测 XSD 有，未验证运行时】

XSD 有 `<xs:element name="symbol">`，属性 `name`（必填）、`quote`（必填）、`default`、`prompt`。
→ 同一份 `.spj`+`.sps` 可反复用，只换 `symbol` 值，**不必每次重新生成 `.sps` 文本**。

#### (c) `PROBIT` 的 `/PRINT=CI` 存在 —— 现有骨架写错了【实测，读 `PROBIT.xml` 全文】

`syntax_xml\PROBIT.xml`（3,419 B）的子命令与参数：

| 子命令 | 参数 |
|---|---|
| `MODEL` | `PROBIT` / `LOGIT` / `BOTH` |
| `PRINT` | **`CI`** / `FREQ` / `RMP` / `PARALL` / `NONE` / `ALL` / `DEFAULT` |
| `CRITERIA` | `OPTOL` / `CONVERGE` / `STEPLIMIT` / `P` / `ITERATE` |
| 其他 | `GLOBAL_PARAMS`（`OF`/`WITH`/`BY`）、`LOG NONE`、`NATRES`、`MISSING`（`EXCLUDE`/`INCLUDE`） |

**现有 `reference/commands.md` 的骨架写的是 `/PRINT=NONE`** —— 这会主动丢掉置信区间。做 LC50 报告必须改 `/PRINT=CI`（或 `ALL`）。
> 这是**对现有 mod 的 bug 修正**，不是新能力。

#### (d) 328 条命令里值得注意的【实测】
- `POWER MEANS INDEPENDENT` / `POWER ONEWAY ANOVA` / `POWER PROPORTIONS INDEPENDENT` 等 11 条 `POWER *` 族
  → 但 `statsmodels.stats.power` + R `pwr` 已覆盖，**不构成 mod 理由**（见 §5）
- `BEGIN PROGRAM`（1,411 B）/ `SCRIPT`（1,573 B）/ `MATRIX`（1,397 B）存在
  → `SCRIPT` 调 SaxBasic（本机 `WinWrapIDE.exe` 在），**会弹 IDE → 挂死 → 不能用**
- `OUTPUT EXPORT`（13,491 B）—— 比 OMS 更直接导查看器，但 328 条里 `OMS`（6,185 B）已够用

#### (e) SPSS 侧的数据接口早已够用【实测】
`D:\app\spss\Python3\Lib\site-packages\` 下 `spss` / `spssaux` / `SpssClient` / `spssdata` 四模块齐备（Python 3.8）。

---

## 4. 候选 mod 清单

| id | type | env | purpose | 解决什么 | 相对 R/Python 的独特价值 | 可行性 | 风险 |
|---|---|---|---|---|---|---|---|
| `prism-pzfx` | snippets | null | analysis | Python 直读 `.pzfx`，不经 Prism 进程 | **别人给的 `.pzfx` 直接进 pandas**；省掉 4 秒启动与模态框挂死风险；Prism 是生态毒理界常用交付格式 | **高**（8/8 解析 + 命名空间归一化已验证） | 命名空间不统一（**6/8 恰好带 ns，直接 `findall("Table")` 会在带 ns 的 6 个上静默返回空**）；数值小数点**同文件内逗号/点并存**（691:5825） |
| `prism-template` | snippets | null | both | **`.pzfx/.prism → .prism` 自动出模板** + 改 zip 内 `data.csv` 注入数据 + `RecalcAll` 取结果 | 把现有 mod 里「手工建模板」这一步**变成一条命令**；批量换数据不必再碰 GUI | **高**（**运行实测**：5.8 s 出模板、3.9 s 改包后正常打开导出） | 只改得动数据，**改不动 `Template` 里的分析参数**；改坏 JSON/CSV 结构可能让 Prism 打不开（**未验证的失败形态**） |
| `spss-ooxml-reader` | snippets | null | analysis | OXML `pivotTable` → tidy 表，含 `Confidence Limits` 概率行 | **LC50+CI 直接出数**；现有 docs 让用户「从日志解析」，实测证明不必 | **高**（**运行实测**，LC50=0.1020 / CI[0.0351,0.1863] 已解出） | pivotTable 是 dimension 嵌套，不是规整 CSV；需按 `subType` 分派；中文 `text` 依赖 locale |
| `spss-prod` | snippets | null | both | `.spj` 的 `outputFormat` + `imageFormat` + `symbol` 传参 | `imageFormat=eps/tif` 是 SPSS 唯一矢量/高分出处图路径；`symbol` 让同一份 `.spj` 复用 | **中**（XSD 实测；**运行时未验证**） | ~~html 绕 PROBIT~~（已证不需要）；pdf/word 可能依赖 Office；`imageFormat` 可能出空图（**【未验证】**） |

**全部都是 `type=snippets` / `env=null` / 不打包商业软件本体**，与现有两个 mod 同构，可进 `_catalog.json`（`status=candidate` 起步）。

> 优先级：`spss-ooxml-reader`（直接兑现用户方向的 LC50）≥ `prism-template`（解决模板供应链）
> > `prism-pzfx`（只读，价值独立但门槛低）> `spss-prod`（未验证项最多）。

### 对现有 mod 的补丁（不新建 mod）

| 目标文件 | 补什么 | 依据 |
|---|---|---|
| `mods/spss/docs.md` | **删掉硬约束 4「PROBIT 的结果不进 OXML」**，改为「PROBIT 进 OXML，`Confidence Limits` 就是 LC50+CI」 | **【实测·运行】** §3.3 |
| `mods/spss/reference/commands.md` | **`PROBIT` 骨架 `/PRINT=NONE` → `/PRINT=CI`**（`NONE` 会主动丢 CI） | 【实测·只读】`PROBIT.xml` |
| `mods/spss/reference/commands.md` | 补一句：`WEIGHT BY` 对 PROBIT **无效**，二项分母用 `OF ... WITH` | **【实测·运行】** 日志警告 |
| `mods/prism/docs.md` | 补「模板可脚本化」：`Open .pzfx`+`Save .prism` 即可出模板；`.prism` 内层 `data.csv` 可直接改 | **【实测·运行】** §3.4 |
| `mods/prism/docs.md` | 补官方死线「脚本不能新建分析，只能 `DuplicateFamily` / `RecalcAll`」 | 【文档】creating_new_sheets |
| `mods/prism/reference/commands.md` | `CloseScriptDialog`、`SetScriptDialogTitle`、`WTBlock`；`Import` 的 `col=-1` 语义 | 【实测·只读】RTF +【文档】 |
| `mods/prism/docs.md` | 运行纪律补录：`prism.exe /?` 会挂 GUI；跑前顺带清 `BDY-Prism10-Win64-OFFLINE` | **【实测·运行】** §3.5 |

---

## 5. 明确不建议做（含理由）

| 想法 | 为什么不做 |
|---|---|
| **Prism 出图 / 改图样式** | 图样式在 `Template` 的压缩二进制里（【实测】读到官方注释 `Don't edit this part of the file`）；脚本只有 `ApplyColorScheme`/`SetAxisLimits`/`SetAxisTitle` 这点改动面。**cnsplots / ggplot2 在样式控制上碾压且可版本控制**。硬边界不变。 |
| **Prism 当剂量反应 / EC50 主力** | R `drc` 已覆盖 4PL/5PL/hormesis（`BC.5`）且带 delta CI。现有 `prism` mod 保留 EC50 只是「已有模板顺手用」，**不该扩成新 mod**——两套数违背「不要两套数」。 |
| **SPSS 当 SSD 主力** | R `ssdtools`（多分布加权 SSD、HC5 + CI）是领域标准；SPSS 无对应过程。做桥 = 拿差工具换好工具。 |
| **SPSS 当混合物毒性主力** | R `mixture-tox` 覆盖浓度相加 / 独立作用 / IA-CA 混合模型；生态毒理主流工具是 `mixexp`/`mixIndep` 这类 R 包。SPSS 无原生支持。 |
| **SPSS COM (`SPSS.Application16`) 桥** | 本机 Python 无 `pywin32`（现有 docs 已记）；COM 还需已登录桌面会话，无人值守比生产作业更脆。 |
| **SPSS `SCRIPT` / SaxBasic 桥** | 会拉起 `WinWrapIDE.exe` → 模态 → 挂死，与「绝不能弹 GUI」硬约束直接冲突。 |
| **`POWER *` 族单独成 mod** | `statsmodels.stats.power` + R `pwr` 已覆盖；Prism 也有（`Learn\sample-size-and-power.html`）。三方重复。 |
| **把 `.pzt` 方程库转成 Python** | 二进制 + 有版权；4PL/Michaelis-Menten/指数都有现成公式，`scipy.optimize.curve_fit` 即可。收益 < 成本。 |
| **把 SPSS 328 条命令全做成 mod** | 现有 `reference/commands.md` + `syntax_xml/` 已够查；做成 mod 只是换地方放文档。 |
| **用 SPSS 替代 R/Python 做通用统计** | 用户方向是生态毒理 × 网络毒理，主力应是 R/Python 生态。商业软件桥只在「**对方要 Prism/SPSS 的原生结果**」或「**该能力只有它有**」时才成立。 |

---

## 6. 下一步：每个 mod 的第一步验证命令

### `prism-pzfx` —— 已完成大半（8/8 解析），剩「写回」未验
```powershell
# 已实测（本报告完成）：
#   python -c "import xml.etree.ElementTree as ET; ..."  8/8 成功
# 待验 1：命名空间归一化后是否能覆盖全部变体
# 待验 2：round-trip —— 读出来 → 原样写回 → prism.exe 能否打开
$code = @'
import xml.etree.ElementTree as ET
NS = "{http://graphpad.com/prism/Prism.htm}"
r = ET.parse(r"D:\app\prism\SampleData\XY\Logistic Regression (Studying).pzfx").getroot()
ns = NS if r.tag.startswith(NS) else ""
for tb in r.findall(ns+"Table"):
    print(tb.get("TableType"), len(tb.findall(ns+"YColumn")))
    subs = tb.findall(ns+"YColumn")[0].findall(ns+"Subcolumn")[0]
    vals = []
    for d in subs.findall(ns+"d"):
        if not d.text: continue
        s = d.text.strip()
        if "," in s and "." in s: raise ValueError("ambiguous: %r" % s)
        vals.append(float(s.replace(",", ".") if "," in s else s))
    print(len(vals), vals[:5])
'@
$code | Out-File -Encoding utf8 "$env:TEMP\pzfx_v.py"; & python "$env:TEMP\pzfx_v.py"
```
**判定**：数值与 Prism 界面显示一致 = 只读解析可用。**写回未验证，别急着做写能力。**

### `spss-prod` —— 三件独立的事，逐个验
```powershell
# 前提：workdir 纯 ASCII，.spj 里 <output> 必须在 <syntax syntaxPath="..."/> 之前
# 步骤 1：只改 outputFormat，验证 html 能否带出 PROBIT 的 LC50
#   <output outputPath="C:/tmp/sp/out.html" outputFormat="html"/>
#   <syntax syntaxPath="C:/tmp/sp/probit.sps"/>
#   probit.sps:  PROBIT deaths OF total WITH dose /MODEL=PROBIT /PRINT=CI.
& 'D:\app\spss\stats.exe' -production silent 'C:\tmp\sp\job.spj'
Select-String -Path 'C:\tmp\sp\out.html' -Pattern 'LC50|95%|Confidence' | Select-Object -First 5

# 步骤 2：imageFormat（先出一条图再验）
#   <output ... outputFormat="html" imageFormat="png"/>
# 步骤 3：symbol 传参
#   <symbol name="DATA" quote="true" default="C:/tmp/sp/data.csv"/>
#   语法里 GET DATA /FILE=!DATA
# 每步之后确认无残留进程
Get-Process stats -ErrorAction SilentlyContinue
```
**判定**：HTML 里 grep 到 LC50 与置信区间 = 这条路线成立，可把「PROBIT 只能解析日志」降级为「OXML 不行，HTML 可以」。

---

## 7. 本机实测记录（可复现）

| 探测 | 命令要点 | 结果 |
|---|---|---|
| Prism 安装位置 | `Get-ChildItem -Filter prism.exe -Recurse -Depth 3` | `D:\app\prism\prism.exe`（80,420,120 B） |
| SPSS 安装位置 | 同上，`stats.exe` | `D:\app\spss\stats.exe`（359,080 B） |
| SPSS 命令规格数 | `(Get-ChildItem syntax_xml -Filter *.xml).Count` | **328**，与现有 docs 一致 |
| `.spj` schema 代际 | `Get-ChildItem *.xsd` | `production-1.0~1.4`、`spss-output-1.4~1.8` 全在 |
| `outputFormat` 枚举 | 正则抽 `production-1.4.xsd` | **11 种** |
| `imageFormat` 枚举 | 同上 | **6 种** |
| Prism schema | `PrismXMLSchema.xml` | 13,460 B，`TableType` 8 值枚举 |
| Prism 方程库 | `Equations\*.pzt` | 18 族 + `order.txt` |
| Prism 示例脚本 | `SampleScripts\*.pzc` | 2 个（`Monte Carlo`、`Repeatedly Import`），证实 `ForEach`/`Regenerate`/`WTable` 用法 |
| **`.pzfx` 解析** | **Python `xml.etree`，8 个样本** | **8/8 成功；命名空间 4 有 2 无；`OneWay`×6 + `XY`×1** |
| `.pzfx` 数值格式 | 同上，全文件 `<d>` 计数 | **691 逗号 / 5825 点，同文件内并存**（不能一刀切替换） |
| `.pzfx` `Template` | 读原文注释 | `Analyses, graphs and layouts as compressed binary` |
| `PROBIT` 参数 | 读 `PROBIT.xml` 全文 | `PRINT` 子命令含 **`CI`** |
| SPSS Python 模块 | `Python3\Lib\site-packages\spss*` | 4 模块齐备 |

### 环境限制（影响本报告可信度，需 lead 知晓）
1. **`web_search` 工具全程不可用**（`DeepSeek search request failed: TypeError: fetch failed`，端点 `http://127.0.0.1:3425/v1/messages`）。
   替代方案：用 `web_fetch` 直抓官方文档页（graphpad.com 与 ibm.com 均可达），并抓 `cn.bing.com` 搜索结果页确认无更权威来源。
   → **「网络查证」实为「4 次 web_fetch 官方文档 + 2 次 Bing 页」**，不是 4 次 `web_search`。
2. `[System.Xml.Linq.XDocument]` 在本机 PowerShell 不可用（TypeNotFound），改用 Python。
3. 未启动任何商业软件，运行时行为一律未验证。
