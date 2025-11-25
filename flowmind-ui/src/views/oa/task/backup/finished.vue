<template>
  <div class="bg-white rounded-2xl shadow-sm border border-gray-100 min-h-[80vh]">
    <!-- 顶部搜索和筛选区域 -->
    <div class="p-6 border-b border-gray-100">
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div class="flex items-center gap-2">
          <h2 class="text-xl font-bold text-gray-800 whitespace-nowrap">已办事项</h2>
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
            刷新
          </el-button>
        </div>
      </div>
    </div>

    <!-- 已办事项列表 - 飞书审批卡片样式 -->
    <div class="p-6">
      <div v-if="loading" class="py-10 text-center text-gray-400">
        <el-icon class="is-loading"><Loading /></el-icon>
        <span class="ml-2">加载中...</span>
      </div>
      
      <div v-else-if="finishedList.length === 0" class="py-16 text-center">
        <el-empty description="暂无已办事项" />
      </div>
      
      <div v-else class="grid grid-cols-1 gap-4">
        <!-- 已办事项卡片 -->
        <div
          v-for="(item, index) in finishedList"
          :key="item.taskId"
          class="bg-white rounded-xl border border-gray-100 p-5 hover:shadow-md hover:border-green-200 transition-all duration-300 cursor-pointer"
          @click="handleDetail(item)"
        >
          <div class="flex items-start justify-between">
            <!-- 左侧内容 -->
            <div class="flex-1">
              <div class="flex items-center gap-2 mb-2">
                <div class="w-10 h-10 rounded-lg flex items-center justify-center bg-green-100 text-green-600">
                  <el-icon><CircleCheck /></el-icon>
                </div>
                <div>
                  <h3 class="text-base font-semibold text-gray-800 hover:text-blue-600 transition-colors">
                    {{ item.procDefName }}
                  </h3>
                  <div class="flex items-center gap-3 mt-1">
                    <span class="text-xs text-gray-500">任务节点: {{ item.taskName }}</span>
                    <span class="text-xs text-gray-500">版本: v{{ item.procDefVersion }}</span>
                    <el-tag v-if="item.categoryName" size="small" type="success">{{ item.categoryName }}</el-tag>
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
                  <span>完成时间: {{ parseTime(item.finishTime) }}</span>
                </div>
                <div class="flex items-center gap-1">
                  <el-icon><Timer /></el-icon>
                  <span>耗时: {{ calculateDuration(item.createTime, item.finishTime) }}</span>
                </div>
              </div>
            </div>
            
            <!-- 右侧操作按钮 -->
            <div class="flex items-center gap-2 ml-4">
              <el-tooltip content="查看详情" placement="top">
                <el-button 
                  type="success" 
                  size="small" 
                  @click.stop="handleDetail(item)"
                >
                  详情
                </el-button>
              </el-tooltip>
              
              <el-tooltip content="撤回" placement="top" v-if="canRevoke(item)">
                <el-button 
                  type="warning" 
                  size="small" 
                  @click.stop="handleRevoke(item)"
                >
                  撤回
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

<script setup name="Finished" lang="js">
import { listFinishedProcess } from "@/api/workflow/work/process";
import { revokeProcess } from "@/api/workflow/work/task";
import { listAllCategory } from "@/api/workflow/category";
import { parseTime } from "@/utils/ruoyi";

const router = useRouter();
const { proxy } = getCurrentInstance();

const finishedList = ref([]);
const loading = ref(true);
const categoryOptions = ref([]);
const dateRange = ref([]);
const paginationTotal = ref(0); // 用于分页的总数

const queryParams = ref({
  pageNum: 1,
  pageSize: 10,
  processName: '',
  category: ''
});

// 查询流程分类列表
const getCategoryList = async () => {
  const res = await listAllCategory();
  categoryOptions.value = res.data.map(item => ({
    ...item,
    categoryName: item.categoryName || item.name
  }));
};

// 查询已办列表
const getList = async () => {
  loading.value = true;
  try {
    const params = proxy.addDateRange(queryParams.value, dateRange.value);
    const res = await listFinishedProcess(params);
    finishedList.value = res.rows.map(item => {
      // 添加分类名称
      const category = categoryOptions.value.find(cat => cat.code === item.category);
      return {
        ...item,
        categoryName: category ? category.categoryName : ''
      };
    });
    // 保存总数用于分页
    paginationTotal.value = res.total;
  } catch (error) {
    console.error('获取已办列表失败:', error);
    proxy.$modal.msgError('获取已办列表失败');
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
    category: ''
  };
  getList();
};

// 查看详情
const handleDetail = (row) => {
  router.push({
    path: '/oa/process/detail/' + row.procInsId,
    query: {
      processed: false
    }
  });
};

// 撤回任务
const handleRevoke = async (row) => {
  try {
    await proxy.$modal.confirm('确认要撤回该任务吗？');
    const params = {
      procInsId: row.procInsId,
      taskId: row.taskId
    };
    const res = await revokeProcess(params);
    proxy.$modal.msgSuccess(res.msg || "撤回成功");
    getList();
  } catch (error) {
    if (error !== 'cancel') {
      console.error("撤回任务失败", error);
      proxy.$modal.msgError('撤回失败');
    }
  }
};

// 判断是否可以撤回
const canRevoke = (item) => {
  // 这里可以根据业务规则判断是否可以撤回
  // 例如：只有最近24小时内处理的任务可以撤回
  if (!item.finishTime) return false;
  
  const finishTime = new Date(item.finishTime);
  const now = new Date();
  const hoursDiff = (now - finishTime) / (1000 * 60 * 60);
  
  return hoursDiff <= 24; // 24小时内可以撤回
};

// 计算处理耗时
const calculateDuration = (startTime, endTime) => {
  if (!startTime || !endTime) return '未知';
  
  const start = new Date(startTime);
  const end = new Date(endTime);
  const diff = end - start;
  
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
</style>