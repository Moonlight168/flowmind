<template>
  <div class="min-h-screen bg-gray-50">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div class="grid grid-cols-1 lg:grid-cols-4 gap-8">
        <!-- 左侧导航 -->
        <div class="lg:col-span-1">
          <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6 sticky top-8">
            <h2 class="text-lg font-semibold text-gray-900 mb-4">工作台</h2>
            <TabNavigation 
              :tabs="tabs" 
              :current-tab="currentTab" 
              @tab-change="handleTabChange" 
            />
          </div>
        </div>
        
        <!-- 右侧内容 -->
        <div class="lg:col-span-3">
          <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div v-if="currentTab === 'apps'" class="space-y-6">
              <div class="flex items-center justify-between">
                <h3 class="text-xl font-semibold text-gray-900">应用中心</h3>
                <!-- <div class="flex items-center gap-4">
                  <el-input 
                    v-model="searchQuery" 
                    placeholder="搜索流程..." 
                    prefix-icon="Search"
                    class="w-64"
                  />
                  <el-select v-model="selectedCategory" placeholder="选择分类" class="w-40">
                    <el-option label="全部" value="all" />
                    <el-option label="行政" value="admin" />
                    <el-option label="人事" value="hr" />
                    <el-option label="财务" value="finance" />
                  </el-select>
                </div> -->
              </div>
              <AppCenterContent :processes="filteredProcesses" />
            </div>
            
            <div v-else-if="currentTab === 'drafts'" class="space-y-6">
              <h3 class="text-xl font-semibold text-gray-900">草稿箱</h3>
              <DraftBoxContent :drafts="drafts" @refresh-drafts="fetchDrafts" />
            </div>
            
            <div v-else class="py-12 text-center text-gray-500">
              <div class="text-6xl mb-4">
                <el-icon><component :is="getTabIcon(currentTab)" /></el-icon>
              </div>
              <p>{{ getTabContent(currentTab) }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import {computed, onMounted, ref} from 'vue'
import {ElMessage} from 'element-plus'
import {listProcess} from '@/api/workflow/work/process'
import {listDraft} from '@/api/workflow/work/draft'
import TabNavigation from './components/TabNavigation.vue'
import AppCenterContent from './components/AppCenterContent.vue'
import DraftBoxContent from './components/DraftBoxContent.vue'

// 响应式数据
const currentTab = ref('apps')
const searchQuery = ref('')
const selectedCategory = ref('all')
const processes = ref([])
const drafts = ref([])
const loading = ref(false)

// 标签页配置
const tabs = ref([
  { key: 'apps', name: '应用中心', icon: 'Grid', count: 0 },
  { key: 'drafts', name: '草稿箱', icon: 'Document', count: 0 }
])

// 计算属性
const filteredProcesses = computed(() => {
  return processes.value
})

// 方法
const handleTabChange = (tab) => {
  currentTab.value = tab
}

const getTabIcon = (tab) => {
  const iconMap = {
    apps: 'Grid',
    drafts: 'Document'
  }
  return iconMap[tab]
}

const getTabContent = (tab) => {
  const contentMap = {
    drafts: '暂无草稿'
  }
  return contentMap[tab]
}

// 获取流程列表
const fetchProcesses = async () => {
  try {
    loading.value = true
    // 添加分页参数，避免后端PageQuery.getPageSize()为null
    const queryParams = {
      pageNum: 1,
      pageSize: 100
    }
    const res = await listProcess(queryParams)
    // 处理后端返回的TableDataInfo结构
    const processData = res.rows || res.data || []
    processes.value = processData.map(item => ({
      definitionId: item.definitionId,
      deploymentId: item.deploymentId,
      processName: item.processName,
      processKey: item.processKey,
      category: item.category,
      version: item.version,
      formId: item.formId,
      formName: item.formName,
      suspended: item.suspended,
      deploymentTime: item.deploymentTime,
      avgTime: Math.floor(Math.random() * 30) + 5
    }))
  } catch (error) {
    console.error('获取流程列表失败:', error)
    ElMessage.error('获取流程列表失败,请稍后重试')
  } finally {
    loading.value = false
  }
}

// 获取草稿列表
const fetchDrafts = async () => {
  try {
    loading.value = true
    // 添加分页参数，避免后端PageQuery.getPageSize()为null
    const queryParams = {
      pageNum: 1,
      pageSize: 100
    }
    const res = await listDraft(queryParams)
    // 处理后端返回的TableDataInfo结构
    const draftData = res.rows || res.data || []
    drafts.value = draftData.map(item => ({
      draftId: item.draftId,
      processName: item.processName,
      definitionId: item.definitionId,
      deployId: item.deployId,
      createTime: item.createTime,
      updateTime: item.updateTime
    }))
    
    // 更新草稿箱标签的计数
    tabs.value.find(tab => tab.key === 'drafts').count = drafts.value.length
  } catch (error) {
    console.error('获取草稿列表失败:', error)
    ElMessage.error('获取草稿列表失败')
  } finally {
    loading.value = false
  }
}

// 生命周期
onMounted(() => {
  fetchProcesses()
  fetchDrafts()
})
</script>