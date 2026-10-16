<template>
 <div class="app-container">
      <div class="search" v-show="showSearch">
        <el-form :model="queryParams" ref="queryFormRef" :inline="true" label-width="70">
          <el-form-item label="流程标识" prop="processKey">
            <el-input v-model="queryParams.processKey" placeholder="请输入流程标识" clearable style="width: 200px" @keyup.enter="handleQuery" />
          </el-form-item>
          <el-form-item label="流程名称" prop="processName">
            <el-input v-model="queryParams.processName" placeholder="请输入流程名称" clearable style="width: 200px" @keyup.enter="handleQuery" />
          </el-form-item>
          <el-form-item label="流程分类" prop="category">
            <el-select v-model="queryParams.category" clearable placeholder="流程分类"  style="width: 240px">
              <el-option v-for="item in categoryOptions" :key="item.categoryId" :label="item.categoryName" :value="item.code" />
            </el-select>
          </el-form-item>
          <el-form-item label="提交时间" style="width: 308px;">
            <el-date-picker
              v-model="dateRange"
              value-format="YYYY-MM-DD"
              type="daterange"
              range-separator="-"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
            ></el-date-picker>
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
            <el-button type="danger" plain icon="Delete" :disabled="multiple" @click="handleDelete()" v-hasPermi="['workflow:process:remove']">
              删除
            </el-button>
          </el-col>
          <right-toolbar v-model:showSearch="showSearch" @queryTable="getList"></right-toolbar>
        </el-row>
      </template>

      <el-table v-loading="loading" :data="ownProcessList" @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="55" align="center" />
        <el-table-column min-width="180" label="流程编号" align="center" prop="procInsId" :show-overflow-tooltip="true" />
        <el-table-column min-width="200" label="流程名称" align="center" prop="procDefName" :show-overflow-tooltip="true" />
        <el-table-column show-overflow-tooltip min-width="120" label="流程类别" align="center" prop="category" :formatter="categoryFormat" />
        <el-table-column label="流程版本" align="center" width="100">
          <template #default="scope">
            <el-tag>v{{ scope.row.procDefVersion }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column show-overflow-tooltip min-width="160" label="当前节点" align="center" prop="taskName" />
        <el-table-column show-overflow-tooltip label="提交时间" align="center" prop="createTime" width="180" />
        <el-table-column label="流程状态" align="center" width="100">
          <template #default="scope">
            <dict-tag :options="wf_process_status" :value="scope.row.processStatus" />
          </template>
        </el-table-column>
        <el-table-column show-overflow-tooltip label="耗时" align="center" prop="duration" width="180" />
        <el-table-column fixed="right" label="操作" width="180" align="center" class-name="small-padding fixed-width">
          <template #default="scope">
            <el-tooltip content="详情" placement="top">
              <el-button link type="primary" icon="View" @click="handleDetails(scope.row)" v-hasPermi="['workflow:process:query']"></el-button>
            </el-tooltip>
            <el-tooltip content="取消" placement="top">
              <el-button link type="primary" icon="CircleClose" @click="handleStop(scope.row)" v-hasPermi="['workflow:process:cancel']"></el-button>
            </el-tooltip>
            <el-tooltip content="删除" placement="top">
              <el-button link type="primary" icon="Delete" @click="handleDelete(scope.row)" v-hasPermi="['workflow:process:remove']"></el-button>
            </el-tooltip>
          </template>
        </el-table-column>
      </el-table>

      <pagination v-show="total > 0" :total="total" v-model:page="queryParams.pageNum" v-model:limit="queryParams.pageSize" @pagination="getList" />
    </el-card>
  </div>
</template>

<script setup name="Own" lang="js">
import { listOwnProcess, stopProcess, delProcess } from "@/api/workflow/work/process";
import { useTaskList } from './useTaskList';

const router = useRouter();
const { proxy } = getCurrentInstance() ;
const { wf_process_status } = proxy.useDict("wf_process_status");

const {
  rows: ownProcessList,
  loading,
  showSearch,
  total,
  dateRange,
  queryFormRef,
  categoryOptions,
  queryParams,
  getList,
  handleQuery,
  resetQuery,
  categoryFormat
} = useTaskList({
  fetcher: listOwnProcess,
  defaultQuery: { processKey: '', processName: '', category: '' }
});

// 多选态：工具栏的删除按钮靠 multiple 决定是否可用
const ids = ref([]);
const multiple = ref(true);

/** 多选框选中数据 */
const handleSelectionChange = (selection) => {
  ids.value = selection.map(item => item.procInsId);
  multiple.value = !selection.length;
}
/** 流程详情 */
const handleDetails = (row) => {
  router.push({
    path: '/oa/task/process/detail/' + row.procInsId,
    query: {
      processed: false
    }
  })
}
/** 取消流程申请 */
const handleStop = async (row) => {
  await stopProcess( { procInsId: row.procInsId });
  proxy?.$modal.msgSuccess("操作成功");
  getList();
}
/** 删除按钮操作 */
const handleDelete = async (row) => {
  const procInsIds = row?.procInsId || ids.value;
  await proxy.$modal.confirm('是否确认删除流程定义编号为"' + procInsIds + '"的数据项?');
  await delProcess(procInsIds);
  getList();
  proxy.$modal.msgSuccess("删除成功");
}
</script>
