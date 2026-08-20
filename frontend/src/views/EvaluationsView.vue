<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { api } from '../api/client'
import AppShell from '../components/AppShell.vue'
import type { EvaluationRun } from '../types'

const dataset = ref('')
const runs = ref<EvaluationRun[]>([])
const running = ref(false)
const error = ref('')
const runsState = ref<'loading' | 'ready' | 'error'>('loading')

async function loadRuns() {
  try {
    runs.value = (await api.evaluationRuns()).items
    runsState.value = 'ready'
  } catch {
    runs.value = []
    runsState.value = 'error'
  }
}

async function runEvaluation() {
  error.value = ''
  running.value = true
  try {
    const cases = dataset.value
      .split('\n')
      .filter((line) => line.trim())
      .map((line) => JSON.parse(line))
    if (!cases.length) throw new Error('请先粘贴至少一条 JSONL 评测用例。')
    const result = await api.runEvaluation(cases)
    runs.value = [result, ...runs.value]
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '评测运行失败。'
  } finally {
    running.value = false
  }
}

function percent(value: number) {
  return `${Math.round(value * 100)}%`
}

onMounted(loadRuns)
</script>

<template>
  <AppShell title="评测中心" subtitle="用固定问题集检验检索、引用与响应时间">
    <section class="evaluation-runner">
      <div class="runner-copy">
        <p class="section-kicker">本地 JSONL</p>
        <h2>运行一组可重复评测</h2>
        <p>每行包含问题和预期文档 ID。实际评测数据只用于本次请求，报告写入本地存储目录。</p>
      </div>
      <label for="evaluation-data">评测用例</label>
      <textarea
        id="evaluation-data"
        v-model="dataset"
        rows="6"
        spellcheck="false"
        placeholder='{"case_id":"skill-001","question":"岗位要求什么？","expected_document_ids":["文档 ID"]}'
      ></textarea>
      <div class="runner-actions">
        <p v-if="error" class="field-error" role="alert">{{ error }}</p>
        <button type="button" :disabled="running" @click="runEvaluation">
          {{ running ? '评测运行中' : '开始评测' }}
        </button>
      </div>
    </section>

    <section class="data-section" aria-labelledby="runs-heading">
      <div class="section-heading-row">
        <div><p class="section-kicker">历史结果</p><h2 id="runs-heading">评测运行</h2></div>
        <span>{{ runs.length }} 次</span>
      </div>
      <div v-if="runsState === 'loading'" class="empty-state">正在读取评测记录…</div>
      <div v-else-if="runsState === 'error'" class="empty-state">
        <strong>评测记录加载失败</strong>
        <p>确认后端服务后重试。</p>
        <button class="secondary-button" type="button" @click="loadRuns">重新加载</button>
      </div>
      <div v-else-if="!runs.length" class="empty-state">
        <strong>还没有评测结果</strong>
        <p>导入资料并准备一组固定问题后，第一次结果会显示在这里。</p>
      </div>
      <article v-for="run in runs" :key="run.id" class="evaluation-result">
        <header><div><strong>{{ run.case_count }} 个问题</strong><span>{{ new Date(run.created_at).toLocaleString('zh-CN') }}</span></div><code>{{ run.id.slice(0, 8) }}</code></header>
        <dl>
          <div><dt>检索命中率</dt><dd>{{ percent(run.metrics.retrieval_hit_rate) }}</dd></div>
          <div><dt>Faithfulness</dt><dd>{{ percent(run.metrics.faithfulness) }}</dd></div>
          <div><dt>引用完整率</dt><dd>{{ percent(run.metrics.citation_completeness) }}</dd></div>
          <div><dt>P95 响应时间</dt><dd>{{ Math.round(run.metrics.latency_p95_ms) }} ms</dd></div>
        </dl>
      </article>
    </section>
  </AppShell>
</template>
