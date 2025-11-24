<template>
  <div class="bg-white rounded-2xl shadow-sm border border-gray-100 min-h-[80vh] flex">
    <!-- 左侧竖向导航栏 -->
    <div class="w-56 border-r border-gray-100 p-4">
      <div class="space-y-1">
        <button 
          v-for="tab in tabs" 
          :key="tab.key"
          @click="currentTab = tab.key"
          class="w-full flex items-center justify-between px-3 py-2.5 text-sm font-medium rounded-lg transition-all"
          :class="currentTab === tab.key ? 'bg-blue-50 text-blue-600' : 'text-gray-600 hover:bg-gray-50'"
        >
          <div class="flex items-center gap-3">
            <el-icon><component :is="getIconName(tab.key)" /></el-icon>
            <span>{{ tab.name }}</span>
          </div>
          <span v-if="tab.count > 0" class="px-1.5 py-0.5 text-[10px] bg-red-100 text-red-600 rounded-full">{{ tab.count }}</span>
        </button>
      </div>
    </div>

    <!-- 右侧内容区域 -->
    <div class="flex-1 flex flex-col p-6">
      <!-- 待办事项 -->
      <div v-if="currentTab === 'todo'" class="h-full">
        <TodoList />
      </div>

      <!-- 已办事项 -->
      <div v-if="currentTab === 'finished'" class="h-full">
        <FinishedList />
      </div>

      <!-- 我的流程 -->
      <div v-if="currentTab === 'own'" class="h-full">
        <OwnList />
      </div>

      <!-- 抄送 -->
      <div v-if="currentTab === 'copy'" class="h-full">

        <CopyList />
      </div>

      <!-- 待签收 -->
      <div v-if="currentTab === 'claim'" class="h-full">
        <ClaimList />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { 
  Bell, 
  Check, 
  Document, 
  Message, 
  User 
} from '@element-plus/icons-vue'

// 导入各个组件
import TodoList from './todo.vue'
import FinishedList from './finished.vue'
import OwnList from './own.vue'
import CopyList from './copy.vue'
import ClaimList from './claim.vue'

// 导入API
import {
  getTodoCount,
  getFinishedCount,
  getOwnCount,
  getCopyCount,
  getClaimCount
} from '@/api/workflow/work/process'

const currentTab = ref('todo')

// 定义 Tab 配置
const tabs = ref([
  { key: 'todo', name: '待办事项', count: 0 },
  { key: 'finished', name: '已办事项', count: 0 },
  { key: 'own', name: '我的流程', count: 0 },
  { key: 'copy', name: '抄送', count: 0 },
  { key: 'claim', name: '待签收', count: 0 }
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

// 获取各个tab的数量
const getTabsCount = async () => {
  try {
    // 获取待办事项数量
    const todoRes = await getTodoCount()
    if (todoRes.code === 200) {
      tabs.value[0].count = todoRes.data || 0
    }
    
    // 获取已办事项数量
    const finishedRes = await getFinishedCount()
    if (finishedRes.code === 200) {
      tabs.value[1].count = finishedRes.data || 0
    }
    
    // 获取我的流程数量
    const ownRes = await getOwnCount()
    if (ownRes.code === 200) {
      tabs.value[2].count = ownRes.data || 0
    }
    
    // 获取抄送数量
    const copyRes = await getCopyCount()
    if (copyRes.code === 200) {
      tabs.value[3].count = copyRes.data || 0
    }
    
    // 获取待签收数量
    const claimRes = await getClaimCount()
    if (claimRes.code === 200) {
      tabs.value[4].count = claimRes.data || 0
    }
  } catch (error) {
    console.error('获取tab数量失败:', error)
  }
}

onMounted(() => {
  getTabsCount()
})
</script>

<style lang="scss" scoped>
// 左侧导航栏样式
:deep(.el-icon) {
  font-size: 16px;
}
</style>