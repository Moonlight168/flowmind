/** 直接执行页面的标签删除函数，防止 userId/id 混用回归。 */
import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'

const source = readFileSync('src/views/workflow/work/detail.vue', 'utf8').replace(/\r\n/g, '\n')
const body = source.match(/const handleClose = \(type, tag\) => \{([\s\S]*?)\n\}\nconst changeCurrentUser/)![1]
const remove = new Function('type', 'tag', 'copyUser', 'nextUser', 'taskForm', body)
describe('审批人员标签', () => {
  it('按 userId 删除指定人员，两种名单互不影响', () => {
    const copy = { value: [{ userId: 11 }, { userId: 22 }, { userId: 33 }] }
    const next = { value: [{ userId: 44 }] }
    const form: any = { nextUserIds: '44' }
    remove('copy', { userId: 11 }, copy, next, form)
    expect(copy.value.map(user => user.userId)).toEqual([22, 33])
    expect(form.copyUserIds).toBe('22,33')
    expect(form.nextUserIds).toBe('44')
    remove('next', { userId: 44 }, copy, next, form)
    expect(form.nextUserIds).toBe('')
    expect(copy.value).toHaveLength(2)
  })
})
