import { flushPromises, mount } from '@vue/test-utils'
import { createMemoryHistory, createRouter } from 'vue-router'
import { afterEach, vi } from 'vitest'

import App from '../src/App.vue'
import ChatView from '../src/views/ChatView.vue'

describe('App', () => {
  afterEach(() => vi.unstubAllGlobals())

  function createTestRouter() {
    const placeholder = { template: '<div />' }
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: '/', component: ChatView },
        { path: '/documents', component: placeholder },
        { path: '/evaluations', component: placeholder },
        { path: '/settings', component: placeholder },
      ],
    })
    return router
  }

  function mockApi() {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: string) => {
        if (input.endsWith('/health')) {
          return new Response(
            JSON.stringify({
              status: 'ok',
              version: '0.1.0',
              services: { llm: 'configured', sqlite: 'ok', qdrant: 'ok', ollama: 'ok' },
            }),
            { status: 200 },
          )
        }
        if (input.endsWith('/documents')) {
          return new Response(JSON.stringify({ items: [], total: 0 }), { status: 200 })
        }
        return new Response(
          JSON.stringify({
            answer: '岗位要求掌握 FastAPI。[S1]',
            grounded: true,
            trace_id: 'trace-1',
            timings: { total: 18 },
            rewritten: false,
            sources: [
              {
                source_id: 'S1',
                document_id: 'doc-1',
                filename: 'ai-jd.md',
                file_type: 'md',
                text: '掌握 FastAPI',
                score: 0.88,
                chunk_index: 0,
                title: '技能要求',
                page: null,
              },
            ],
          }),
          { status: 200 },
        )
      }),
    )
  }

  it('shows the project name and clear grounded-answer workflow', async () => {
    mockApi()
    const router = createTestRouter()
    router.push('/')
    await router.isReady()

    const wrapper = mount(App, {
      global: { plugins: [router] },
    })

    expect(wrapper.get('h1').text()).toBe('RAG 求职知识库')
    expect(wrapper.text()).toContain('答案会显示行内引用')
    expect(wrapper.text()).not.toContain('资料不会提交 GitHub')
    expect(wrapper.get('textarea').attributes('placeholder')).toContain('RAG 技能')
  })

  it('submits a question and renders the cited source', async () => {
    mockApi()
    const router = createTestRouter()
    router.push('/')
    await router.isReady()
    const wrapper = mount(App, { global: { plugins: [router] } })
    await flushPromises()

    await wrapper.get('textarea').setValue('岗位要求什么？')
    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(wrapper.text()).toContain('岗位要求掌握 FastAPI。[S1]')
    expect(wrapper.text()).toContain('ai-jd.md')
    expect(wrapper.text()).toContain('相似度 0.88')

    await wrapper.get('.citation-link').trigger('click')
    expect(wrapper.get('#source-S1').classes()).toContain('highlighted')
  })
})
