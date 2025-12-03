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
          <span v-if="tab.count > 0" class="ml-2 px-1.5 py-0.5 text-[10px] bg-red-100 text-red-600 rounded-full">{{ tab.count }}</span>
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
import {
  getTaskCounts
} from '@/api/workflow/work/process'

const router = useRouter()
const route = useRoute()

// 定义 Tab 配置
const tabs = ref([
  { key: 'own', name: '我的流程', count: 0 },
  { key: 'todo', name: '待办事项', count: 0 },
  { key: 'claim', name: '待签收', count: 0 },
  { key: 'finished', name: '已办事项', count: 0 },
  { key: 'copy', name: '抄送', count: 0 },
])

// 获取图标名称
const getIconName = (tab) => {
  const map = { 
    todo: 'Bell', 
    finished: 'Check', 
    own: 'Document', 
    copy: 'Message', 
    claim: 'User' 
  }
  return map[tab]
}

// 导航到指定tab
const navigateToTab = (tabKey) => {
  router.push(`/oa/task/${tabKey}`)
}

// 获取各tab数量
const getTabsCount = async () => {
  const res = await getTaskCounts()
  if (res.code === 200) {
    // 确保tabs数组与后端返回字段正确对应
    tabs.value[0].count = res.data.ownCount    // 我的流程
    tabs.value[1].count = res.data.todoCount   // 待办事项
    tabs.value[2].count = res.data.claimCount  // 待签收
    //tabs.value[3].count = res.data.finishedCount // 已办事项 不显示
    tabs.value[3].count = 0
    tabs.value[4].count = res.data.copyCount   // 抄送
  }
}

// 初始化时，如果当前路由不是任何tab，则导航到待办事项
onMounted(() => {
  getTabsCount()
  
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
</style>