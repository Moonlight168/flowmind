<template>
  <div class="ai-assistant-container" v-if="!hasPageAiDesign">
    <!-- 浮窗按钮 -->
    <el-tooltip v-if="!isVisible" content="AI 助手" placement="left" effect="dark">
      <div
        class="ai-assistant-button cursor-pointer hover:scale-110 transition-all duration-300"
        @click="toggleVisible"
      >
        <el-icon :size="26"><ChatDotRound /></el-icon>
      </div>
    </el-tooltip>

    <!-- 对话窗口（复用 AiFloatingWindow 的拖拽/缩放/头部；常驻挂载以保留拖拽位置） -->
    <AiFloatingWindow
      :model-value="isVisible"
      title="AI 助手"
      :icon="ChatDotRound"
      :width="440"
      :height="620"
      :min-width="MIN_WIDTH"
      :min-height="MIN_HEIGHT"
      @update:model-value="handleVisibleChange"
    >
      <template #actions>
        <el-button link type="info" @click="toggleHistoryList" title="历史对话">
          <el-icon><List /></el-icon>
        </el-button>
        <el-button link type="info" @click="handleNewChat" title="新建对话">
          <el-icon><Plus /></el-icon>
        </el-button>
      </template>

      <div class="assistant-body">

      <!-- 历史列表 (覆盖在消息列表上方) -->
      <div
        v-if="showHistoryList"
        class="history-overlay absolute inset-0 bg-white z-10 flex flex-col"
      >
        <!-- 历史列表头部 -->
        <div class="history-header flex items-center justify-between p-3 border-b border-gray-200">
          <div class="flex items-center gap-2">
            <el-checkbox
              v-if="historyList.length > 0"
              :model-value="selectedThreadIds.length === historyList.length && historyList.length > 0"
              :indeterminate="selectedThreadIds.length > 0 && selectedThreadIds.length < historyList.length"
              @change="toggleSelectAll"
              size="small"
            />
            <span class="text-sm font-semibold text-gray-700">历史对话</span>
            <el-button
              v-if="selectedThreadIds.length > 0"
              link
              type="danger"
              :icon="Delete"
              size="small"
              @click="handleBatchDeleteHistory"
            >
              删除{{ selectedThreadIds.length }}
            </el-button>
          </div>
          <el-button link type="info" @click="toggleHistoryList">
            <el-icon><Close /></el-icon>
          </el-button>
        </div>
        <!-- 历史列表 -->
        <div class="history-list flex-1 overflow-y-auto p-2">
          <div
            v-for="session in historyList"
            :key="session.thread_id"
            :class="['history-item flex flex-col p-2 rounded-lg mb-1 cursor-pointer', session.thread_id === threadId ? 'active bg-blue-50' : 'hover:bg-gray-50']"
            @click="handleSelectHistory(session)"
          >
            <div class="flex items-center gap-2">
              <el-checkbox
                :model-value="selectedThreadIds.includes(session.thread_id)"
                @change="() => toggleSelectOne(session.thread_id)"
                @click.stop
                size="small"
              />
              <div class="history-preview text-xs text-gray-700 truncate flex-1">{{ session.preview || '新对话' }}</div>
            </div>
            <div class="history-meta flex items-center justify-between mt-1 pl-6">
              <span class="history-time text-xs text-gray-400">{{ formatTime(session.updated_at) }}</span>
              <el-button
                link
                type="danger"
                :icon="Delete"
                :size="12"
                title="删除"
                @click.stop="handleDeleteHistory(session.thread_id)"
              />
            </div>
          </div>
          <div v-if="historyList.length === 0" class="empty-history text-center text-gray-400 text-xs py-4">
            暂无历史对话
          </div>
        </div>
      </div>

      <!-- 消息列表 -->
      <div class="window-messages flex-1 overflow-y-auto p-4 bg-gray-100" ref="messagesContainer">
        <MessageItem
          v-for="(message, index) in messages"
          :key="message.id"
          :message="message"
        />
        <!-- 加载状态 -->
        <div v-if="isLoading && !hasStreamingContent" class="message assistant flex gap-3 mb-4">
          <div class="message-avatar flex-shrink-0 flex items-center justify-center text-blue-500">
            <el-icon :size="20"><ChatDotRound /></el-icon>
          </div>
          <div class="message-content max-w-[75%]">
            <div class="thinking-indicator flex items-center gap-2 px-3.5 py-2.5 bg-white rounded-3xl text-sm">
              <span class="typing-dot" v-for="i in 3" :key="i"></span>
              <span class="text-gray-500 ml-2">AI 正在思考中...</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="window-input p-3 bg-white border-t border-gray-200 flex gap-2 items-end">
        <div class="flex-1 relative">
          <el-input
            v-model="inputMessage"
            type="textarea"
            :rows="1"
            :maxlength="MAX_INPUT_LENGTH"
            placeholder=""
            @keydown.enter.exact="sendMessage"
            :disabled="isLoading"
            class="flex-1"
            show-word-limit
          />
        </div>
        <el-button
          type="primary"
          :loading="isLoading"
          @click="sendMessage"
          class="send-button flex-shrink-0"
        >
          发送
        </el-button>
      </div>

      </div>
    </AiFloatingWindow>
  </div>
</template>

<script setup>
import { ref, nextTick, getCurrentInstance, onMounted, onUnmounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { ChatDotRound, Close, Delete, Plus, List } from '@element-plus/icons-vue'
import { aiFormChatStream, getAiFormState, deleteAiFormState, batchDeleteAiFormState, getChatHistoryList } from '@/api/workflow/ai'
import { ElMessage } from 'element-plus'
import { useAiSessionStore } from '@/store/modules/aiSession'
import MessageItem from './MessageItem.vue'
import AiFloatingWindow from '@/components/AiFloatingWindow/index.vue'

const { proxy } = getCurrentInstance()
const route = useRoute()

// 已有 AI 设计按钮的页面，隐藏全局助手
const PAGE_WITH_AI_DESIGN = ['/process/model', '/process/form', '/process/category']
const hasPageAiDesign = computed(() => PAGE_WITH_AI_DESIGN.includes(route.path))

// 引入 Pinia Store
const aiSession = useAiSessionStore()

// 状态管理
const MAX_INPUT_LENGTH = 2000
const isVisible = ref(false)
const isLoading = ref(false)
const hasStreamingContent = ref(false)
const inputMessage = ref('')
const messages = ref([])
const messagesContainer = ref(null)

// 创建带唯一 ID 的消息对象
let messageIdCounter = 0
function createMessage(data) {
  return { id: `msg-${++messageIdCounter}`, time: getCurrentTime(), ...data }
}

// 使用计算属性访问 session 状态
const threadId = computed(() => aiSession.threadId)

// 历史面板相关
const showHistoryList = ref(false)
const historyList = ref([])
const selectedThreadIds = ref([])
const isLoadingHistory = ref(false)

const requestController = ref(null)

// 最小窗口尺寸（作为 AiFloatingWindow 缩放下限）
const MIN_WIDTH = 300
const MIN_HEIGHT = 400

// 切换窗口可见性
async function toggleVisible() {
  isVisible.value = !isVisible.value
  if (!isVisible.value) requestController.value?.abort()
  if (isVisible.value) {
    // 恢复已有会话
    if (aiSession.hasActiveSession) {
      const chatHistory = await aiSession.restoreSession()
      if (chatHistory && chatHistory.length > 0) {
        messages.value = chatHistory.map((msg) => createMessage(msg))
      } else {
        showWelcome()
      }
    } else if (messages.value.length === 0) {
      showWelcome()
    }
    // 加载历史列表
    handleLoadHistoryList()
  }
}

// AiFloatingWindow 头部关闭按钮回调
function handleVisibleChange(val) {
  isVisible.value = val
  if (!val) requestController.value?.abort()
}

function showWelcome() {
  messages.value.push(createMessage({
    role: 'assistant',
    content: '您好！我是 FlowMind AI 助手，有什么可以帮您的吗？'
  }))
}

// 切换历史列表显示
function toggleHistoryList() {
  showHistoryList.value = !showHistoryList.value
  if (showHistoryList.value) {
    // 打开时加载历史列表
    handleLoadHistoryList()
  }
}

// 新开聊天
function handleNewChat() {
  aiSession.resetSession()
  // 生成新的 threadId
  const newThreadId = crypto.randomUUID()
  aiSession.initializeSession({ threadId: newThreadId, targetPageType: null })
  messages.value = []
  inputMessage.value = ''
  showHistoryList.value = false
  showWelcome()
}

// 加载聊天历史列表
async function handleLoadHistoryList() {
  if (isLoadingHistory.value) return
  isLoadingHistory.value = true
  try {
    const res = await getChatHistoryList()
    historyList.value = Array.isArray(res) ? res : (Array.isArray(res?.data) ? res.data : [])
  } catch (error) {
    console.error('加载聊天历史列表失败:', error)
    historyList.value = []
  } finally {
    isLoadingHistory.value = false
  }
}

// 选择历史记录
async function handleSelectHistory(session) {
  if (session.thread_id === aiSession.threadId) {
    return
  }

  // 初始化会话
  aiSession.initializeSession({ threadId: session.thread_id, targetPageType: null })
  inputMessage.value = ''
  showHistoryList.value = false

  try {
    const res = await getAiFormState(session.thread_id)
    const state = res?.data || res || {}
    const messagesData = Array.isArray(state.messages) ? state.messages : []
    messages.value = messagesData.map((msg, index) => createMessage({
      role: msg.type === 'human' ? 'user' : 'assistant',
      content: msg.content || ''
    }))
    scrollToBottom()
  } catch (error) {
    console.error('加载历史会话失败:', error)
    ElMessage.error('加载历史会话失败')
  }
}

// 删除历史会话
async function handleDeleteHistory(threadIdToDelete) {
  try {
    await proxy.$modal.confirm('确定要删除这条对话记录吗？', '提示', { type: 'warning' })

    const res = await deleteAiFormState(threadIdToDelete)
    if (res?.status === 'success' || res?.code === 200) {
      ElMessage.success('删除成功')
      // 重新加载历史列表
      handleLoadHistoryList()
      // 如果删除的是当前会话，只清空消息和 session，保持历史列表
      if (threadIdToDelete === aiSession.threadId) {
        aiSession.resetSession()
        messages.value = []
        inputMessage.value = ''
      }
    } else {
      ElMessage.error(res?.message || '删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除历史会话失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

// 批量删除历史会话
async function handleBatchDeleteHistory() {
  if (selectedThreadIds.value.length === 0) {
    ElMessage.warning('请先选择要删除的对话')
    return
  }
  try {
    await proxy.$modal.confirm(`确定要删除选中的 ${selectedThreadIds.value.length} 条对话记录吗？`, '提示', { type: 'warning' })

    const res = await batchDeleteAiFormState(selectedThreadIds.value)
    if (res?.status === 'success' || res?.code === 200) {
      ElMessage.success('批量删除成功')
      const deletedIds = [...selectedThreadIds.value]
      selectedThreadIds.value = []
      handleLoadHistoryList()
      // 如果删除的包含当前会话，清空
      if (deletedIds.includes(aiSession.threadId)) {
        aiSession.resetSession()
        messages.value = []
        inputMessage.value = ''
      }
    } else {
      ElMessage.error(res?.message || '批量删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量删除历史会话失败:', error)
      ElMessage.error('批量删除失败')
    }
  }
}

// 全选/取消全选
function toggleSelectAll() {
  if (selectedThreadIds.value.length === historyList.value.length) {
    selectedThreadIds.value = []
  } else {
    selectedThreadIds.value = historyList.value.map(s => s.thread_id)
  }
}

// 切换单个选中
function toggleSelectOne(threadId) {
  const index = selectedThreadIds.value.indexOf(threadId)
  if (index > -1) {
    selectedThreadIds.value.splice(index, 1)
  } else {
    selectedThreadIds.value.push(threadId)
  }
}

// 获取当前时间
function getCurrentTime() {
  const now = new Date()
  return now.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

// 格式化历史时间
function formatTime(isoString) {
  if (!isoString) return ''
  const date = new Date(isoString)
  const now = new Date()
  const diff = now - date

  // 小于 1 分钟
  if (diff < 60000) return '刚刚'
  // 小于 1 小时
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  // 小于 24 小时
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  // 小于 7 天
  if (diff < 604800000) return `${Math.floor(diff / 86400000)}天前`

  // 超过 7 天显示具体日期
  return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

// 滚动到底部
function scrollToBottom() {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

// 发送消息
async function sendMessage() {
  if (isLoading.value) return

  const content = inputMessage.value.trim()
  if (!content) return

  // 添加用户消息
  messages.value.push(createMessage({
    role: 'user',
    content: content
  }))

  inputMessage.value = ''
  isLoading.value = true
  hasStreamingContent.value = false
  scrollToBottom()
  let aiMessageIndex = -1
  const controller = new AbortController()
  requestController.value = controller

  try {
    await aiFormChatStream({
      user_input: content,
      thread_id: aiSession.threadId
    }, (event) => {
      if (event.type === 'meta' && event.thread_id) {
        aiSession.initializeSession({
          threadId: event.thread_id,
          targetPageType: null
        })
      } else if (event.type === 'delta' && event.content) {
        if (aiMessageIndex === -1) {
          messages.value.push(createMessage({ role: 'assistant', content: '' }))
          aiMessageIndex = messages.value.length - 1
          hasStreamingContent.value = true
        }
        messages.value[aiMessageIndex].content += event.content
        scrollToBottom()
      } else if (event.type === 'done') {
        if (aiMessageIndex === -1) {
          messages.value.push(createMessage({
            role: 'assistant',
            content: event.response || '服务未返回有效响应,请稍后重试。'
          }))
          aiMessageIndex = messages.value.length - 1
        } else if (event.response && messages.value[aiMessageIndex].content !== event.response) {
          messages.value[aiMessageIndex].content = event.response
        }
        scrollToBottom()
      } else if (event.type === 'error') {
        throw new Error(event.message || '流式响应失败')
      }
    }, controller.signal)

  } catch (error) {
    if (error?.name === 'AbortError') return
    console.error('AI 对话失败:', error)
    if (aiMessageIndex === -1) {
      messages.value.push(createMessage({
        role: 'assistant',
        content: '抱歉，处理您的请求时出现问题，请稍后重试。'
      }))
    } else {
      messages.value[aiMessageIndex].content += '\n\n（响应中断，请稍后重试。）'
    }
    scrollToBottom()
  } finally {
    if (requestController.value === controller) requestController.value = null
    hasStreamingContent.value = false
    isLoading.value = false
  }
}

// 暴露方法给父组件
defineExpose({
  toggleVisible
})

// 生命周期
onMounted(async () => {
  // 监听打开事件
  window.addEventListener('open-ai-assistant', handleOpenAssistant)

  // 恢复会话
  if (aiSession.hasActiveSession) {
    const chatHistory = await aiSession.restoreSession()
    if (chatHistory) {
      messages.value = chatHistory.map((msg) => createMessage(msg))
    }
  }
})

onUnmounted(() => {
  requestController.value?.abort()
  window.removeEventListener('open-ai-assistant', handleOpenAssistant)
})

/**
 * 处理打开 AI 助手事件
 */
function handleOpenAssistant() {
  isVisible.value = true
}
</script>

<style lang="scss" scoped>
.ai-assistant-container {
  position: fixed;
  right: 20px;
  bottom: 20px;
  z-index: 9999;

  .ai-assistant-button {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    width: 56px;
    height: 56px;
    background: linear-gradient(135deg, #409eff 0%, #337ecc 100%);
    border-radius: 14px;
    box-shadow: 0 4px 12px rgba(64, 158, 255, 0.35);
    color: #fff;
    transition: all 0.3s ease;

    &:hover {
      transform: scale(1.06);
      box-shadow: 0 6px 16px rgba(64, 158, 255, 0.45);
    }

    .button-text {
      font-size: 11px;
      margin-top: 2px;
    }
  }
}

.assistant-body {
    flex: 1;
    min-height: 0;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    position: relative;

    // 消息区域
    .window-messages {
      flex: 1;
      overflow-y: auto;
      padding: 16px;
      background: #f5f7fa;

      &::-webkit-scrollbar {
        width: 4px;
      }

      &::-webkit-scrollbar-track {
        background: transparent;
      }

      &::-webkit-scrollbar-thumb {
        background: #dcdfe6;
        border-radius: 2px;
      }
    }

    // 输入区域
    .window-input {
      flex-shrink: 0;
      padding: 12px 16px;
      background: #fff;
      border-top: 1px solid #f0f0f0;

      .el-textarea {
        :deep(.el-textarea__inner) {
          background: #f5f7fa;
          border: 1px solid #dcdfe6;
          border-radius: 6px;
          color: #303133;
          padding: 10px 14px;
          resize: none;
          font-size: 14px;

          &::placeholder {
            color: #a0a0a0;
          }

          &:focus {
            border-color: #409eff;
            background: #fff;
          }
        }
      }

      .send-button {
        background: linear-gradient(135deg, #409eff 0%, #337ecc 100%);
        border: none;
        border-radius: 6px;
        padding: 8px 18px;
        color: #fff;
        font-weight: 500;
        font-size: 14px;
        transition: all 0.3s ease;

        &:hover:not(:disabled) {
          transform: translateY(-1px);
          box-shadow: 0 4px 10px rgba(64, 158, 255, 0.35);
        }

        &:disabled {
          opacity: 0.6;
        }
      }
    }

    // 历史列表覆盖层
    .history-overlay {
      display: flex;
      flex-direction: column;
      background: #fff;

      .history-header {
        flex-shrink: 0;
        padding: 14px 16px;
        border-bottom: 1px solid #f0f0f0;

        span {
          color: #303133;
          font-size: 14px;
          font-weight: 500;
        }

        .el-button {
          color: #909399;
          padding: 4px;

          &:hover {
            color: #409eff;
          }
        }
      }

      .history-list {
        flex: 1;
        overflow-y: auto;
        padding: 12px;

        &::-webkit-scrollbar {
          width: 4px;
        }

        &::-webkit-scrollbar-thumb {
          background: #dcdfe6;
          border-radius: 2px;
        }

        .history-item {
          padding: 12px 14px;
          border-radius: 6px;
          margin-bottom: 8px;
          cursor: pointer;
          transition: all 0.2s;
          background: #f5f7fa;
          border: 1px solid transparent;

          &:hover {
            background: #ecf5ff;
          }

          &.active {
            background: #ecf5ff;
            border-color: #409eff;
          }

          .history-preview {
            color: #606266;
            font-size: 13px;
            line-height: 1.4;
          }

          .history-meta {
            margin-top: 8px;

            .history-time {
              color: #c0c4cc;
              font-size: 12px;
            }

            .el-button {
              color: #c0c4cc;
              padding: 2px;

              &:hover {
                color: #f56c6c;
              }
            }
          }
        }

        .empty-history {
          color: #909399;
          font-size: 13px;
          text-align: center;
          padding: 40px 0;
        }
      }
    }
  }

// 消息样式
.message {
  margin-bottom: 14px;
  display: flex;
  gap: 10px;

  &.user {
    flex-direction: row-reverse;

    .message-content {
      .message-bubble {
        background: linear-gradient(135deg, #409eff 0%, #337ecc 100%);
        color: #fff;
        border-radius: 16px 16px 4px 16px;
      }
    }
  }

  &.assistant {
    .message-content {
      .message-bubble {
        background: #fff;
        color: #303133;
        border-radius: 16px 16px 16px 4px;
        box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
      }
    }
  }

  .message-avatar {
    width: 34px;
    height: 34px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    background: #ecf5ff;
    color: #409eff;
    font-size: 15px;
  }

  .message-content {
    max-width: 72%;

    .message-bubble {
      padding: 10px 14px;
      font-size: 14px;
      line-height: 1.5;
      word-break: break-word;
    }
  }
}

// Thinking 动画样式
.thinking-indicator {
  .typing-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background-color: #409eff;
    animation: typing 1.4s infinite;
    animation-fill-mode: both;

    &:nth-child(1) { animation-delay: 0s; }
    &:nth-child(2) { animation-delay: 0.2s; }
    &:nth-child(3) { animation-delay: 0.4s; }
  }
}

@keyframes typing {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.4);
    opacity: 0.6;
  }
}
</style>

<!-- 全局样式修复 modal z-index -->
<style>
.el-overlay-dialog {
  z-index: 10000 !important;
}
.el-message-box {
  z-index: 10001 !important;
}
</style>
