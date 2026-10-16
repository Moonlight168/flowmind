import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import DesignWindow from '@/components/AiChatWindow/design/index.vue'
import { designStream, rollbackDesignState } from '@/api/workflow/design'
import { addForm } from '@/api/workflow/form'
import { activeAiWindow } from '@/utils/aiWindow'
import useUserStore from '@/store/modules/user'

vi.mock('@/store/modules/user', async () => {
  const { reactive } = await import('vue')
  const user = reactive({ id: '42' })
  return { default: () => user }
})

vi.mock('@/api/workflow/design', () => ({
  designStream: vi.fn(), clearDesignState: vi.fn().mockResolvedValue({}),
  rollbackDesignState: vi.fn().mockResolvedValue({})
}))
vi.mock('@/api/workflow/form', () => ({ addForm: vi.fn() }))
vi.mock('@/api/workflow/category', () => ({
  listCategory: vi.fn().mockResolvedValue({ rows: [] }), addCategory: vi.fn()
}))
vi.mock('@/components/AiChatWindow/assistant/MessageItem.vue', () => ({
  default: { template: '<span />' }
}))

beforeEach(() => {
  vi.clearAllMocks()
  localStorage.clear()
  activeAiWindow.value = null
  useUserStore().id = '42'
})

async function openPreview() {
  let resolve!: (value: any) => void
  vi.mocked(addForm).mockReturnValue(new Promise(r => { resolve = r }))
  vi.mocked(designStream).mockImplementation(async (_type, _data, onEvent) => {
    onEvent({
      type: 'done', status: 'ready', message_count: 3,
      form_data: { nodes: [{ id: 'approve' }], bpmn_xml: '' },
      pending_entities: { forms: [{
        form_name: '审批意见', widgetList: [{ type: 'textarea' }], formConfig: {}, node_ids: ['approve']
      }] }
    })
  })
  const wrapper = mount(DesignWindow, {
    props: { modelValue: true, designType: 'flow', formData: { nodes: [] } },
    global: { stubs: { AiFloatingWindow: { template: '<div><slot /></div>' } } }
  })
  await flushPromises()
  await wrapper.find('.dialog-footer input').setValue('新增审批表单')
  await wrapper.find('.send-button').trigger('click')
  await flushPromises()
  return { wrapper, resolve }
}

describe('AI 设计窗口应用预览', () => {
  it('切换账号隔离记录、版本和未完成的应用', async () => {
    const { wrapper, resolve } = await openPreview()
    const oldKeys = Object.keys(localStorage).filter(key => key.startsWith('ai_design_'))
    expect(oldKeys.length).toBeGreaterThan(0)
    expect(oldKeys.every(key => key.includes('user:42_'))).toBe(true)
    await wrapper.findAll('.change-preview__actions button')[1].trigger('click')
    useUserStore().id = '43'
    await flushPromises()
    expect(wrapper.find('.change-preview').exists()).toBe(false)
    resolve({ code: 200, data: { formId: 99 } })
    await flushPromises()
    expect(wrapper.emitted('fill')).toBeUndefined()
    await wrapper.setProps({ modelValue: false })
    const sessions = Object.keys(localStorage).filter(key => key.startsWith('ai_design_user:43_'))
    expect(sessions).toHaveLength(1)
    expect(JSON.parse(localStorage.getItem(sessions[0])!).messages.some((m: any) => m.role === 'user')).toBe(false)
    wrapper.unmount()
  })
  it('重复点击仅创建一次并绑定创建接口返回的表单 ID', async () => {
    const { wrapper, resolve } = await openPreview()
    const button = wrapper.findAll('.change-preview__actions button')[1]
    await button.trigger('click')
    await button.trigger('click')
    await flushPromises()
    expect(addForm).toHaveBeenCalledOnce()
    resolve({ code: 200, data: { formId: 99 } })
    await flushPromises()
    expect(wrapper.emitted('fill')).toHaveLength(1)
    expect((wrapper.emitted('fill')![0][0] as any).nodes[0].form_key).toBe('key_99')
    wrapper.unmount()
  })

  it.each(['close', 'discard', 'unmount'])('%s 后创建完成也不写入画布或裁剪会话', async action => {
    const { wrapper, resolve } = await openPreview()
    await wrapper.findAll('.change-preview__actions button')[1].trigger('click')
    await flushPromises()
    if (action === 'close') await wrapper.setProps({ modelValue: false })
    if (action === 'discard') await wrapper.findAll('.change-preview__actions button')[0].trigger('click')
    if (action === 'unmount') wrapper.unmount()
    resolve({ code: 200, data: { formId: 99 } })
    await flushPromises()
    expect(wrapper.emitted('fill')).toBeUndefined()
    expect(rollbackDesignState).not.toHaveBeenCalled()
    if (action !== 'unmount') wrapper.unmount()
  })
})
