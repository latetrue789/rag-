<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'

import { api } from '../api/client'
import AppShell from '../components/AppShell.vue'
import type { AskResponse, DocumentItem } from '../types'

const question = ref('')
const loading = ref(false)
const error = ref('')
const response = ref<AskResponse | null>(null)
const documents = ref<DocumentItem[]>([])
const documentState = ref<'loading' | 'ready' | 'error'>('loading')
const answerRegion = ref<HTMLElement | null>(null)
const highlightedSource = ref('')

const indexedDocuments = computed(() =>
  documents.value.filter((item) => item.status === 'indexed'),
)
const chunkCount = computed(() =>
  indexedDocuments.value.reduce((total, item) => total + item.chunk_count, 0),
)

onMounted(async () => {
  try {
    documents.value = (await api.documents()).items
    documentState.value = 'ready'
  } catch {
    documents.value = []
    documentState.value = 'error'
  }
})

async function submitQuestion() {
  const content = question.value.trim()
  if (content.length < 2 || loading.value) return
  loading.value = true
  error.value = ''
  try {
    response.value = await api.ask(content)
    await nextTick()
    answerRegion.value?.focus()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '问答失败，请稍后重试。'
  } finally {
    loading.value = false
  }
}

function useSuggestion(value: string) {
  question.value = value
}

function sourceLocation(source: AskResponse['sources'][number]) {
  if (source.page) return `第 ${source.page} 页`
  if (source.title) return source.title
  return `片段 ${source.chunk_index + 1}`
}

function answerParts(answer: string) {
  return answer.split(/(\[S\d+\])/g).filter(Boolean).map((text) => ({
    text,
    sourceId: /^\[(S\d+)\]$/.exec(text)?.[1] ?? null,
  }))
}

async function jumpToSource(sourceId: string) {
  highlightedSource.value = sourceId
  await nextTick()
  const target = document.getElementById(`source-${sourceId}`)
  target?.scrollIntoView?.({ behavior: 'smooth', block: 'center' })
  target?.focus({ preventScroll: true })
  window.setTimeout(() => {
    if (highlightedSource.value === sourceId) highlightedSource.value = ''
  }, 1800)
}
</script>

<template>
  <AppShell title="RAG 求职知识库" subtitle="岗位 JD、官方文档、面试题与学习资料">
    <section class="chat-toolbar" aria-label="知识库概况">
      <div v-if="documentState === 'ready'" class="library-count">
        <strong>{{ indexedDocuments.length }}</strong> 份已索引资料
        <span aria-hidden="true">·</span>
        <strong>{{ chunkCount }}</strong> 个知识片段
      </div>
      <div v-else class="library-count">
        {{ documentState === 'loading' ? '正在读取资料状态…' : '资料状态暂不可用' }}
      </div>
      <div class="scope-chips" aria-label="支持的资料类型">
        <span>岗位 JD</span><span>面试笔记</span><span>学习资料</span>
      </div>
    </section>

    <section class="ask-panel" aria-labelledby="ask-heading">
      <div class="ask-intro">
        <p class="section-kicker">基于已导入资料回答</p>
        <h2 id="ask-heading">今天想研究哪个岗位问题？</h2>
        <p>答案会显示行内引用；证据不足时，系统会直接告诉你还缺什么资料。</p>
      </div>

      <form class="question-form" @submit.prevent="submitQuestion">
        <label class="sr-only" for="question">输入求职问题</label>
        <textarea
          id="question"
          v-model="question"
          rows="2"
          maxlength="1000"
          placeholder="例如：目标岗位最常要求哪些 RAG 技能？"
          @keydown.ctrl.enter="submitQuestion"
        ></textarea>
        <button type="submit" :disabled="loading || question.trim().length < 2">
          <span v-if="loading" class="spinner" aria-hidden="true"></span>
          {{ loading ? '检索中' : '开始检索' }}
        </button>
      </form>
      <p class="input-hint">Ctrl + Enter 发送</p>

      <div v-if="!response && !error" class="suggestion-row">
        <span>可以这样问</span>
        <button type="button" @click="useSuggestion('这个岗位最常要求哪些后端技能？')">岗位技能</button>
        <button type="button" @click="useSuggestion('帮我找出常见的 RAG 面试题。')">面试准备</button>
        <button type="button" @click="useSuggestion('根据资料给我一份学习优先级建议。')">学习规划</button>
      </div>
      <div v-if="documentState === 'ready' && !indexedDocuments.length" class="empty-guidance">
        <span>还没有已索引资料，问答会返回证据不足。</span>
        <RouterLink to="/documents">前往文档管理</RouterLink>
      </div>
      <div v-if="error" class="error-message" role="alert">
        <strong>暂时无法回答</strong>
        <span>{{ error }}</span>
        <button type="button" @click="submitQuestion">重新尝试</button>
      </div>
    </section>

    <section v-if="response" ref="answerRegion" class="answer-section" tabindex="-1" aria-labelledby="answer-heading">
      <div class="answer-card">
        <div class="answer-meta">
          <span :class="response.grounded ? 'grounded' : 'ungrounded'">
            {{ response.grounded ? '已有来源支持' : '需要查看来源' }}
          </span>
          <span>总耗时 {{ Math.round(response.timings.total ?? 0) }} ms</span>
        </div>
        <h2 id="answer-heading">回答</h2>
        <p class="answer-copy">
          <template v-for="(part, index) in answerParts(response.answer)" :key="`${part.text}-${index}`">
            <button v-if="part.sourceId" class="citation-link" type="button" @click="jumpToSource(part.sourceId)">[{{ part.sourceId }}]</button>
            <template v-else>{{ part.text }}</template>
          </template>
        </p>
        <p v-if="response.rewritten" class="rewrite-note">系统已优化检索词后重试。</p>
      </div>

      <div class="sources-block">
        <div class="section-heading-row">
          <div><p class="section-kicker">本次检索证据</p><h2>引用来源</h2></div>
          <span>{{ response.sources.length }} 条</span>
        </div>
        <div v-if="response.sources.length" class="source-list">
          <article
            v-for="source in response.sources"
            :id="`source-${source.source_id}`"
            :key="source.source_id"
            class="source-item"
            :class="{ highlighted: highlightedSource === source.source_id }"
            tabindex="-1"
          >
            <span class="source-id">{{ source.source_id }}</span>
            <div>
              <h3>{{ source.filename }}</h3>
              <p class="source-place">{{ sourceLocation(source) }} · 相似度 {{ source.score.toFixed(2) }}</p>
              <p>{{ source.text }}</p>
            </div>
          </article>
        </div>
        <p v-else class="empty-inline">没有达到相似度阈值的来源，请先补充资料。</p>
      </div>
    </section>
  </AppShell>
</template>
