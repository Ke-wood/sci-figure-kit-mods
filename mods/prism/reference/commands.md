# Prism 脚本命令参考（10.6）

来源：本机 `{root}/prism/ScriptHelper.rtf`（Prism 自带命令帮助）+ `SampleScripts/`。
`[必填] <可选>`；`//` 单行注释，`/* */` 块注释。

## 文件与工程

| 命令 | 作用 | 备注 |
|---|---|---|
| `Open [Prism 文件]` | 打开工程 | 打开 `.prism` / `.pzfx` 都行 |
| `Save <文件名>` | 另存 | **没有 `SaveAs`**；不写文件名则原地保存 |
| `Close` | 关闭工程 | |
| `SetPath [目录]` | 设定后续相对路径的基准 | 建议永远写绝对 ASCII 路径 |
| `SetProjectName [名字]` | 改工程名 | |
| `OpenOutput [文件], <clear>, <分隔符>` | 打开文本输出 | `.pzc` 里也靠它写日志 |
| `CloseOutput` | 关闭文本输出 | |

## 数据表

| 命令 | 作用 |
|---|---|
| `Import <文件名>, <row>, <col>` | 导入 CSV/文本到当前数据表（按位置） |
| `ImportLink <文件名>, <row>, <col>, <subcol>` | 导入并保持链接（源改则图改） |
| `InsertData <row>, <col>, <subcol>` + `<data>…</data>` | 把数据直接写进脚本再插入 |
| `InsertDataLink <row>, <col>, <subcol>` | 插入链接式数据 |
| `ClearTable <row>, <col>, <subcol>` | 清空表 |
| `Copy [行数] [列数] [首行] [首列] <首子列>` / `Paste [首行] [首列] <首子列>` | 表格间复制粘贴 |
| `SetYReplicates [#]` | 设 Y 重复数 |
| `DuplicateDataTable <clear>` / `DuplicateFamily <前缀> <clear>` | 复制表 / 复制一族 |
| `DeleteAllDataSets <clear>` | 清空所有数据 |
| `ExportTable [文件名] <ALL>` | 导出数据表 |

## 图

| 命令 | 作用 |
|---|---|
| `ApplyColorScheme [方案名]` | 套配色方案 |
| `SetAxisLimits [X Y Y2] <段号> [下, 上, 间隔号]` | 轴范围 |
| `SetAxisTitle <X Y Y2> [标题]` | 轴标题（中文要 GBK 写 `.pzc`） |
| `SetGraphTitle [标题]` | 图标题 |
| `CreateLayout [#行] [#列] <方向> <起始图号> <图数>` | 拼版 |
| `Print` | 打印 |

导出（`[文件名]` 必填，其余可选）：

```
ExportSVG <background> <clear>     ExportPDF <mode> <clear>     ExportAllPDF <mode> <clear>
ExportEPS <mode> <nofonts>         ExportPNG                     ExportJPG <resolution>
ExportTIF <resolution> <mode> <compress>                          ExportBMP <resolution>
ExportEMF <background> <clear>     ExportWMF <background> <clear>
Copy / SendToWord / SendToPP
```

> 图**样式**（字体、柱形、误差棒、图例）只能模板里配，脚本改不了；
> `ExportSVG` 要 10.6+。

## 结果表 → 文本 / 表格

```
Table Prism [#] <clear>     Table Text <&> <分隔符>
Table CSV <分隔符>          Table HTML <border #> <width #>
Table XML [文件名]          Table SQL [数据源] [表名] [登录] [密码] <clear>

WTable [列标题] [行] [列] <子列>    → 写一格；第一个参数是新表的列标题
WCell [行], [列] <子列>            WRow [行] <列> <子列>
WCol [行], [列]                    WBlock [行] [列] <行标题>
EndTable                            NextRow
```

`WTitle / WVersion / WText / WDate / WSheet / WTCol / WTRow / WTSheet / WBlock` 是文本输出版本。

## 流程与控制

| 命令 | 作用 |
|---|---|
| `GoTo <section> <sheet> <view>` | 跳到 数据(D)/结果(R)/图(G) 的第 n 个 |
| `GoTo +` | 下一个 |
| `RecalcAll` | **真的重算**（不是读缓存） |
| `ForEach [文件规格]` … `Next` | 遍历文件；`%F` 文件名、`%X` 扩展名、`%N` 循环号、`%S` 当前表名 |
| `ForEachSheet` … `Next` | 遍历表 |
| `ForEach [#循环次数]` + `Regenerate` … `Next` | 模拟 |
| `Beep` | 响一声 |
| `SetSheetTitle [新名] <K>` | 改表名 |
| `SetInfo [值] <行号> <位置>` | 写脚本信息 |
| `CreateLog` | 建日志 |
| `Exit` | **关掉所有文件、不保存、不询问、退出**（脚本必须以它结尾） |

## 实测过的坑（本机 + 朋友项目）

- `GoTo R n` 的编号与分析的 `viewIdx` 对不上，某些 view 直接 `No such sheet!` 并挂死；
  结果表编号要靠「连续导 R1..RN，看哪张断掉」探明。
- 脚本任何命令报错 → 模态框 → **永久挂死**，没有退出码。
- 脚本改了数据不保存就退出 → 「是否保存」→ 同样挂死。`Exit` 避开。
- `.pzc` 按系统 ANSI（GBK）解码，路径与脚本都必须是纯 ASCII。
