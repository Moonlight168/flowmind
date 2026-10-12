<template>
 <div class="app-container">
      <div class="search" v-show="showSearch">
        <el-form :model="queryParams" ref="queryFormRef" :inline="true" label-width="70">
          <el-form-item label="流程名称" prop="processName">
            <el-input v-model="queryParams.processName" placeholder="请输入流程名称" clearable style="width: 200px" @keyup.enter="handleQuery" />
          </el-form-item>
          <el-form-item label="流程分类" prop="category">
            <el-select v-model="queryParams.category" clearable placeholder="请选择"  style="width: 240px">
              <el-option v-for="item in categoryOptions" :key="item.categoryId" :label="item.categoryName" :value="item.code" />
            </el-select>
          </el-form-item>
          <el-form-item label="审批时间" style="width: 308px;">
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
          <right-toolbar v-model:showSearch="showSearch" @queryTable="getList"></right-toolbar>
        </el-row>
      </template>

      <el-table v-loading="loading" :data="finishedList">
        <el-table-column type="selection" width="55" align="center" />
        <el-table-column label="任务编号" align="center" prop="taskId" :show-overflow-tooltip="true" />
        <el-table-column label="流程名称" align="center" prop="procDefName" :show-overflow-tooltip="true" />
        <el-table-column label="流程分类" align="center" prop="category" :formatter="categoryFormat" />
        <el-table-column label="任务节点" align="center" prop="taskName" />
        <el-table-column label="流程发起人" align="center" prop="startUserName" />
        <el-table-column label="接收时间" align="center" prop="createTime" width="180" />
        <el-table-column label="审批时间" align="center" prop="finishTime" width="180" />
        <el-table-column label="耗时" align="center" prop="duration" width="180" />
        <el-table-column label="操作" width="180" align="center" class-name="small-padding fixed-width">
          <template #default="scope">
            <el-tooltip content="详情" placement="top">
              <el-button link type="primary" icon="View" @click="handleDetails(scope.row)" v-hasPermi="['workflow:process:query']"></el-button>
            </el-tooltip>
            <el-tooltip content="撤回" placement="top">
              <el-button link type="primary" icon="RefreshLeft" @click="handleRevoke(scope.row)" v-hasPermi="['workflow:process:revoke']"></el-button>
            </el-tooltip>
          </template>
        </el-table-column>
      </el-table>

      <pagination v-show="total > 0" :total="total" v-model:page="queryParams.pageNum" v-model:limit="queryParams.pageSize" @pagination="getList" />
    </el-card>
  </div>
</template>

<script setup name="Finished" lang="js">
import { listFinishedProcess } from "@/api/workflow/work/process";
import { revokeProcess } from "@/api/workflow/work/task";
import { useTaskList } from './useTaskList';

const router = useRouter();
const { proxy } = getCurrentInstance() ;

const {
  rows: finishedList,
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
  fetcher: listFinishedProcess,
  defaultQuery: { processName: '', category: '' }
});

/** 流程流转记录 */
const handleDetails = (row) => {
  router.push({
    path: '/oa/task/process/detail/' + row.procInsId,
    query: {
      processed: false
    }
  })
}
/** 撤回任务 */
const handleRevoke = async (row) => {
  const params = {
    procInsId: row.procInsId,
    taskId: row.taskId
  };
  const res = await revokeProcess(params);
  proxy.$modal.msgSuccess(res.msg);
  getList();
}
</script>
