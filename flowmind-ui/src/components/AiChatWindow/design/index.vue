<template>
  <AiFloatingWindow
    :model-value="visible"
    :title="title"
    :icon="ChatDotRound"
    :width="540"
    :height="640"
    :min-width="380"
    :min-height="460"
    @update:model-value="visible = $event"
  >
    <template #actions>
      <el-button
        link
        type="info"
        title="新建对话"
        :disabled="loading"
        @click="clearMessages"
      >
        <el-icon><Plus /></el-icon>
      </el-button>
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

    <div v-if="pendingPreview" class="change-preview">
      <div class="change-preview__title">变更预览</div>
      <div class="change-preview__summary">
        共 {{ pendingPreview.operation_count || pendingPreview.operations?.length || 0 }} 项变更，
        已通过语法和业务校验
      </div>
      <ul v-if="pendingPreview.operations?.length" class="change-preview__operations">
        <li v-for="(operation, index) in pendingPreview.operations" :key="index">
          {{ operationLabel(operation) }}
        </li>
      </ul>
      <div class="change-preview__actions">
        <el-button @click="discardPreview">放弃</el-button>
        <el-button type="primary" @click="applyPreview">应用变更</el-button>
      </div>
    </div>

    <div class="dialog-footer">
      <el-checkbox v-if="mode === 'design' && designType !== 'category'" v-model="allowFullReplace" :disabled="loading">
        全部重新生成
      </el-checkbox>
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
  </AiFloatingWindow>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { designStream, clearDesignState } from '@/api/workflow/design'
import { ChatDotRound, Plus } from '@element-plus/icons-vue'
import AiFloatingWindow from '@/components/AiFloatingWindow/index.vue'
import useUserStore from '@/store/modules/user'
import MarkdownIt from 'markdown-it'
import DOMPurify from 'dompurify'
import { ElMessageBox } from 'element-plus'

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

const emit = defineEmits(['update:modelValue', 'fill', 'preview', 'discard', 'progress', 'designing'])

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
const pendingPreview = ref(null)
const previewBaseline = ref(null)
const allowFullReplace = ref(false)
const messagesContainer = ref(null)
const requestController = ref(null)
// 统一维护当前表单数据：AI 更新和外部修改都同步到这里
const currentFormData = ref({})

// 监听外部 formData 变化，同步到 currentFormData
watch(() => props.formData, (newVal) => {
  if (newVal && Object.keys(newVal).length > 0) {
    // 父页面保存后的数据是权威基线，完整替换可避免已删除字段被旧会话带回。
    currentFormData.value = cloneData(newVal)
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

// 新建对象无业务标识时生成临时会话 id，保证不同对象会话/版本历史不串扰
const localSessionId = ref(
  props.formData?.code || 's_' + Date.now().toString(36) + Math.random().toString(36).slice(2, 8)
)

// 流程标识：优先用 formData 业务标识，否则 sessionId，否则临时 id，否则 'new'
const flowKey = computed(() => {
  const fd = props.formData || {}
  return fd.modelId || fd.modelKey || fd.formId || props.sessionId || localSessionId.value
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
  versions.push(cloneData(formData))
  if (versions.length > VERSION_LIMIT) versions.splice(1, 1)
  sessionStorage.setItem(versionKey.value, JSON.stringify(versions))
}

function ensureBaselineVersion() {
  if (getVersions().length === 0) saveVersion(currentFormData.value)
}

function rollbackTo(target) {
  const versions = getVersions()
  const idx = target === 'start' ? 0 : versions.length - 2  // "prev" = 倒数第二
  const version = versions[idx]
  if (version) {
    currentFormData.value = cloneData(version)
    emit('fill', currentFormData.value)
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
      currentFormData.value = cloneData(props.formData)
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
        currentFormData.value = cloneData(props.formData)
      } catch (e) {
        currentFormData.value = { ...props.formData }
      }
    } else {
      currentFormData.value = { ...props.formData }
    }
  } else {
    requestController.value?.abort()
    discardPreview()
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
  if (allowFullReplace.value) {
    try {
      await ElMessageBox.confirm(
        '全部重新生成会丢弃当前设计，确认继续吗？',
        '二次确认',
        { type: 'warning', confirmButtonText: '确认重新生成', cancelButtonText: '取消' }
      )
    } catch {
      return
    }
  }
  inputText.value = ''

  messages.value.push({ role: 'user', content: userInput })
  scrollToBottom()

  loading.value = true
  progressText.value = ''
  emit('designing', true)
  const controller = new AbortController()
  requestController.value = controller

  try {
    await designStream(props.designType, {
      user_input: userInput,
      current_form_data: currentFormData.value,
      mode: props.mode,
      thread_id: flowKey.value,
      allow_full_replace: allowFullReplace.value
    }, (event) => {
      if (event.type === 'progress') {
        progressText.value = event.message
        emit('progress', event.message)
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
        } else if (data.status === 'ready' && data.form_data != null) {
          previewBaseline.value = cloneData(currentFormData.value)
          pendingPreview.value = data
          emit('preview', data.form_data)
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
    }, controller.signal)
  } catch (error) {
    if (error?.name === 'AbortError') return
    console.error('AI 设计失败:', error)
    messages.value.push({ role: 'assistant', content: '抱歉，服务暂时不可用，请稍后重试。' })
    scrollToBottom()
  } finally {
    if (requestController.value === controller) requestController.value = null
    allowFullReplace.value = false
    loading.value = false
    progressText.value = ''
    emit('designing', false)
  }
}

function scrollToBottom() {
  setTimeout(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  }, 0)
}

onBeforeUnmount(() => requestController.value?.abort())

function operationLabel(operation) {
  const labels = {
    replace_graph: '生成流程结构', add_node: '新增流程节点', update_node: '修改流程节点',
    remove_node: '删除流程节点', add_edge: '新增流程连线', update_edge: '修改流程连线',
    remove_edge: '删除流程连线', replace_form: '生成表单结构', add_widget: '新增表单字段',
    update_widget: '修改表单字段', remove_widget: '删除表单字段', move_widget: '移动表单字段',
    update_category: '修改分类信息', update_flow_metadata: '修改流程基本信息'
  }
  const target = operation.node_id || operation.widget_name || operation.node?.name || operation.widget?.options?.label
  return `${labels[operation.op] || operation.op}${target ? `：${target}` : ''}`
}

function cloneData(value) {
  return JSON.parse(JSON.stringify(value || {}))
}

async function applyPreview() {
  if (!pendingPreview.value) return
  ensureBaselineVersion()
  const formData = pendingPreview.value.form_data
  currentFormData.value = cloneData(formData)
  emit('fill', formData)
  saveVersion(formData)
  pendingPreview.value = null
  previewBaseline.value = null
  visible.value = false
}

function discardPreview() {
  if (!pendingPreview.value) return
  if (previewBaseline.value) currentFormData.value = cloneData(previewBaseline.value)
  pendingPreview.value = null
  previewBaseline.value = null
  emit('discard')
}


function clearMessages() {
  discardPreview()
  messages.value = []
  // 保留 props.formData 中的基本信息（modelId, modelName, modelKey 等）
  // 只清空 AI 生成的数据
  currentFormData.value = { ...props.formData }
  sessionStorage.removeItem(storageKey.value)
  sessionStorage.removeItem(versionKey.value)
  // 同步清除后端 Redis 中的对话历史
  clearDesignState(props.designType, flowKey.value, props.mode).catch((error) => {
    console.warn('清除后端对话历史失败:', error)
  })
}

defineExpose({
  clearMessages
})
</script>

<style lang="scss" scoped>
.dialog-messages {
  flex: 1;
  min-height: 0;
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

.change-preview {
  padding: 12px 16px;
  border-top: 1px solid #dcdfe6;
  background: #f0f9eb;
}

.change-preview__title { font-weight: 600; color: #303133; }
.change-preview__summary { margin-top: 4px; font-size: 12px; color: #606266; }
.change-preview__operations { margin: 8px 0; max-height: 96px; overflow: auto; font-size: 12px; }
.change-preview__actions { display: flex; justify-content: flex-end; gap: 8px; }
</style>
