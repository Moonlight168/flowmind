<template>
  <div class="bg-white rounded-2xl shadow-sm border border-gray-100 min-h-[80vh] flex flex-col">
    <div class="px-6 pt-4 border-b border-gray-100">
      <div class="flex space-x-6 overflow-x-auto no-scrollbar">
        <button 
          v-for="tab in tabs" 
          :key="tab.key"
          @click="currentTab = tab.key"
          class="pb-3 text-sm font-medium transition-all relative whitespace-nowrap"
          :class="currentTab === tab.key ? 'text-blue-600' : 'text-gray-500 hover:text-gray-700'"
        >
          {{ tab.name }}
          <span v-if="tab.count > 0" class="ml-1 px-1.5 py-0.5 text-[10px] bg-red-100 text-red-600 rounded-full">{{ tab.count }}</span>
          <span v-if="currentTab === tab.key" class="absolute bottom-0 left-0 w-full h-0.5 bg-blue-600 rounded-full"></span>
        </button>
      </div>
    </div>

    <div class="flex-1 p-2" v-loading="loading">
      <div v-if="taskList.length > 0">
        <div 
          v-for="task in taskList" 
          :key="task.taskId || task.procInsId"
          @click="handleProcess(task)"
          class="group flex items-center justify-between p-4 hover:bg-gray-50 rounded-xl cursor-pointer transition-colors border-b border-gray-50 last:border-0"
        >
          <div class="flex items-center gap-4">
            <div 
              class="w-10 h-10 rounded-full flex items-center justify-center transition-colors"
              :class="getIconStyle(currentTab)"
            >
              <el-icon><component :is="getIconName(currentTab)" /></el-icon>
            </div>
            
            <div>
              <div class="text-sm font-bold text-gray-800 mb-1">
                {{ task.procDefName || task.processDefinitionName || '未知流程' }} 
                <span class="font-normal text-gray-500 mx-1">-</span> 
                {{ task.taskName || task.activityName || '详情' }}
              </div>
              <div class="flex items-center text-xs text-gray-400 gap-3">
                <span>申请人: <span class="text-gray-600">{{ task.startUserName || task.createBy }}</span></span>
                <span class="w-px h-3 bg-gray-200"></span>
                <span>{{ task.createTime }}</span>
              </div>
            </div>
          </div>

          <div>
            <button 
              class="px-4 py-1.5 text-xs font-medium rounded-full transition shadow-sm"
              :class="getButtonStyle(currentTab)"
            >
              {{ getButtonText(currentTab) }}
            </button>
          </div>
        </div>
      </div>
      
      <el-empty v-else description="暂无相关任务" :image-size="100" />
      
      <div class="flex justify-end p-4" v-if="total > 0">
        <el-pagination
          v-model:current-page="queryParams.pageNum"
          v-model:page-size="queryParams.pageSize"
          :total="total"
          layout="prev, pager, next"
          @current-change="fetchData"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { Timer, CircleCheck, User, EditPen, CopyDocument } from '@element-plus/icons-vue'
// 引入所有 API
import { listTodoProcess as todoList, listFinishedProcess as finishedList, listOwnProcess as listOwn, listClaimProcess as listClaim, listCopyProcess as listCopy } from "@/api/workflow/work/process"; 

const router = useRouter()
const loading = ref(false)
const taskList = ref([])
const total = ref(0)
const currentTab = ref('todo')

// 定义 Tab 配置
const tabs = [
  { key: 'todo', name: '待办任务', count: 0 }, // workflow:process:todoList
  { key: 'claim', name: '待签任务', count: 0 }, // workflow:process:claimList
  { key: 'done', name: '已办任务', count: 0 }, // workflow:process:finishedList
  { key: 'own', name: '我发起的', count: 0 },  // workflow:process:ownList
  { key: 'copy', name: '抄送我的', count: 0 }   // workflow:process:copyList
]

const queryParams = reactive({
  pageNum: 1,
  pageSize: 10
})

// 数据获取逻辑
const fetchData = async () => {
  loading.value = true
  taskList.value = []
  try {
    let res;
    // 根据当前 Tab 调用不同 API
    switch (currentTab.value) {
      case 'todo': res = await todoList(queryParams); break;
      case 'claim': res = await listClaim(queryParams); break;
      case 'done': res = await finishedList(queryParams); break;
      case 'own': res = await listOwn(queryParams); break;
      case 'copy': res = await listCopy(queryParams); break;
    }
    
    if (res) {
      taskList.value = res.data || res.rows || []
      total.value = res.total || 0
    }
  } catch (error) {
    console.error("加载任务失败", error)
  } finally {
    loading.value = false
  }
}

// 监听 Tab 切换
watch(currentTab, () => {
  queryParams.pageNum = 1
  fetchData()
}, { immediate: true })

// 跳转处理
const handleProcess = (task) => {
  // 待签任务需要特殊处理，可能需要先签收，或者跳转到详情页有签收按钮
  const typeMap = {
    todo: 'todo',
    claim: 'claim',
    done: 'read',
    own: 'read',
    copy: 'read'
  }

  router.push({
    path: '/oa/process/detail',
    query: {
      procInsId: task.procInsId,
      taskId: task.taskId, // claim/todo/copy 都有 taskId
      deployId: task.deployId,
      type: typeMap[currentTab.value] // 告诉详情页是“审批”还是“只读”
    }
  })
}

// --- UI 辅助函数 ---

const getIconName = (tab) => {
  const map = { todo: 'Timer', claim: 'EditPen', done: 'CircleCheck', own: 'User', copy: 'CopyDocument' }
  return map[tab]
}

const getIconStyle = (tab) => {
  if (['todo', 'claim'].includes(tab)) return 'bg-blue-50 text-blue-600'
  if (tab === 'done') return 'bg-green-50 text-green-600'
  if (tab === 'copy') return 'bg-purple-50 text-purple-600'
  return 'bg-gray-100 text-gray-500'
}

const getButtonText = (tab) => {
  if (tab === 'todo') return '去审批'
  if (tab === 'claim') return '去签收'
  return '查看详情'
}

const getButtonStyle = (tab) => {
  if (['todo', 'claim'].includes(tab)) {
    return 'text-white bg-blue-600 hover:bg-blue-700'
  }
  return 'text-gray-600 bg-gray-100 hover:bg-gray-200'
}
</script>