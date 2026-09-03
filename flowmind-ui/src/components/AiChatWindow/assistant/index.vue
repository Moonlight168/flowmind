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

    <!-- 对话窗口 (可拖拽悬浮球) -->
    <div
      v-else
      ref="windowRef"
      class="ai-assistant-window"
      :style="{
        left: windowPosition.x + 'px',
        top: windowPosition.y + 'px',
        width: windowSize.width + 'px',
        height: windowSize.height + 'px'
      }"
    >
      <!-- 窗口头部 (拖拽区域) -->
      <div
        class="window-header flex items-center justify-between p-4 bg-gradient-to-r from-blue-500 to-purple-600 text-white cursor-move select-none"
        @mousedown="startDrag"
      >
        <div class="header-title flex items-center gap-2 text-base font-semibold">
          <el-icon :size="20"><ChatDotRound /></el-icon>
          <span>AI 助手</span>
        </div>
        <div class="header-actions flex items-center gap-1">
          <!-- 切换历史列表显示 -->
          <el-button link type="info" @click="toggleHistoryList" title="历史对话">
            <el-icon><List /></el-icon>
          </el-button>
                    <!-- 新建对话 -->
          <el-button link type="info" @click="handleNewChat" title="新建对话">
            <el-icon><Plus /></el-icon>
          </el-button>
          <el-button link type="info" @click="toggleVisible" title="关闭">
            <el-icon><Close /></el-icon>
          </el-button>
        </div>
      </div>

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
            :disabled="isLoading || awaitingConfirmation"
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

      <!-- 右下角调整大小手柄 -->
      <div
        class="resize-handle resize-handle-se"
        @mousedown="startResize('se')"
      >
        <el-icon :size="12"><MoreFilled /></el-icon>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, getCurrentInstance, onMounted, onUnmounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { ChatDotRound, Close, Delete, Plus, List, MoreFilled, Check } from '@element-plus/icons-vue'
import { aiFormChatStream, getAiFormState, deleteAiFormState, batchDeleteAiFormState, getChatHistoryList } from '@/api/workflow/ai'
import { ElMessage } from 'element-plus'
import { useAiSessionStore } from '@/store/modules/aiSession'
import MessageItem from './MessageItem.vue'

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
const windowRef = ref(null)

// 创建带唯一 ID 的消息对象
let messageIdCounter = 0
function createMessage(data) {
  return { id: `msg-${++messageIdCounter}`, time: getCurrentTime(), ...data }
}

// 使用计算属性访问 session 状态
const threadId = computed(() => aiSession.threadId)

// 最后一条消息是否处于待确认状态，禁用输入框强制用户点击按钮
const PENDING_STATUSES = ['category_pending', 'form_pending', 'flow_pending', 'awaiting_confirm']
const awaitingConfirmation = computed(() => {
  if (messages.value.length === 0) return false
  const last = messages.value[messages.value.length - 1]
  return last?.role === 'assistant' && PENDING_STATUSES.includes(last.workflow_status)
})

// 历史面板相关
const showHistoryList = ref(false)
const historyList = ref([])
const selectedThreadIds = ref([])
const isLoadingHistory = ref(false)

// 窗口位置（支持拖拽）
const windowPosition = ref({ x: 0, y: 0 })
const isDragging = ref(false)
const dragOffset = ref({ x: 0, y: 0 })

// 窗口大小（支持调整）
const windowSize = ref({ width: 400, height: 560 })
const isResizing = ref(false)
const resizeDirection = ref('')
const resizeStart = ref({ x: 0, y: 0 })
const resizeStartSize = ref({ width: 0, height: 0 })
const requestController = ref(null)

// 最小窗口尺寸
const MIN_WIDTH = 300
const MIN_HEIGHT = 400

// 初始化窗口位置（右下角）
function initWindowPosition() {
  const windowWidth = window.innerWidth
  const windowHeight = window.innerHeight
  windowPosition.value = {
    x: windowWidth - 440,
    y: windowHeight - 620
  }
}

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
      selectedThreadIds.value = []
      handleLoadHistoryList()
      // 如果删除的包含当前会话，清空
      if (selectedThreadIds.value.includes(aiSession.threadId)) {
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

// 拖拽相关方法
function startDrag(e) {
  isDragging.value = true
  const rect = windowRef.value.getBoundingClientRect()
  dragOffset.value = {
    x: e.clientX - rect.left,
    y: e.clientY - rect.top
  }

  document.addEventListener('mousemove', onDrag)
  document.addEventListener('mouseup', stopDrag)
  e.preventDefault()
}

function onDrag(e) {
  if (!isDragging.value) return

  const newX = e.clientX - dragOffset.value.x
  const newY = e.clientY - dragOffset.value.y

  // 限制在视口范围内
  const maxX = window.innerWidth - windowRef.value.offsetWidth
  const maxY = window.innerHeight - windowRef.value.offsetHeight

  windowPosition.value = {
    x: Math.max(0, Math.min(newX, maxX)),
    y: Math.max(0, Math.min(newY, maxY))
  }
}

function stopDrag() {
  isDragging.value = false
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
}


// 调整窗口大小
function startResize(direction) {
  isResizing.value = true
  resizeDirection.value = direction
  resizeStart.value = {
    x: event.clientX,
    y: event.clientY
  }
  resizeStartSize.value = {
    width: windowSize.value.width,
    height: windowSize.value.height
  }

  document.addEventListener('mousemove', onResize)
  document.addEventListener('mouseup', stopResize)
  event.preventDefault()
}

function onResize(e) {
  if (!isResizing.value) return

  const deltaX = e.clientX - resizeStart.value.x
  const deltaY = e.clientY - resizeStart.value.y

  // 根据拖拽方向调整大小
  if (resizeDirection.value === 'se') {
    // 右下角：同时调整宽度和高度
    const newWidth = resizeStartSize.value.width + deltaX
    const newHeight = resizeStartSize.value.height + deltaY

    windowSize.value.width = Math.max(MIN_WIDTH, newWidth)
    windowSize.value.height = Math.max(MIN_HEIGHT, newHeight)
  }

  // 确保窗口不超出视口
  const maxX = window.innerWidth - windowSize.value.width
  const maxY = window.innerHeight - windowSize.value.height

  windowPosition.value.x = Math.min(windowPosition.value.x, maxX)
  windowPosition.value.y = Math.min(windowPosition.value.y, maxY)
}

function stopResize() {
  isResizing.value = false
  resizeDirection.value = ''
  document.removeEventListener('mousemove', onResize)
  document.removeEventListener('mouseup', stopResize)
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
  initWindowPosition()

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

  .ai-assistant-window {
    position: fixed;
    width: 420px;
    height: 580px;
    background: #fff;
    border-radius: 8px;
    box-shadow: 0 6px 24px rgba(0, 0, 0, 0.15);
    display: flex;
    flex-direction: column;
    overflow: hidden;
    z-index: 9999;
    min-width: 360px;
    min-height: 480px;
    border: 1px solid #e4e7ed;

    // 头部
    .window-header {
      flex-shrink: 0;
      padding: 14px 16px;
      background: #fff;
      border-bottom: 1px solid #f0f0f0;

      .header-title {
        .el-icon {
          color: #409eff;
        }
        span {
          color: #303133;
          font-size: 15px;
        }
      }

      .header-actions {
        .el-button {
          color: #909399;
          padding: 6px 8px;
          border-radius: 6px;
          transition: all 0.2s;

          &:hover {
            color: #409eff;
            background: #f5f7fa;
          }
        }
      }
    }

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

    // 右下角调整大小手柄
    .resize-handle-se {
      position: absolute;
      right: 0;
      bottom: 0;
      width: 18px;
      height: 18px;
      cursor: nwse-resize;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #c0c4cc;
      transition: color 0.2s;
      z-index: 10;

      &:hover {
        color: #409eff;
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

// Markdown 内容样式
.markdown-content {
  word-break: break-word;
  white-space: normal;

  :deep(p) {
    margin: 0.5em 0;
    line-height: 1.6;
    white-space: pre-wrap;
    word-wrap: break-word;
  }

  :deep(p:first-child) { margin-top: 0; }
  :deep(p:last-child) { margin-bottom: 0; }

  :deep(code) {
    background-color: #f0f2f5;
    padding: 2px 6px;
    border-radius: 4px;
    font-family: 'Consolas', 'Monaco', monospace;
    font-size: 0.9em;
  }

  :deep(pre) {
    background-color: #f6f8fa;
    padding: 12px;
    border-radius: 6px;
    overflow-x: auto;
    margin: 0.8em 0;

    code {
      background-color: transparent;
      padding: 0;
    }
  }

  :deep(ul), :deep(ol) {
    padding-left: 1.5em;
    margin: 0.5em 0;
  }

  :deep(li) {
    margin: 0.25em 0;
  }

  :deep(blockquote) {
    border-left: 3px solid #409eff;
    padding-left: 1em;
    margin: 0.8em 0;
    color: #606266;
  }

  :deep(strong) { font-weight: 600; }
  :deep(em) { font-style: italic; }

  :deep(h1), :deep(h2), :deep(h3), :deep(h4) {
    margin: 1em 0 0.5em;
    font-weight: 600;
    color: #303133;
  }

  :deep(table) {
    border-collapse: collapse;
    width: 100%;
    margin: 0.8em 0;
  }

  :deep(th), :deep(td) {
    border: 1px solid #dcdfe6;
    padding: 8px 12px;
  }

  :deep(th) {
    background-color: #f5f7fa;
    font-weight: 600;
  }

  :deep(a) {
    color: #409eff;
    text-decoration: none;

    &:hover { text-decoration: underline; }
  }

  :deep(hr) {
    border: none;
    border-top: 1px solid #dcdfe6;
    margin: 1em 0;
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
