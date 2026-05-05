<template>
  <el-dialog
    v-model="visible"
    :title="title"
    width="520px"
    destroy-on-close
    class="ai-design-dialog"
  >
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
            'message-text px-3.5 py-2.5 rounded-3xl text-sm leading-relaxed break-all',
            msg.role === 'user' ? 'bg-blue-500 text-white' : 'bg-white text-gray-800'
          ]"
        >
          {{ msg.content }}
        </div>
      </div>
      <div v-if="loading" class="message assistant flex gap-3 mb-4">
        <div class="message-avatar flex-shrink-0 flex items-center justify-center text-blue-500">
          <el-icon :size="20"><ChatDotRound /></el-icon>
        </div>
        <div class="message-text px-3.5 py-2.5 rounded-3xl text-sm bg-white">
          <span class="typing-dot"></span>
          <span class="typing-dot"></span>
          <span class="typing-dot"></span>
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
import { designCategory, designFlow, designForm } from '@/api/workflow/design'
import { ChatDotRound } from '@element-plus/icons-vue'
import useUserStore from '@/store/modules/user'

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
const messagesContainer = ref(null)

const designApi = { category: designCategory, flow: designFlow, form: designForm }

const storageKey = computed(() => {
  const id = props.sessionId || 'new'
  return `ai_design_${props.designType}_${id}`
})

onMounted(() => {
  const saved = sessionStorage.getItem(storageKey.value)
  if (saved) {
    try {
      messages.value = JSON.parse(saved).messages || []
    } catch (e) {
      console.error('恢复聊天记录失败:', e)
    }
  }
})

watch(visible, (val) => {
  if (val) {
    const saved = sessionStorage.getItem(storageKey.value)
    if (saved) {
      try {
        messages.value = JSON.parse(saved).messages || []
      } catch (e) {
        messages.value = []
      }
    }
  } else {
    sessionStorage.setItem(storageKey.value, JSON.stringify({ messages: messages.value }))
  }
})

async function handleSend() {
  if (!inputText.value.trim() || loading.value) return

  const userInput = inputText.value.trim()
  inputText.value = ''

  messages.value.push({ role: 'user', content: userInput })
  scrollToBottom()

  loading.value = true

  try {
    const api = designApi[props.designType]
    const res = await api({
      user_input: userInput,
      conversation_history: messages.value,
      current_form_data: props.formData,
      mode: props.mode
    })

    const data = res.data || res

    if (data.form_data) {
      emit('fill', data.form_data)
    }
    if (data.message) {
      messages.value.push({ role: 'assistant', content: data.message })
      scrollToBottom()
    }

    sessionStorage.setItem(storageKey.value, JSON.stringify({ messages: messages.value }))
  } catch (error) {
    console.error('AI 设计失败:', error)
    messages.value.push({ role: 'assistant', content: '抱歉，服务暂时不可用，请稍后重试。' })
    scrollToBottom()
  } finally {
    loading.value = false
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
  sessionStorage.removeItem(storageKey.value)
}

defineExpose({
  clearMessages
})
</script>

<style lang="scss" scoped>
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
