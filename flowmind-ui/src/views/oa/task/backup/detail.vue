<template>
  <div class="bg-white rounded-2xl shadow-sm border border-gray-100 min-h-[80vh]">
    <!-- 顶部标题和操作区域 -->
    <div class="p-6 border-b border-gray-100">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <el-button @click="goBack" size="small">
            <el-icon><ArrowLeft /></el-icon>
            返回
          </el-button>
          <h2 class="text-xl font-bold text-gray-800">流程详情</h2>
          <el-tag :type="getStateTagType(processInfo.state)" size="small">
            {{ getStateText(processInfo.state) }}
          </el-tag>
        </div>
        
        <div class="flex items-center gap-2">
          <el-button v-if="canRevoke" type="warning" size="small" @click="handleRevoke">
            <el-icon><RefreshLeft /></el-icon>
            撤回
          </el-button>
          
          <el-button v-if="canCancel" type="danger" size="small" @click="handleCancel">
            <el-icon><Close /></el-icon>
            取消流程
          </el-button>
          
          <el-button v-if="canClaim" type="success" size="small" @click="handleClaim">
            <el-icon><Select /></el-icon>
            签收
          </el-button>
        </div>
      </div>
    </div>

    <!-- 流程信息卡片 -->
    <div class="p-6">
      <!-- 基本信息卡片 -->
      <div class="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-5 mb-6 border border-blue-100">
        <div class="flex items-center gap-4 mb-4">
          <div class="w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center">
            <el-icon size="24" class="text-blue-600"><Document /></el-icon>
          </div>
          <div>
            <h3 class="text-lg font-semibold text-gray-800">{{ processInfo.procDefName }}</h3>
            <p class="text-sm text-gray-600">流程实例ID: {{ processInfo.instanceId }}</p>
          </div>
        </div>
        
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div class="flex items-center gap-2">
            <el-icon class="text-gray-500"><User /></el-icon>
            <span class="text-gray-500">发起人:</span>
            <span class="font-medium">{{ processInfo.startUserName }}</span>
          </div>
          
          <div class="flex items-center gap-2">
            <el-icon class="text-gray-500"><Clock /></el-icon>
            <span class="text-gray-500">发起时间:</span>
            <span class="font-medium">{{ parseTime(processInfo.createTime) }}</span>
          </div>
          
          <div class="flex items-center gap-2">
            <el-icon class="text-gray-500"><Timer /></el-icon>
            <span class="text-gray-500">持续时间:</span>
            <span class="font-medium">{{ calculateDuration(processInfo.createTime, processInfo.endTime) }}</span>
          </div>
        </div>
      </div>

      <!-- 标签页内容 -->
      <el-tabs v-model="activeTab" class="detail-tabs">
        <!-- 任务办理标签页 -->
        <el-tab-pane label="任务办理" name="task" v-if="showTaskTab">
          <div class="bg-white rounded-xl border border-gray-100 p-5">
            <div class="mb-4">
              <h3 class="text-base font-semibold text-gray-800 mb-3">当前任务信息</h3>
              <div class="bg-gray-50 rounded-lg p-4">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                  <div>
                    <span class="text-gray-500">任务名称:</span>
                    <span class="ml-2 font-medium">{{ taskInfo.taskName }}</span>
                  </div>
                  <div>
                    <span class="text-gray-500">任务创建时间:</span>
                    <span class="ml-2 font-medium">{{ parseTime(taskInfo.createTime) }}</span>
                  </div>
                  <div>
                    <span class="text-gray-500">任务负责人:</span>
                    <span class="ml-2 font-medium">{{ taskInfo.assigneeName || '未分配' }}</span>
                  </div>
                  <div>
                    <span class="text-gray-500">优先级:</span>
                    <el-tag :type="getPriorityTagType(taskInfo.priority)" size="small" class="ml-2">
                      {{ getPriorityText(taskInfo.priority) }}
                    </el-tag>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- 表单区域 -->
            <div class="mb-4">
              <h3 class="text-base font-semibold text-gray-800 mb-3">表单信息</h3>
              <div v-if="formLoading" class="py-4 text-center">
                <el-icon class="is-loading"><Loading /></el-icon>
                <span class="ml-2">加载表单中...</span>
              </div>
              <div v-else-if="formData.length === 0" class="py-4 text-center text-gray-500">
                暂无表单数据
              </div>
              <div v-else>
                <el-form :model="formModel" label-width="100px">
                  <el-form-item
                    v-for="field in formData"
                    :key="field.id"
                    :label="field.label"
                    :required="field.required"
                  >
                    <!-- 根据字段类型渲染不同的表单组件 -->
                    <el-input
                      v-if="field.type === 'input'"
                      v-model="formModel[field.id]"
                      :placeholder="field.placeholder"
                      :disabled="field.disabled"
                    />
                    <el-select
                      v-else-if="field.type === 'select'"
                      v-model="formModel[field.id]"
                      :placeholder="field.placeholder"
                      :disabled="field.disabled"
                      style="width: 100%"
                    >
                      <el-option
                        v-for="option in field.options"
                        :key="option.value"
                        :label="option.label"
                        :value="option.value"
                      />
                    </el-select>
                    <el-date-picker
                      v-else-if="field.type === 'date'"
                      v-model="formModel[field.id]"
                      type="date"
                      :placeholder="field.placeholder"
                      :disabled="field.disabled"
                      style="width: 100%"
                    />
                    <el-input
                      v-else-if="field.type === 'textarea'"
                      v-model="formModel[field.id]"
                      type="textarea"
                      :placeholder="field.placeholder"
                      :disabled="field.disabled"
                      :rows="3"
                    />
                  </el-form-item>
                </el-form>
              </div>
            </div>
            
            <!-- 审批意见 -->
            <div class="mb-4">
              <h3 class="text-base font-semibold text-gray-800 mb-3">审批意见</h3>
              <el-input
                v-model="comment"
                type="textarea"
                placeholder="请输入审批意见"
                :rows="3"
              />
            </div>
            
            <!-- 操作按钮 -->
            <div class="flex justify-end gap-3">
              <el-button @click="handleReturn">退回</el-button>
              <el-button @click="handleDelegate">委派</el-button>
              <el-button @click="handleTransfer">转办</el-button>
              <el-button type="primary" @click="handleComplete">通过</el-button>
              <el-button type="danger" @click="handleReject">驳回</el-button>
            </div>
          </div>
        </el-tab-pane>
        
        <!-- 表单信息标签页 -->
        <el-tab-pane label="表单信息" name="form">
          <div class="bg-white rounded-xl border border-gray-100 p-5">
            <div v-if="formLoading" class="py-4 text-center">
              <el-icon class="is-loading"><Loading /></el-icon>
              <span class="ml-2">加载表单中...</span>
            </div>
            <div v-else-if="formData.length === 0" class="py-4 text-center text-gray-500">
              暂无表单数据
            </div>
            <div v-else>
              <el-descriptions :column="2" border>
                <el-descriptions-item
                  v-for="field in formData"
                  :key="field.id"
                  :label="field.label"
                >
                  {{ getFieldValue(field) }}
                </el-descriptions-item>
              </el-descriptions>
            </div>
          </div>
        </el-tab-pane>
        
        <!-- 流转记录标签页 -->
        <el-tab-pane label="流转记录" name="history">
          <div class="bg-white rounded-xl border border-gray-100 p-5">
            <el-timeline>
              <el-timeline-item
                v-for="(record, index) in historyProcNodeList"
                :key="index"
                :timestamp="parseTime(record.createTime)"
                placement="top"
              >
                <div class="bg-gray-50 rounded-lg p-4">
                  <div class="flex items-center justify-between mb-2">
                    <h4 class="font-medium text-gray-800">{{ record.taskName }}</h4>
                    <el-tag :type="getHistoryTagType(record.type)" size="small">
                      {{ getHistoryTypeText(record.type) }}
                    </el-tag>
                  </div>
                  <div class="text-sm text-gray-600">
                    <div class="mb-1">处理人: {{ record.assigneeName || record.startUserName }}</div>
                    <div v-if="record.comment" class="mb-1">处理意见: {{ record.comment }}</div>
                    <div>处理时间: {{ parseTime(record.endTime || record.createTime) }}</div>
                  </div>
                </div>
              </el-timeline-item>
            </el-timeline>
          </div>
        </el-tab-pane>
        
        <!-- 流程跟踪标签页 -->
        <el-tab-pane label="流程跟踪" name="track">
          <div class="bg-white rounded-xl border border-gray-100 p-5">
            <ProcessViewer
              :key="`designer-${loadIndex}`"
              :style="'height:' + height"
              :xml="processXml"
              :finishedInfo="finishedInfo"
              :allCommentList="historyProcNodeList"
            />
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup name="ProcessDetail" lang="js">
import { detailProcess } from "@/api/workflow/work/process";
import { completeTask, returnTask, delegateTask, transferTask, rejectTask, claimTask, revokeProcess } from "@/api/workflow/work/task";
import { parseTime } from "@/utils/ruoyi";
import ProcessViewer from "@/components/ProcessViewer";

const route = useRoute();
const router = useRouter();
const { proxy } = getCurrentInstance();

const instanceId = route.params.instanceId;
const taskId = route.query.taskId;
const processed = route.query.processed === 'true';
const own = route.query.own === 'true';
const copy = route.query.copy === 'true';
const claim = route.query.claim === 'true';

const activeTab = ref('task');
const processInfo = ref({});
const taskInfo = ref({});
const formData = ref([]);
const formModel = ref({});
const comment = ref('');
const loading = ref(false);
const formLoading = ref(false);
const trackLoading = ref(false);
const processXml = ref('');
const historyProcNodeList = ref();
const finishedInfo = ref({});
const loadIndex = ref(0);
const height = ref(document.documentElement.clientHeight - 205 + 'px;');

// 是否显示任务办理标签页
const showTaskTab = computed(() => {
  return !processed && !own && !copy && taskId;
});

// 是否可以撤回
const canRevoke = computed(() => {
  return processed && !own && !copy;
});

// 是否可以取消流程
const canCancel = computed(() => {
  return own && processInfo.value.state === 'running';
});

// 是否可以签收
const canClaim = computed(() => {
  return claim && !taskInfo.value.assignee;
});

// 获取流程详情
const getProcessInfo = async () => {
  loading.value = true;
  try {
    const res = await detailProcess({ procInsId: instanceId });
    processInfo.value = res.data.process;
    taskInfo.value = res.data.task || {};
    
    // 设置默认标签页
    if (!showTaskTab.value) {
      activeTab.value = 'form';
    }
  } catch (error) {
    console.error('获取流程详情失败:', error);
    proxy.$modal.msgError('获取流程详情失败');
  } finally {
    loading.value = false;
  }
};

// 获取表单数据
const getFormData = async () => {
  if (!taskId) return;
  
  formLoading.value = true;
  try {
    // 这里应该调用获取表单数据的API
    // const res = await getTaskFormData(taskId);
    // formData.value = res.data;
    
    // 模拟表单数据
    formData.value = [
      { id: 'title', label: '标题', type: 'input', value: processInfo.value.procDefName, disabled: true },
      { id: 'applicant', label: '申请人', type: 'input', value: processInfo.value.startUserName, disabled: true },
      { id: 'applyTime', label: '申请时间', type: 'date', value: processInfo.value.createTime, disabled: true },
      { id: 'reason', label: '申请原因', type: 'textarea', value: '测试申请原因', disabled: processed || copy },
      { id: 'category', label: '分类', type: 'select', value: '1', disabled: processed || copy, 
        options: [{ label: '分类1', value: '1' }, { label: '分类2', value: '2' }] }
    ];
    
    // 初始化表单模型
    const model = {};
    formData.value.forEach(field => {
      model[field.id] = field.value || '';
    });
    formModel.value = model;
  } catch (error) {
    console.error('获取表单数据失败:', error);
    proxy.$modal.msgError('获取表单数据失败');
  } finally {
    formLoading.value = false;
  }
};

// 获取流程图数据
const getTrackData = async () => {
  trackLoading.value = true;
  try {
    // 使用detailProcess获取流程详情，其中包含bpmnXml数据
    const res = await detailProcess({ procInsId: instanceId });
    processXml.value = res.data.bpmnXml;
    historyProcNodeList.value = res.data.historyProcNodeList;
    finishedInfo.value = res.data.flowViewer;
  } catch (error) {
    console.error('获取流程图数据失败:', error);
    proxy.$modal.msgError('获取流程图数据失败');
  } finally {
    trackLoading.value = false;
  }
};

// 返回上一页
const goBack = () => {
  router.go(-1);
};

// 完成任务
const handleComplete = async () => {
  try {
    await proxy.$modal.confirm('确认要通过该任务吗？');
    const params = {
      taskId: taskId,
      comment: comment.value,
      variables: formModel.value
    };
    const res = await completeTask(params);
    proxy.$modal.msgSuccess(res.msg || "处理成功");
    goBack();
  } catch (error) {
    if (error !== 'cancel') {
      console.error("完成任务失败", error);
      proxy.$modal.msgError('完成任务失败');
    }
  }
};

// 驳回任务
const handleReject = async () => {
  try {
    await proxy.$modal.confirm('确认要驳回该任务吗？');
    const params = {
      taskId: taskId,
      comment: comment.value
    };
    const res = await rejectTask(params);
    proxy.$modal.msgSuccess(res.msg || "驳回成功");
    goBack();
  } catch (error) {
    if (error !== 'cancel') {
      console.error("驳回任务失败", error);
      proxy.$modal.msgError('驳回任务失败');
    }
  }
};

// 退回任务
const handleReturn = async () => {
  try {
    await proxy.$modal.confirm('确认要退回该任务吗？');
    const params = {
      taskId: taskId,
      comment: comment.value
    };
    const res = await returnTask(params);
    proxy.$modal.msgSuccess(res.msg || "退回成功");
    goBack();
  } catch (error) {
    if (error !== 'cancel') {
      console.error("退回任务失败", error);
      proxy.$modal.msgError('退回任务失败');
    }
  }
};

// 委派任务
const handleDelegate = async () => {
  try {
    const { value: userId } = await proxy.$prompt('请输入委派人的用户ID', '委派任务');
    if (!userId) return;
    
    const params = {
      taskId: taskId,
      userId: userId,
      comment: comment.value
    };
    const res = await delegateTask(params);
    proxy.$modal.msgSuccess(res.msg || "委派成功");
    goBack();
  } catch (error) {
    if (error !== 'cancel') {
      console.error("委派任务失败", error);
      proxy.$modal.msgError('委派任务失败');
    }
  }
};

// 转办任务
const handleTransfer = async () => {
  try {
    const { value: userId } = await proxy.$prompt('请输入转办人的用户ID', '转办任务');
    if (!userId) return;
    
    const params = {
      taskId: taskId,
      userId: userId,
      comment: comment.value
    };
    const res = await transferTask(params);
    proxy.$modal.msgSuccess(res.msg || "转办成功");
    goBack();
  } catch (error) {
    if (error !== 'cancel') {
      console.error("转办任务失败", error);
      proxy.$modal.msgError('转办任务失败');
    }
  }
};

// 签收任务
const handleClaim = async () => {
  try {
    await proxy.$modal.confirm('确认要签收该任务吗？');
    const params = {
      taskId: taskId
    };
    const res = await claimTask(params);
    proxy.$modal.msgSuccess(res.msg || "签收成功");
    // 刷新任务信息
    getProcessInfo();
  } catch (error) {
    if (error !== 'cancel') {
      console.error("签收任务失败", error);
      proxy.$modal.msgError('签收任务失败');
    }
  }
};

// 撤回流程
const handleRevoke = async () => {
  try {
    await proxy.$modal.confirm('确认要撤回该流程吗？');
    const params = {
      procInsId: instanceId,
      taskId: taskId
    };
    const res = await revokeProcess(params);
    proxy.$modal.msgSuccess(res.msg || "撤回成功");
    goBack();
  } catch (error) {
    if (error !== 'cancel') {
      console.error("撤回流程失败", error);
      proxy.$modal.msgError('撤回流程失败');
    }
  }
};

// 取消流程
const handleCancel = async () => {
  try {
    await proxy.$modal.confirm('确认要取消该流程吗？取消后将无法恢复。');
    const params = {
      instanceId: instanceId
    };
    const res = await revokeProcess(params);
    proxy.$modal.msgSuccess(res.msg || "取消成功");
    goBack();
  } catch (error) {
    if (error !== 'cancel') {
      console.error("取消流程失败", error);
      proxy.$modal.msgError('取消流程失败');
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

// 获取历史记录类型文本
const getHistoryTypeText = (type) => {
  const typeMap = {
    'start': '开始',
    'approve': '通过',
    'reject': '驳回',
    'return': '退回',
    'delegate': '委派',
    'transfer': '转办',
    'end': '结束'
  };
  return typeMap[type] || type;
};

// 获取历史记录标签类型
const getHistoryTagType = (type) => {
  const typeMap = {
    'start': 'info',
    'approve': 'success',
    'reject': 'danger',
    'return': 'warning',
    'delegate': 'primary',
    'transfer': 'primary',
    'end': 'info'
  };
  return typeMap[type] || 'info';
};

// 获取字段显示值
const getFieldValue = (field) => {
  if (field.type === 'select') {
    const option = field.options?.find(opt => opt.value === field.value);
    return option ? option.label : field.value;
  }
  return field.value;
};

// 计算持续时间
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
  getProcessInfo();
  getFormData();
  getTrackData();
});
</script>

<style lang="scss" scoped>
// 飞书审批详情样式
.detail-tabs {
  :deep(.el-tabs__header) {
    margin-bottom: 20px;
  }
  
  :deep(.el-tabs__nav-wrap) {
    &::after {
      background-color: #f0f0f0;
    }
  }
  
  :deep(.el-tabs__item) {
    font-weight: 500;
    padding: 0 20px;
  }
  
  :deep(.el-tabs__item.is-active) {
    color: #3370ff;
    font-weight: 600;
  }
  
  :deep(.el-tabs__active-bar) {
    background-color: #3370ff;
  }
}

// 时间线样式
:deep(.el-timeline-item__tail) {
  border-left: 2px solid #e4e7ed;
}

:deep(.el-timeline-item__node) {
  background-color: #3370ff;
}

:deep(.el-timeline-item__wrapper) {
  padding-left: 28px;
}
</style>