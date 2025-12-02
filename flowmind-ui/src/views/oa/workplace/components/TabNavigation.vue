<template>
  <div class="space-y-1">
    <button 
      v-for="tab in tabs" 
      :key="tab.key"
      @click="$emit('tab-change', tab.key)"
      class="w-full flex items-center justify-between px-3 py-2.5 text-sm font-medium rounded-lg transition-all"
      :class="currentTab === tab.key ? 'bg-blue-50 text-blue-600' : 'text-gray-600 hover:bg-gray-50'"
    >
      <div class="flex items-center gap-3">
        <el-icon><component :is="getIconName(tab.key)" /></el-icon>
        <span>{{ tab.name }}</span>
      </div>
      <span v-if="tab.count > 0" class="px-1.5 py-0.5 text-[10px] bg-red-100 text-red-600 rounded-full">
        {{ tab.count > 99 ? '99+' : tab.count }}
      </span>
    </button>
  </div>
</template>

<script setup>
import { Grid, Document } from '@element-plus/icons-vue'

defineProps({
  tabs: {
    type: Array,
    required: true
  },
  currentTab: {
    type: String,
    required: true
  }
})

defineEmits(['tab-change'])

// 获取图标名称
const getIconName = (tab) => {
  const map = { 
    apps: 'Grid', 
    drafts: 'Document'
  }
  return map[tab]
}
</script>