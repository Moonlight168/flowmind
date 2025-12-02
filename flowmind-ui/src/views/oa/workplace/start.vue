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
          </div>
        </div>
      </template>
      <div class="form-conf" v-if="dialog.visible">
        <v-form-render :form-json="formModel" :form-data="formData" ref="vfRenderRef"></v-form-render>
        <div class="cu-submit">
          <el-button type="primary" @click="confirmSubmit">提交</el-button>
          <el-button type="warning" @click="confirmReset">重置</el-button>
          <el-button  @click="saveDraft">保存草稿</el-button>
          <el-button type="warning" @click="confirmCancel">取消</el-button>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup name="WorkStart" lang="js">
import { getProcessForm, startProcess } from '@/api/workflow/work/process.js';
import { saveDraft as saveDraftApi, getDraftByDefId, getDraft } from '@/api/workflow/work/draft.js';
import { ElMessage, ElMessageBox } from 'element-plus';
import { EditPen, Clock, Refresh } from '@element-plus/icons-vue';


const route = useRoute();
const { proxy } = getCurrentInstance() ;

const vfRenderRef = ref(null);

const deployId = ref();
const definitionId = ref();
const formModel = ref({});
const formData = ref({}); // 初始化为空对象

// 草稿相关变量
const draftId = ref(null);
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
        // 解析formModel和formData，后端返回的是JSON字符串
        formModel.value = JSON.parse(draftRes.data.formModel || '{}');
        formData.value = JSON.parse(draftRes.data.formData || '{}');
      } else {
        logger.error('获取草稿数据失败');
        return;
      }
    } catch (error) {
      logger.error('获取草稿数据失败:', error);
      return;
    }
  } else {
    // 正常流程初始化
    try {
      const res = await getProcessForm({ definitionId: definitionId.value, deployId: deployId.value });
      formModel.value = res.data.formModel;

      // 检查是否有远程草稿数据
      try {
        const draftRes = await getDraftByDefId(definitionId.value);
        if (draftRes.code === 200 && draftRes.data) {
          draftId.value = draftRes.data.draftId;
          // 解析formData，后端返回的是JSON字符串
          formData.value = JSON.parse(draftRes.data.formData || '{}');
        }
      } catch (error) {
        logger.error('获取远程草稿失败:', error);
      }
    } catch (error) {
      logger.error('获取流程表单失败:', error);
      return;
    }
  }

  dialog.visible = true;
  nextTick(async () => {
    vfRenderRef.value.setFormJson(formModel.value || {formConfig: {}, widgetList: []});
    // 设置表单数据，确保即使formData为空对象也要设置
    vfRenderRef.value.setFormData(formData.value || {});
  });
}

const submit = async () => {
  // 提交时需要验证表单数据
  const data = await vfRenderRef.value.getFormData(true);
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

// 保存草稿
const saveDraft = async () => {
  try {
    // 先验证必填字段
    const currentFormData = await vfRenderRef.value.getFormData(true);
    
    // 准备草稿数据
    const draftData = {
      definitionId: definitionId.value,
      deployId: deployId.value,
      formModel: JSON.stringify(formModel.value),
      formData: JSON.stringify(currentFormData)
    };
    
    // 如果已有草稿ID，则更新草稿
    if (draftId.value) {
      draftData.draftId = draftId.value;
    }
    
    // 保存草稿 - 调用API函数
    const res = await saveDraftApi(draftData);
    if (res.code === 200) {
      // 更新草稿ID
      if (res.data && res.data.draftId) {
        draftId.value = res.data.draftId;
      }
      ElMessage.info('保存草稿成功');
    } else {
      ElMessage.info('保存草稿失败');
    }
  } catch (error) {
    console.error('保存草稿失败:', error);
    // 如果有必填字段未填写，显示提示信息
    if (error && error.includes('表单数据校验失败')) {
      ElMessage.warning('请填写所有必填字段后再保存草稿');
    }
  }
};

// 保存草稿并退出
const saveDraftAndExit = async () => {
  // 先保存草稿
  await saveDraft();
  
  // 保存成功后退出
  setTimeout(() => {
    proxy.$router.push('/oa/workplace');
  }, 100);
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
    '确定要取消编辑吗？',
    '取消确认',
    {
      confirmButtonText: '保存并退出',
      cancelButtonText: '仅退出',
      type: 'warning',
      distinguishCancelAndClose: true,
      closeOnClickModal: false,
      closeOnPressEscape: false
    }
  ).then(() => {
    // 保存并退出
    saveDraftAndExit();
  }).catch(action => {
    if (action === 'cancel') {
      // 仅退出
      proxy.$router.push('/oa/workplace');
    } else {
      // 继续编辑（点击关闭按钮或其他情况）
      // 不执行任何操作，留在当前页面
    }
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