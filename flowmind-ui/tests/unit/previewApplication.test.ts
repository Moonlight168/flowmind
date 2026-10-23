import { describe, expect, it, vi } from 'vitest'
import { createPreviewApplication, createGeneratedForm } from '@/components/AiChatWindow/design/previewApplication'

function deferred() {
  let resolve!: (value: any) => void
  const promise = new Promise(resolvePromise => { resolve = resolvePromise })
  return { promise, resolve }
}

describe('应用设计预览', () => {
  it('连续点击仅执行一次创建和应用', async () => {
    const pending = deferred()
    const work = vi.fn(() => pending.promise)
    const fill = vi.fn()
    const application = createPreviewApplication()
    const first = application.run(work, fill)
    await application.run(work, fill)
    pending.resolve({ nodes: [] })
    await first
    expect(work).toHaveBeenCalledOnce()
    expect(fill).toHaveBeenCalledOnce()
  })

  it('关闭或放弃后不再应用迟到结果', async () => {
    const pending = deferred()
    const application = createPreviewApplication()
    const fill = vi.fn()
    const result = application.run(() => pending.promise, fill)
    application.cancel()
    pending.resolve({ nodes: [] })
    await result
    expect(fill).not.toHaveBeenCalled()
  })

  it('失败后可以重试，取消后的旧任务不能清除新任务的忙碌状态', async () => {
    const busy = vi.fn()
    const application = createPreviewApplication(busy)
    await expect(application.run(() => Promise.reject(new Error('failed')), vi.fn())).rejects.toThrow('failed')
    const old = deferred()
    const newer = deferred()
    const oldRun = application.run(() => old.promise, vi.fn())
    application.cancel()
    const newRun = application.run(() => newer.promise, vi.fn())
    old.resolve({})
    await oldRun
    expect(busy).toHaveBeenLastCalledWith(true)
    newer.resolve({})
    await newRun
    expect(busy).toHaveBeenLastCalledWith(false)
  })

  it('新建草案使用创建返回的 ID，保留模型生成的字段，不按名称查旧表单', async () => {
    const add = vi.fn().mockResolvedValue({ code: 200, data: { formId: 99 } })
    const draft = { form_name: '审批意见表', widgetList: [{ type: 'textarea' }], formConfig: {} }
    const create = createGeneratedForm(add)
    expect(await create(draft)).toEqual({ formId: 99 })
    expect(JSON.parse(add.mock.calls[0][0].content).widgetList).toEqual(draft.widgetList)
    expect(await create(draft)).toEqual({ formId: 99 })
    expect(add).toHaveBeenCalledOnce()
  })

  it('创建失败允许重试，同名的不同草案分别创建', async () => {
    const add = vi.fn().mockRejectedValueOnce(new Error('failed'))
      .mockResolvedValue({ code: 200, data: { formId: 100 } })
    const create = createGeneratedForm(add)
    const draft = { form_name: '同名表单', widgetList: [] }
    await expect(create(draft)).rejects.toThrow('failed')
    await create(draft)
    await create({ ...draft, widgetList: [{ type: 'input' }] })
    expect(add).toHaveBeenCalledTimes(3)
  })
})
