<template>
  <!-- 统一 AI 对话窗口：不传 designType 时即全局助手；传入 designType 时为该类型的设计浮窗 -->
  <AiAssistant v-if="!isDesign" />
  <AiDesignDialog
    v-else
    ref="designRef"
    :model-value="modelValue"
    :design-type="designType"
    :form-data="formData"
    :mode="mode"
    :session-id="sessionId"
    :get-current-baseline="getCurrentBaseline"
    @update:model-value="emit('update:modelValue', $event)"
    @fill="emit('fill', $event)"
    @preview="emit('preview', $event)"
    @discard="emit('discard')"
    @progress="emit('progress', $event)"
    @designing="emit('designing', $event)"
  />
</template>

<script setup>
import { ref, computed } from 'vue'
import AiAssistant from './assistant/index.vue'
import AiDesignDialog from './design/index.vue'

const props = defineProps({
  // 设计场景由父级用 v-model 控制显隐；全局助手自己管理浮球与显隐，不需要传
  modelValue: { type: Boolean, default: false },
  // 传入 'category' | 'flow' | 'form' 即设计场景；不传则渲染全局助手
  designType: { type: String, default: null },
  formData: { type: Object, default: () => ({}) },
  mode: { type: String, default: 'design' },
  sessionId: { type: String, default: null },
  // 宿主提供：返回设计器当前最新数据。必须显式声明并往下传 ——
  // 之前靠属性透传落到子组件，模板多一个根节点就会静默失效
  getCurrentBaseline: { type: Function, default: null }
})

const emit = defineEmits(['update:modelValue', 'fill', 'preview', 'discard', 'progress', 'designing'])

const isDesign = computed(() => !!props.designType)
const designRef = ref(null)

// 暴露给父级（如切换记录时清空对话），与旧 AiDesignDialog API 保持一致
function clearMessages() {
  designRef.value?.clearMessages?.()
}

defineExpose({ clearMessages })
</script>
