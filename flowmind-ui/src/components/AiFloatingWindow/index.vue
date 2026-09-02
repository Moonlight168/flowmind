<template>
  <teleport to="body">
    <div
      v-if="modelValue"
      ref="rootEl"
      class="fm-float-window"
      :style="windowStyle"
    >
      <!-- 头部：拖拽区域 -->
      <div class="fm-fw-header" @mousedown.prevent="onHeaderMouseDown">
        <div class="fm-fw-title">
          <el-icon v-if="icon" :size="20" class="fm-fw-title-icon"><component :is="icon" /></el-icon>
          <slot name="title">{{ title }}</slot>
        </div>
        <div class="fm-fw-actions" @mousedown.stop>
          <slot name="actions" />
          <el-button v-if="closable !== false" link type="info" class="fm-fw-close" title="关闭" @click="close">
            <el-icon><Close /></el-icon>
          </el-button>
        </div>
      </div>

      <!-- 内容区 -->
      <div class="fm-fw-body">
        <slot />
      </div>

      <!-- 右下角缩放手柄 -->
      <div class="fm-fw-resize fm-fw-resize-se" @mousedown.prevent.stop="onResizeMouseDown">
        <el-icon :size="12"><MoreFilled /></el-icon>
      </div>
    </div>
  </teleport>
</template>

<script setup>
import { ref, reactive, computed, watch, onUnmounted } from 'vue'
import { Close, MoreFilled } from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  title: { type: String, default: '' },
  icon: { type: [Object, String], default: null },
  width: { type: Number, default: 420 },
  height: { type: Number, default: 600 },
  minWidth: { type: Number, default: 340 },
  minHeight: { type: Number, default: 460 },
  // 默认出现位置（相对视口右下角的右边距 / 顶部偏移）
  right: { type: Number, default: 24 },
  top: { type: Number, default: 96 },
  closable: { type: Boolean, default: true }
})

const emit = defineEmits(['update:modelValue'])

const rootEl = ref(null)
const pos = reactive({ x: 0, y: 0, ready: false })
const size = reactive({ w: props.width, h: props.height })

const windowStyle = computed(() => ({
  left: pos.x + 'px',
  top: pos.y + 'px',
  width: size.w + 'px',
  height: size.h + 'px'
}))

function close() {
  emit('update:modelValue', false)
}

function ensureInitialized() {
  if (pos.ready) return
  pos.x = window.innerWidth - size.w - props.right
  pos.y = props.top
  pos.ready = true
}

watch(
  () => props.modelValue,
  (val) => {
    if (val) ensureInitialized()
  },
  { immediate: true }
)

// 供父级动态修改默认尺寸（如不同场景换默认大小）
watch(
  () => [props.width, props.height],
  ([w, h]) => {
    if (!props.modelValue) {
      size.w = w
      size.h = h
    }
  }
)

// ---------- 拖拽 ----------
const dragState = ref(null)

function onHeaderMouseDown(e) {
  if (e.button !== 0) return
  dragState.value = {
    startX: e.clientX,
    startY: e.clientY,
    originX: pos.x,
    originY: pos.y
  }
  document.addEventListener('mousemove', onMove)
  document.addEventListener('mouseup', onUp)
}

function onMove(e) {
  const state = dragState.value
  if (!state) return
  const maxX = window.innerWidth - size.w
  const maxY = window.innerHeight - 48
  pos.x = Math.min(Math.max(0, state.originX + e.clientX - state.startX), maxX)
  pos.y = Math.min(Math.max(0, state.originY + e.clientY - state.startY), maxY)
}

function onUp() {
  dragState.value = null
  document.removeEventListener('mousemove', onMove)
  document.removeEventListener('mouseup', onUp)
}

// ---------- 缩放 ----------
const resizeState = ref(null)

function onResizeMouseDown(e) {
  if (e.button !== 0) return
  resizeState.value = {
    startX: e.clientX,
    startY: e.clientY,
    width: size.w,
    height: size.h
  }
  document.addEventListener('mousemove', onResizeMove)
  document.addEventListener('mouseup', onResizeUp)
}

function onResizeMove(e) {
  const state = resizeState.value
  if (!state) return
  size.w = Math.min(
    Math.max(props.minWidth, state.width + (e.clientX - state.startX)),
    window.innerWidth - pos.x
  )
  size.h = Math.min(
    Math.max(props.minHeight, state.height + (e.clientY - state.startY)),
    window.innerHeight - pos.y - 8
  )
}

function onResizeUp() {
  resizeState.value = null
  document.removeEventListener('mousemove', onResizeMove)
  document.removeEventListener('mouseup', onResizeUp)
}

onUnmounted(() => {
  document.removeEventListener('mousemove', onMove)
  document.removeEventListener('mouseup', onUp)
  document.removeEventListener('mousemove', onResizeMove)
  document.removeEventListener('mouseup', onResizeUp)
})
</script>

<style lang="scss" scoped>
.fm-float-window {
  position: fixed;
  z-index: 3100;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 12px 40px rgba(15, 23, 42, 0.18), 0 0 0 1px rgba(15, 23, 42, 0.05);
}

.fm-fw-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 10px 10px 16px;
  color: #fff;
  cursor: move;
  user-select: none;
  background-image: linear-gradient(90deg, #3b82f6, #8b5cf6);
}

.fm-fw-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 15px;
  font-weight: 600;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.fm-fw-actions {
  display: flex;
  align-items: center;
  gap: 2px;
  flex-shrink: 0;

  :deep(.el-button) {
    color: rgba(255, 255, 255, 0.92);

    &:hover {
      color: #fff;
      background: rgba(255, 255, 255, 0.14);
    }
  }
}

.fm-fw-body {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.fm-fw-resize {
  position: absolute;
  right: 2px;
  bottom: 2px;
  width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #b6c2d1;
  cursor: nwse-resize;
  z-index: 1;
}
</style>
