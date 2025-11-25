<template>
  <div class="app-container">
    <el-card class="box-card">
      <template #header>
        <div class="flex justify-between items-center">
          <span>发起流程</span>
          <div class="flex items-center text-sm text-gray-500">
            <span v-if="isFromDraft" class="mr-4 text-orange-500">
              <el-icon><EditPen /></el-icon>
              从草稿恢复
            </span>
            <span v-if="lastSaveTime" class="mr-4">
              <el-icon><Clock /></el-icon>
              上次保存: {{ formatTime(lastSaveTime) }}
            </span>
            <span v-if="autoSaveTimer" class="text-green-500">
              <el-icon><Refresh /></el-icon>
              自动保存已开启
            </span>
          </div>
        </div>
      </template>
      <div class="form-conf" v-if="dialog.visible">
        <v-form-render :form-json="formModel" :form-data="formData" ref="vfRenderRef"></v-form-render>
        <div class="cu-submit">
          <el-button type="primary" @click="confirmSubmit">提交</el-button>
          <el-button type="warning" @click="confirmReset">重置</el-button>
          <el-button  @click="saveDraftAndExit">保存草稿并退出</el-button>
          <el-button type="warning" @click="confirmCancel">取消</el-button>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup name="WorkStart" lang="js">
import { getProcessForm, startProcess } from '@/api/workflow/work/process.js';
import { saveDraft, updateDraft, getDraftByDefId } from '@/api/workflow/work/draft.js';
import { ElMessage, ElMessageBox } from 'element-plus';
import { EditPen, Clock, Refresh } from '@element-plus/icons-vue';


const route = useRoute();
const { proxy } = getCurrentInstance() ;

const vfRenderRef = ref(null);

const deployId = ref();
const definitionId = ref();
const formModel = ref({});
const formData = ref({});

// 草稿相关变量
const draftId = ref(null);
const autoSaveTimer = ref(null);
const lastSaveTime = ref(null);
const isFromDraft = ref(false);

const dialog = reactive({
  visible: false,
  title: ''
});

const initData = async () => {
  deployId.value = route.params && route.params.deployId;
  definitionId.value = route.query && route.query.definitionId;
  
  // 检查是否从草稿恢复
  if (route.query && route.query.draftId) {
    isFromDraft.value = true;
    draftId.value = route.query.draftId;
    // 从草稿恢复数据
    try {
      const draftRes = await getDraft(draftId.value);
      if (draftRes.code === 200 && draftRes.data) {
        formModel.value = draftRes.data.formModel;
        formData.value = draftRes.data.formData || {};
      } else {
        ElMessage.error('获取草稿数据失败');
        return;
      }
    } catch (error) {
      console.error('获取草稿数据失败:', error);
      ElMessage.error('获取草稿数据失败');
      return;
    }
  } else {
    // 正常流程初始化
    try {
      const res = await getProcessForm({ definitionId: definitionId.value, deployId: deployId.value });
      formModel.value = res.data.formModel;
    } catch (error) {
      console.error('获取流程表单失败:', error);
      ElMessage.error('获取流程表单失败');
      return;
    }
    
    // 没有草稿ID，检查是否已有草稿
    try {
      const draftRes = await getDraftByDefId(definitionId.value);
      if (draftRes.code === 200 && draftRes.data) {
        draftId.value = draftRes.data.draftId;
        formData.value = draftRes.data.formData || {};
        ElMessage.info('检测到已有草稿，已自动恢复');
      }
    } catch (error) {
      console.error('检查草稿失败:', error);
    }
  }
  
  dialog.visible = true;
  nextTick(async () => {
    vfRenderRef.value.setFormJson(formModel.value || {formConfig: {}, widgetList: []});
    // 设置表单数据
    if (formData.value && Object.keys(formData.value).length > 0) {
      vfRenderRef.value.setFormData(formData.value);
    }
    
    // 启动自动保存
    startAutoSave();
  });
}

const submit = async () => {
  const data = await vfRenderRef.value.getFormData();
  if (definitionId.value) {
    const res = await startProcess(definitionId.value, JSON.stringify(data));
    proxy.$modal.msgSuccess(res.msg);
    // const obj = { path: "/work/own" };
    // proxy?.$tab.closeOpenPage(obj);
    proxy.$tab.closePage();
    proxy.$router.back();
  }
}

const reset = () => {
  vfRenderRef.value.resetForm();
}

// 自动保存功能
const startAutoSave = () => {
  // 清除之前的定时器
  if (autoSaveTimer.value) {
    clearInterval(autoSaveTimer.value);
  }
  
  // 每30秒自动保存一次
  autoSaveTimer.value = setInterval(() => {
    saveDraftData();
  }, 30000);
}

// 保存草稿数据
const saveDraftData = async () => {
  if (!vfRenderRef.value) return;
  
  try {
    // 获取当前表单数据，即使有验证错误也获取
    let currentFormData = {};
    try {
      currentFormData = await vfRenderRef.value.getFormData();
    } catch (error) {
      console.warn('获取表单数据时遇到验证错误，但仍将保存部分数据:', error);
      // 尝试获取表单数据，忽略验证错误
      try {
        currentFormData = await vfRenderRef.value.getFormData(true); // 传递参数跳过验证
      } catch (e) {
        // 如果还是失败，使用空对象
        currentFormData = {};
      }
    }
    
    // 检查表单数据是否有变化
    const hasChanges = JSON.stringify(currentFormData) !== JSON.stringify(formData.value);
    
    if (!hasChanges) return; // 没有变化则不保存
    
    const draftData = {
      definitionId: definitionId.value,
      deployId: deployId.value,
      formModel: formModel.value,
      formData: currentFormData,
      processName: formModel.value?.formConfig?.modelName || '未命名流程'
    };
    
    let res;
    if (draftId.value) {
      // 更新现有草稿
      draftData.id = draftId.value;
      res = await updateDraft(draftData);
    } else {
      // 创建新草稿
      res = await saveDraft(draftData);
      if (res.code === 200 && res.data) {
        draftId.value = res.data;
      }
    }
    
    if (res.code === 200) {
      formData.value = currentFormData; // 更新保存的数据
      lastSaveTime.value = new Date();
      // 如果返回了草稿ID，更新本地draftId
      if (res.data && !draftId.value) {
        draftId.value = res.data;
      }
      console.log('草稿自动保存成功');
    }
  } catch (error) {
    console.error('自动保存草稿失败:', error);
  }
}

// 组件卸载时清除定时器
onBeforeUnmount(() => {
  if (autoSaveTimer.value) {
    clearInterval(autoSaveTimer.value);
  }
});

// 格式化时间
const formatTime = (time) => {
  if (!time) return '';
  const date = new Date(time);
  return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}:${date.getSeconds().toString().padStart(2, '0')}`;
}

// 保存草稿并退出
const saveDraftAndExit = async () => {
  if (!vfRenderRef.value) return;
  
  try {
    // 获取当前表单数据，即使有验证错误也获取
    let currentFormData = {};
    try {
      currentFormData = await vfRenderRef.value.getFormData();
    } catch (error) {
      console.warn('获取表单数据时遇到验证错误，但仍将保存部分数据:', error);
      // 尝试获取表单数据，忽略验证错误
      try {
        currentFormData = await vfRenderRef.value.getFormData(true); // 传递参数跳过验证
      } catch (e) {
        // 如果还是失败，使用空对象
        currentFormData = {};
      }
    }
    
    const draftData = {
      definitionId: definitionId.value,
      deployId: deployId.value,
      formModel: formModel.value,
      formData: currentFormData,
      processName: formModel.value?.formConfig?.modelName || '未命名流程'
    };
    
    let res;
    if (draftId.value) {
      // 更新现有草稿
      draftData.id = draftId.value;
      res = await updateDraft(draftData);
    } else {
      // 创建新草稿
      res = await saveDraft(draftData);
      if (res.code === 200 && res.data) {
        draftId.value = res.data;
      }
    }
    
    if (res.code === 200) {
      ElMessage.success('草稿保存成功');
      // 返回工作台
      proxy.$router.push('/oa/workplace');
    } else {
      ElMessage.error('草稿保存失败: ' + (res.msg || '未知错误'));
    }
  } catch (error) {
    console.error('保存草稿失败:', error);
    ElMessage.error('保存草稿失败: ' + (error.message || '网络错误'));
  }
}

// 确认提交
const confirmSubmit = () => {
  ElMessageBox.confirm(
    '确定要提交当前流程吗？提交后将无法修改。',
    '提交确认',
    {
      confirmButtonText: '确定提交',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(() => {
    submit();
  }).catch(() => {
    // 用户取消提交
  });
}

// 确认重置
const confirmReset = () => {
  ElMessageBox.confirm(
    '确定要重置表单吗？所有已填写的数据将被清空。',
    '重置确认',
    {
      confirmButtonText: '确定重置',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(() => {
    reset();
  }).catch(() => {
    // 用户取消重置
  });
}

// 确认取消
const confirmCancel = () => {
  ElMessageBox.confirm(
    '确定要取消编辑吗？未保存的修改将会丢失。',
    '取消确认',
    {
      confirmButtonText: '确定取消',
      cancelButtonText: '继续编辑',
      type: 'warning',
    }
  ).then(() => {
    // 返回工作台
    proxy.$router.push('/oa/workplace');
  }).catch(() => {
    // 用户取消操作
  });
}

onMounted(() => {
  initData();
});
</script>

<style lang="scss" scoped>
.form-conf {
  margin: 15px auto;
  width: 80%;
  padding: 15px;
}
</style>
