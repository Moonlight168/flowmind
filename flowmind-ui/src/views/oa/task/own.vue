<template>
  <div class="bg-white rounded-2xl shadow-sm border border-gray-100 min-h-[80vh]">
    <!-- 顶部搜索和筛选区域 -->
    <div class="p-6 border-b border-gray-100">
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div class="flex items-center gap-2">
          <h2 class="text-xl font-bold text-gray-800">我的流程</h2>
          <span class="px-2 py-1 text-xs bg-blue-100 text-blue-600 rounded-full">{{ total }}</span>
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
            v-model="queryParams.state"
            placeholder="流程状态"
            clearable
            class="w-40"
          >
            <el-option label="进行中" value="running" />
            <el-option label="已完成" value="completed" />
            <el-option label="已终止" value="terminated" />
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
        </div>
      </div>
    </div>

    <!-- 我的流程列表 - 飞书审批卡片样式 -->
    <div class="p-6">
      <div v-if="loading" class="py-10 text-center text-gray-400">
        <el-icon class="is-loading"><Loading /></el-icon>
        <span class="ml-2">加载中...</span>
      </div>
      
      <div v-else-if="processList.length === 0" class="py-16 text-center">
        <el-empty description="暂无流程数据" />
      </div>
      
      <div v-else class="grid grid-cols-1 gap-4">
        <!-- 流程卡片 -->
        <div
          v-for="(item, index) in processList"
          :key="item.instanceId"
          class="bg-white rounded-xl border border-gray-100 p-5 hover:shadow-md hover:border-blue-200 transition-all duration-300 cursor-pointer"
          @click="handleDetail(item)"
        >
          <div class="flex items-start justify-between">
            <!-- 左侧内容 -->
            <div class="flex-1">
              <div class="flex items-center gap-2 mb-2">
                <div class="w-10 h-10 rounded-lg flex items-center justify-center"
                     :class="getStateClass(item.state)">
                  <el-icon><component :is="getStateIcon(item.state)" /></el-icon>
                </div>
                <div>
                  <h3 class="text-base font-semibold text-gray-800 hover:text-blue-600 transition-colors">
                    {{ item.procDefName }}
                  </h3>
                  <div class="flex items-center gap-3 mt-1">
                    <span class="text-xs text-gray-500">版本: v{{ item.procDefVersion }}</span>
                    <el-tag v-if="item.categoryName" size="small" type="info">{{ item.categoryName }}</el-tag>
                    <el-tag :type="getStateTagType(item.state)" size="small">
                      {{ getStateText(item.state) }}
                    </el-tag>
                  </div>
                </div>
              </div>
              
              <div class="flex items-center gap-4 mt-3 text-xs text-gray-500">
                <div class="flex items-center gap-1">
                  <el-icon><Clock /></el-icon>
                  <span>发起时间: {{ parseTime(item.createTime) }}</span>
                </div>
                <div class="flex items-center gap-1" v-if="item.duration">
                  <el-icon><Timer /></el-icon>
                  <span>总耗时: {{ item.duration }}</span>
                </div>
                <div class="flex items-center gap-1" v-if="item.currentTask">
                  <el-icon><User /></el-icon>
                  <span>当前处理人: {{ item.currentTask }}</span>
                </div>
              </div>
            </div>
            
            <!-- 右侧操作按钮 -->
            <div class="flex items-center gap-2 ml-4">
              <el-tooltip content="查看详情" placement="top">
                <el-button 
                  type="primary" 
                  size="small" 
                  @click.stop="handleDetail(item)"
                >
                  详情
                </el-button>
              </el-tooltip>
              
              <el-tooltip content="取消流程" placement="top" v-if="item.state === 'running'">
                <el-button 
                  type="danger" 
                  size="small" 
                  @click.stop="handleCancel(item)"
                >
                  取消
                </el-button>
              </el-tooltip>
              
              <el-tooltip content="删除流程" placement="top" v-if="item.state === 'completed' || item.state === 'terminated'">
                <el-button 
                  type="danger" 
                  size="small" 
                  @click.stop="handleDelete(item)"
                >
                  删除
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

<script setup name="Own" lang="js">
import { listOwnProcess } from "@/api/workflow/work/process";
import { revokeProcess } from "@/api/workflow/work/task";
import { delProcess } from "@/api/workflow/work/process";
import { listAllCategory } from "@/api/workflow/category";
import { parseTime } from "@/utils/ruoyi";

const router = useRouter();
const { proxy } = getCurrentInstance();

const processList = ref([]);
const loading = ref(true);
const total = ref(0);
const categoryOptions = ref([]);
const dateRange = ref([]);

const queryParams = ref({
  pageNum: 1,
  pageSize: 10,
  processName: '',
  category: '',
  state: ''
});

// 查询流程分类列表
const getCategoryList = async () => {
  const res = await listAllCategory();
  categoryOptions.value = res.data.map(item => ({
    ...item,
    categoryName: item.categoryName || item.name
  }));
};

// 查询我的流程列表
const getList = async () => {
  loading.value = true;
  try {
    const params = proxy.addDateRange(queryParams.value, dateRange.value);
    const res = await listOwnProcess(params);
    processList.value = res.rows.map(item => {
      // 添加分类名称和状态文本
      const category = categoryOptions.value.find(cat => cat.code === item.category);
      return {
        ...item,
        categoryName: category ? category.categoryName : '',
        stateText: getStateText(item.state),
        duration: calculateDuration(item.createTime, item.endTime)
      };
    });
    total.value = res.total;
  } catch (error) {
    console.error('获取我的流程列表失败:', error);
    proxy.$modal.msgError('获取我的流程列表失败');
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
    state: ''
  };
  getList();
};

// 查看详情
const handleDetail = (row) => {
  router.push({
    path: '/oa/process/detail/' + row.instanceId,
    query: {
      own: true
    }
  });
};

// 取消流程
const handleCancel = async (row) => {
  try {
    await proxy.$modal.confirm('确认要取消该流程吗？取消后将无法恢复。');
    const params = {
      instanceId: row.instanceId
    };
    const res = await revokeProcess(params);
    proxy.$modal.msgSuccess(res.msg || "取消成功");
    getList();
  } catch (error) {
    if (error !== 'cancel') {
      console.error("取消流程失败", error);
      proxy.$modal.msgError('取消失败');
    }
  }
};

// 删除流程
const handleDelete = async (row) => {
  try {
    await proxy.$modal.confirm('确认要删除该流程吗？删除后将无法恢复。');
    const params = row.instanceId;
    const res = await delProcess(params);
    proxy.$modal.msgSuccess(res.msg || "删除成功");
    getList();
  } catch (error) {
    if (error !== 'cancel') {
      console.error("删除流程失败", error);
      proxy.$modal.msgError('删除失败');
    }
  }
};

// 获取状态文本
const getStateText = (state) => {
  const stateMap = {
    'running': '进行中',
    'completed': '已完成',
    'terminated': '已终止',
    'suspended': '已挂起'
  };
  return stateMap[state] || '未知';
};

// 获取状态标签类型
const getStateTagType = (state) => {
  const typeMap = {
    'running': 'primary',
    'completed': 'success',
    'terminated': 'danger',
    'suspended': 'warning'
  };
  return typeMap[state] || 'info';
};

// 获取状态图标
const getStateIcon = (state) => {
  const iconMap = {
    'running': 'Loading',
    'completed': 'CircleCheck',
    'terminated': 'CircleClose',
    'suspended': 'VideoPause'
  };
  return iconMap[state] || 'QuestionFilled';
};

// 获取状态样式类
const getStateClass = (state) => {
  const classMap = {
    'running': 'bg-blue-100 text-blue-600',
    'completed': 'bg-green-100 text-green-600',
    'terminated': 'bg-red-100 text-red-600',
    'suspended': 'bg-yellow-100 text-yellow-600'
  };
  return classMap[state] || 'bg-gray-100 text-gray-600';
};

// 计算流程持续时间
const calculateDuration = (startTime, endTime) => {
  if (!startTime) return '未知';
  
  const start = new Date(startTime);
  const end = endTime ? new Date(endTime) : new Date();
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