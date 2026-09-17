import { getToken } from '@/utils/auth'
import { promptRelogin } from '@/utils/relogin'

/**
 * HTTP 层失败：读取响应体错误信息；401 走与 request.js 一致的重新登录引导。
 */
async function raiseHttpError(response) {
  let message = `请求失败: ${response.status}`
  try {
    const body = await response.json()
    if (body?.message || body?.msg) {
      message = body.message || body.msg
    }
  } catch (e) {
    // 响应体不是 JSON（如网关返回的纯文本错误），保留状态码信息
  }
  if (response.status === 401) {
    promptRelogin()
    throw new Error('登录状态已过期，请重新登录')
  }
  throw new Error(message)
}

/**
 * 发起 POST SSE 请求并逐条解析 data 事件。
 */
export async function postSse(path, data, onEvent, options = {}) {
  const token = getToken()
  const response = await fetch(`${import.meta.env.VITE_APP_BASE_API}${path}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: 'Bearer ' + token } : {})
    },
    body: JSON.stringify(data),
    signal: options.signal
  })

  if (!response.ok) {
    await raiseHttpError(response)
  }
  if (!response.body) {
    throw new Error('浏览器不支持流式响应')
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buffer = ''
  let completed = false
  let receivedTerminalEvent = false
  let aborted = false

  // 解析一条以 data: 开头的事件（可能没有 \n\n 结尾的最后一帧）
  function dispatchChunk(chunk) {
    if (!chunk.startsWith('data:')) return
    let event
    try {
      event = JSON.parse(chunk.slice(5).trimStart())
    } catch (error) {
      console.warn('SSE 事件解析失败:', chunk, error)
      return
    }
    if (event.type === 'done' || event.type === 'error') {
      receivedTerminalEvent = true
    }
    onEvent(event)
  }

  try {
    while (true) {
      const { done, value } = await reader.read()
      buffer += decoder.decode(value || new Uint8Array(), { stream: !done })
      buffer = buffer.replace(/\r\n/g, '\n')

      let separatorIndex
      while ((separatorIndex = buffer.indexOf('\n\n')) !== -1) {
        const chunk = buffer.slice(0, separatorIndex).trim()
        buffer = buffer.slice(separatorIndex + 2)
        dispatchChunk(chunk)
      }

      if (done) {
        // 服务端若以不带 \n\n 的数据帧收尾，需要把残留在 buffer 的最后一帧解析掉
        const rest = buffer.trim()
        if (rest) dispatchChunk(rest)
        buffer = ''
        if (!receivedTerminalEvent) throw new Error('流式响应意外中断')
        completed = true
        break
      }
    }
  } catch (error) {
    if (error?.name === 'AbortError') aborted = true
    throw error
  } finally {
    if (!completed && !aborted) {
      try {
        await reader.cancel()
      } catch (error) {
        // 主动 abort 后 cancel 会以 AbortError 拒绝，属正常路径，不告警
        if (error?.name !== 'AbortError') {
          console.warn('SSE 连接取消失败:', error)
        }
      }
    }
    reader.releaseLock()
  }
}
