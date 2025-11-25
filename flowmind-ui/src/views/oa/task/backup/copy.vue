<template>
  <div class="bg-white rounded-2xl shadow-sm border border-gray-100 min-h-[80vh]">
    <!-- 顶部搜索和筛选区域 -->
    <div class="p-6 border-b border-gray-100">
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div class="flex items-center gap-2">
          <h2 class="text-xl font-bold text-gray-800 whitespace-nowrap">抄送事项</h2>
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
            v-model="queryParams.readStatus"
            placeholder="阅读状态"
            clearable
            class="w-40"
          >
            <el-option label="已读" value="1" />
            <el-option label="未读" value="0" />
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
          
          <el-button type="success" @click="markAllAsRead" :disabled="!hasUnread">
            <el-icon><Select /></el-icon>
            全部标记已读
          </el-button>
        </div>
      </div>
    </div>

    <!-- 抄送事项列表 - 飞书审批卡片样式 -->
    <div class="p-6">
      <div v-if="loading" class="py-10 text-center text-gray-400">
        <el-icon class="is-loading"><Loading /></el-icon>
        <span class="ml-2">加载中...</span>
      </div>
      
      <div v-else-if="copyList.length === 0" class="py-16 text-center">
        <el-empty description="暂无抄送事项" />
      </div>
      
      <div v-else class="grid grid-cols-1 gap-4">
        <!-- 抄送事项卡片 -->
        <div
          v-for="(item, index) in copyList"
          :key="item.taskId"
          class="bg-white rounded-xl border border-gray-100 p-5 hover:shadow-md hover:border-purple-200 transition-all duration-300 cursor-pointer"
          :class="{ 'bg-purple-50 border-purple-100': item.readStatus === '0' }"
          @click="handleDetail(item)"
        >
          <div class="flex items-start justify-between">
            <!-- 左侧内容 -->
            <div class="flex-1">
              <div class="flex items-center gap-2 mb-2">
                <div class="w-10 h-10 rounded-lg flex items-center justify-center"
                     :class="item.readStatus === '0' ? 'bg-purple-100 text-purple-600' : 'bg-gray-100 text-gray-600'">
                  <el-icon><Bell /></el-icon>
                </div>
                <div class="flex-1">
                  <div class="flex items-center gap-2">
                    <h3 class="text-base font-semibold text-gray-800 hover:text-blue-600 transition-colors">
                      {{ item.procDefName }}
                    </h3>
                    <span v-if="item.readStatus === '0'" class="w-2 h-2 bg-purple-500 rounded-full"></span>
                  </div>
                  <div class="flex items-center gap-3 mt-1">
                    <span class="text-xs text-gray-500">任务节点: {{ item.taskName }}</span>
                    <span class="text-xs text-gray-500">版本: v{{ item.procDefVersion }}</span>
                    <el-tag v-if="item.categoryName" size="small" type="warning">{{ item.categoryName }}</el-tag>
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
                  <span>抄送时间: {{ parseTime(item.createTime) }}</span>
                </div>
                <div class="flex items-center gap-1">
                  <el-icon><View /></el-icon>
                  <span>状态: {{ item.readStatus === '0' ? '未读' : '已读' }}</span>
                </div>
              </div>
              
              <!-- 抄送备注 -->
              <div v-if="item.comment" class="mt-3 p-2 bg-gray-50 rounded text-xs text-gray-600">
                <span class="font-medium">备注: </span>{{ item.comment }}
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
              
              <el-tooltip content="标记已读" placement="top" v-if="item.readStatus === '0'">
                <el-button 
                  type="success" 
                  size="small" 
                  @click.stop="markAsRead(item)"
                >
                  标记已读
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

<script setup name="Copy" lang="js">
import { listCopyProcess } from "@/api/workflow/work/process";
import { markAsRead as markAsReadApi } from "@/api/workflow/work/task";
import { listAllCategory } from "@/api/workflow/category";
import { parseTime } from "@/utils/ruoyi";

const router = useRouter();
const { proxy } = getCurrentInstance();

const copyList = ref([]);
const loading = ref(true);
const total = ref(0);
const paginationTotal = ref(0); // 用于分页的总数
const categoryOptions = ref([]);
const dateRange = ref([]);

const queryParams = ref({
  pageNum: 1,
  pageSize: 10,
  processName: '',
  category: '',
  readStatus: ''
});

// 计算是否有未读项
const hasUnread = computed(() => {
  return copyList.value.some(item => item.readStatus === '0');
});

// 查询流程分类列表
const getCategoryList = async () => {
  const res = await listAllCategory();
  categoryOptions.value = res.data.map(item => ({
    ...item,
    categoryName: item.categoryName || item.name
  }));
};

// 查询抄送列表
const getList = async () => {
  loading.value = true;
  try {
    const params = proxy.addDateRange(queryParams.value, dateRange.value);
    const res = await listCopyProcess(params);
    copyList.value = res.rows.map(item => {
      // 添加分类名称
      const category = categoryOptions.value.find(cat => cat.code === item.category);
      return {
        ...item,
        categoryName: category ? category.categoryName : ''
      };
    });
    total.value = res.total;
    paginationTotal.value = res.total;
  } catch (error) {
    console.error('获取抄送列表失败:', error);
    proxy.$modal.msgError('获取抄送列表失败');
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
    readStatus: ''
  };
  getList();
};

// 查看详情
const handleDetail = (row) => {
  // 如果是未读状态，自动标记为已读
  if (row.readStatus === '0') {
    markAsRead(row);
  }
  
  router.push({
    path: '/oa/process/detail/' + row.instanceId,
    query: {
      taskId: row.taskId,
      copy: true
    }
  });
};

// 标记单个为已读
const markAsRead = async (row) => {
  try {
    const params = {
      taskId: row.taskId
    };
    await markAsReadApi(params);
    row.readStatus = '1';
    proxy.$modal.msgSuccess('标记已读成功');
  } catch (error) {
    console.error("标记已读失败", error);
    proxy.$modal.msgError('标记已读失败');
  }
};

// 全部标记为已读
const markAllAsRead = async () => {
  try {
    await proxy.$modal.confirm('确认要将所有未读抄送事项标记为已读吗？');
    
    const unreadTasks = copyList.value.filter(item => item.readStatus === '0');
    const promises = unreadTasks.map(item => {
      const params = {
        taskId: item.taskId
      };
      return markAsReadApi(params);
    });
    
    await Promise.all(promises);
    
    // 更新本地状态
    copyList.value.forEach(item => {
      if (item.readStatus === '0') {
        item.readStatus = '1';
      }
    });
    
    proxy.$modal.msgSuccess('全部标记已读成功');
  } catch (error) {
    if (error !== 'cancel') {
      console.error("全部标记已读失败", error);
      proxy.$modal.msgError('标记已读失败');
    }
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

// 未读卡片样式
.unread-card {
  position: relative;
  
  &::before {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 4px;
    background-color: #8b5cf6;
    border-top-left-radius: 8px;
    border-bottom-left-radius: 8px;
  }
}
</style>