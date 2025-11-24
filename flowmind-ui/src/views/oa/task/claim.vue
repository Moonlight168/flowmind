<template>
  <div class="bg-white rounded-2xl shadow-sm border border-gray-100 min-h-[80vh]">
    <!-- 顶部搜索和筛选区域 -->
    <div class="p-6 border-b border-gray-100">
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div class="flex items-center gap-2">
          <h2 class="text-xl font-bold text-gray-800 whitespace-nowrap">待签收事项</h2>
          <span class="px-2 py-1 text-xs bg-orange-100 text-orange-600 rounded-full">{{ total }}</span>
        </div>
        
        <div class="flex flex-wrap items-center gap-3">
          <div class="relative">
            <el-input
              v-model="queryParams.processName"
              placeholder="搜索流程名称"
              clearable
              class="w-64"
              @keyup.enter="handleQuery"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </div>
          
          <el-select
            v-model="queryParams.category"
            placeholder="流程分类"
            clearable
            class="w-40"
          >
            <el-option
              v-for="item in categoryOptions"
              :key="item.categoryId"
              :label="item.categoryName"
              :value="item.code"
            />
          </el-select>
          
          <el-select
            v-model="queryParams.priority"
            placeholder="优先级"
            clearable
            class="w-32"
          >
            <el-option label="高" value="high" />
            <el-option label="中" value="medium" />
            <el-option label="低" value="low" />
          </el-select>
          
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            class="w-56"
          />
          
          <el-button type="primary" @click="handleQuery">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          
          <el-button @click="resetQuery">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
          
          <el-button type="success" @click="batchClaim" :disabled="!hasSelected">
            <el-icon><Select /></el-icon>
            批量签收
          </el-button>
        </div>
      </div>
    </div>

    <!-- 待签收事项列表 - 飞书审批卡片样式 -->
    <div class="p-6">
      <div v-if="loading" class="py-10 text-center text-gray-400">
        <el-icon class="is-loading"><Loading /></el-icon>
        <span class="ml-2">加载中...</span>
      </div>
      
      <div v-else-if="claimList.length === 0" class="py-16 text-center">
        <el-empty description="暂无待签收事项" />
      </div>
      
      <div v-else class="grid grid-cols-1 gap-4">
        <!-- 待签收事项卡片 -->
        <div
          v-for="(item, index) in claimList"
          :key="item.taskId"
          class="bg-white rounded-xl border border-gray-100 p-5 hover:shadow-md hover:border-orange-200 transition-all duration-300"
          :class="{ 'ring-2 ring-orange-200': selectedItems.includes(item.taskId) }"
        >
          <div class="flex items-start justify-between">
            <!-- 左侧选择框和内容 -->
            <div class="flex items-start gap-3 flex-1">
              <el-checkbox
                v-model="selectedItems"
                :value="item.taskId"
                @change="handleSelectionChange"
              />
              
              <div class="flex-1">
                <div class="flex items-center gap-2 mb-2">
                  <div class="w-10 h-10 rounded-lg flex items-center justify-center"
                       :class="getPriorityClass(item.priority)">
                    <el-icon><component :is="getPriorityIcon(item.priority)" /></el-icon>
                  </div>
                  <div class="flex-1">
                    <h3 class="text-base font-semibold text-gray-800 hover:text-blue-600 transition-colors cursor-pointer"
                        @click="handleDetail(item)">
                      {{ item.procDefName }}
                    </h3>
                    <div class="flex items-center gap-3 mt-1">
                      <span class="text-xs text-gray-500">任务节点: {{ item.taskName }}</span>
                      <span class="text-xs text-gray-500">版本: v{{ item.procDefVersion }}</span>
                      <el-tag v-if="item.categoryName" size="small" type="info">{{ item.categoryName }}</el-tag>
                      <el-tag :type="getPriorityTagType(item.priority)" size="small">
                        {{ getPriorityText(item.priority) }}
                      </el-tag>
                    </div>
                  </div>
                </div>
                
                <div class="flex items-center gap-4 mt-3 text-xs text-gray-500">
                  <div class="flex items-center gap-1">
                    <el-icon><User /></el-icon>
                    <span>发起人: {{ item.startUserName }}</span>
                  </div>
                  <div class="flex items-center gap-1">
                    <el-icon><Clock /></el-icon>
                    <span>创建时间: {{ parseTime(item.createTime) }}</span>
                  </div>
                  <div class="flex items-center gap-1">
                    <el-icon><Timer /></el-icon>
                    <span>待处理: {{ calculateWaitTime(item.createTime) }}</span>
                  </div>
                </div>
                
                <!-- 候选人信息 -->
                <div v-if="item.candidateUsers && item.candidateUsers.length > 0" class="mt-3 p-2 bg-orange-50 rounded text-xs">
                  <span class="font-medium text-orange-700">候选人: </span>
                  <span class="text-orange-600">{{ item.candidateUsers.join(', ') }}</span>
                </div>
              </div>
            </div>
            
            <!-- 右侧操作按钮 -->
            <div class="flex items-center gap-2 ml-4">
              <el-tooltip content="查看详情" placement="top">
                <el-button 
                  type="primary" 
                  size="small" 
                  @click="handleDetail(item)"
                >
                  详情
                </el-button>
              </el-tooltip>
              
              <el-tooltip content="签收" placement="top">
                <el-button 
                  type="success" 
                  size="small" 
                  @click="handleClaim(item)"
                >
                  签收
                </el-button>
              </el-tooltip>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 分页 -->
      <div v-if="total > 0" class="mt-6 flex justify-center">
        <el-pagination
          v-model:current-page="queryParams.pageNum"
          v-model:page-size="queryParams.pageSize"
          :page-sizes="[10, 20, 30, 50]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="getList"
          @current-change="getList"
        />
      </div>
    </div>
  </div>
</template>

<script setup name="Claim" lang="js">
import { listClaimProcess } from "@/api/workflow/work/process";
import { claimTask, batchClaimTask } from "@/api/workflow/work/task";
import { listAllCategory } from "@/api/workflow/category";
import { parseTime } from "@/utils/ruoyi";

const router = useRouter();
const { proxy } = getCurrentInstance();

const claimList = ref([]);
const loading = ref(true);
const total = ref(0);
const categoryOptions = ref([]);
const dateRange = ref([]);
const selectedItems = ref([]);

const queryParams = ref({
  pageNum: 1,
  pageSize: 10,
  processName: '',
  category: '',
  priority: ''
});

// 计算是否有选中项
const hasSelected = computed(() => {
  return selectedItems.value.length > 0;
});

// 查询流程分类列表
const getCategoryList = async () => {
  const res = await listAllCategory();
  categoryOptions.value = res.data.map(item => ({
    ...item,
    categoryName: item.categoryName || item.name
  }));
};

// 查询待签收列表
const getList = async () => {
  loading.value = true;
  try {
    const params = proxy.addDateRange(queryParams.value, dateRange.value);
    const res = await listClaimProcess(params);
    claimList.value = res.rows.map(item => {
      // 添加分类名称和优先级文本
      const category = categoryOptions.value.find(cat => cat.code === item.category);
      return {
        ...item,
        categoryName: category ? category.categoryName : '',
        priorityText: getPriorityText(item.priority)
      };
    });
    total.value = res.total;
    // 清空选中项
    selectedItems.value = [];
  } catch (error) {
    console.error('获取待签收列表失败:', error);
    proxy.$modal.msgError('获取待签收列表失败');
  } finally {
    loading.value = false;
  }
};

// 搜索按钮操作
const handleQuery = () => {
  queryParams.value.pageNum = 1;
  getList();
};

// 重置按钮操作
const resetQuery = () => {
  dateRange.value = [];
  queryParams.value = {
    pageNum: 1,
    pageSize: 10,
    processName: '',
    category: '',
    priority: ''
  };
  getList();
};

// 查看详情
const handleDetail = (row) => {
  router.push({
    path: '/oa/process/detail/' + row.instanceId,
    query: {
      taskId: row.taskId,
      claim: true
    }
  });
};

// 签收任务
const handleClaim = async (row) => {
  try {
    await proxy.$modal.confirm('确认要签收该任务吗？');
    const params = {
      taskId: row.taskId
    };
    const res = await claimTask(params);
    proxy.$modal.msgSuccess(res.msg || "签收成功");
    getList();
  } catch (error) {
    if (error !== 'cancel') {
      console.error("签收任务失败", error);
      proxy.$modal.msgError('签收失败');
    }
  }
};

// 批量签收
const batchClaim = async () => {
  try {
    await proxy.$modal.confirm(`确认要签收选中的 ${selectedItems.value.length} 个任务吗？`);
    const params = {
      taskIds: selectedItems.value
    };
    const res = await batchClaimTask(params);
    proxy.$modal.msgSuccess(res.msg || "批量签收成功");
    getList();
  } catch (error) {
    if (error !== 'cancel') {
      console.error("批量签收失败", error);
      proxy.$modal.msgError('批量签收失败');
    }
  }
};

// 选择项变化处理
const handleSelectionChange = () => {
  // 选择项变化时，更新selectedItems数组
};

// 获取优先级文本
const getPriorityText = (priority) => {
  const priorityMap = {
    'high': '高',
    'medium': '中',
    'low': '低'
  };
  return priorityMap[priority] || '中';
};

// 获取优先级标签类型
const getPriorityTagType = (priority) => {
  const typeMap = {
    'high': 'danger',
    'medium': 'warning',
    'low': 'info'
  };
  return typeMap[priority] || 'info';
};

// 获取优先级图标
const getPriorityIcon = (priority) => {
  const iconMap = {
    'high': 'Warning',
    'medium': 'InfoFilled',
    'low': 'CircleCheck'
  };
  return iconMap[priority] || 'InfoFilled';
};

// 获取优先级样式类
const getPriorityClass = (priority) => {
  const classMap = {
    'high': 'bg-red-100 text-red-600',
    'medium': 'bg-yellow-100 text-yellow-600',
    'low': 'bg-green-100 text-green-600'
  };
  return classMap[priority] || 'bg-gray-100 text-gray-600';
};

// 计算等待时间
const calculateWaitTime = (createTime) => {
  if (!createTime) return '未知';
  
  const create = new Date(createTime);
  const now = new Date();
  const diff = now - create;
  
  if (diff < 60 * 1000) {
    return Math.floor(diff / 1000) + '秒';
  } else if (diff < 60 * 60 * 1000) {
    return Math.floor(diff / (60 * 1000)) + '分钟';
  } else if (diff < 24 * 60 * 60 * 1000) {
    return Math.floor(diff / (60 * 60 * 1000)) + '小时';
  } else {
    return Math.floor(diff / (24 * 60 * 60 * 1000)) + '天';
  }
};

onMounted(() => {
  getCategoryList();
  getList();
});
</script>

<style lang="scss" scoped>
// 飞书审批卡片样式
.approve-card {
  transition: all 0.3s ease;
  
  &:hover {
    transform: translateY(-2px);
  }
}

// 选中卡片样式
.selected-card {
  position: relative;
  box-shadow: 0 0 0 2px rgba(251, 146, 60, 0.3);
}
</style>