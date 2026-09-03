import request from '@/utils/request'
import { postSse } from '@/utils/sse'

export function designCategory(data) {
  return request({
    url: '/flowmind-ai/design/category',
    method: 'post',
    data
  })
}

export function designFlow(data) {
  return request({
    url: '/flowmind-ai/design/flow',
    method: 'post',
    data
  })
}

export function designForm(data) {
  return request({
    url: '/flowmind-ai/design/form',
    method: 'post',
    data
  })
}

export function clearDesignState(designType, threadId, mode = 'design') {
  return request({
    url: '/flowmind-ai/design/state/' + designType,
    method: 'delete',
    params: { ...(threadId ? { thread_id: threadId } : {}), mode }
  })
}

/**
 * 流式设计（SSE）：POST + 逐条解析后端推送的进度/done 事件
 *
 * @param {string} designType - 'category' | 'flow' | 'form'
 * @param {object} data - 请求体 { user_input, current_form_data, mode }
 * @param {function} onEvent - 回调，逐条接收事件对象
 *   进度事件：{ type: 'progress', phase, message }
 *   完成事件：{ type: 'done', status, form_data, operations, validation, trace_id }
 *   错误事件：{ type: 'error', message }
 */
export async function designStream(designType, data, onEvent) {
  return postSse(`/flowmind-ai/design/${designType}`, data, onEvent)
}
