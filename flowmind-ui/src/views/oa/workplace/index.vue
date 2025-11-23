<template>
  <div class="max-w-7xl mx-auto">
    <div class="mb-6">
      <h3 class="text-lg font-bold text-gray-800 mb-2">常用应用</h3>
      <p class="text-xs text-gray-500">点击即可发起新的流程申请</p>
    </div>

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
          {{ item.name ? item.name.charAt(0) : 'P' }}
        </div>

        <div class="flex-1 min-w-0">
          <h4 class="text-sm font-bold text-gray-800 truncate group-hover:text-blue-600 transition-colors">
            {{ item.name }}
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
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
// 引入 RuoYi Flowable 原有 API
import { listPublish } from "@/api/workflow/deploy";

const router = useRouter()
const loading = ref(false)
const processList = ref([])

// 颜色轮换，模仿飞书应用图标
const bgColors = [
  'bg-gradient-to-br from-blue-500 to-blue-600',
  'bg-gradient-to-br from-emerald-400 to-emerald-600',
  'bg-gradient-to-br from-orange-400 to-orange-600',
  'bg-gradient-to-br from-purple-500 to-purple-600',
  'bg-gradient-to-br from-rose-400 to-rose-600'
]
const getColorClass = (index) => bgColors[index % bgColors.length]

const getList = async () => {
  loading.value = true
  try {
    // TODO: 暂时注释API调用，先生成布局
    // const res = await listPublish({ 
    //   pageNum: 1, 
    //   pageSize: 50,
    //   processKey: '' // 可以根据需要设置具体的流程key
    // })
    // processList.value = res.rows || []
    
    // 临时使用模拟数据
    processList.value = [
      { name: '请假流程', key: 'leave', version: 1 },
      { name: '报销流程', key: 'expense', version: 1 },
      { name: '采购流程', key: 'purchase', version: 1 }
    ]
  } finally {
    loading.value = false
  }
}

const handleStart = (proc) => {
  // 跳转到发起详情页
  router.push({
    path: '/oa/process/detail',
    query: {
      deployId: proc.deploymentId,
      procDefId: proc.id,
      type: 'start' // 标记为发起
    }
  })
}

onMounted(() => {
  getList()
})
</script>