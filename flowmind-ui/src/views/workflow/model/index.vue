<template>
 <div class="app-container">
      <div class="search" v-show="showSearch">
        <el-form :model="queryParams" ref="queryFormRef" :inline="true" label-width="70">
          <el-form-item label="模型标识" prop="modelKey">
            <el-input v-model="queryParams.modelKey" placeholder="请输入模型标识" clearable style="width: 200px" @keyup.enter="handleQuery" />
          </el-form-item>
          <el-form-item label="模型名称" prop="modelName">
            <el-input v-model="queryParams.modelName" placeholder="请输入模型名称" clearable style="width: 200px" @keyup.enter="handleQuery" />
          </el-form-item>
          <el-form-item label="流程分类" prop="category">
            <el-select v-model="queryParams.category" clearable placeholder="请选择" @change="handleQuery"  style="width: 240px">
              <el-option
                v-for="item in categoryOptions"
                :key="item.categoryId"
                :label="item.categoryName"
                :value="item.code">
              </el-option>
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" icon="Search" @click="handleQuery">搜索</el-button>
            <el-button icon="Refresh" @click="resetQuery">刷新</el-button>
          </el-form-item>
        </el-form>
      </div>
    <el-card shadow="never">
      <template #header>
        <el-row :gutter="10" class="mb8">
          <el-col :span="1.5">
            <el-button type="primary" plain icon="Plus" @click="handleAdd" v-hasPermi="['workflow:model:add']">新增</el-button>
          </el-col>
          <el-col :span="1.5">
            <el-button type="danger" plain icon="Delete" :disabled="multiple" @click="handleDelete" v-hasPermi="['workflow:model:remove']">删除</el-button>
          </el-col>
          <el-col :span="1.5">
            <el-button type="warning" plain icon="Download" @click="handleExport" v-hasPermi="['workflow:model:export']">导出</el-button>
          </el-col>
          <right-toolbar v-model:showSearch="showSearch" @queryTable="getList"></right-toolbar>
        </el-row>
      </template>

      <el-table v-loading="loading" :data="modelList" @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="55" align="center" />
        <el-table-column label="模型标识" align="center" prop="modelKey" :show-overflow-tooltip="true" />
        <el-table-column label="模型名称" align="center" :show-overflow-tooltip="true">
          <template #default="scope">
            <a class="link-type" @click="handleProcessView(scope.row)">
              <span>{{ scope.row.modelName }}</span>
            </a>
          </template>
        </el-table-column>
        <el-table-column label="流程分类" align="center" prop="categoryName" :formatter="categoryFormat" />
        <el-table-column label="模型版本" align="center">
          <template #default="scope">
            <el-tag size="small">v{{ scope.row.version }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="描述" align="center" prop="description" :show-overflow-tooltip="true" />
        <el-table-column label="创建时间" align="center" prop="createTime" width="180" >
          <template #default="scope">
              {{  parseTime(scope.row.createTime, '{y}-{m}-{d}  {h}:{i}:{s}')}}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" align="center" class-name="small-padding fixed-width">
          <template #default="scope">
            <el-tooltip content="修改" placement="top">
              <el-button link type="primary" icon="Edit" @click="handleUpdate(scope.row)" v-hasPermi="['workflow:model:edit']"></el-button>
            </el-tooltip>
            <el-tooltip content="删除" placement="top">
              <el-button link type="primary" icon="Delete" @click="handleDelete(scope.row)" v-hasPermi="['workflow:model:remove']"></el-button>
            </el-tooltip>
            <el-tooltip content="设计" placement="top">
              <el-button link type="primary" icon="Brush" @click="handleDesigner(scope.row)" v-hasPermi="['workflow:model:designer']"></el-button>
            </el-tooltip>
            <el-tooltip content="部署" placement="top">
              <el-button link type="primary" icon="Promotion" @click="handleDeploy(scope.row)" v-hasPermi="['workflow:model:deploy']"></el-button>
            </el-tooltip>
            <el-tooltip content="历史" placement="top">
              <el-button link type="primary" icon="Discount" @click="handleHistory(scope.row)" v-hasPermi="['workflow:model:list']"></el-button>
            </el-tooltip>
          </template>
        </el-table-column>
      </el-table>

      <pagination v-show="total > 0" :total="total" v-model:page="queryParams.pageNum" v-model:limit="queryParams.pageSize" @pagination="getList" />
    </el-card>

    <!--  添加或修改模型信息对话框  -->
    <el-dialog :title="dialog.title" v-model="dialog.visible" width="500px" append-to-body>
      <el-form ref="modelFormRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="模型标识" prop="modelKey">
          <el-input v-model="form.modelKey" clearable disabled placeholder="请输入模型标识" />
        </el-form-item>
        <el-form-item label="模型名称" prop="modelName">
          <el-input v-model="form.modelName" clearable :disabled="form.modelId !== undefined" placeholder="请输入模型名称" />
        </el-form-item>
        <el-form-item label="流程分类" prop="category">
          <el-select v-model="form.category" placeholder="请选择" clearable style="width:100%">
            <el-option v-for="item in categoryOptions" :key="item.categoryId" :label="item.categoryName" :value="item.code" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="form.description" type="textarea" placeholder="请输入内容" maxlength="200" show-word-limit />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button type="warning" plain icon="MagicStick" @click="handleAiDesignBasic">AI 设计</el-button>
          <el-button type="primary" @click="submitForm">确 定</el-button>
          <el-button @click="cancel">取 消</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 基础信息 AI 设计对话框 -->
    <AiDesignDialog
      ref="aiDesignBasicDialogRef"
      v-model="aiDesignBasicVisible"
      designType="flow"
      mode="basic"
      :formData="form"
      @fill="handleAiFillBasic"
    />

    <el-dialog :title="designer.title" v-model="designer.visible" append-to-body fullscreen>
      <ProcessDesigner
        :key="`designer-${reloadIndex}`"
        ref="modelDesignerRef"
        v-loading="designerLoading"
        :designer-form="designerForm"
        :bpmn-xml="bpmnXml"
        @save="onSaveDesigner"
      >
        <template #custom-buttons>
          <el-button :size="'default'" :type="'primary'" icon="MagicStick" @click="handleAiDesign">AI 设计</el-button>
        </template>
      </ProcessDesigner>
    </el-dialog>

    <!-- AI 设计对话框 -->
    <AiDesignDialog
      ref="aiDesignDialogRef"
      v-model="aiDesignVisible"
      designType="flow"
      mode="design"
      :formData="designerFlowInfo"
      @fill="handleAiFill"
    />

    <el-dialog :title="history.title" v-model="history.visible" append-to-body>
      <el-table v-loading="historyLoading" :data="historyList" @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="55" align="center" />
        <el-table-column label="模型标识" align="center" prop="modelKey" :show-overflow-tooltip="true" />
        <el-table-column label="模型名称" align="center" prop="modelName" :show-overflow-tooltip="true" />
        <el-table-column label="流程分类" align="center" prop="categoryName" :formatter="categoryFormat" />
        <el-table-column label="模型版本" align="center">
          <template #default="scope">
            <el-tag>v{{ scope.row.version }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="描述" align="center" prop="description" :show-overflow-tooltip="true" />
        <el-table-column label="创建时间" align="center" prop="createTime" width="180" />
        <el-table-column label="操作" width="180" align="center" class-name="small-padding fixed-width">
          <template #default="scope">
            <el-tooltip content="部署" placement="top">
              <el-button link type="primary" icon="Promotion" @click="handleDeploy(scope.row)" v-hasPermi="['workflow:model:deploy']"></el-button>
            </el-tooltip>
            <el-tooltip content="设为最新" placement="top">
              <el-button link type="primary" icon="Star" @click="handleLatest(scope.row)" v-hasPermi="['workflow:model:save']"></el-button>
            </el-tooltip>
          </template>
        </el-table-column>
      </el-table>

      <pagination v-show="total > 0" :total="total" v-model:page="queryParams.pageNum" v-model:limit="queryParams.pageSize" @pagination="getList" />
    </el-dialog>

    <!-- 流程图 -->
    <el-dialog :title="processDialog.title" v-model="processDialog.visible" width="70%">
      <ProcessViewer :key="`designer-${reloadIndex}`" :xml="processXml" :style="{height: '650px'}" />
    </el-dialog>
  </div>
</template>

<script setup name="Model" lang="js">
import { getBpmnXml, listModel, historyModel, latestModel, addModel, updateModel, saveModel, delModel, deployModel, getModel } from "@/api/workflow/model";
import { listAllCategory } from "@/api/workflow/category";
import ProcessDesigner from "@/components/ProcessDesigner";
import ProcessViewer from "@/components/ProcessViewer";
import { useAiSessionStore } from '@/store/modules/aiSession';
import AiDesignDialog from "@/components/AiDesignDialog/index.vue";
import useUserStore from "@/store/modules/user";

const { proxy } = getCurrentInstance() ;

const modelList = ref([]);
const loading = ref(true);
const showSearch = ref(true);
const ids = ref([]);
const single = ref(true);
const multiple = ref(true);
const total = ref(0);
const categoryOptions = ref([]);
const designerLoading = ref(true);
const bpmnXml = ref('');
const reloadIndex = ref(0);
const processXml = ref("");

const historyList = ref([]);
const historyLoading = ref(true);
const historyTotal = ref(0);

const modelFormRef = ref();
const queryFormRef = ref();
const modelDesignerRef = ref(null)
const aiDesignVisible = ref(false);
const aiDesignDialogRef = ref();
const aiDesignBasicVisible = ref(false);
const aiDesignBasicDialogRef = ref();
const designerFlowInfo = ref({});

const dialog = reactive({
  visible: false,
  title: ''
});

const processDialog = reactive({
  visible: false,
  title: '流程图'
});

const designer = reactive({
  visible: false,
  title: ''
});

const history = reactive({
  visible: false,
  title: ''
});

const initFormData={
  modelId: undefined,
  modelKey: `Process_${new Date().getTime()}`,
  modelName: `业务流程_${new Date().getTime()}`,
  category: '',
  description: '',
  formType: undefined,
  formId: undefined,
  bpmnXml: '',
  newVersion: false
}

const data = reactive({
  form: {...initFormData},
  queryParams: {
    pageNum: 1,
    pageSize: 10,
    modelKey: '',
    modelName: '',
    category: ''
  },
  rules: {
    modelKey: [{ required: true, message: "岗位名称不能为空", trigger: "blur" }],
    modelName: [{ required: true, message: "岗位编码不能为空", trigger: "blur" }],
  }
});

const designerForm = reactive({
  modelId: '',
  form: {
    processName: '',
    processKey: ''
  }
});

const { queryParams, form, rules } = toRefs(data);

const router = useRouter();
const aiSession = useAiSessionStore();
const userStore = useUserStore();

/** 查询模型列表 */
const getList = async () => {
  loading.value = true;
  const res = await listModel(queryParams.value);
  modelList.value = res.rows;
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
  modelFormRef.value.resetFields();
}
/** 搜索按钮操作 */
const handleQuery = () => {
  queryParams.value.pageNum = 1;
  getList();
}
/** 重置按钮操作 */
const resetQuery = () => {
  queryFormRef.value.resetFields();
  handleQuery();
}
/** 多选框选中数据 */
const handleSelectionChange = (selection) => {
  ids.value = selection.map(item => item.modelId);
  single.value = selection.length != 1;
  multiple.value = !selection.length;
}
/** 新增按钮操作 */
const handleAdd = () => {
  dialog.visible = true;
  dialog.title = "添加模型";
  nextTick(() => {
    reset();
  })
}
/** 修改按钮操作 */
const handleUpdate = async (row) => {
  dialog.visible = true;
  dialog.title = "修改模型";
  nextTick(async () => {
    reset();
    const modelId = row.modelId || ids.value[0];
    const res = await getModel(modelId);
    form.value = res.data;
  });
};
/** 删除按钮操作 */
const handleDelete = async (row) => {
  const modelIds = row.modelId || ids.value;
  await proxy?.$modal.confirm('是否确认删除参数编号为"' + modelIds + '"的数据项？');
  await delModel(modelIds);
  getList();
  proxy?.$modal.msgSuccess("删除成功");
}
/** 导出按钮操作 */
const handleExport = () => {
  proxy?.download("flowable/model/export", {
    ...queryParams.value
  }, `model_${new Date().getTime()}.xlsx`);
}
/** 查看流程图 */
const handleProcessView = async (row) => {
  reloadIndex.value++;
  // 发送请求，获取 xml
  const res = await getBpmnXml(row.modelId);
  processXml.value = res.data;
  processDialog.visible = true;
}
/** 设计按钮操作 */
const handleDesigner = async (row) => {
  reloadIndex.value++;
  designerForm.modelId = row.modelId;
  // 设置设计器表单信息
  designerForm.form.processName = row.modelName || '';
  designerForm.form.processKey = row.modelKey || '';
  const res = await getBpmnXml(row.modelId);
  bpmnXml.value = res.data || '';
  designerFlowInfo.value = {
    modelId: row.modelId,
    modelName: row.modelName,
    modelKey: row.modelKey,
    category: row.category,
    description: row.description || ''
  };
  designerLoading.value = false;
  designer.title = "流程设计 - " + row.modelName;
  designer.visible = true;
}
const handleDeploy = (row) => {
  loading.value = true;
  nextTick(async () => {
    await deployModel({ modelId: row?.modelId });
    proxy.$modal.msgSuccess("操作成功");
    router.push({
      name: 'Deploy',
      path: '/workflow/deploy'
    });
    loading.value = false;
  });
}
const handleLatest = async (row) => {
  await proxy.$modal.confirm('是否将此模型保存为新版本？');
  historyLoading.value = true;
  await latestModel({modelId: row.modelId});
  history.visible = false;
  getList();
  proxy?.$modal.msgSuccess("操作成功");
  historyLoading.value = false;
}
/** 查询历史列表 */
const getHistoryList = async () => {
  historyLoading.value = true;
  const res = await historyModel(queryParams.value);
  historyList.value = res.rows;
  historyTotal.value = res.total;
  historyLoading.value = false;
}
const handleHistory = (row) => {
  history.visible = true;
  history.title = "模型历史";
  queryParams.value.modelKey = row?.modelKey;
  getHistoryList();
}
/** 提交表单操作 */
const submitForm = async () => {
  modelFormRef.value.validate(async (valid) => {
    if (valid) {
      // 普通模式：直接保存模型
      form.value.modelId ? await updateModel(form.value) : await addModel(form.value);
      proxy.$modal.msgSuccess("操作成功");
      dialog.visible = false;
      getList();
    }
  })
}
/** 查询流程分类列表 */
const getCategoryList = async () => {
  const res = await listAllCategory();
  categoryOptions.value = res.data;
}

const onSaveDesigner = async (str) => {
  bpmnXml.value = str;

  // 检查是否为新模型（AI 生成的流程）
  if (!designerForm.modelId) {
    // 新模型，先弹出表单让用户填写模型信息
    dialog.visible = true;
    dialog.title = "新增模型";
    form.value = {
      ...initFormData,
      modelName: designerForm.form.processName || '新流程',
      modelKey: designerForm.form.processKey || `Process_${new Date().getTime()}`
    };
    return;
  }

  // 已有模型，直接询问是否保存为新版本
  let dataBody = {
    modelId: designerForm.modelId,
    bpmnXml: str
  }
  proxy.$modal.confirm('是否将此模型保存为新版本？').then(() => {
    confirmSave(dataBody, true)
  }).catch(action => {
    if (action === 'cancel') {
      confirmSave(dataBody, false)
    }
  })
}
const confirmSave = async (body, newVersion) => {
  designerLoading.value = true;
  console.log(body,"body");
  try {
    await saveModel(Object.assign(body, { newVersion: newVersion }));
    getList();
    proxy.$modal.msgSuccess("保存成功");
    designerLoading.value = false;
    designer.visible = false;
  } catch (error) {
    designerLoading.value = false;
    // 保存失败时不关闭设计器，不刷新页面
  }
}

const categoryFormat = (row) => {
  var category = categoryOptions.value.find(function(k) {
        return k.code === row.category;
    });
    return category ? category.categoryName : '';
}

/** 基础信息表单 AI 设计按钮 */
const handleAiDesignBasic = () => {
  aiDesignBasicVisible.value = true;
};

/** 基础信息表单 AI 填充 */
const handleAiFillBasic = (data) => {
  if (!data) return;
  if (data.flow_name) {
    form.value.modelName = data.flow_name;
  }
  if (data.code) {
    form.value.category = data.code;
  }
  if (data.description) {
    form.value.description = data.description;
  }
};

/** 可视化设计 AI 设计按钮 */
const handleAiDesign = async () => {
  // 从设计器获取最新的 BPMN XML（包括未保存的修改）
  if (modelDesignerRef.value) {
    const latestXml = await modelDesignerRef.value.getCurrentXml();
    if (latestXml) {
      bpmnXml.value = latestXml;
    }
  }
  // 同步流程基本信息到 designerFlowInfo
  designerFlowInfo.value = {
    ...designerFlowInfo.value,
    modelId: designerForm.modelId,
    modelName: designerForm.form.processName || designerFlowInfo.value.modelName || '',
    modelKey: designerForm.form.processKey || designerFlowInfo.value.modelKey || '',
    category: designerFlowInfo.value.category || '',
    description: designerFlowInfo.value.description || '',
    bpmnXml: bpmnXml.value,
  };
  // 等待 Vue 更新后再打开弹窗
  await nextTick();
  aiDesignVisible.value = true;
};

/** 可视化设计 AI 填充 */
const handleAiFill = (data) => {
  if (!data) return;
  // 填充 BPMN XML 到设计器
  if (data.bpmn_xml && data.bpmn_xml.trim()) {
    bpmnXml.value = data.bpmn_xml;
  }
  // 填充流程基本信息
  if (data.flow_name) {
    designerForm.form.processName = data.flow_name;
  }
  if (data.flow_key) {
    designerForm.form.processKey = data.flow_key;
  }
};

// 监听基础信息对话框关闭，清空 AI 聊天和后端 checkpoint
watch(() => dialog.visible, (val) => {
  if (!val) {
    aiDesignBasicDialogRef.value?.clearMessages();
  }
});

// 监听设计器关闭，清空 AI 聊天和后端 checkpoint
watch(() => designer.visible, (val) => {
  if (!val) {
    aiDesignDialogRef.value?.clearMessages();
  }
});

onMounted(async () => {
  getCategoryList()
  getList();

  // 恢复 AI 会话历史（如有）
  if (aiSession.hasActiveSession) {
    const chatHistory = await aiSession.restoreSession()
    if (chatHistory) {
      console.log('AI 会话已恢复，历史消息数:', chatHistory.length)
    }
  }
});
</script>

<style lang="scss" scoped>
.el-dialog__body {
  max-height: calc(100vh) !important;
  overflow-y: auto;
  overflow-x: hidden;
}
</style>
