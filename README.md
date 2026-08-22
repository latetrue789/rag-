# RAG 求职知识库

一个面向个人求职的本地 RAG 知识库。把岗位 JD、官方文档、面试题笔记和学习资料导入后，可以查询岗位技能、检索面试题、生成学习建议，并查看每条回答引用的来源。

## 项目特点

- 支持 Markdown、TXT 和可提取文字的 PDF。
- 使用 Ollama `bge-m3` 生成本地 Embedding。
- 使用 Qdrant 做向量检索，SQLite 保存文档与评测元数据。
- LLM 使用 OpenAI 兼容 API，可替换服务地址和模型。
- 事实性回答使用 `[S1]`、`[S2]` 行内引用；无证据时明确拒答。
- 自动监控 `data/documents/`，支持增量索引、缺失确认清除、服务健康检查和 RAG 评测报告。
- Vue 工作台包含智能问答、文档管理、评测中心和模型设置。

## 技术栈

- 后端：Python 3.11、FastAPI、HTTPX、Pydantic Settings
- 前端：Vue 3、TypeScript、Vite
- 向量库：Qdrant
- 元数据：SQLite
- Embedding：Ollama + `bge-m3`
- 部署：Docker Compose、Nginx

## 资料与密钥边界

仓库不包含实际求职资料。请自行收集岗位 JD、官方文档、面试题笔记和学习资料。

## 本地开发（Windows PowerShell）

### 1. 启动 Ollama Embedding

```powershell
ollama pull bge-m3
ollama list
```

模型只需下载一次。Markdown、TXT、PDF 的读取由后端解析器完成；Ollama 只接收解析和切分后的文本，所以文件格式不由 Embedding 模型决定。

### 2. 启动 Qdrant

如果 `docker` 不在 PATH，可以使用 Docker Desktop 的完整路径：

```powershell
$dockerCli = "$env:LOCALAPPDATA\Programs\DockerDesktop\resources\bin\docker.exe"
& $dockerCli compose up -d qdrant
```

Qdrant 只绑定到本机 `127.0.0.1:6333`，不会直接监听公网网卡。

### 3. 创建本地 `.env`

在项目根目录创建 `.env`，按你的 LLM 服务填写：

```dotenv
RAG_LLM_BASE_URL=https://your-provider.example/v1
RAG_LLM_API_KEY=replace-with-your-local-key
RAG_LLM_MODEL=your-chat-model
RAG_EMBEDDING_BASE_URL=http://127.0.0.1:11434
RAG_EMBEDDING_MODEL=bge-m3
RAG_QDRANT_URL=http://127.0.0.1:6333
```

可选配置：

```dotenv
RAG_QDRANT_COLLECTION=job_knowledge_chunks
RAG_SQLITE_PATH=storage/app.db
RAG_CHUNK_SIZE=800
RAG_CHUNK_OVERLAP=120
RAG_RETRIEVAL_TOP_K=5
RAG_RETRIEVAL_SCORE_THRESHOLD=0.55
RAG_EVALUATION_REPORT_DIR=storage/evaluations
RAG_DOCUMENT_SCAN_INTERVAL_SECONDS=60
RAG_DOCUMENT_STABLE_SECONDS=10
RAG_DOCUMENT_MAX_SIZE_MB=25
RAG_EMBEDDING_BATCH_SIZE=32
```

### 4. 启动后端

标准方式：

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m uvicorn app.main:app --reload
```

如果 Windows 虚拟环境受中文用户路径影响，可以回到仓库根目录，使用项目本地依赖目录：

```powershell
$python311 = "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe"
& $python311 -m pip install --upgrade --target .python-packages ".\backend[dev]"
$env:PYTHONPATH = "$PWD\.python-packages;$PWD\backend"
& $python311 -m uvicorn app.main:app --reload --app-dir backend
```

API 默认地址是 `http://127.0.0.1:8000`，接口文档位于 `http://127.0.0.1:8000/docs`。

### 5. 放入资料

把资料放进项目根目录的对应子目录：

```text
data/documents/
├─ md/    Markdown 文档
├─ txt/   纯文本
└─ pdf/   可提取文字的 PDF
```

后端启动时扫描一次，此后默认每 60 秒扫描。网页“文档管理”页也可以点击“立即扫描”。没有变化的文件不会调用 Ollama；新文件需保持稳定 10 秒后才会处理，单文件默认上限为 25 MB。

资料只需放入一次，不需要每次提问都上传。修改文件会自动更新索引；从目录移除文件后，网页会显示“源文件已移除”，确认清除后才删除对应向量和记录。

### 6. 启动前端

打开另一个 PowerShell：

```powershell
cd frontend
npm install
npm run dev
```

访问 `http://127.0.0.1:5173`。Vite 会把 `/api` 请求代理到本地 FastAPI。

## 评测数据

评测输入使用 UTF-8 JSONL，每行一个问题：

```json
{"case_id":"skill-001","question":"这个岗位需要哪些后端技能？","expected_document_ids":["替换为导入后的文档 ID"]}
```

详细字段见 [docs/evaluation-data-format.md](docs/evaluation-data-format.md)。评测会生成检索命中率、Faithfulness、引用完整率、平均响应时间和 P95 响应时间。

## Docker Compose 演示

根目录 `.env` 配置完成且主机 Ollama 已启动后：

```powershell
$dockerCli = "$env:LOCALAPPDATA\Programs\DockerDesktop\resources\bin\docker.exe"
& $dockerCli compose up -d --build
```

访问 `http://127.0.0.1:8080`。前端只对外暴露一个入口；Qdrant 与后端通过 Compose 内部网络通信。

Compose 会把 `./data/documents` 只读挂载到后端容器。把资料放入三个分类目录后，后台会自动同步，无需执行额外导入命令。

如果容器无法访问主机 Ollama，请让 Ollama 监听主机接口后重启它。容器默认使用 `http://host.docker.internal:11434`；需要覆盖时在 `.env` 增加 `RAG_DOCKER_EMBEDDING_BASE_URL`。

## 测试

后端：

```powershell
cd backend
python -m pytest
python -m ruff check .
```

前端：

```powershell
cd frontend
npm run test -- --run
npm run typecheck
npm run build
```

普通测试使用 Fake Provider，不会调用收费 LLM API。

## API

- `POST /api/v1/ask`：带来源引用的 RAG 问答
- `GET /api/v1/documents`：文档与索引状态
- `GET /api/v1/documents/scan`：自动同步状态
- `POST /api/v1/documents/scan`：立即扫描固定资料目录
- `POST /api/v1/documents/{document_id}/retry`：重试失败文档
- `DELETE /api/v1/documents/{document_id}`：确认清除缺失文档及向量
- `POST /api/v1/evaluations/run`：运行评测用例
- `GET /api/v1/evaluations/runs`：查询评测结果
- `GET /api/v1/health`：检查 SQLite、Qdrant、Ollama 与 LLM 配置

## 公网部署提示

在自己的云服务器上可以继续使用本项目的 Docker Compose，不需要购买 Qdrant Cloud。云服务器本身、域名、在线 LLM API 和公网流量是否收费，取决于你选择的服务商。

正式公网部署前应增加 HTTPS 反向代理、访问控制、请求限速和备份策略。不要把 Qdrant 端口或 `.env` 直接暴露到公网。
