<template>
 <div class="app-container">
      <div class="search" v-show="showSearch">
        <el-form :model="queryParams" ref="queryFormRef" :inline="true" label-width="70">
          <el-form-item label="表单名称" prop="formName">
            <el-input v-model="queryParams.formName" placeholder="请输入表单名称" clearable @keyup.enter="handleQuery" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" icon="Search" @click="handleQuery">搜索</el-button>
            <el-button icon="Refresh" @click="resetQuery">重置</el-button>
          </el-form-item>
        </el-form>
      </div>
    <el-card shadow="never">
      <template #header>
        <el-row :gutter="10" class="mb8">
          <el-col :span="1.5">
            <el-button type="primary" plain icon="Plus" @click="handleAdd" v-hasPermi="['workflow:form:add']">新增</el-button>
          </el-col>
          <el-col :span="1.5">
            <el-button type="success" plain icon="Edit" :disabled="single" @click="handleUpdate()" v-hasPermi="['workflow:form:edit']">修改</el-button>
          </el-col>
          <el-col :span="1.5">
            <el-button type="danger" plain icon="Delete" :disabled="multiple" @click="handleDelete()" v-hasPermi="['workflow:form:remove']">删除</el-button>
          </el-col>
          <right-toolbar v-model:showSearch="showSearch" @queryTable="getList"></right-toolbar>
        </el-row>
      </template>

      <el-table v-loading="loading" :data="formList" @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="55" align="center" />
        <el-table-column label="表单主键" align="center" prop="formId" v-if="false" />
        <el-table-column label="表单名称" align="center" prop="formName" />
        <el-table-column label="备注" align="center" prop="remark" />
        <el-table-column label="操作" align="center" class-name="small-padding fixed-width">
          <template #default="scope">
            <el-tooltip content="详情" placement="top">
              <el-button link type="primary" icon="View" @click="handleDetail(scope.row)" v-hasPermi="['workflow:form:query']"></el-button>
            </el-tooltip>
            <el-tooltip content="修改" placement="top">
              <el-button link type="primary" icon="Edit" @click="handleUpdate(scope.row)" v-hasPermi="['workflow:form:edit']"></el-button>
            </el-tooltip>
            <el-tooltip content="删除" placement="top">
              <el-button link type="primary" icon="Delete" @click="handleDelete(scope.row)" v-hasPermi="['workflow:form:remove']"></el-button>
            </el-tooltip>
          </template>
        </el-table-column>
      </el-table>
      <pagination v-show="total > 0" :total="total" v-model:page="queryParams.pageNum" v-model:limit="queryParams.pageSize" @pagination="getList" />
    </el-card>

    <!-- 流程表单设计器对话框 -->
    <el-dialog
      v-model="designer.visible"
      fullscreen
      @opened="handleDesignerOpened"
      @closed="handleDesignerClosed"
    >
      <template #header>
        <div class="designer-dialog-header">
          <span class="designer-dialog-title">{{ designer.title }}</span>
        </div>
      </template>
      <div id="form-designer" class="ai-designer-wrap">
        <v-form-designer
          ref="vfDesignerRef"
          :resetFormJson="true"
          :designer-config="designerConfig"
          v-if="designer.visible"
          :global-dsv="{}"
        >
        </v-form-designer>
        <!-- 与 vform3 工具栏（PC/Pad/H5）同一行，位置由脚本按该行实际几何算 -->
        <div class="ai-designer-actions" :style="actionsStyle">
          <el-button type="primary" plain @click="handleAiDesign">AI 设计</el-button>
          <el-button type="success" plain :disabled="Boolean(aiPreviewData)" @click="dialog.visible = true">保存</el-button>
        </div>
        <div v-if="aiDesigning" class="ai-design-mask">
          <div class="ai-design-mask-spinner"></div>
          <div class="ai-design-mask-text">{{ aiDesignProgress || 'AI 正在生成…' }}</div>
        </div>
      </div>
    </el-dialog>

    <!-- AI 设计对话框 -->
    <AiChatWindow
      ref="aiDesignDialogRef"
      v-model="aiDesignVisible"
      designType="form"
      :formData="form"
      :get-current-baseline="getCurrentBaseline"
      @preview="handleAiPreview"
      @discard="discardAiPreview"
      @fill="handleAiFill"
      @designing="onAiDesigning"
      @progress="onAiProgress"
    />

    <!-- 预览表单对话框 -->
    <el-dialog :title="render.title" v-model="render.visible" width="60%" append-to-body>
      <v-form-render :form-json="{}" :form-data="{}" ref="vfRenderRef" />
    </el-dialog>

    <!-- 添加或修改流程表单对话框 -->
    <el-dialog :title="dialog.title" v-model="dialog.visible" width="600px" append-to-body>
      <el-form ref="formFormRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="表单名称" prop="formName">
          <el-input v-model="form.formName" placeholder="请输入表单名称" />
        </el-form-item>
        <el-form-item label="备注" prop="remark">
          <el-input v-model="form.remark" placeholder="请输入备注" />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button type="primary" @click="submitForm">确 定</el-button>
          <el-button @click="cancel">取 消</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup name="Form" >
import { listForm, addForm, updateForm, getForm, delForm } from "@/api/workflow/form";
import AiChatWindow from "@/components/AiChatWindow/index.vue";
import useUserStore from "@/store/modules/user";
import { watch, onUnmounted } from 'vue';

const { proxy } = getCurrentInstance();

const formList = ref([]);
const loading = ref(true);
const showSearch = ref(true);
const ids = ref([]);
const single = ref(true);
const multiple = ref(true);
const total = ref(0);

const vfDesignerRef = ref(null);
const vfRenderRef = ref(null);
const formFormRef = ref();
const queryFormRef = ref();

const designerConfig = reactive({
  externalLink: false,
  toolbarMaxWidth: 800,
  formTemplates: false,
})
const designer = reactive({
  visible: false,
  title: ''
})
const aiDesignVisible = ref(false);
const aiPreviewData = ref(null);
const aiDesignDialogRef = ref();
const aiDesigning = ref(false);
const aiDesignProgress = ref('');
const userStore = useUserStore();
const render = reactive({
  visible: false,
  title: ''
})
const dialog = reactive({
  visible: false,
  title: ''
});

const initFormData = {
  formId: undefined,
  formName: '',
  content: '',
  remark: ''
}
const data = reactive({
  form: {...initFormData},
  queryParams: {
    pageNum: 1,
    pageSize: 10,
    formName: ''
  },
  rules: {
    formName: [{ required: true, message: "表单名称不能为空", trigger: "blur" }]
  }
});

const { queryParams, form, rules } = toRefs(data);

/** 查询岗位列表 */
const getList = async () => {
  loading.value = true;
  const res = await listForm(queryParams.value);
  formList.value = res.rows;
  total.value = res.total;
  loading.value = false;
}
/** 取消按钮 */
const cancel = () => {
  reset();
  dialog.visible = false;
}
/** 表单重置 */
const reset = () => {
  form.value = {...initFormData};
}
/** 搜索按钮操作 */
const handleQuery = () => {
  queryParams.value.pageNum = 1;
  getList();
}
/** 重置按钮操作 */
const resetQuery = () => {
  if (queryFormRef.value) {
    queryFormRef.value.resetFields();
  }
  handleQuery();
}
/** 多选框选中数据 */
const handleSelectionChange = (selection) => {
  ids.value = selection.map(item => item.formId);
  single.value = selection.length != 1;
  multiple.value = !selection.length;
}
/** 新增表单操作 */
const handleAdd = () => {
  designer.visible = true;
  nextTick(() => {
    reset();
    if (vfDesignerRef.value && vfDesignerRef.value.clearDesigner) {
      vfDesignerRef.value.clearDesigner();
    } else {
      console.warn('v-form-designer component is not ready yet');
      setTimeout(() => {
        if (vfDesignerRef.value && vfDesignerRef.value.clearDesigner) {
          vfDesignerRef.value.clearDesigner();
        }
      }, 500);
    }
  })
}
/** 修改表单操作 */
const handleUpdate = (row) => {
  designer.visible = true;
  nextTick(async () => {
    try {
      const formId = row?.formId || ids.value[0];
      const res = await getForm(formId);
      form.value = res.data;

      if (vfDesignerRef.value && vfDesignerRef.value.setFormJson) {
        vfDesignerRef.value.setFormJson(form.value.content);
      } else {
        console.warn('v-form-designer component is not ready yet');
        setTimeout(() => {
          if (vfDesignerRef.value && vfDesignerRef.value.setFormJson) {
            vfDesignerRef.value.setFormJson(form.value.content);
          }
        }, 500);
      }
    } catch (error) {
      console.error('Failed to update form:', error);
    }
  })
}
/** 查看表单操作 */
const handleDetail = (row) => {
  render.visible = true;
  render.title = '查看表单详情';
  nextTick(async () => {
    if (vfRenderRef.value && vfRenderRef.value.setFormJson) {
      vfRenderRef.value.setFormJson(row.content || {formConfig: {}, widgetList: []});
    } else {
      console.warn('v-form-render component is not ready yet');
      setTimeout(() => {
        if (vfRenderRef.value && vfRenderRef.value.setFormJson) {
          vfRenderRef.value.setFormJson(row.content || {formConfig: {}, widgetList: []});
        }
      }, 500);
    }
  });
}
/** 提交表单操作 */
const submitForm = () => {
  if (!vfDesignerRef.value || !vfDesignerRef.value.getFormJson) {
    console.error('v-form-designer component is not available');
    return;
  }

  const formJson = vfDesignerRef.value.getFormJson();
  form.value.content = JSON.stringify(formJson);
  nextTick(async () => {
    form.value.formId ? await updateForm(form.value) : await addForm(form.value);
    proxy?.$modal.msgSuccess("操作成功");
    // 设计已落定，本轮 AI 会话结束：清前端记录与后端 checkpoint
    aiDesignDialogRef.value?.clearMessages();
    dialog.visible = false;
    designer.visible = false;
    getList();
  })
}
/** 删除按钮操作 */
const handleDelete = async (row) => {
  const formIds = row?.formId || ids.value;
  await proxy?.$modal.confirm('是否确认删除表单编号为"' + formIds + '"的数据项？');
  await delForm(formIds);
  getList();
  proxy?.$modal.msgSuccess("删除成功");
}

/** AI 浮窗每轮发送前调用的最新基线：表单设计器当前 JSON + 表单信息 */
const getCurrentBaseline = () => {
  if (vfDesignerRef.value && vfDesignerRef.value.getFormJson) {
    const formJson = vfDesignerRef.value.getFormJson();
    if (formJson && Object.keys(formJson).length > 0) {
      form.value.content = JSON.stringify(formJson);
    }
  }
  return { ...form.value };
};

/** AI 设计按钮：同步设计器最新数据后打开浮窗 */
const handleAiDesign = () => {
  getCurrentBaseline();
  aiDesignVisible.value = true;
};

/** AI 填充表单（兼容后端蛇形与版本快照的驼峰字段） */
const handleAiFill = (data) => {
  // data 是 form_data（完整 VForm3 JSON + form_name）
  if (!data) return;

  // 更新表单名称
  const formName = data.form_name || data.formName;
  if (formName) {
    form.value.formName = formName;
  }

  // 提取 VForm3 需要的核心字段，存储到 form.value.content
  const formJson = {
    widgetList: data.widgetList || [],
    formConfig: data.formConfig || {}
  };
  form.value.content = JSON.stringify(formJson);

  // 加载到设计器（如设计器已挂载）
  if (vfDesignerRef.value?.setFormJson) {
    vfDesignerRef.value.setFormJson(formJson);
  }
  aiPreviewData.value = null;
};

const handleAiPreview = (data) => {
  aiPreviewData.value = data;
  const formJson = {
    widgetList: data?.widgetList || [],
    formConfig: data?.formConfig || {}
  };
  vfDesignerRef.value?.setFormJson?.(formJson);
};

const discardAiPreview = () => {
  if (!aiPreviewData.value) return;
  if (vfDesignerRef.value?.setFormJson) {
    const baseline = form.value.content
      ? JSON.parse(form.value.content)
      : { widgetList: [], formConfig: {} };
    vfDesignerRef.value.setFormJson(baseline);
  }
  aiPreviewData.value = null;
};

/** AI 生成状态：开始/结束 */
const onAiDesigning = (val) => {
  aiDesigning.value = val;
  if (val) aiDesignProgress.value = '';
};

/** AI 阶段进度文案 */
const onAiProgress = (msg) => {
  aiDesignProgress.value = msg;
};

/** 把 AI 设计/保存 对齐到 vform3 工具栏那一行的最右侧。
 *
 *  vform3 的 `.toolbar-container` 里两个子元素都是 float，右侧那组会换行，
 *  导致容器比肉眼所见的一行要高 —— 按它垂直居中会把按钮压到行以下（实测症状）。
 *  所以：垂直位置与行高取 `.left-toolbar`（PC/Pad/H5 所在的那一行），
 *  水平右边界取 `.toolbar-container` 的右边缘。 */
const actionsStyle = ref({});
const positionDesignerActions = () => {
  const wrap = document.getElementById('form-designer');
  const row = wrap?.querySelector('.left-toolbar');
  const container = wrap?.querySelector('.toolbar-container');
  if (!wrap || !row || !container) return;
  const wrapRect = wrap.getBoundingClientRect();
  const rowRect = row.getBoundingClientRect();
  const containerRect = container.getBoundingClientRect();
  actionsStyle.value = {
    top: `${rowRect.top - wrapRect.top}px`,
    height: `${rowRect.height}px`,
    right: `${Math.max(0, wrapRect.right - containerRect.right + 12)}px`
  };
};

/** 表单设计器打开后 */
const handleDesignerOpened = () => {
  // Dialog 完全打开后的回调，确保 DOM 已渲染
  nextTick(positionDesignerActions);
  window.addEventListener('resize', positionDesignerActions);
};

/** 表单设计器关闭后 */
const handleDesignerClosed = () => {
  window.removeEventListener('resize', positionDesignerActions);
};

// 页面卸载时兜底移除监听（设计器未走关闭流程时也要清）
onUnmounted(() => {
  window.removeEventListener('resize', positionDesignerActions);
});

// 监听设计器关闭：只收掉 AI 浮窗，会话保留（保存时才清）
watch(() => designer.visible, (val) => {
  if (!val) {
    aiDesignVisible.value = false;
    aiDesigning.value = false;
    aiDesignProgress.value = '';
  }
});

getList();
</script>

<style lang="scss" scoped>
#form-designer {
  .main-container {
    margin: 0;
  }
  label {
    font-weight: normal;
  }
  :deep(.external-link) {
    display: flex;
    align-items: center;
  }

  /* 覆盖 VForm 3 组件库中的高度样式 */
  :deep(.widget-collapse .el-collapse-item__content ul .container-widget-item),
  :deep(.widget-collapse .el-collapse-item__content ul .field-widget-item) {
    height: auto !important;
  }

  /* 修复字段操作按钮显示问题 */
  :deep(.field-action), :deep(.container-action) {
    display: flex !important;
    align-items: center;
    justify-content: center;
    opacity: 1 !important;
    visibility: visible !important;

    i {
      display: inline-flex !important;
      align-items: center;
      justify-content: center;
      width: 20px;
      height: 20px;
      margin: 0 2px;
      cursor: pointer;
      border-radius: 2px;

      &:hover {
        background-color: rgba(64, 158, 255, 0.1);
        color: #409eff;
      }
    }
  }

  /* 确保拖拽手柄正确显示 */
  :deep(.drag-handler) {
    display: flex !important;
    align-items: center;
    opacity: 1 !important;
    visibility: visible !important;

    i {
      display: inline-flex !important;
      align-items: center;
      justify-content: center;
    }
  }
}

.ai-designer-wrap {
  position: relative;
  min-height: 60vh;
}

.designer-dialog-header {
  display: flex;
  align-items: center;
  padding-right: 8px;
}

.designer-dialog-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

/* vform3 工具栏行内部是 float 布局，不要改它的排版（会把它自己裁掉的按钮露出来）。
   按钮单独用绝对定位对齐到该行的右侧，top/height 由脚本按行实际位置算 */
.ai-designer-actions {
  position: absolute;
  display: flex;
  align-items: center;
  gap: 8px;
  z-index: 10;
  line-height: 1;
}

.ai-design-mask {
  position: absolute;
  inset: 0;
  z-index: 10;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(2px);
  color: #3b82f6;
  font-size: 14px;
}

.ai-design-mask-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(59, 130, 246, 0.2);
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: ai-design-spin 0.9s linear infinite;
}

@keyframes ai-design-spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
