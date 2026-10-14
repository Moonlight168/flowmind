/**
 * 读取当前申请数据用于保存草稿。
 *
 * 草稿允许处于未完成状态，因此不能触发表单必填校验。
 * 正式提交仍由发起页面调用 getFormData(true) 完成校验。
 *
 * @param {{ getFormData: (validate: boolean) => Promise<Record<string, unknown>> }} formRenderer
 * @returns {Promise<Record<string, unknown>>}
 */
export function collectDraftFormData(formRenderer) {
  return formRenderer.getFormData(false)
}
