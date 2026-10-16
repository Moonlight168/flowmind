import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import useAiSessionStore from '@/store/modules/aiSession'
import { getAiFormState } from '@/api/workflow/ai'

vi.mock('@/api/workflow/ai', () => ({ getAiFormState: vi.fn() }))

beforeEach(() => {
  setActivePinia(createPinia())
  localStorage.clear()
  vi.clearAllMocks()
})

describe('AI 会话账号隔离', () => {
  it('不读取旧公共缓存，切换账号清空内存且各自恢复自己的会话', async () => {
    const store = useAiSessionStore()
    localStorage.setItem('aiSession', JSON.stringify({ threadId: 'legacy' }))
    store.setOwner(42)
    expect(await store.restoreSession()).toBeNull()
    store.initializeSession({ threadId: 'alice', targetPageType: 'flow' })
    store.setGeneratedData({ bpmnXml: 'private' })
    store.setOwner(43)
    expect(store.threadId).toBeNull()
    expect(store.generatedData.bpmnXml).toBe('')
    expect(await store.restoreSession()).toBeNull()
    store.initializeSession({ threadId: 'bob' })
    store.resetSession()
    expect(store.ownerId).toBe('43')
    expect(localStorage.getItem('aiSession:43')).toBeNull()
    store.setOwner(42)
    vi.mocked(getAiFormState).mockResolvedValue({ messages: [] })
    await store.restoreSession()
    expect(store.threadId).toBe('alice')
    expect(store.generatedData.bpmnXml).toBe('private')
  })

  it('退出后不持久化，旧账号迟到的历史不返回给新账号', async () => {
    const store = useAiSessionStore()
    store.setOwner(42)
    store.initializeSession({ threadId: 'alice' })
    let resolve!: (value: any) => void
    vi.mocked(getAiFormState).mockReturnValue(new Promise(r => { resolve = r }))
    const restoring = store.restoreSession()
    store.setOwner(null)
    store.persistState()
    store.setOwner(43)
    resolve({ messages: [{ role: 'user', content: 'private' }] })
    expect(await restoring).toBeNull()
    expect(store.threadId).toBeNull()
    expect(localStorage.getItem('aiSession:')).toBeNull()
  })
})
