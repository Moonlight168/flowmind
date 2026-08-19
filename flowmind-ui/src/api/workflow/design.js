import request from '@/utils/request'
import { getToken } from '@/utils/auth'

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

export function clearDesignState(designType) {
  return request({
    url: '/flowmind-ai/design/state/' + designType,
    method: 'delete'
  })
}

/**
 * 流式设计（SSE）：POST + 逐条解析后端推送的进度/done 事件
 *
 * @param {string} designType - 'category' | 'flow' | 'form'
 * @param {object} data - 请求体 { user_input, current_form_data, mode }
 * @param {function} onEvent - 回调，逐条接收事件对象
 *   进度事件：{ type: 'progress', phase, message }
 *   完成事件：{ type: 'done', form_data, message, intent, partial }
 *   错误事件：{ type: 'error', message }
 */
export async function designStream(designType, data, onEvent) {
  const url = `${import.meta.env.VITE_APP_BASE_API}/flowmind-ai/design/${designType}`
  const token = getToken()

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: 'Bearer ' + token } : {})
    },
    body: JSON.stringify(data)
  })

  if (!response.ok) {
    throw new Error(`请求失败: ${response.status}`)
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })

    // SSE：每个事件以 \n\n 分隔，格式 "data: {...}"
    let sepIndex
    while ((sepIndex = buffer.indexOf('\n\n')) !== -1) {
      const chunk = buffer.slice(0, sepIndex).trim()
      buffer = buffer.slice(sepIndex + 2)
      if (chunk.startsWith('data: ')) {
        try {
          onEvent(JSON.parse(chunk.slice(6)))
        } catch (e) {
          console.warn('SSE 事件解析失败:', chunk, e)
        }
      }
    }
  }
}
