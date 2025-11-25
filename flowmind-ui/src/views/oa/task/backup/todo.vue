<template>
  <div class="bg-white rounded-2xl shadow-sm border border-gray-100 min-h-[80vh]">
    <!-- 顶部搜索和筛选区域 -->
    <div class="p-6 border-b border-gray-100">
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div class="flex items-center gap-2">
          <h2 class="text-xl font-bold text-gray-800 whitespace-nowrap">待办事项</h2>
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
          
          <el-button type="primary" @click="handleQuery">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          
          <el-button @click="resetQuery">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </div>
    </div>

    <!-- 待办事项列表 - 飞书审批卡片样式 -->
    <div class="p-6">
      <div v-if="loading" class="py-10 text-center text-gray-400">
        <el-icon class="is-loading"><Loading /></el-icon>
        <span class="ml-2">加载中...</span>
      </div>
      
      <div v-else-if="todoList.length === 0" class="py-16 text-center">
        <el-empty description="暂无待办事项" />
      </div>
      
      <div v-else class="grid grid-cols-1 gap-4">
        <!-- 待办事项卡片 -->
        <div
          v-for="(item, index) in todoList"
          :key="item.taskId"
          class="bg-white rounded-xl border border-gray-100 p-5 hover:shadow-md hover:border-blue-200 transition-all duration-300 cursor-pointer"
          @click="handleDetail(item)"
        >
          <div class="flex items-start justify-between">
            <!-- 左侧内容 -->
            <div class="flex-1">
              <div class="flex items-center gap-2 mb-2">
                <div 
                  class="w-10 h-10 rounded-lg flex items-center justify-center text-white font-medium"
                  :class="getPriorityColor(item.priority)"
                >
                  {{ getPriorityIcon(item.priority) }}
                </div>
                <div>
                  <h3 class="text-base font-semibold text-gray-800 hover:text-blue-600 transition-colors">
                    {{ item.procDefName }}
                  </h3>
                  <div class="flex items-center gap-3 mt-1">
                    <span class="text-xs text-gray-500">任务节点: {{ item.taskName }}</span>
                    <span class="text-xs text-gray-500">版本: v{{ item.procDefVersion }}</span>
                    <el-tag v-if="item.categoryName" size="small" type="info">{{ item.categoryName }}</el-tag>
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
                  <span>接收时间: {{ parseTime(item.createTime) }}</span>
                </div>
              </div>
            </div>
            
            <!-- 右侧操作按钮 -->
            <div class="flex items-center gap-2 ml-4">
              <el-tooltip content="办理" placement="top">
                <el-button 
                  type="primary" 
                  size="small" 
                  @click.stop="handleDetail(item)"
                >
                  办理
                </el-button>
              </el-tooltip>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 分页 -->
      <div v-if="paginationTotal > 0" class="mt-6 flex justify-center">
        <el-pagination
          v-model:current-page="queryParams.pageNum"
          v-model:page-size="queryParams.pageSize"
          :page-sizes="[10, 20, 30, 50]"
          :total="paginationTotal"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="getList"
          @current-change="getList"
        />
      </div>
    </div>
  </div>
</template>

<script setup name="Todo" lang="js">
import { listTodoProcess } from "@/api/workflow/work/process";
import { listAllCategory } from "@/api/workflow/category";
import { parseTime } from "@/utils/ruoyi";

const router = useRouter();
const { proxy } = getCurrentInstance();

const todoList = ref([]);
const loading = ref(true);
const total = ref(0);
const paginationTotal = ref(0); // 用于分页的总数
const categoryOptions = ref([]);

const queryParams = ref({
  pageNum: 1,
  pageSize: 10,
  processName: '',
  category: ''
});

// 根据优先级获取颜色类
const getPriorityColor = (priority) => {
  const colors = {
    high: 'bg-gradient-to-br from-red-500 to-red-600',
    medium: 'bg-gradient-to-br from-blue-500 to-blue-600',
    low: 'bg-gradient-to-br from-gray-500 to-gray-600'
  };
  return colors[priority] || colors.medium;
};

// 根据优先级获取图标
const getPriorityIcon = (priority) => {
  const icons = {
    high: '急',
    medium: '中',
    low: '低'
  };
  return icons[priority] || '中';
};

// 查询流程分类列表
const getCategoryList = async () => {
  const res = await listAllCategory();
  categoryOptions.value = res.data.map(item => ({
    ...item,
    categoryName: item.categoryName || item.name
  }));
};

// 查询待办列表
const getList = async () => {
  loading.value = true;
  try {
    const res = await listTodoProcess(queryParams.value);
    todoList.value = res.rows.map(item => {
      // 添加分类名称
      const category = categoryOptions.value.find(cat => cat.code === item.category);
      return {
        ...item,
        categoryName: category ? category.categoryName : '',
        // 随机设置优先级，实际应用中应该从后端获取
        priority: ['high', 'medium', 'low'][Math.floor(Math.random() * 3)]
      };
    });
    total.value = res.total;
    paginationTotal.value = res.total;
  } catch (error) {
    console.error('获取待办列表失败:', error);
    proxy.$modal.msgError('获取待办列表失败');
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
  queryParams.value = {
    pageNum: 1,
    pageSize: 10,
    processName: '',
    category: ''
  };
  getList();
};

// 查看详情
const handleDetail = (row) => {
  router.push({
    path: '/oa/process/detail/' + row.instanceId,
    query: {
      taskId: row.taskId,
      processed: false
    }
  });
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
</style>