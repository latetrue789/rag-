<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { api } from '../api/client'
import AppShell from '../components/AppShell.vue'
import type { DocumentItem } from '../types'

const documents = ref<DocumentItem[]>([])
const loading = ref(true)
const error = ref('')
const deleting = ref('')

async function loadDocuments() {
  loading.value = true
  error.value = ''
  try {
    documents.value = (await api.documents()).items
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '资料列表加载失败。'
  } finally {
    loading.value = false
  }
}

async function removeDocument(document: DocumentItem) {
  if (!window.confirm(`确认从知识库删除“${document.filename}”？`)) return
  deleting.value = document.id
  error.value = ''
  try {
    await api.deleteDocument(document.id)
    documents.value = documents.value.filter((item) => item.id !== document.id)
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '删除失败。'
  } finally {
    deleting.value = ''
  }
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}

function statusText(status: DocumentItem['status']) {
  return { pending: '等待索引', indexed: '已索引', failed: '失败', deleted: '已删除' }[status]
}

onMounted(loadDocuments)
</script>

<template>
  <AppShell title="文档管理" subtitle="查看本地资料的解析与索引状态">
    <section class="import-guide">
      <div>
        <p class="section-kicker">从本地目录导入</p>
        <h2>先收集资料，再执行一次批量索引</h2>
        <p>支持 Markdown、TXT 和可复制文字的 PDF。内容不变的文件再次运行会自动跳过。</p>
      </div>
      <code>python -m app.cli ingest &lt;文件路径&gt;</code>
    </section>

    <div v-if="error" class="error-message compact" role="alert">
      <span>{{ error }}</span><button type="button" @click="loadDocuments">重试</button>
    </div>

    <section class="data-section" aria-labelledby="documents-heading">
      <div class="section-heading-row">
        <div><p class="section-kicker">知识库内容</p><h2 id="documents-heading">已导入资料</h2></div>
        <span>{{ documents.length }} 份</span>
      </div>
      <div v-if="loading" class="empty-state">正在读取资料状态…</div>
      <div v-else-if="!documents.length" class="empty-state">
        <strong>知识库还是空的</strong>
        <p>准备好岗位 JD、面试笔记或学习资料后，用上方命令完成首次导入。</p>
      </div>
      <div v-else class="document-table-wrap">
        <table class="document-table">
          <thead>
            <tr><th>文件</th><th>状态</th><th>片段</th><th>更新时间</th><th><span class="sr-only">操作</span></th></tr>
          </thead>
          <tbody>
            <tr v-for="document in documents" :key="document.id">
              <td><strong>{{ document.filename }}</strong><span>{{ document.file_type.toUpperCase() }}</span></td>
              <td>
                <span class="status-label" :class="document.status">{{ statusText(document.status) }}</span>
                <small v-if="document.error_message">{{ document.error_message }}</small>
              </td>
              <td>{{ document.chunk_count }}</td>
              <td>{{ formatDate(document.updated_at) }}</td>
              <td>
                <button class="text-button danger" type="button" :disabled="deleting === document.id" @click="removeDocument(document)">
                  {{ deleting === document.id ? '删除中' : '删除' }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </AppShell>
</template>
