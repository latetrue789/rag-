import { flushPromises, mount } from '@vue/test-utils'
import { createMemoryHistory, createRouter } from 'vue-router'
import { afterEach, vi } from 'vitest'

import DocumentsView from '../src/views/DocumentsView.vue'

describe('DocumentsView', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
    vi.useRealTimers()
  })

  async function mountView() {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: '/documents', component: DocumentsView },
        { path: '/:pathMatch(.*)*', component: { template: '<div />' } },
      ],
    })
    router.push('/documents')
    await router.isReady()
    const wrapper = mount(DocumentsView, { global: { plugins: [router] } })
    await flushPromises()
    return wrapper
  }

  it('shows the watched folders and triggers an immediate scan', async () => {
    const fetchMock = vi.fn(async (input: string, init?: RequestInit) => {
      if (input.endsWith('/documents/scan') && init?.method === 'POST') {
        return new Response(
          JSON.stringify({
            indexed: 1,
            skipped: 0,
            failed: 0,
            waiting: 0,
            missing: 0,
            oversized: 0,
            busy: false,
            scanned_at: '2026-08-22T00:01:00+00:00',
          }),
          { status: 200 },
        )
      }
      if (input.endsWith('/documents/scan')) {
        return new Response(
          JSON.stringify({
            directory: 'data/documents/',
            subdirectories: ['md/', 'txt/', 'pdf/'],
            interval_seconds: 60,
            scanning: false,
            last_scan: null,
          }),
          { status: 200 },
        )
      }
      return new Response(JSON.stringify({ items: [], total: 0 }), { status: 200 })
    })
    vi.stubGlobal('fetch', fetchMock)

    const wrapper = await mountView()
    expect(wrapper.text()).toContain('data/documents/')
    expect(wrapper.text()).toContain('md/')
    expect(wrapper.text()).not.toContain('python -m app.cli')

    await wrapper.get('.primary-button').trigger('click')
    await flushPromises()

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/documents/scan',
      expect.objectContaining({ method: 'POST' }),
    )
    wrapper.unmount()
  })

  it('only offers confirmed cleanup for a missing source', async () => {
    vi.stubGlobal('confirm', vi.fn(() => true))
    const fetchMock = vi.fn(async (input: string, init?: RequestInit) => {
      if (input.endsWith('/documents/scan')) {
        return new Response(
          JSON.stringify({
            directory: 'data/documents/',
            subdirectories: ['md/', 'txt/', 'pdf/'],
            interval_seconds: 60,
            scanning: false,
            last_scan: null,
          }),
          { status: 200 },
        )
      }
      if (input.endsWith('/documents/doc-1') && init?.method === 'DELETE') {
        return new Response(null, { status: 204 })
      }
      return new Response(
        JSON.stringify({
          items: [
            {
              id: 'doc-1',
              filename: '岗位.md',
              file_type: 'md',
              status: 'missing',
              chunk_count: 4,
              error_message: '源文件已从资料目录移除',
              updated_at: '2026-08-22T00:00:00+00:00',
            },
          ],
          total: 1,
        }),
        { status: 200 },
      )
    })
    vi.stubGlobal('fetch', fetchMock)

    const wrapper = await mountView()
    expect(wrapper.text()).toContain('源文件已移除')

    await wrapper.get('.text-button.danger').trigger('click')
    await flushPromises()

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/documents/doc-1',
      expect.objectContaining({ method: 'DELETE' }),
    )
    expect(wrapper.text()).not.toContain('岗位.md')
    wrapper.unmount()
  })
})
