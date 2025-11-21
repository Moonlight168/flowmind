<template>
 <div class="app-container">
    <!-- 查询条件 -->
      <div v-show="showSearch" class="search">
        <el-form ref="queryFormRef" :inline="true" :model="queryParams" label-width="120">
          <el-form-item label="监听类型" prop="listenerType">
            <el-select v-model="queryParams.listenerType" clearable placeholder="请选择监听类型" @change="handleQuery">
              <el-option v-for="dict in sys_listener_type" :key="dict.value" :label="dict.label" :value="dict.value" />
            </el-select>
          </el-form-item>
          <el-form-item label="名称" prop="name">
            <el-input v-model="queryParams.name" clearable placeholder="请输入名称" @keyup.enter="handleQuery" />
          </el-form-item>
          <el-form-item label="事件类型" prop="eventType">
            <el-select v-model="queryParams.eventType" clearable placeholder="请选择事件类型" @change="handleQuery">
              <el-option
                v-for="dict in sys_task_listener_event_type"
                v-if="queryParams.listenerType === 'task'"
                :key="dict.value"
                :label="dict.label"
                :value="dict.value"
              />
              <el-option
                v-for="dict in sys_execution_listener_event_type"
                v-if="queryParams.listenerType === 'execution'"
                :key="dict.value"
                :label="dict.label"
                :value="dict.value"
              />
              <el-option
                v-for="dict in sys_task_listener_event_type"
                v-if="!queryParams.listenerType"
                :key="dict.value"
                :label="dict.label"
                :value="dict.value"
              />
              <el-option
                v-for="dict in sys_execution_listener_event_type"
                v-if="!queryParams.listenerType"
                :key="dict.value"
                :label="dict.label"
                :value="dict.value"
              />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button icon="Search" type="primary" @click="handleQuery">搜索</el-button>
            <el-button icon="Refresh" @click="resetQuery">重置</el-button>
          </el-form-item>
        </el-form>
      </div>

    <el-card shadow="never">
      <template #header>
        <!-- 操作按钮 -->
        <el-row :gutter="10" class="mb8">
          <el-col :span="1.5">
            <el-button v-hasPermi="['workflow:listener:add']" icon="Plus" plain type="primary" @click="handleAdd">新增</el-button>
          </el-col>
          <el-col :span="1.5">
            <el-button v-hasPermi="['workflow:listener:edit']" :disabled="single" icon="Edit" plain type="success" @click="handleUpdate()"
              >修改</el-button
            >
          </el-col>
          <el-col :span="1.5">
            <el-button v-hasPermi="['workflow:listener:remove']" :disabled="multiple" icon="Delete" plain type="danger" @click="handleDelete()"
              >删除</el-button
            >
          </el-col>
          <el-col :span="1.5">
            <el-button v-hasPermi="['workflow:listener:export']" icon="Download" plain type="warning" @click="handleExport">导出</el-button>
          </el-col>
          <right-toolbar v-model:showSearch="showSearch" @queryTable="getList"></right-toolbar>
        </el-row>
      </template>

      <!-- 分页列表 -->
      <el-table
        v-loading="tableLoading"
        :data="listenerList"
        @selection-change="handleSelectionChange"
        v-fixTableHeight
        highlight-current-row
        show-overflow-tooltip
      >
        <el-table-column align="center" type="selection" width="55" />
        <el-table-column type="expand" width="50px">
          <template #default="props">
            <el-table :data="props.row.fields" width="60%">
              <el-table-column v-if="false" label="主键" prop="id" />
              <el-table-column label="字段名称" prop="fieldName" />
              <el-table-column label="字段类型" prop="fieldType">
                <template #default="scope">
                  <dict-tag :options="sys_listener_field_type" :value="scope.row.fieldType" />
                </template>
              </el-table-column>
              <el-table-column label="字段值" prop="fieldValue" />
              <el-table-column align="center" class-name="small-padding fixed-width" label="操作">
                <template #default="scope">
                  <el-tooltip content="修改" placement="top">
                    <el-button
                      v-hasPermi="['workflow:listener:edit']"
                      icon="Edit"
                      link
                      type="primary"
                      @click="handleFieldUpdate(scope.row)"
                    ></el-button>
                  </el-tooltip>
                  <el-tooltip content="删除" placement="top">
                    <el-button
                      v-hasPermi="['workflow:listener:remove']"
                      icon="Delete"
                      link
                      type="danger"
                      @click="handleFieldDelete(scope.row)"
                    ></el-button>
                  </el-tooltip>
                </template>
              </el-table-column>
            </el-table>
          </template>
        </el-table-column>
        <el-table-column v-if="false" align="center" label="主键" prop="id" />
        <el-table-column align="center" label="监听类型" prop="listenerType">
          <template #default="scope">
            <dict-tag :options="sys_listener_type" :value="scope.row.listenerType" />
          </template>
        </el-table-column>
        <el-table-column align="center" label="名称" prop="name" />
        <el-table-column align="center" label="值类型" prop="valueType">
          <template #default="scope">
            <dict-tag :options="sys_listener_value_type" :value="scope.row.valueType" />
          </template>
        </el-table-column>
        <el-table-column align="center" label="值" prop="value" />
        <el-table-column align="center" label="事件类型" prop="eventType">
          <template #default="scope">
            <dict-tag v-if="scope.row.listenerType === 'task'" :options="sys_task_listener_event_type" :value="scope.row.eventType" />
            <dict-tag v-if="scope.row.listenerType === 'execution'" :options="sys_execution_listener_event_type" :value="scope.row.eventType" />
          </template>
        </el-table-column>
        <el-table-column align="center" class-name="small-padding fixed-width" label="操作">
          <template #default="scope">
            <el-tooltip content="添加字段" placement="top">
              <el-button v-hasPermi="['workflow:listener:edit']" icon="Plus" link type="primary" @click="addField(scope.row)"></el-button>
            </el-tooltip>
            <el-tooltip content="修改" placement="top">
              <el-button v-hasPermi="['workflow:listener:edit']" icon="Edit" link type="primary" @click="handleUpdate(scope.row)"></el-button>
            </el-tooltip>
            <el-tooltip content="删除" placement="top">
              <el-button v-hasPermi="['workflow:listener:remove']" icon="Delete" link type="danger" @click="handleDelete(scope.row)"></el-button>
            </el-tooltip>
          </template>
        </el-table-column>
      </el-table>
      <pagination v-show="total > 0" v-model:limit="queryParams.pageSize" v-model:page="queryParams.pageNum" :total="total" @pagination="getList" />
    </el-card>

    <!-- 添加或修改流程表单对话框 -->
    <el-dialog v-model="dialog.visible" :close-on-click-modal="false" :title="dialog.title" append-to-body width="600px">
      <el-form ref="listenerFormRef" v-loading="formLoading" :model="form" :rules="rules" label-width="120px">
        <el-form-item label="监听类型" prop="listenerType">
          <el-radio-group v-model="form.listenerType">
            <el-radio v-for="dict in sys_listener_type" :key="dict.value" :label="dict.value">{{ dict.label }}</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入名称" />
        </el-form-item>
        <el-form-item label="值类型" prop="valueType">
          <el-radio-group v-model="form.valueType">
            <el-radio v-for="dict in sys_listener_value_type" :key="dict.value" :label="dict.value">{{ dict.label }}</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="值" prop="value">
          <el-input v-model="form.value" placeholder="请输入值" />
        </el-form-item>
        <el-form-item label="事件类型" prop="eventType">
          <el-select v-model="form.eventType" clearable placeholder="请选择事件类型" style="width: 100%">
            <el-option
              v-for="dict in sys_task_listener_event_type"
              v-if="form.listenerType === 'task'"
              :key="dict.value"
              :label="dict.label"
              :value="dict.value"
            />
            <el-option
              v-for="dict in sys_execution_listener_event_type"
              v-if="form.listenerType === 'execution'"
              :key="dict.value"
              :label="dict.label"
              :value="dict.value"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button type="primary" @click="submitForm">确 定</el-button>
          <el-button @click="cancel">取 消</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 监听器字段对话框 -->
    <el-dialog v-model="fieldDialog.visible" :close-on-click-modal="false" :title="fieldDialog.title" append-to-body width="600px">
      <el-form ref="listenerFieldFormRef" v-loading="fieldFormLoading" :model="initFieldFormData" :rules="filedRules" label-width="120px">
        <el-form-item label="名称" prop="fieldName">
          <el-input v-model="filedForm.fieldName" placeholder="请输入名称" />
        </el-form-item>
        <el-form-item label="字段类型" prop="fieldType">
          <el-radio-group v-model="filedForm.fieldType">
            <el-radio v-for="dict in sys_listener_field_type" :key="dict.value" :label="dict.value">{{ dict.label }}</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="值" prop="fieldValue">
          <el-input v-model="filedForm.fieldValue" placeholder="请输入值" />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button type="primary" @click="submitFieldForm">确 定</el-button>
          <el-button @click="cancel">取 消</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script  name="Form" setup>
getList();

import {
  addListener,
  deleteListenerFieldAPI,
  delListener,
  getListener,
  insertListenerFieldAPI,
  queryListenerPage,
  updateListener,
  updateListenerFieldAPI
} from "@/api/workflow/listener";



const { proxy } = getCurrentInstance() ;
const {
  sys_listener_type,
  sys_listener_value_type,
  sys_task_listener_event_type,
  sys_execution_listener_event_type,
  sys_listener_field_type
} = proxy.useDict("sys_listener_type", "sys_listener_value_type", "sys_task_listener_event_type", "sys_execution_listener_event_type", "sys_listener_field_type");

const listenerList = ref([]);
const showSearch = ref(true);
const ids = ref([]);
const names = ref([]);
const single = ref(true);
const multiple = ref(true);
const total = ref(0);
const tableLoading = ref(false);
const formLoading = ref(false);
const fieldFormLoading = ref(false);
const listenerFormRef = ref();
const listenerFieldFormRef = ref();
const queryFormRef = ref();
const listenerId = ref('');

const dialog = reactive({
  visible: false,
  title: ''
});

const fieldDialog = reactive({
  visible: false,
  title: ''
});
const initFormData = {
  id: undefined,
  valueType: '',
  eventType: '',
  listenerType: '',
  name: '',
  value: ''
}

const data = reactive({
  form: {...initFormData},
  queryParams: {
    pageNum: 1,
    pageSize: 10,
    name: '',
    listenerType: '',
    eventType: ''
  },
  rules: {
    listenerType: [{ required: true, message: "监听类型不能为空", trigger: "blur" }],
    name: [{ required: true, message: "名称不能为空", trigger: "blur" }],
    valueType: [{ required: true, message: "值类型不能为空", trigger: "blur" }],
    value: [{ required: true, message: "值不能为空", trigger: "blur" }]
  }
});

const { queryParams, form, rules } = toRefs(data);

const initFieldFormData={
  id: undefined,
  listenerId: undefined,
  fieldName: undefined,
  fieldType: undefined,
  fieldValue: undefined
}

const filedData = reactive({
  filedForm: {...initFieldFormData},
  filedRules: {
    fieldName: [{ required: true, message: "请输入字段名称", trigger: "blur" }],
    fieldType: [{ required: true, message: "请选择字段类型", trigger: "blur" }]
  }
})

const { filedForm, filedRules } = toRefs(filedData);

/** 查询列表 */
const getList = async () => {
  tableLoading.value = true;
  const res = await queryListenerPage(queryParams.value);
  listenerList.value = res.rows;
  total.value = res.total;
  tableLoading.value = false;
}
/** 取消按钮 */
const cancel = () => {
  reset();
  dialog.visible = false;
  fieldDialog.visible = false;
}
/** 表单重置 */
const reset = () => {
  form.value = {...initFormData};
  filedForm.value = {...initFieldFormData};
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
  ids.value = selection.map(item => item.id);
  names.value = selection.map(item => item.name);
  single.value = selection.length != 1;
  multiple.value = !selection.length;
}
/** 新增表单操作 */
const handleAdd = () => {
  dialog.visible = true;
  nextTick(() => {
    reset();
  })
}
/** 修改表单操作 */
const handleUpdate = (row) => {
  dialog.visible = true;
  const id = row?.id || ids.value[0];
  nextTick(async () => {
    formLoading.value = true;
    reset();
    const res = await getListener(id);
    formLoading.value = false;
    form.value = res.data;
  })
}
/** 提交表单操作 */
const submitForm = () => {
  listenerFormRef.value.validate(async (valid) => {
    if (valid) {
      dialog.visible = true;
      formLoading.value = true;
      try {
        form.value.id ? await updateListener(form.value) : await addListener(form.value);
      } finally {
        formLoading.value = false;
      }
      dialog.visible = false;
      proxy?.$modal.msgSuccess("操作成功");
      getList();
    }
  });
}
/** 删除按钮操作 */
const handleDelete = async (row) => {
  const listenerIds = row?.id || ids.value;
  const listenerNames = row?.name || ids.value;
  await proxy?.$modal.confirm('是否确认删除【' + listenerNames + '】的数据项？');
  tableLoading.value = true;
  try {
    await delListener(listenerIds);
  } finally {
    tableLoading.value = false;
  }
  getList();
  proxy?.$modal.msgSuccess("删除成功");
}
/** 添加字段操作 */
const addField = (ro) => {
  fieldDialog.visible = true;
  // listenerField.value = row.fields;
  listenerId.value = row.id;
  nextTick(() => {
    reset();
    filedForm.value.listenerId = row.id;
  })
}
/** 修改字段操作 */
const handleFieldUpdate = (row) => {
  fieldDialog.visible = true;
  filedForm.value.id = row.id;
  filedForm.value.listenerId = row.listenerId;
  filedForm.value.fieldName = row.fieldName;
  filedForm.value.fieldType = row.fieldType;
  filedForm.value.fieldValue = row.fieldValue;
}
/** 提交字段表单操作 */
const submitFieldForm = () => {
  listenerFieldFormRef.value.validate(async (vali) => {
    if (valid) {
      fieldDialog.visible = true;
      fieldFormLoading.value = true;
      try {
        filedForm.value.id ? await updateListenerFieldAPI(filedForm.value) : await insertListenerFieldAPI(filedForm.value);
      } finally {
        fieldFormLoading.value = false;
      }
      listenerId.value = '';
      fieldDialog.visible = false;
      proxy.$modal.msgSuccess("操作成功");
      getList();
    }
  });
}
/** 删除字段按钮操作 */
const handleFieldDelete = async (ro) => {
  const fieldIds = row?.id || ids.value;
  const fieldNames = row?.fieldName || ids.value;
  await proxy?.$modal.confirm('是否确认删除【' + fieldNames + '】的数据项？');
  tableLoading.value = true;
  try {
    await deleteListenerFieldAPI(fieldIds);
  } finally {
    tableLoading.value = false;
  }
  getList();
  proxy?.$modal.msgSuccess("删除成功");
}
/** 导出按钮操作 */
const handleExport = () => {
  proxy?.download("workflow/form/export", {
    ...queryParams.value
  }, `form_${new Date().getTime()}.xlsx`);
}

</script>
