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
      <!-- 常用应用标题 -->
      <div v-if="currentTab === 'apps' && $route.name === 'Workplace'" class="mb-6">
        <h3 class="text-lg font-bold text-gray-800 mb-2">常用应用</h3>
        <p class="text-xs text-gray-500">点击即可发起新的流程申请</p>
      </div>

      <!-- 应用网格 -->
      <div v-if="currentTab === 'apps' && $route.name === 'Workplace'">
        <div v-if="loading" class="py-10 text-center text-gray-400">加载中...</div>

        <div v-else class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-5">
          <div
              v-for="(item, index) in processList"
              :key="item.deploymentId"
              @click="handleStart(item)"
              class="group bg-white rounded-2xl p-5 border border-gray-100 cursor-pointer hover:shadow-xl hover:shadow-blue-500/10 hover:-translate-y-1 hover:border-blue-200 transition-all duration-300 flex items-start"
          >
            <div
                class="w-12 h-12 rounded-xl flex items-center justify-center text-white text-xl font-bold mr-4 shadow-sm transition-transform group-hover:scale-110"
                :class="getColorClass(index)"
            >
              {{ item.processName ? item.processName.charAt(0) : 'P' }}
            </div>

            <div class="flex-1 min-w-0">
              <h4 class="text-sm font-bold text-gray-800 truncate group-hover:text-blue-600 transition-colors">
                {{ item.processName }}
              </h4>
              <p class="text-xs text-gray-400 mt-1 truncate">版本: v{{ item.version }}</p>
              <div class="mt-3 flex items-center text-[10px] text-gray-400 bg-gray-50 w-max px-2 py-1 rounded-md">
                {{ item.category || '通用流程' }}
              </div>
            </div>
          </div>
        </div>

        <el-empty v-if="!loading && processList.length === 0" description="暂无可用流程" />
      </div>

      <!-- 草稿箱内容 -->
      <div v-if="currentTab === 'drafts' && $route.name === 'Workplace'">
        <div v-if="draftLoading" class="py-10 text-center text-gray-400">加载中...</div>

        <div v-else class="space-y-4">
          <div
              v-for="(item, index) in draftList"
              :key="item.id"
              class="group bg-white rounded-xl p-5 border border-gray-100 hover:shadow-md hover:border-blue-200 transition-all duration-300"
          >
            <div class="flex items-start justify-between">
              <div class="flex-1">
                <div class="flex items-center gap-3 mb-2">
                  <div
                      class="w-10 h-10 rounded-lg flex items-center justify-center text-white text-sm font-bold shadow-sm"
                      :class="getColorClass(index)"
                  >
                    {{ item.processName ? item.processName.charAt(0) : 'D' }}
                  </div>
                  <div>
                    <h4 class="text-sm font-bold text-gray-800">
                      {{ item.processName }}
                    </h4>
                    <p class="text-xs text-gray-400">
                      保存时间: {{ formatDateTime(item.updateTime) }}
                    </p>
                  </div>
                </div>
                <div class="mt-3 flex items-center gap-2">
                  <el-button size="small" type="primary" @click="handleEditDraft(item)">
                    <el-icon><EditPen /></el-icon>
                    继续编辑
                  </el-button>
                  <el-button size="small" type="danger" plain @click="handleDeleteDraft(item)">
                    <el-icon><Delete /></el-icon>
                    删除
                  </el-button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <el-empty v-if="!draftLoading && draftList.length === 0" description="暂无草稿" />
      </div>
      <!-- 子路由内容 -->
      <router-view />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Grid, Document, Setting, DataAnalysis, User, EditPen, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
// 引入 RuoYi Flowable 原有 API
import { listProcess } from "@/api/workflow/work/process.js";
import { listDraft, delDraft } from "@/api/workflow/work/draft.js";

const router = useRouter()
const loading = ref(false)
const processList = ref([])
const draftLoading = ref(false)
const draftList = ref([])
const currentTab = ref('apps')

// 定义 Tab 配置
const tabs = [
  { key: 'apps', name: '应用中心', count: 0 },
  { key: 'drafts', name: '草稿箱', count: 0 },
]

// 颜色轮换，模仿飞书应用图标
const bgColors = [
  'bg-gradient-to-br from-blue-500 to-blue-600',
  'bg-gradient-to-br from-emerald-400 to-emerald-600',
  'bg-gradient-to-br from-orange-400 to-orange-600',
  'bg-gradient-to-br from-purple-500 to-purple-600',
  'bg-gradient-to-br from-rose-400 to-rose-600'
]
const getColorClass = (index) => bgColors[index % bgColors.length]

// 获取图标名称
const getIconName = (tab) => {
  const map = { 
    apps: 'Grid', 
    recent: 'Document', 
    favorites: 'User', 
    drafts: 'Document', 
    statistics: 'DataAnalysis' 
  }
  return map[tab]
}

const getList = async () => {
  loading.value = true
  try {
    // 使用listProcess API获取真实流程数据
    const res = await listProcess({ 
      pageNum: 1, 
      pageSize: 50
    })
    processList.value = res.rows || []
  } catch (error) {
    console.error('获取流程列表失败:', error)
    processList.value = []
  } finally {
    loading.value = false
  }
}

const handleStart = (proc) => {
  // 跳转到发起流程表单
  router.push({
    path: '/oa/workplace/start/' + proc.deploymentId,
    query: {
      definitionId: proc.definitionId,
    }
  })
}

// 获取草稿列表
const getDraftList = async () => {
  draftLoading.value = true
  try {
    const res = await listDraft({ 
      pageNum: 1, 
      pageSize: 50
    })
    draftList.value = res.rows || []
    // 更新草稿数量
    tabs[1].count = draftList.value.length
  } catch (error) {
    console.error('获取草稿列表失败:', error)
    draftList.value = []
  } finally {
    draftLoading.value = false
  }
}

// 编辑草稿
const handleEditDraft = (draft) => {
  // 跳转到发起流程表单，并传入草稿ID
  router.push({
    path: '/oa/workplace/start/' + draft.deployId,
    query: {
      definitionId: draft.definitionId,
      draftId: draft.id
    }
  })
}

// 删除草稿
const handleDeleteDraft = (draft) => {
  ElMessageBox.confirm(
    `确定要删除草稿"${draft.processName}"吗？`,
    '删除确认',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(async () => {
    try {
      const res = await delDraft(draft.id)
      if (res.code === 200) {
        ElMessage.success('删除成功')
        // 重新获取草稿列表
        getDraftList()
      } else {
        ElMessage.error('删除失败')
      }
    } catch (error) {
      console.error('删除草稿失败:', error)
      ElMessage.error('删除失败')
    }
  }).catch(() => {
    // 用户取消删除
  })
}

// 格式化日期时间
const formatDateTime = (dateTime) => {
  if (!dateTime) return ''
  const date = new Date(dateTime)
  return `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}-${date.getDate().toString().padStart(2, '0')} ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
}

// 监听Tab切换
watch(currentTab, (newTab) => {
  if (newTab === 'drafts') {
    getDraftList()
  }
})

onMounted(() => {
  getList()
  getDraftList()
})
</script>