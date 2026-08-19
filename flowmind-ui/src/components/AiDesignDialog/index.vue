<template>
  <el-dialog
    v-model="visible"
    width="520px"
    destroy-on-close
    class="ai-design-dialog"
  >
    <template #header>
      <div class="dialog-header">
        <span class="dialog-title">{{ title }}</span>
        <el-button link type="info" @click="clearMessages" :disabled="loading">
          新建对话
        </el-button>
      </div>
    </template>
    <div class="dialog-messages" ref="messagesContainer">
      <div
        v-for="(msg, index) in messages"
        :key="index"
        :class="['message flex gap-3 mb-4', msg.role === 'user' ? 'flex-row-reverse' : '']"
      >
        <div class="message-avatar flex-shrink-0 flex items-center justify-center text-blue-500">
          <el-icon v-if="msg.role === 'assistant'" :size="20">
            <ChatDotRound />
          </el-icon>
          <el-avatar v-else size="small" :src="userStore.avatar" />
        </div>
        <div
          :class="[
            'message-text px-3.5 py-2.5 rounded-3xl text-sm leading-relaxed break-all markdown-content',
            msg.role === 'user' ? 'bg-blue-500 text-white' : 'bg-white text-gray-800'
          ]"
          v-html="renderMarkdown(msg.content)"
        ></div>
      </div>
      <div v-if="loading" class="message assistant flex gap-3 mb-4">
        <div class="message-avatar flex-shrink-0 flex items-center justify-center text-blue-500">
          <el-icon :size="20"><ChatDotRound /></el-icon>
        </div>
        <div class="message-text px-3.5 py-2.5 rounded-3xl text-sm bg-white">
          <span v-if="progressText" class="text-gray-600">{{ progressText }}</span>
          <template v-else>
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
          </template>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-input
          v-model="inputText"
          placeholder="请描述您的需求"
          @keydown.enter="handleSend"
          :disabled="loading"
          size="default"
          maxlength="2000"
          show-word-limit
        />
        <el-button type="primary" @click="handleSend" :loading="loading" :disabled="!inputText.trim()">
          发送
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { designStream, clearDesignState } from '@/api/workflow/design'
import { ChatDotRound } from '@element-plus/icons-vue'
import useUserStore from '@/store/modules/user'
import MarkdownIt from 'markdown-it'
import DOMPurify from 'dompurify'

const userStore = useUserStore()

const props = defineProps({
  modelValue: Boolean,
  designType: {
    type: String,
    default: 'category'
  },
  formData: {
    type: Object,
    default: () => ({})
  },
  mode: {
    type: String,
    default: 'design'
  },
  sessionId: {
    type: String,
    default: null
  }
})

const emit = defineEmits(['update:modelValue', 'fill'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const title = computed(() => ({
  category: 'AI 设计分类',
  flow: 'AI 设计流程',
  form: 'AI 设计表单'
}[props.designType] || 'AI 设计'))

const inputText = ref('')
const messages = ref([])
const loading = ref(false)
const progressText = ref('')
const messagesContainer = ref(null)
// 统一维护当前表单数据：AI 更新和外部修改都同步到这里
const currentFormData = ref({})

// 监听外部 formData 变化，同步到 currentFormData
watch(() => props.formData, (newVal) => {
  if (newVal && Object.keys(newVal).length > 0) {
    // 合并外部数据，保留 AI 已返回的数据
    currentFormData.value = { ...currentFormData.value, ...newVal }
  }
}, { deep: true, immediate: true })

// Markdown 渲染配置
const md = new MarkdownIt({
  html: true,
  breaks: true,
  linkify: true,
  typographer: true
})

// 渲染 Markdown 并处理换行
function renderMarkdown(content) {
  if (!content) return ''

  let formattedContent = content
    .replace(/\r\n/g, '\n')
    .replace(/\r/g, '\n')

  return DOMPurify.sanitize(md.render(formattedContent))
}

// 流程标识：优先用 formData 里的业务标识（区分不同流程），否则 sessionId，否则 'new'
const flowKey = computed(() => {
  const fd = props.formData || {}
  return fd.modelId || fd.modelKey || fd.formId || fd.code || props.sessionId || 'new'
})

const storageKey = computed(() => {
  return `ai_design_${props.designType}_${flowKey.value}`
})

// 版本历史：每轮 AI 生成成功后存一个版本，用于"回到一开始/上一步"
const VERSION_LIMIT = 20
const versionKey = computed(() => {
  return `ai_design_versions_${props.designType}_${flowKey.value}`
})

function getVersions() {
  const saved = sessionStorage.getItem(versionKey.value)
  try {
    return saved ? JSON.parse(saved) : []
  } catch (e) {
    return []
  }
}

function saveVersion(formData) {
  const versions = getVersions()
  versions.push(formData)
  if (versions.length > VERSION_LIMIT) versions.shift()
  sessionStorage.setItem(versionKey.value, JSON.stringify(versions))
}

function rollbackTo(target) {
  const versions = getVersions()
  const idx = target === 'start' ? 0 : versions.length - 2  // "prev" = 倒数第二
  const version = versions[idx]
  if (version) {
    currentFormData.value = version
    emit('fill', version)
    // 截断到目标版本（丢弃之后的），这样连续"上一步"能逐级回退
    sessionStorage.setItem(versionKey.value, JSON.stringify(versions.slice(0, idx + 1)))
    return true
  }
  return false
}

onMounted(() => {
  const saved = sessionStorage.getItem(storageKey.value)
  if (saved) {
    try {
      const state = JSON.parse(saved)
      messages.value = state.messages || []
      // 恢复已保存的表单数据
      if (state.currentFormData && Object.keys(state.currentFormData).length > 0) {
        currentFormData.value = state.currentFormData
      } else {
        currentFormData.value = { ...props.formData }
      }
    } catch (e) {
      console.error('恢复聊天记录失败:', e)
      currentFormData.value = { ...props.formData }
    }
  } else {
    currentFormData.value = { ...props.formData }
  }
})

watch(visible, (val) => {
  if (val) {
    // 弹窗打开时：优先用 sessionStorage 保存的数据，其次用外部传入的
    const saved = sessionStorage.getItem(storageKey.value)
    if (saved) {
      try {
        const state = JSON.parse(saved)
        messages.value = state.messages || []
        if (state.currentFormData && Object.keys(state.currentFormData).length > 0) {
          currentFormData.value = state.currentFormData
        } else {
          currentFormData.value = { ...props.formData }
        }
      } catch (e) {
        currentFormData.value = { ...props.formData }
      }
    } else {
      currentFormData.value = { ...props.formData }
    }
  } else {
    // 弹窗关闭时：保存状态
    sessionStorage.setItem(storageKey.value, JSON.stringify({
      messages: messages.value,
      currentFormData: currentFormData.value
    }))
  }
})

async function handleSend() {
  if (!inputText.value.trim() || loading.value) return

  const userInput = inputText.value.trim()
  inputText.value = ''

  messages.value.push({ role: 'user', content: userInput })
  scrollToBottom()

  loading.value = true
  progressText.value = ''

  try {
    await designStream(props.designType, {
      user_input: userInput,
      current_form_data: currentFormData.value,
      mode: props.mode
    }, (event) => {
      if (event.type === 'progress') {
        progressText.value = event.message
      } else if (event.type === 'done') {
        const data = event
        // 回退指令：恢复到目标版本（后端判别返回 rollback）
        if (data.kind === 'rollback') {
          if (rollbackTo(data.target)) {
            messages.value.push({ role: 'assistant', content: data.message || '已回退到指定版本' })
          } else {
            messages.value.push({ role: 'assistant', content: '没有可回退的版本' })
          }
          scrollToBottom()
        } else if (data.kind === 'reset') {
          currentFormData.value = { ...props.formData }
          emit('fill', currentFormData.value)
          sessionStorage.removeItem(versionKey.value)
          messages.value.push({ role: 'assistant', content: data.message || '已清空，重新开始' })
          scrollToBottom()
        } else if (data.form_data != null && JSON.stringify(data.form_data) !== '{}') {
          currentFormData.value = data.form_data
          emit('fill', data.form_data)
          // 完整成功才存版本 + 关闭；半成品草稿（partial）保持打开
          if (data.intent === 'success' && !data.partial) {
            saveVersion(data.form_data)
            visible.value = false
          }
        }
        if (data.message && data.kind !== 'rollback') {
          messages.value.push({ role: 'assistant', content: data.message })
          scrollToBottom()
        }
      } else if (event.type === 'error') {
        messages.value.push({ role: 'assistant', content: event.message || '服务暂时不可用，请稍后重试。' })
        scrollToBottom()
      }

      sessionStorage.setItem(storageKey.value, JSON.stringify({
        messages: messages.value,
        currentFormData: currentFormData.value
      }))
    })
  } catch (error) {
    console.error('AI 设计失败:', error)
    messages.value.push({ role: 'assistant', content: '抱歉，服务暂时不可用，请稍后重试。' })
    scrollToBottom()
  } finally {
    loading.value = false
    progressText.value = ''
  }
}

function scrollToBottom() {
  setTimeout(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  }, 0)
}


function clearMessages() {
  messages.value = []
  // 保留 props.formData 中的基本信息（modelId, modelName, modelKey 等）
  // 只清空 AI 生成的数据
  currentFormData.value = { ...props.formData }
  sessionStorage.removeItem(storageKey.value)
  sessionStorage.removeItem(versionKey.value)
  // 同步清除后端 Redis 中的对话历史
  clearDesignState(props.designType)
}

defineExpose({
  clearMessages
})
</script>

<style lang="scss" scoped>
.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.dialog-messages {
  height: 320px;
  overflow-y: auto;
  padding: 16px;
  background: #f5f7fa;
}

.message {
  &.user .message-text {
    border-radius: 16px 16px 4px 16px;
  }

  &.assistant .message-text {
    border-radius: 16px 16px 16px 4px;
  }
}

.message-avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: #ecf5ff;
}

.message-text {
  max-width: 75%;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
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

  :deep(p:first-child) {
    margin-top: 0;
  }

  :deep(p:last-child) {
    margin-bottom: 0;
  }

  :deep(code) {
    background-color: rgba(0, 0, 0, 0.06);
    padding: 2px 6px;
    border-radius: 4px;
    font-family: 'Consolas', 'Monaco', monospace;
    font-size: 0.9em;
    white-space: pre;
  }

  :deep(pre) {
    background-color: #f6f8fa;
    padding: 12px;
    border-radius: 6px;
    overflow-x: auto;
    margin: 0.5em 0;

    code {
      background-color: transparent;
      padding: 0;
      white-space: pre;
    }
  }

  :deep(ul), :deep(ol) {
    padding-left: 1.5em;
    margin: 0.5em 0;
  }

  :deep(li) {
    margin: 0.25em 0;
    white-space: normal;
  }

  :deep(li > p) {
    margin: 0;
    display: inline;
  }

  :deep(blockquote) {
    border-left: 4px solid #667eea;
    padding-left: 1em;
    margin: 0.5em 0;
    color: #666;
  }

  :deep(strong) {
    font-weight: 600;
  }

  :deep(em) {
    font-style: italic;
  }

  :deep(h1), :deep(h2), :deep(h3), :deep(h4), :deep(h5), :deep(h6) {
    margin: 0.75em 0 0.5em;
    font-weight: 600;
    line-height: 1.25;
  }

  :deep(h1:first-child), :deep(h2:first-child), :deep(h3:first-child) {
    margin-top: 0;
  }

  :deep(table) {
    border-collapse: collapse;
    width: 100%;
    margin: 0.5em 0;
    display: block;
    overflow-x: auto;
  }

  :deep(th), :deep(td) {
    border: 1px solid #ddd;
    padding: 6px 12px;
    text-align: left;
  }

  :deep(th) {
    background-color: #f6f8fa;
    font-weight: 600;
  }

  :deep(a) {
    color: #667eea;
    text-decoration: none;

    &:hover {
      text-decoration: underline;
    }
  }

  :deep(hr) {
    border: none;
    border-top: 1px solid #ddd;
    margin: 1em 0;
  }
}

.typing-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: #409eff;
  animation: typing 1.4s infinite;
  animation-fill-mode: both;
  display: inline-block;
  margin-right: 4px;

  &:nth-child(1) { animation-delay: 0s; }
  &:nth-child(2) { animation-delay: 0.2s; }
  &:nth-child(3) { animation-delay: 0.4s; }
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

.dialog-footer {
  display: flex;
  gap: 10px;
  padding: 12px 16px;
  border-top: 1px solid #ebeef5;

  .el-input {
    flex: 1;
  }
}
</style>
