<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'

import { api } from '../api/client'
import AppShell from '../components/AppShell.vue'
import type {
  DocumentItem,
  DocumentScanStatus,
  DocumentScanSummary,
} from '../types'

const documents = ref<DocumentItem[]>([])
const scanStatus = ref<DocumentScanStatus | null>(null)
const loading = ref(true)
const error = ref('')
const deleting = ref('')
const retrying = ref('')
const scanning = ref(false)
let refreshTimer: number | undefined

async function loadDocuments() {
  loading.value = true
  error.value = ''
  try {
    const [documentResponse, statusResponse] = await Promise.all([
      api.documents(),
      api.documentScanStatus(),
    ])
    documents.value = documentResponse.items
    scanStatus.value = statusResponse
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '资料状态加载失败。'
  } finally {
    loading.value = false
  }
}

async function refreshStatus() {
  try {
    const [documentResponse, statusResponse] = await Promise.all([
      api.documents(),
      api.documentScanStatus(),
    ])
    documents.value = documentResponse.items
    scanStatus.value = statusResponse
  } catch {
    // Background refresh stays quiet; the visible retry handles blocking errors.
  }
}

async function scanNow() {
  if (scanning.value) return
  scanning.value = true
  error.value = ''
  try {
    const result = await api.scanDocuments()
    scanStatus.value = scanStatus.value
      ? { ...scanStatus.value, scanning: false, last_scan: result }
      : null
    await refreshStatus()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '扫描失败，请检查本地服务。'
  } finally {
    scanning.value = false
  }
}

async function removeDocument(document: DocumentItem) {
  if (document.status !== 'missing') return
  if (!window.confirm(`确认清除“${document.filename}”的知识库向量和记录？本地原文件不会被删除。`)) return
  deleting.value = document.id
  error.value = ''
  try {
    await api.deleteDocument(document.id)
    documents.value = documents.value.filter((item) => item.id !== document.id)
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '清除失败。'
  } finally {
    deleting.value = ''
  }
}

async function retryDocument(document: DocumentItem) {
  retrying.value = document.id
  error.value = ''
  try {
    await api.retryDocument(document.id)
    await refreshStatus()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '重试失败。'
  } finally {
    retrying.value = ''
  }
}

function formatDate(value: string | null | undefined) {
  if (!value) return '尚未扫描'
  return new Intl.DateTimeFormat('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}

function statusText(status: DocumentItem['status']) {
  return {
    pending: '等待索引',
    indexed: '已索引',
    failed: '索引失败',
    missing: '源文件已移除',
    deleted: '已删除',
  }[status]
}

function scanSummary(result: DocumentScanSummary | null | undefined) {
  if (!result) return '等待首次扫描'
  if (result.busy) return '已有扫描任务正在运行'
  const changes = [
    result.indexed ? `新增或更新 ${result.indexed}` : '',
    result.missing ? `待确认清除 ${result.missing}` : '',
    result.failed ? `失败 ${result.failed}` : '',
    result.waiting ? `等待文件稳定 ${result.waiting}` : '',
    result.oversized ? `超限 ${result.oversized}` : '',
  ].filter(Boolean)
  return changes.length ? changes.join(' · ') : '没有发现变化'
}

onMounted(() => {
  void loadDocuments()
  refreshTimer = window.setInterval(() => void refreshStatus(), 15_000)
})

onUnmounted(() => {
  if (refreshTimer !== undefined) window.clearInterval(refreshTimer)
})
</script>

<template>
  <AppShell title="文档管理" subtitle="把资料放进固定目录，系统会自动解析并更新知识库">
    <section class="import-guide sync-guide" aria-labelledby="sync-heading">
      <div class="sync-copy">
        <p class="section-kicker">自动同步目录</p>
        <h2 id="sync-heading">data/documents/</h2>
        <p>资料每 60 秒检查一次。文件内容没有变化时不会调用 Ollama，也不会重复生成向量。</p>
        <div class="directory-list" aria-label="推荐资料子目录">
          <span>md/</span><span>txt/</span><span>pdf/</span>
        </div>
      </div>
      <div class="sync-control" aria-live="polite">
        <span class="sync-state">
          {{ scanning || scanStatus?.scanning ? '正在扫描资料…' : scanSummary(scanStatus?.last_scan) }}
        </span>
        <small>上次扫描：{{ formatDate(scanStatus?.last_scan?.scanned_at) }}</small>
        <button
          class="primary-button"
          type="button"
          :disabled="scanning || scanStatus?.scanning"
          @click="scanNow"
        >
          {{ scanning || scanStatus?.scanning ? '扫描中' : '立即扫描' }}
        </button>
      </div>
    </section>

    <div v-if="error" class="error-message compact" role="alert">
      <span>{{ error }}</span><button type="button" @click="loadDocuments">重试加载</button>
    </div>

    <section class="data-section" aria-labelledby="documents-heading">
      <div class="section-heading-row">
        <div><p class="section-kicker">知识库内容</p><h2 id="documents-heading">资料状态</h2></div>
        <span>{{ documents.length }} 份</span>
      </div>
      <div v-if="loading" class="empty-state">正在读取资料状态…</div>
      <div v-else-if="!documents.length" class="empty-state">
        <strong>知识库还是空的</strong>
        <p>把 Markdown、TXT 或可复制文字的 PDF 放入上方对应子目录，系统会自动处理。</p>
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
              <td class="document-actions">
                <button
                  v-if="document.status === 'missing'"
                  class="text-button danger"
                  type="button"
                  :disabled="deleting === document.id"
                  @click="removeDocument(document)"
                >
                  {{ deleting === document.id ? '清除中' : '确认清除' }}
                </button>
                <button
                  v-else-if="document.status === 'failed'"
                  class="text-button"
                  type="button"
                  :disabled="retrying === document.id"
                  @click="retryDocument(document)"
                >
                  {{ retrying === document.id ? '重试中' : '重试' }}
                </button>
                <span v-else class="no-action">自动维护</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </AppShell>
</template>
