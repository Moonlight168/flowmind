import { getToken } from '@/utils/auth'

/**
 * 发起 POST SSE 请求并逐条解析 data 事件。
 */
export async function postSse(path, data, onEvent) {
  const token = getToken()
  const response = await fetch(`${import.meta.env.VITE_APP_BASE_API}${path}`, {
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
  if (!response.body) {
    throw new Error('浏览器不支持流式响应')
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buffer = ''
  let completed = false
  let receivedTerminalEvent = false

  try {
    while (true) {
      const { done, value } = await reader.read()
      buffer += decoder.decode(value || new Uint8Array(), { stream: !done })
      buffer = buffer.replace(/\r\n/g, '\n')

      let separatorIndex
      while ((separatorIndex = buffer.indexOf('\n\n')) !== -1) {
        const chunk = buffer.slice(0, separatorIndex).trim()
        buffer = buffer.slice(separatorIndex + 2)
        if (!chunk.startsWith('data:')) continue

        let event
        try {
          event = JSON.parse(chunk.slice(5).trimStart())
        } catch (error) {
          console.warn('SSE 事件解析失败:', chunk, error)
          continue
        }
        if (event.type === 'done' || event.type === 'error') {
          receivedTerminalEvent = true
        }
        onEvent(event)
      }

      if (done) {
        if (!receivedTerminalEvent) throw new Error('流式响应意外中断')
        completed = true
        break
      }
    }
  } finally {
    if (!completed) {
      try {
        await reader.cancel()
      } catch (error) {
        console.warn('SSE 连接取消失败:', error)
      }
    }
    reader.releaseLock()
  }
}
