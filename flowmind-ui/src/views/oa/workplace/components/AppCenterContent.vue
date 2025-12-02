<template>
  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
    <div 
      v-for="process in processes" 
      :key="process.definitionId"
      :class="[
        'group bg-white rounded-xl border transition-all duration-200 overflow-hidden',
        process.suspended 
          ? 'border-gray-200 cursor-not-allowed opacity-60' 
          : 'border-gray-200 hover:border-blue-300 hover:shadow-lg cursor-pointer'
      ]"
      @click="!process.suspended && handleProcessClick(process)"
    >
      <div class="p-4">
        <div class="flex items-center justify-between mb-2">
          <h3 class="font-medium text-gray-900">{{ process.processName || '未命名流程' }}</h3>
          <el-button 
            :type="process.suspended ? 'info' : 'primary'" 
            size="small"
            :disabled="process.suspended"
            @click.stop="!process.suspended && handleProcessClick(process)"
          >
            {{ process.suspended ? '已挂起' : '发起流程' }}
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Timer } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'

defineProps({
  processes: {
    type: Array,
    required: true
  }
})

const router = useRouter()

// 处理流程点击
const handleProcessClick = (process) => {
  router.push({
    path: '/oa/workplace/start/'+process.deploymentId,
    query: {
      definitionId: process.definitionId
    }
  })
}
</script>