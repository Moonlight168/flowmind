/** 单次预览应用：重复点击不重入，关闭或放弃后丢弃迟到结果。 */
export function createPreviewApplication(onBusy = () => {}) {
  let active = null
  return {
    cancel() {
      active = null
      onBusy(false)
    },
    async run(work, commit) {
      if (active) return false
      const token = {}
      active = token
      onBusy(true)
      const isCurrent = () => active === token
      try {
        const result = await work(isCurrent)
        if (!isCurrent()) return false
        commit(result)
        return true
      } catch (error) {
        if (isCurrent()) throw error
        return false
      } finally {
        if (isCurrent()) {
          active = null
          onBusy(false)
        }
      }
    }
  }
}

/** pending.forms 是模型明确生成的新表单；仅复用同一草案已创建的结果。 */
export function createGeneratedForm(addForm) {
  const created = new WeakMap()
  return async function ensureGeneratedForm(draft) {
    if (!created.has(draft)) {
      const request = Promise.resolve().then(() => addForm({
        formName: draft.form_name,
        content: JSON.stringify({ widgetList: draft.widgetList || [], formConfig: draft.formConfig || {} }),
        remark: 'AI 流程设计生成，已在应用变更前由用户确认'
      })).then(response => {
        if (response?.code !== 200 || !response.data?.formId) {
          throw new Error(response?.msg || `表单「${draft.form_name}」创建失败`)
        }
        return response.data
      }).catch(error => {
        created.delete(draft)
        throw error
      })
      created.set(draft, request)
    }
    return created.get(draft)
  }
}
