import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { mount } from '@vue/test-utils'
import useOaCounts from '@/store/modules/oaCounts'
import useUserStore from '@/store/modules/user'
import { getTaskCounts } from '@/api/workflow/work/process'
import OaCountBadge from '@/components/OaCountBadge/index.vue'

vi.mock('@/api/workflow/work/process', () => ({ getTaskCounts: vi.fn() }))
vi.mock('@/store/modules/user', () => {
  const user = { id: '42' }
  return { default: () => user }
})
beforeEach(() => {
  setActivePinia(createPinia())
  vi.clearAllMocks()
  useUserStore().id = '42'
})
describe('OA 提醒数量', () => {
  it.each([[null, ''], [0, ''], [1, '1'], [99, '99'], [100, '99+']])('角标 %s', (count, text) => {
    const wrapper = mount(OaCountBadge, { props: { count } })
    expect(wrapper.text()).toBe(text)
    wrapper.unmount()
  })
  it('待办包含待签收，不重复累加；失败保留上次结果', async () => {
    const store = useOaCounts()
    expect(store.pending).toBeNull()
    vi.mocked(getTaskCounts).mockResolvedValue({ code: 200, data: { todoCount: 5, claimCount: 2 } })
    await store.refresh()
    expect(store.pending).toBe(5)
    expect(store.claim).toBe(2)
    vi.mocked(getTaskCounts).mockResolvedValue({ code: 500 })
    await store.refresh()
    expect(store.pending).toBe(5)
  })
  it('旧请求不能覆盖新数量，也不能跨账号回填', async () => {
    const store = useOaCounts()
    let resolve!: (value: any) => void
    vi.mocked(getTaskCounts).mockReturnValueOnce(new Promise(r => { resolve = r }))
    const old = store.refresh()
    vi.mocked(getTaskCounts).mockResolvedValue({ code: 200, data: { todoCount: 0, claimCount: 0 } })
    await store.refresh()
    resolve({ code: 200, data: { todoCount: 9, claimCount: 2 } })
    await old
    expect(store.pending).toBe(0)
    useUserStore().id = ''
    await store.refresh()
    expect(store.pending).toBeNull()
  })
})
