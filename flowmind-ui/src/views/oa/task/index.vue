<template>
  <div class="bg-white rounded-2xl shadow-sm border border-gray-100 min-h-[80vh] flex w-full max-w-full overflow-hidden">
    <!-- 左侧竖向导航栏 -->
    <div class="w-56 md:w-56 sm:w-48 border-r border-gray-100 p-4 flex-shrink-0">
      <div class="space-y-1">
        <button 
          v-for="tab in tabs" 
          :key="tab.key"
          @click="navigateToTab(tab.key)"
          class="w-full flex items-center justify-between px-3 py-2.5 text-sm font-medium rounded-lg transition-all"
          :class="route.path.endsWith(tab.key) ? 'bg-blue-50 text-blue-600' : 'text-gray-600 hover:bg-gray-50'"
        >
          <span class="flex items-center gap-3">
            <el-icon><component :is="getIconName(tab.key)" /></el-icon>
            <span class="w-full text-ellipsis overflow-hidden whitespace-nowrap">{{ tab.name }}</span>
          </span>
          <OaCountBadge :count="tab.key === 'todo' ? counts.todo : tab.key === 'claim' ? counts.claim : null" :label="tab.name" class="ml-2" />
        </button>
      </div>
    </div>

    <!-- 右侧内容区域 -->
    <div class="flex-1 flex flex-col p-4 sm:p-6 min-w-0 overflow-hidden">
      <router-view />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { 
  Bell, 
  Check, 
  Document, 
  Message, 
  User 
} from '@element-plus/icons-vue'

// 导入API
import useOaCounts from '@/store/modules/oaCounts'
import OaCountBadge from '@/components/OaCountBadge/index.vue'
const counts = useOaCounts()

const router = useRouter()
const route = useRoute()

// 定义 Tab 配置
const tabs = ref([
  { key: 'own', name: '我的流程' },
  { key: 'todo', name: '待办事项' },
  { key: 'claim', name: '待签收' },
  { key: 'finished', name: '已办事项' },
  { key: 'copy', name: '抄送' },
])

// 获取图标名称
const getIconName = (tab) => {
  const map = { 
    todo: Bell,
    finished: Check,
    own: Document,
    copy: Message,
    claim: User
  }
  return map[tab]
}

// 导航到指定tab
const navigateToTab = (tabKey) => {
  router.push(`/oa/task/${tabKey}`)
}

// 初始化时，如果当前路由不是任何tab，则导航到待办事项
onMounted(() => {
  
  // 检查当前路由是否是任何tab
  const isTabRoute = tabs.value.some(tab => route.path.endsWith(tab.key))
  if (!isTabRoute) {
    router.replace('/oa/task/todo')
  }
})
</script>

<style lang="scss" scoped>
// 左侧导航栏样式
:deep(.el-icon) {
  font-size: 16px;
}
:deep(.el-table th .cell), :deep(.el-table td .cell) {
  white-space: nowrap;
}
</style>
