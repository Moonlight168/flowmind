import request from '@/utils/request'

function normalizeChatRequest(data = {}) {
  return {
    user_input: data.user_input ?? '',
    thread_id: data.thread_id ?? null,
    control_intent: data.control_intent ?? null,
    confirmation_id: data.confirmation_id ?? null
  }
}

// AI 对话（统一接口）
export function aiFormChat(data) {
  return request({
    url: '/flowmind-ai/chat',
    method: 'post',
    data: normalizeChatRequest(data)
  })
}

// 获取 AI 状态
export function getAiFormState(threadId) {
  return request({
    url: '/flowmind-ai/chat/state/' + threadId,
    method: 'get'
  })
}

// 删除 AI 状态
export function deleteAiFormState(threadId) {
  return request({
    url: '/flowmind-ai/chat/state/' + threadId,
    method: 'delete'
  })
}

// 批量删除 AI 状态
export function batchDeleteAiFormState(threadIds) {
  return request({
    url: '/flowmind-ai/chat/state/batch-delete',
    method: 'post',
    data: threadIds
  })
}

// 检查 AI 服务健康状态
export function checkAiHealth() {
  return request({
    url: '/flowmind-ai/health',
    method: 'get'
  })
}

// 检查 AI 模型健康状态
export function checkAiModelHealth() {
  return request({
    url: '/flowmind-ai/health/models',
    method: 'get'
  })
}

// 获取聊天历史列表
export function getChatHistoryList() {
  return request({
    url: '/flowmind-ai/chat/history',
    method: 'get'
  })
}
