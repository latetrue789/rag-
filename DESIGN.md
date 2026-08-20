---
name: RAG 求职知识库
description: 清晰、可靠、以来源为中心的个人求职知识工作台
colors:
  navy-spine: "#081b31"
  navy-command: "#0d2744"
  signal-blue: "#2457dc"
  signal-blue-deep: "#1948c4"
  evidence-blue: "#e8efff"
  evidence-surface: "#f4f7ff"
  ink: "#121b2d"
  ink-muted: "#627189"
  canvas: "#f4f6f9"
  surface: "#ffffff"
  line: "#dce3ed"
  success: "#16764a"
  danger: "#b42333"
typography:
  headline:
    fontFamily: "Microsoft YaHei UI, PingFang SC, Segoe UI, sans-serif"
    fontSize: "clamp(27px, 3vw, 36px)"
    fontWeight: 750
    lineHeight: 1.18
    letterSpacing: "-0.03em"
  title:
    fontFamily: "Microsoft YaHei UI, PingFang SC, Segoe UI, sans-serif"
    fontSize: "clamp(21px, 2.5vw, 28px)"
    fontWeight: 700
    lineHeight: 1.3
    letterSpacing: "-0.025em"
  body:
    fontFamily: "Microsoft YaHei UI, PingFang SC, Segoe UI, sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.7
  label:
    fontFamily: "Microsoft YaHei UI, PingFang SC, Segoe UI, sans-serif"
    fontSize: "13px"
    fontWeight: 700
    lineHeight: 1.4
rounded:
  sm: "8px"
  md: "12px"
  lg: "16px"
  pill: "999px"
spacing:
  xs: "8px"
  sm: "12px"
  md: "20px"
  lg: "28px"
  xl: "40px"
components:
  button-primary:
    backgroundColor: "{colors.signal-blue}"
    textColor: "{colors.surface}"
    rounded: "{rounded.sm}"
    padding: "0 20px"
    height: "46px"
  button-primary-hover:
    backgroundColor: "{colors.signal-blue-deep}"
    textColor: "{colors.surface}"
    rounded: "{rounded.sm}"
  input-question:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    padding: "9px"
  source-card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    padding: "20px 22px"
---

# Design System: RAG 求职知识库

## Overview

**Creative North Star: "证据工作台"**

界面像一张专注工作的研究桌：左侧是稳定、沉静的导航脊柱，右侧是明亮且高密度的证据阅读区。视觉表达服务于“提问—得到有依据的回答—核对来源”这一条主流程，不使用营销式大标题、装饰插画或聊天气泡堆叠。

**Key Characteristics:**

- 深海军蓝窄侧栏与冷白内容区形成明确分区。
- 单一高纯度蓝色只标记当前操作、引用和主按钮。
- 文字层级紧凑，来源卡片比普通说明更醒目。
- 状态通过文字、图标和颜色共同表达，不只依赖颜色。

## Colors

采用 Restrained 策略：Canvas Gray 承载大面积工作区，Navy Spine 提供结构，Signal Blue 承担唯一交互强调，成功和错误色只用于状态。颜色值以 frontmatter 为准。

### Primary

- **Signal Blue**：当前导航、主要动作、焦点与来源编号。
- **Navy Spine**：侧栏和命令示例背景，稳定界面结构。

### Neutral

- **Canvas Gray**：应用工作区底色。
- **Evidence Surface**：回答区域底色，让生成结果与普通容器区分。
- **Ink / Ink Muted**：标题正文与辅助说明。
- **Line**：静止组件的结构边界。

**The One Signal Rule.** 主蓝色只用于当前导航、主要动作、焦点和引用；同一视口不引入第二种竞争性强调色。

## Typography

使用 Windows 与现代浏览器稳定支持的中文系统字体栈。标题通过字重、尺寸和紧凑字距建立权威感，正文保持自然行高，技术元数据与标签使用更小字号但不使用全大写装饰。

### Hierarchy

- **Headline**：页面唯一 H1，紧凑字距并随视口缩放。
- **Title**：页面内主任务标题和分区标题。
- **Body**：说明和结果正文，回答正文最大阅读宽度为 72ch。
- **Label**：导航、状态与操作标签，依赖字重而非大写建立层级。

**The Evidence Reads First Rule.** 回答正文和来源标题的可读性优先于品牌装饰；任何标签都不能比来源内容更抢眼。

## Layout

桌面端使用 232px 固定窄侧栏与最大 1320px 的弹性主内容区。主内容使用随视口变化的 28–72px 水平内边距，问答输入、答案和来源共享同一水平基线。900px 以下侧栏收拢为顶部导航；620px 以下隐藏导航文字并切换为单列，触控目标不小于 44px。

## Elevation & Depth

系统以色块分层和细边框为主。只有获得焦点的主问题输入区使用带垂直偏移的柔和阴影；普通卡片保持扁平，不同时叠加边框与常驻阴影。

**The Quiet Surface Rule.** 静止状态主要依赖边界与底色，阴影只表示层级或交互，不作为装饰。

## Shapes

组件使用 8px、12px、16px 三档圆角，保持专业但不僵硬。按钮、输入框、引用卡片共享这一家族；999px 只用于状态胶囊和短筛选标签。

## Components

### Buttons

- **Shape:** 紧凑矩形主按钮使用小圆角，最小高度 46px。
- **Primary:** Signal Blue 底色、白色文字；悬停时加深并上移 1px。
- **Focus:** 使用半透明蓝色 3px 外轮廓，不能只改变颜色。

### Chips

- **Style:** 白色或浅蓝底、细边界，仅用于短筛选、建议问题与状态。
- **State:** 选中态使用 Signal Blue，不增加第二种强调色。

### Cards / Containers

- **Corner Style:** 主容器使用大圆角，来源与数据容器使用中圆角。
- **Background:** 普通容器使用 Surface，回答使用 Evidence Surface。
- **Shadow Strategy:** 静止状态无阴影，依靠底色和结构边界区分。

### Inputs / Fields

- **Style:** 冷白底、清晰边界、可调整高度；问题输入与按钮组成一个连续操作区。
- **Focus:** 边界变为 Signal Blue，并出现有偏移的柔和阴影。
- **Error / Disabled:** 错误状态给出恢复动作；禁用按钮降低不透明度并改变鼠标状态。

### Navigation

桌面导航是深色固定脊柱，当前项以 Signal Blue 整块强调。移动端变为横向顶部导航，并在窄屏只保留图标与可访问名称。

### Source Item

来源编号、文件名、位置/相似度与原文按固定阅读顺序排列；来源编号使用 Evidence Blue，原文宽度不超过 78ch。

## Do's and Don'ts

### Do:

- **Do** 让答案、引用和当前系统状态在三秒内可扫读。
- **Do** 在空状态、错误状态和加载状态中提供下一步动作。
- **Do** 用短而具体的中文标签，避免抽象产品术语。
- **Do** 同时设计加载、空、错误、无依据与未配置状态。

### Don't:

- **Don't** 在侧栏展示“资料不会提交 GitHub”。
- **Don't** 使用渐变、拟物插画或大面积发光效果。
- **Don't** 把内容拆成过多同权重的小卡片。
- **Don't** 用卡片装饰代替真实来源、状态或操作内容。
