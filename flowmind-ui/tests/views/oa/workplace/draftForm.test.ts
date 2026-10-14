import { describe, expect, it, vi } from 'vitest'

import { collectDraftFormData } from '@/views/oa/workplace/draftForm.js'

describe('OA 发起申请保存草稿', () => {
  it('必填项未完成时读取当前数据但不触发校验', async () => {
    const currentData = { reason: '' }
    const getFormData = vi.fn((validate: boolean) => {
      if (validate) return Promise.reject('validation failed')
      return Promise.resolve(currentData)
    })

    await expect(collectDraftFormData({ getFormData })).resolves.toEqual(currentData)
    expect(getFormData).toHaveBeenCalledOnce()
    expect(getFormData).toHaveBeenCalledWith(false)
  })
})
