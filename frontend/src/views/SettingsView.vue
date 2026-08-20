<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { api } from '../api/client'
import AppShell from '../components/AppShell.vue'
import type { HealthResponse } from '../types'

const health = ref<HealthResponse | null>(null)
const loading = ref(true)
const error = ref('')

async function loadHealth() {
  loading.value = true
  error.value = ''
  try {
    health.value = await api.health()
  } catch (reason) {
    health.value = null
    error.value = reason instanceof Error ? reason.message : '服务状态检查失败。'
  } finally {
    loading.value = false
  }
}

onMounted(loadHealth)

const services = [
  { key: 'sqlite', label: 'SQLite', detail: '文档与评测元数据' },
  { key: 'qdrant', label: 'Qdrant', detail: '向量索引与检索' },
  { key: 'ollama', label: 'Ollama', detail: '本地 bge-m3 Embedding' },
] as const
</script>

<template>
  <AppShell title="模型设置" subtitle="确认本地服务与在线 LLM 配置状态">
    <section class="settings-grid">
      <div class="service-panel">
        <p class="section-kicker">运行状态</p>
        <h2>依赖服务</h2>
        <div v-if="loading" class="empty-inline">正在检查…</div>
        <div v-else-if="error" class="error-message compact" role="alert">
          <span>{{ error }}</span><button type="button" @click="loadHealth">重试</button>
        </div>
        <ul v-else class="service-list">
          <li v-for="service in services" :key="service.key">
            <div><strong>{{ service.label }}</strong><span>{{ service.detail }}</span></div>
            <span class="service-state" :class="health?.services[service.key] === 'ok' ? 'ok' : 'unavailable'">
              {{ health?.services[service.key] === 'ok' ? '正常' : '不可用' }}
            </span>
          </li>
          <li>
            <div><strong>在线 LLM</strong><span>生成带引用答案与运行 Judge 评测</span></div>
            <span class="service-state" :class="health?.services.llm === 'configured' ? 'ok' : 'unavailable'">
              {{ health?.services.llm === 'configured' ? '已配置' : '未配置' }}
            </span>
          </li>
        </ul>
      </div>

      <div class="config-panel">
        <p class="section-kicker">项目根目录 .env</p>
        <h2>需要配置的变量</h2>
        <p>模型密钥只保存在本地 `.env`。前端不会读取或显示密钥内容。</p>
        <dl class="config-list">
          <div><dt>RAG_LLM_BASE_URL</dt><dd>OpenAI 兼容 API 地址</dd></div>
          <div><dt>RAG_LLM_API_KEY</dt><dd>在线 LLM 密钥</dd></div>
          <div><dt>RAG_LLM_MODEL</dt><dd>聊天模型名称</dd></div>
          <div><dt>RAG_EMBEDDING_MODEL</dt><dd>默认 bge-m3</dd></div>
          <div><dt>RAG_QDRANT_URL</dt><dd>本地 Qdrant 地址</dd></div>
        </dl>
      </div>
    </section>
  </AppShell>
</template>
