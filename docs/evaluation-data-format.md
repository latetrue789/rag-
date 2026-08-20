# 本地评测数据格式

评测数据使用 UTF-8 JSONL 文件，每行一个问题。实际评测集包含你的文档 ID 和问题，放在本地即可，不要提交 GitHub。

```json
{"case_id":"skill-001","question":"这个岗位需要哪些后端技能？","expected_document_ids":["替换为导入后的文档 ID"]}
```

字段说明：

- `case_id`：用例的稳定唯一标识。
- `question`：向知识库提出的问题。
- `expected_document_ids`：预期出现在 Top-K 来源中的一个或多个文档 ID。

运行后会统计检索命中率、Faithfulness、引用完整率，以及平均/P95 总响应时间。JSON 和 Markdown 报告默认写入 `storage/evaluations/`，该目录被 Git 忽略。
