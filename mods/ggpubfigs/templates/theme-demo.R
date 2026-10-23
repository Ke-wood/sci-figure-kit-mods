# figwork: name=ggpubfigs 期刊主题与色盲安全配色
# figwork: size=nature1
# figwork: dpi=300
# figwork: out=out.png
# figwork: vector=pdf,svg
#
# 这是**自带示例数据**的模板：项目里不需要有 data.csv，建完项目直接就能出图，
# 用来看清这个 mod 到底提供什么 —— 8 个现成主题 + 15 个色盲安全色板。
#
# 换成自己的数据：把下面 df 的构造整段换成
#     df <- read.csv("data.csv", check.names = FALSE)
# 并在 front-matter 里补一行 `# figwork: data=data.csv`。
#
# ⚠️ check.names = FALSE 不是可有可无的：R 默认会把表头里的空格换成点、把数字
#    开头的列名前面加个 X，于是脚本里每一处列名引用都会**静默**失配 —— 报错在
#    很远的地方，原因在这里。这是最常见的「先算后画」翻车点。

suppressPackageStartupMessages({
  library(ggplot2)
  library(ggpubfigs)
  library(showtext)
  library(sysfonts)
})

# ---- 示例数据：三组，各 8 个时间点 ----
df <- data.frame(
  grp = rep(c("对照组", "处理组", "恢复组"), each = 8),
  t   = rep(1:8, times = 3),
  y   = c(1.0, 1.2, 1.1, 1.4, 1.3, 1.5, 1.6, 1.5,
          2.1, 2.4, 2.2, 2.6, 2.5, 2.8, 2.7, 3.0,
          1.5, 1.6, 1.4, 1.7, 1.6, 1.8, 1.7, 1.9)
)

# ---- 作图 ----
# ⚠️ friendly_pal() 返回的是**色值向量**，不是 ggplot2 的 scale。
#    所以必须 scale_*_manual(values = ...)；写成 `+ friendly_pal(...)` 会报
#    Can't add <palette> to a <ggplot> object。
p <- ggplot(df, aes(t, y, colour = grp)) +
  geom_line(linewidth = .3, alpha = .5, aes(group = grp)) +
  geom_point(size = 1.5) +
  scale_colour_manual(values = friendly_pal("wong_eight", n = 3)) +
  labs(x = "时间点", y = "表达量（标准化）", colour = NULL) +
  # ⚠️ 实测 args(theme_simple) 是 function() —— **这些主题函数不接受任何参数**。
  #    写 theme_simple(base_size = 8) 会报 unused argument。字号要自己补，
  #    见下面那行 theme()。
  theme_simple()

# ---- 中文必须显式设字体，否则是方框 ----
# 用 showtext 而不是 cairo：本机的 r-cairo 钉在 R 4.1，与 R 4.6.1 不兼容。
# （这里说的是 R **包** Cairo；内置的 cairo_pdf 设备本身是好的 —— 见文件末尾。）
showtext_auto()
font_add("SimHei", "C:/Windows/Fonts/simhei.ttf")
p <- p + theme(text = element_text(family = "SimHei", size = 8),
               axis.title = element_text(family = "SimHei"))

# ---- 期刊尺寸：Nature 单栏 89mm / 双栏 183mm。必须与 front-matter 的 size= 一致。
#      这里的 89/60 与 front-matter 的 size=nature1 是同一件事的两种写法，
#      改一个必须改另一个（工作台的尺寸闸门查的就是这个一致性）。
ggsave("out.png", p, width = 89, height = 60, units = "mm", dpi = 300)

# ---- 矢量：投稿要 PDF，进 PPT 要 SVG ----
# ⚠️ 存矢量前**必须关掉 showtext**：它把字形画成多边形，于是 PDF 里没有字体、
#    SVG 里没有 <text>，两者都成了改不了的路径（工作台的矢量字体闸门会判失败）。
#    实测 cairo_pdf + family="SimHei" 不靠 showtext 也能正确出中文，所以关掉无损。
# ⚠️ 出 PDF 必须**显式写 device = cairo_pdf**：ggsave 按扩展名默认挑的是 pdf()，
#    它会报 invalid font type，中文还会 mbcsToSbcs 转换失败。
# ⚠️ 出 SVG 用 svglite::svglite，不能靠 ggsave 的默认 svg() 设备。
showtext_auto(FALSE)
ggsave("out.pdf", p, width = 89, height = 60, units = "mm", device = cairo_pdf)
ggsave("out.svg", p, width = 89, height = 60, units = "mm",
       device = svglite::svglite)

# ---------------------------------------------------------------------------
# 别的色板：names(friendly_pals) 有 15 个，投稿常用 wong_eight / ito_seven /
#   tol_eight。连续型用 friendly_pal("viridis_eight", n = N, type = "continuous")。
# 别的主题：theme_grid / theme_big_grid / theme_big_simple / theme_black /
#   theme_blue / theme_grey / theme_red。
# 该 mod 的完整导出对象见 mods/ggpubfigs/docs.md。
