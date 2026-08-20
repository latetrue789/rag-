# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

主要用户是正在投递 AI 应用开发岗位的个人求职者。当前使用者希望优先提升自身岗位竞争力，后续再将项目适配到跨境电商等具体业务方向。

## Product Purpose

把岗位 JD、官方文档、面试题笔记和学习资料整理为个人本地知识库。用户可以查询岗位技能、检索面试题并获得学习建议；成功标准是回答有明确来源、系统可评测、项目可复现并适合作为 GitHub 求职作品展示。

## Positioning

它不是通用聊天机器人，而是以个人求职资料为证据边界的 RAG 工作台：所有事实性结论都必须对应本次召回的来源，证据不足时明确拒答。

## Operating Context

首版在 Windows 本地运行，使用 FastAPI、Vue、SQLite、Qdrant、Ollama Embedding 与在线 OpenAI 兼容 LLM API。资料先自行收集并从本地目录批量导入；未来可部署到用户自己的云服务器。

## Capabilities and Constraints

- 支持 Markdown、TXT 和可提取文字的 PDF；首版不支持 OCR。
- 支持带引用问答、资料状态管理、删除、服务健康检查与固定评测集。
- 实际资料、SQLite、Qdrant 数据、评测集、报告与 `.env` 不提交 GitHub。
- 不提供登录、多用户、网页抓取、混合检索或 Reranker。
- LLM 与 Embedding Provider 独立，Embedding 首选本地 Ollama `bge-m3`。

## Brand Commitments

产品名固定为“RAG 求职知识库”。沟通与界面使用清晰、克制、直接的中文；不把具体行业写死在产品名称中。界面不出现“资料不会提交 GitHub”这类侧栏说明，隐私边界写入 README。

## Evidence on Hand

已有经用户确认的桌面端界面方向：深色窄侧栏、浅色内容区、单一蓝色强调色，问答页突出提问、答案和来源。当前仓库没有真实岗位资料或真实评测数据，后续界面示例只能作为演示内容，不能伪装成真实数据。

## Product Principles

- 引用正确优先于功能数量。
- 证据不足时拒答，不用模型常识补齐事实。
- 本地资料与公开代码严格分离。
- 核心链路可测试、可评测、可复现。
- 页面围绕求职任务组织，不围绕技术组件组织。

## Accessibility & Inclusion

Web 界面需支持键盘操作、清晰焦点、足够色彩对比、可读的中文字号和移动端响应式布局，并尊重减少动态效果的系统设置。
