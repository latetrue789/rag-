<!--
THESIS: 证据工作台拒绝聊天产品的气泡堆叠，以导航脊柱和连续阅读区组织任务。
OWN-WORLD: 深海军蓝侧栏、冷白工作面、钴蓝单一信号、克制圆角与结构性边界。
STORY: 用户先看清服务是否可用，再完成提问、核对来源，并按需进入资料和评测。
FIRST VIEWPORT: 左侧 232px 导航，右侧标题与状态同排，主任务在首屏剩余空间内展开。
FORM: Operate 模式的固定工作台；沿用用户确认的方案 A，无随机种子。
-->
<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'

import { api } from '../api/client'
import type { HealthResponse } from '../types'

defineProps<{ title: string; subtitle: string }>()

const health = ref<HealthResponse | null>(null)
const healthState = ref<'checking' | 'ready' | 'error'>('checking')

onMounted(async () => {
  try {
    health.value = await api.health()
    healthState.value = 'ready'
  } catch {
    health.value = null
    healthState.value = 'error'
  }
})
</script>

<template>
  <div class="app-shell">
    <aside class="sidebar">
      <RouterLink class="brand" to="/" aria-label="RAG 求职知识库首页">
        <span class="brand-mark" aria-hidden="true">R</span>
        <span>RAG 求职知识库</span>
      </RouterLink>

      <nav class="primary-nav" aria-label="主要导航">
        <RouterLink to="/" exact-active-class="is-active">
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m12 3 1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8L12 3Z" /></svg>
          <span>智能问答</span>
        </RouterLink>
        <RouterLink to="/documents">
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 3h9l4 4v14H6V3Zm9 1v4h4M9 12h7M9 16h7" /></svg>
          <span>文档管理</span>
        </RouterLink>
        <RouterLink to="/evaluations">
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 19V9m6 10V5m6 14v-7m4 7H2" /></svg>
          <span>评测中心</span>
        </RouterLink>
        <RouterLink to="/settings">
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 8.5a3.5 3.5 0 1 0 0 7 3.5 3.5 0 0 0 0-7Zm8 3.5-2.1-1.1.2-2.4-2.6-1.5-2 1.3L11.5 7 9 8.3 7 7 4.4 8.5l.2 2.4L2.5 12l2.1 1.1-.2 2.4L7 17l2-1.3 2.5 1.3 2-1.3 2 1.3 2.6-1.5-.2-2.4L20 12Z" /></svg>
          <span>模型设置</span>
        </RouterLink>
      </nav>

      <div class="sidebar-version">本地工作台 · v{{ health?.version ?? '0.1.0' }}</div>
    </aside>

    <main class="workspace">
      <header class="workspace-header">
        <div>
          <h1>{{ title }}</h1>
          <p>{{ subtitle }}</p>
        </div>
        <div class="service-badge" :class="{ offline: healthState === 'error', checking: healthState === 'checking' }">
          <span aria-hidden="true"></span>
          {{ healthState === 'checking' ? '正在检查' : health ? '服务已连接' : '服务未连接' }}
        </div>
      </header>
      <slot />
    </main>
  </div>
</template>
