/** OA 待处理提醒：不把历史总数当作未读数，失败保留上次成功值。 */
import { defineStore } from 'pinia'
import { getTaskCounts } from '@/api/workflow/work/process'
import useUserStore from './user'

export default defineStore('oaCounts', {
  state: () => ({ ownerId: '', todo: null, claim: null, request: 0 }),
  getters: {
    // 后端 todoCount 已包含候选待签收任务，不能再相加。
    pending: state => state.todo
  },
  actions: {
    async refresh() {
      const ownerId = String(useUserStore().id || '')
      if (ownerId !== this.ownerId) {
        this.ownerId = ownerId
        this.todo = this.claim = null
      }
      const request = ++this.request
      if (!ownerId) return
      try {
        const res = await getTaskCounts()
        if (request !== this.request || ownerId !== String(useUserStore().id || '')) return
        if (res.code !== 200) return
        const { todoCount, claimCount } = res.data || {}
        if (![todoCount, claimCount].every(value => Number.isSafeInteger(value) && value >= 0)) return
        this.todo = todoCount
        this.claim = claimCount
      } catch (error) {
        console.warn('OA 待处理数量刷新失败，保留上次结果', error)
      }
    }
  }
})
