<template>
  <AiFloatingWindow
    :model-value="visible"
    :title="title"
    :icon="ChatDotRound"
    :width="440"
    :height="600"
    :min-width="380"
    :min-height="460"
    @update:model-value="visible = $event"
  >
    <template #actions>
      <el-button
        link
        type="info"
        title="回退上一版"
        :disabled="loading || pendingPreview || !canRollback"
        @click="handleRollback('prev')"
      >
        <el-icon><Back /></el-icon>
      </el-button>
      <el-select
        v-model="currentVersionIndex"
        class="version-select"
        size="small"
        teleported
        popper-class="version-select-popper"
        :placeholder="''"
        :disabled="loading || pendingPreview || versionCount < 2"
        @change="jumpToVersion"
      >
        <el-option
          v-for="(v, i) in versionOptions"
          :key="i"
          :label="`v${i + 1} · ${v.time || '—'}`"
          :value="i"
        />
      </el-select>
      <el-button
        link
        type="info"
        title="前进"
        :disabled="loading || pendingPreview || !canRedo"
        @click="handleRedo"
      >
        <el-icon><Right /></el-icon>
      </el-button>
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
      <MessageItem
        v-for="(msg, index) in visibleMessages"
        :key="index"
        :message="msg"
      />
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
      <div v-if="pendingPreview.pending_entities?.start_form_name" class="change-preview__pending">
        将创建占位表单「{{ pendingPreview.pending_entities.start_form_name }}」，字段需你稍后完善
      </div>
      <div v-if="pendingPreview.pending_entities?.category_name" class="change-preview__pending">
        将创建流程分类「{{ pendingPreview.pending_entities.category_name }}」
      </div>
      <ul v-if="pendingPreview.operations?.length" class="change-preview__operations">
        <li v-for="(operation, index) in pendingPreview.operations" :key="index">
          {{ operationLabel(operation) }}
        </li>
      </ul>
      <dl v-if="previewChanges.length" class="change-preview__fields">
        <div v-for="field in previewChanges" :key="field.key">
          <dt>{{ field.label }}</dt>
          <dd>{{ field.before }} → {{ field.after }}</dd>
        </div>
      </dl>
      <div class="change-preview__actions">
        <el-button @click="discardPreview">放弃</el-button>
        <el-button type="primary" @click="applyPreview">应用变更</el-button>
      </div>
    </div>

    <div v-if="pendingChoices.length" class="clarification-choices">
      <el-button
        v-for="(choice, index) in pendingChoices"
        :key="index"
        size="small"
        @click="selectChoice(choice)"
      >
        {{ choiceLabel(choice) }}
      </el-button>
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
      />
      <el-button
        class="send-button"
        type="primary"
        :icon="Promotion"
        @click="handleSend"
        :loading="loading"
        :disabled="!inputText.trim() || loading"
        aria-label="发送消息"
        title="发送"
      />
    </div>
  </AiFloatingWindow>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { designStream, clearDesignState, rollbackDesignState } from '@/api/workflow/design'
import { ChatDotRound, Plus, Back, Right, Promotion } from '@element-plus/icons-vue'
import AiFloatingWindow from '@/components/AiFloatingWindow/index.vue'
import MessageItem from '../assistant/MessageItem.vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { activeAiWindow } from '@/utils/aiWindow'
import { addForm, listForm } from '@/api/workflow/form'
import { addCategory, listCategory } from '@/api/workflow/category'

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
  },
  // 宿主提供：返回画布/设计器当前最新数据，用于每轮发送前刷新基线
  getCurrentBaseline: {
    type: Function,
    default: null
  }
})

const emit = defineEmits(['update:modelValue', 'fill', 'preview', 'discard', 'progress', 'designing'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const title = computed(() => {
  // 流程设计分两个窗口：基本信息（basic）与流程模型（design）
  if (props.designType === 'flow') {
    return props.mode === 'basic' ? '流程信息' : '流程模型'
  }
  return {
    category: '流程分类',
    form: '表单设计'
  }[props.designType] || 'AI 设计'
})

// 首次进入（无历史消息）时展示的固定欢迎语
const WELCOME_BY_TYPE = {
  category: '您好！我是 **AI 设计助手**，可以帮您创建和维护流程分类。\n\n' +
    '试着这样描述：\n' +
    '- 「创建『费用报销』分类，下设差旅、办公、招待三个子类」\n' +
    '- 「把『采购管理』下的子类合并，再新增『供应商管理』」\n\n' +
    '描述越具体，生成越准确。',
  // 流程基本信息：只生成名称、分类、描述
  'flow:basic': '您好！我是 **AI 流程基本信息助手**，可以根据描述生成流程的名称、分类和描述。\n\n' +
    '试着这样描述：\n' +
    '- 「员工请假审批流程，归到人事管理分类」\n' +
    '- 「采购申请流程，用于供应商采购审批」\n\n' +
    '生成后点「应用变更」填入基本信息表单。',
  // 流程模型：生成 BPMN 节点与连线
  flow: '您好！我是 **AI 流程模型设计助手**，可以把业务需求转成可运行的 BPMN 流程图。\n\n' +
    '试着这样描述：\n' +
    '- 「请假审批：员工提交申请，主管审批通过后归档」\n' +
    '- 「采购申请需要会签和驳回修改」\n\n' +
    '也可以让我在现有流程上做局部调整。',
  form: '您好！我是 **AI 表单设计助手**，可以根据描述生成 v-form-designer 表单。\n\n' +
    '试着这样描述：\n' +
    '- 「差旅报销单：申请人、出差事由、金额、附件」\n' +
    '- 「在表单里加上字段校验和联动」'
}

function ensureGreeting() {
  if (messages.value.length) return
  const key = props.designType === 'flow' && props.mode === 'basic'
    ? 'flow:basic'
    : props.designType
  const text = WELCOME_BY_TYPE[key] || WELCOME_BY_TYPE.category
  // 欢迎语是纯前端展示，不在后端 checkpoint 里，标记 local 以便算后端历史条数
  messages.value.push({ role: 'assistant', content: text, local: true })
}

const inputText = ref('')
const messages = ref([])
// 版本导航时只改显示范围，不截断 messages —— 这样切回新版本能恢复历史。
// null 表示显示全部（停在最新版本）；数字表示只显示前 N 条。
const displayLimit = ref(null)
const visibleMessages = computed(() =>
  displayLimit.value == null ? messages.value : messages.value.slice(0, displayLimit.value)
)
// 后端 checkpoint 的逻辑消息条数（由 done 事件回传）。前端条数与后端不一致
// （后端会因校验重试追加消息），版本指针必须用后端自己的计数才准确。
const lastBackendCount = ref(null)
const loading = ref(false)
const progressText = ref('')
const pendingPreview = ref(null)
const pendingChoices = ref([])
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

// 新建对象无业务标识时生成临时会话 id，保证不同对象会话/版本历史不串扰
const localSessionId = ref(
  props.formData?.code || 's_' + Date.now().toString(36) + Math.random().toString(36).slice(2, 8)
)

// 流程标识：优先用 formData 业务标识，否则 sessionId，否则临时 id，否则 'new'
const flowKey = computed(() => {
  const fd = props.formData || {}
  return fd.modelId || fd.modelKey || fd.formId || props.sessionId || localSessionId.value
})

// 存储命名空间：必须区分 mode，否则基本信息（basic）与流程模型（design）窗口
// 会共用同一份会话消息与版本历史，互相污染
const storageKey = computed(() => {
  return `ai_design_${props.designType}_${props.mode}_${flowKey.value}`
})

// 版本历史：每次"应用变更"存一个版本；导航（回退/前进/下拉）只移动当前指针，不删除版本
const VERSION_LIMIT = 20
// sessionStorage 不是响应式：版本数必须镜像到 ref，否则按钮状态会永久缓存
const versionCount = ref(0)
// 当前所在版本索引；null 表示还没有任何版本
const currentVersionIndex = ref(null)
const versionKey = computed(() => {
  return `ai_design_versions_${props.designType}_${props.mode}_${flowKey.value}`
})

function getVersions() {
  const saved = sessionStorage.getItem(versionKey.value)
  let list = []
  try {
    list = saved ? JSON.parse(saved) : []
  } catch (e) {
    return []
  }
  // 兼容旧格式（纯 formData 数组）→ 统一为带元数据的版本对象
  return list.map((item) =>
    item && typeof item === 'object' && 'data' in item
      ? item
      : { data: item, time: '' }
  )
}

// 下拉框选项（依赖 versionCount 触发重算，sessionStorage 本身非响应式）
const versionOptions = computed(() => {
  versionCount.value
  return getVersions()
})

function syncVersionCount() {
  const versions = getVersions()
  versionCount.value = versions.length
  if (!versions.length) {
    currentVersionIndex.value = null
  } else if (currentVersionIndex.value == null || currentVersionIndex.value >= versions.length) {
    currentVersionIndex.value = versions.length - 1
  }
}

function saveVersion(formData) {
  const versions = getVersions()
  // 从当前版本继续：丢弃当前版本之后的
  if (currentVersionIndex.value != null && currentVersionIndex.value < versions.length - 1) {
    versions.splice(currentVersionIndex.value + 1)
  }
  versions.push({
    data: cloneData(formData),
    time: new Date().toLocaleTimeString('zh-CN', { hour12: false }),
    messageCount: messages.value.length,
    // 后端 checkpoint 的逻辑条数，作为回退/分叉时的历史指针
    backendCount: lastBackendCount.value
  })
  if (versions.length > VERSION_LIMIT) versions.splice(0, versions.length - VERSION_LIMIT)
  sessionStorage.setItem(versionKey.value, JSON.stringify(versions))
  currentVersionIndex.value = versions.length - 1
  syncVersionCount()
}

const canRollback = computed(() => currentVersionIndex.value > 0)
const canRedo = computed(() =>
  currentVersionIndex.value != null && currentVersionIndex.value < versionCount.value - 1
)

function jumpToVersion(index) {
  const versions = getVersions()
  if (index < 0 || index >= versions.length) return
  const version = versions[index]
  currentVersionIndex.value = index
  currentFormData.value = cloneData(version.data)
  // 只改显示范围，不截断 messages —— 切回较新版本时历史能恢复
  displayLimit.value =
    typeof version.messageCount === 'number' && version.messageCount < messages.value.length
      ? version.messageCount
      : null
  saveSession()
  emit('fill', currentFormData.value)
  ElMessage.info(`已跳转到版本 ${index + 1}`)
}

function handleRollback(target) {
  const index = target === 'start' ? 0 : currentVersionIndex.value - 1
  if (index < 0 || index === currentVersionIndex.value) {
    ElMessage.info('没有可回退的版本')
    return
  }
  jumpToVersion(index)
}

function handleRedo() {
  const index = currentVersionIndex.value + 1
  if (currentVersionIndex.value == null || index >= versionCount.value) {
    ElMessage.info('没有可前进的版本')
    return
  }
  jumpToVersion(index)
}

function saveSession() {
  sessionStorage.setItem(storageKey.value, JSON.stringify({
    messages: messages.value,
    currentFormData: currentFormData.value
  }))
}

function restoreSession() {
  // 消息从草稿恢复；设计基线始终以外部传入的 props.formData 为准
  currentFormData.value = cloneData(props.formData)
  syncVersionCount()
  const saved = sessionStorage.getItem(storageKey.value)
  if (saved) {
    try {
      const state = JSON.parse(saved)
      if (Array.isArray(state.messages)) messages.value = state.messages
    } catch (e) {
      console.error('恢复聊天记录失败:', e)
    }
  }
  ensureGreeting()
  scrollToBottom()
}

onMounted(restoreSession)

// 全局助手打开时关闭设计窗口
watch(activeAiWindow, (kind) => {
  if (kind === 'assistant') emit('update:modelValue', false)
})

watch(visible, (val) => {
  if (val) {
    restoreSession()
    activeAiWindow.value = 'design'
  } else {
    if (activeAiWindow.value === 'design') activeAiWindow.value = null
    cancelCurrentRequest()
    discardPreview()
    saveSession()
  }
})

function cancelCurrentRequest() {
  const controller = requestController.value
  if (!controller) return
  requestController.value = null
  controller.abort()
  allowFullReplace.value = false
  loading.value = false
  progressText.value = ''
  emit('designing', false)
}

async function refreshBaseline() {
  // 每轮发送前从宿主取最新画布/数据：AI 增量必须基于用户当前的最新修改，
  // 而不是打开浮窗那一刻的冻结快照。
  if (typeof props.getCurrentBaseline !== 'function') return
  try {
    const fresh = await props.getCurrentBaseline()
    if (fresh && Object.keys(fresh).length > 0) {
      currentFormData.value = { ...currentFormData.value, ...fresh }
    }
  } catch (e) {
    console.error('获取最新设计基线失败:', e)
  }
}

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
  pendingChoices.value = []

  // 停在旧版本时继续生成 = 分叉：截断当前显示范围之后的历史，再追加本轮输入
  let forkBackendCount = null
  if (displayLimit.value != null && displayLimit.value < messages.value.length) {
    const versions = getVersions()
    forkBackendCount = versions[currentVersionIndex.value]?.backendCount ?? null
    messages.value = messages.value.slice(0, displayLimit.value)
  }
  displayLimit.value = null

  messages.value.push({ role: 'user', content: userInput })
  scrollToBottom()

  loading.value = true
  progressText.value = ''
  emit('designing', true)
  const controller = new AbortController()
  requestController.value = controller
  let wasAborted = false

  try {
    await refreshBaseline()
    await designStream(props.designType, {
      user_input: userInput,
      current_form_data: currentFormData.value,
      mode: props.mode,
      thread_id: flowKey.value,
      allow_full_replace: allowFullReplace.value,
      history_count: forkBackendCount
    }, (event) => {
      if (requestController.value !== controller) return
      if (event.type === 'progress') {
        progressText.value = event.message
        emit('progress', event.message)
      } else if (event.type === 'done') {
        const data = event
        if (typeof data.message_count === 'number') {
          lastBackendCount.value = data.message_count
        }
        pendingChoices.value = data.status === 'needs_input' && Array.isArray(data.choices)
          ? data.choices
          : []
        // 回退指令：恢复到目标版本（后端判别返回 rollback）
        if (data.kind === 'rollback') {
          const target = data.target
          const index = target === 'start' ? 0 : currentVersionIndex.value - 1
          if (index >= 0 && index !== currentVersionIndex.value) {
            jumpToVersion(index)
            messages.value.push({ role: 'assistant', content: data.message || '已回退到指定版本', local: true })
          } else {
            messages.value.push({ role: 'assistant', content: '没有可回退的版本', local: true })
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
        messages.value.push({ role: 'assistant', content: event.message || '服务暂时不可用，请稍后重试。', local: true })
        scrollToBottom()
      }
    }, controller.signal)
  } catch (error) {
    if (error?.name === 'AbortError') {
      wasAborted = true
      return
    }
    console.error('AI 设计失败:', error)
    messages.value.push({ role: 'assistant', content: '抱歉，服务暂时不可用，请稍后重试。', local: true })
    scrollToBottom()
  } finally {
    if (requestController.value === controller) {
      requestController.value = null
      allowFullReplace.value = false
      loading.value = false
      progressText.value = ''
      emit('designing', false)
      if (!wasAborted) saveSession()
    }
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

onBeforeUnmount(cancelCurrentRequest)

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

const previewChanges = computed(() => {
  if (!pendingPreview.value) return []
  const fields = props.designType === 'category'
    ? [
        ['category_name', 'categoryName', '分类名称'],
        ['code', 'code', '分类编码'],
        ['remark', 'remark', '备注']
      ]
    : props.designType === 'flow' && props.mode === 'basic'
      ? [
          ['flow_name', 'modelName', '流程名称'],
          ['code', 'category', '流程分类'],
          ['description', 'description', '流程描述'],
          ['flow_key', 'modelKey', '流程标识']
        ]
      : []
  return fields.map(([key, oldKey, label]) => ({
    key,
    label,
    before: formatPreviewValue(previewBaseline.value?.[oldKey] ?? previewBaseline.value?.[key]),
    after: formatPreviewValue(pendingPreview.value.form_data?.[key])
  })).filter((field) => field.before !== field.after)
})

function formatPreviewValue(value) {
  return value === undefined || value === null || value === '' ? '未设置' : String(value)
}

function choiceLabel(choice) {
  if (typeof choice !== 'object' || choice === null) return String(choice)
  const label = choice.label || choice.name || choice.value || choice.code || choice.id
  return label == null ? JSON.stringify(choice) : String(label)
}

function selectChoice(choice) {
  inputText.value = choiceLabel(choice)
  handleSend()
}

function cloneData(value) {
  return JSON.parse(JSON.stringify(value || {}))
}

// 待创建的开始表单占位 key（与后端 design_models.PENDING_FORM_KEY 保持一致）
const PENDING_FORM_KEY = 'key_ai_pending_form'

// 占位表单骨架：保证表单设计器能正常打开
const EMPTY_FORM_CONTENT = JSON.stringify({ widgetList: [], formConfig: {} })

/** 按名称取表单，不存在则创建空占位（幂等，避免重复创建） */
async function ensurePlaceholderForm(formName) {
  const findByName = async () => {
    const res = await listForm({ formName })
    const rows = res?.rows || res?.data || []
    return rows.find((item) => item.formName === formName)
  }
  const existing = await findByName()
  if (existing) return existing
  await addForm({
    formName,
    content: EMPTY_FORM_CONTENT,
    remark: 'AI 流程设计自动创建的占位表单，待完善字段'
  })
  // 新增接口只回 {code,msg}，不回实体，必须回查拿 formId
  const created = await findByName()
  if (!created?.formId) throw new Error(`占位表单「${formName}」创建后未能查到`)
  return created
}

/** 按名称取分类，不存在则创建（幂等）。
 *  新增接口不回实体，所以直接沿用提交时的 code —— 不能读响应的 code（那是状态码 200）。 */
async function ensureCategory(categoryName, code) {
  const res = await listCategory({ categoryName })
  const rows = res?.rows || res?.data || []
  const existing = rows.find((item) => item.categoryName === categoryName)
  if (existing) return existing
  const created = await addCategory({
    categoryName,
    code,
    remark: 'AI 流程设计自动创建'
  })
  if (created?.code !== 200) {
    throw new Error(created?.msg || `分类「${categoryName}」创建失败`)
  }
  return { categoryName, code }
}

/** 应用变更前先把缺失的依赖实体建出来，并把引用写回 form_data。
 *  后端对业务库只读，实体创建统一在这里（用户点「应用变更」）完成。 */
async function materializePendingEntities(formData, pending) {
  const result = cloneData(formData)
  if (pending?.start_form_name) {
    const form = await ensurePlaceholderForm(pending.start_form_name)
    if (form?.formId) {
      const realKey = `key_${form.formId}`
      const start = (result.nodes || []).find(
        (node) => String(node.type || '').toUpperCase() === 'START_EVENT'
      )
      if (start) start.form_key = realKey
      // bpmn_xml 才是设计器的输入，占位 key 必须一并替换
      if (typeof result.bpmn_xml === 'string' && result.bpmn_xml.includes(PENDING_FORM_KEY)) {
        result.bpmn_xml = result.bpmn_xml.split(PENDING_FORM_KEY).join(realKey)
      }
    }
  }
  if (pending?.category_name) {
    const category = await ensureCategory(pending.category_name, result.code)
    if (category?.code) result.code = category.code
  }
  return result
}

async function applyPreview() {
  if (!pendingPreview.value) return
  // 生成期间画布若被手动修改过，应用会整份覆盖这些改动——先提醒用户
  if (typeof props.getCurrentBaseline === 'function' && previewBaseline.value?.bpmnXml) {
    try {
      const fresh = await props.getCurrentBaseline()
      if (fresh?.bpmnXml && fresh.bpmnXml !== previewBaseline.value.bpmnXml) {
        await ElMessageBox.confirm(
          '画布在 AI 生成期间被手动修改过，应用变更将覆盖这些改动，继续吗？',
          '注意',
          { type: 'warning', confirmButtonText: '继续应用', cancelButtonText: '取消' }
        )
      }
    } catch (e) {
      if (e === 'cancel' || e === 'close') return
      console.error('检查画布最新状态失败:', e)
    }
  }
  // 从旧版本继续生成：应用将丢弃当前版本之后的版本，先确认
  const versions = getVersions()
  if (currentVersionIndex.value != null && currentVersionIndex.value < versions.length - 1) {
    const dropped = versions.length - 1 - currentVersionIndex.value
    try {
      await ElMessageBox.confirm(
        `将从版本 ${currentVersionIndex.value + 1} 继续，后续 ${dropped} 个版本将被丢弃，继续吗？`,
        '提示',
        { type: 'warning', confirmButtonText: '继续', cancelButtonText: '取消' }
      )
    } catch {
      return
    }
  }
  // 缺失的表单/分类在这里创建（后端只读），失败则中止本次应用、保留预览让用户重试
  let formData = pendingPreview.value.form_data
  const pending = pendingPreview.value.pending_entities
  if (pending) {
    try {
      formData = await materializePendingEntities(formData, pending)
      if (pending.start_form_name) {
        ElMessage.warning(`已创建占位表单「${pending.start_form_name}」，请到「表单设计」完善字段`)
      }
    } catch (e) {
      console.error('创建依赖实体失败:', e)
      ElMessage.error('创建表单/分类失败，请稍后重试')
      return
    }
  }
  currentFormData.value = cloneData(formData)
  emit('fill', formData)
  saveVersion(formData)
  // 版本覆盖：裁剪后端 checkpoint 到本轮的分支长度（丢弃回退掉的旧分支）
  if (lastBackendCount.value != null) {
    rollbackDesignState(props.designType, {
      message_count: lastBackendCount.value,
      thread_id: flowKey.value,
      mode: props.mode
    }).catch((e) => console.warn('回退会话历史失败:', e))
  }
  pendingPreview.value = null
  previewBaseline.value = null
}

function discardPreview() {
  if (!pendingPreview.value) return
  if (previewBaseline.value) currentFormData.value = cloneData(previewBaseline.value)
  pendingPreview.value = null
  previewBaseline.value = null
  emit('discard')
}


function clearMessages() {
  cancelCurrentRequest()
  discardPreview()
  messages.value = []
  displayLimit.value = null
  lastBackendCount.value = null
  pendingChoices.value = []
  syncVersionCount()
  // 保留 props.formData 中的基本信息（modelId, modelName, modelKey 等）
  // 只清空 AI 生成的数据
  currentFormData.value = { ...props.formData }
  sessionStorage.removeItem(storageKey.value)
  sessionStorage.removeItem(versionKey.value)
  ensureGreeting()
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
.version-select {
  width: 128px;
  margin: 0 4px;

  :deep(.el-select__wrapper) {
    background: rgba(255, 255, 255, 0.15);
    box-shadow: none;
    min-height: 26px;
  }
  :deep(.el-select__selection) {
    justify-content: center;
    flex-wrap: nowrap;
  }
  :deep(.el-select__placeholder) {
    color: transparent;
    flex: 1;
    justify-content: center;
  }
  :deep(.el-select__selected-item) {
    color: #fff;
    flex: 1;
    justify-content: center;
  }
  :deep(.el-select__caret) {
    color: #fff;
  }
}

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
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  border-top: 1px solid #ebeef5;

  .el-input {
    flex: 1;

    :deep(.el-input__wrapper) {
      min-height: 40px;
      padding: 0 14px;
      background: #f7f8fa;
      border-radius: 12px;
      box-shadow: inset 0 0 0 1px #e4e7ed;
      transition: box-shadow 0.2s, background 0.2s;

      &.is-focus {
        background: #fff;
        box-shadow: 0 0 0 3px rgba(64, 158, 255, 0.12), inset 0 0 0 1px #409eff;
      }
    }
  }

  .send-button {
    width: 40px;
    height: 40px;
    padding: 0;
    border: 0;
    border-radius: 12px;
    background: #409eff;
    font-size: 16px;
    transition: background 0.2s, box-shadow 0.2s;

    &:hover:not(:disabled) {
      background: #337ecc;
      box-shadow: 0 4px 12px rgba(64, 158, 255, 0.28);
    }
  }
}

.change-preview {
  padding: 12px 16px;
  border-top: 1px solid #dcdfe6;
  background: #f0f9eb;
}

.change-preview__title { font-weight: 600; color: #303133; }
.change-preview__summary { margin-top: 4px; font-size: 12px; color: #606266; }
.change-preview__pending { margin-top: 4px; font-size: 12px; color: #b88230; }
.change-preview__operations { margin: 8px 0; max-height: 96px; overflow: auto; font-size: 12px; }
.change-preview__fields { margin: 8px 0; font-size: 12px; }
.change-preview__fields div { display: grid; grid-template-columns: 88px 1fr; gap: 8px; }
.change-preview__fields dt { color: #606266; }
.change-preview__fields dd { margin: 0; color: #303133; overflow-wrap: anywhere; }
.change-preview__actions { display: flex; justify-content: flex-end; gap: 8px; }
.clarification-choices { display: flex; flex-wrap: wrap; justify-content: center; gap: 8px; padding: 10px 16px; background: #fff; }
</style>

<style>
/* 版本下拉框弹出层 teleport 到 body，需高于浮窗 z-index（3100+） */
.version-select-popper {
  z-index: 3300 !important;
}
</style>
