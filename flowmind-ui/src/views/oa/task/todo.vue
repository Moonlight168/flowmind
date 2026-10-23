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
          <el-form-item label="接收时间" style="width: 308px;">
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

      <el-table v-loading="loading" :data="todoList">
        <el-table-column type="selection" width="55" align="center" />
        <el-table-column min-width="180" label="任务编号" align="center" prop="taskId" :show-overflow-tooltip="true" />
        <el-table-column show-overflow-tooltip min-width="200" label="流程名称" align="center" prop="procDefName" />
        <el-table-column show-overflow-tooltip min-width="160" label="任务节点" align="center" prop="taskName" />
        <el-table-column show-overflow-tooltip min-width="120" label="流程分类" align="center" prop="category" :formatter="categoryFormat" />
        <el-table-column min-width="100" label="流程版本" align="center">
          <template #default="scope">
            <el-tag>v{{scope.row.procDefVersion}}</el-tag>
          </template>
        </el-table-column>
        <el-table-column show-overflow-tooltip min-width="120" label="流程发起人" align="center" prop="startUserName" />
        <el-table-column show-overflow-tooltip label="接收时间" align="center" prop="createTime" width="180" />
        <el-table-column fixed="right" label="操作" width="180" align="center" class-name="small-padding fixed-width">
          <template #default="scope">
            <el-tooltip content="办理" placement="top">
              <el-button link type="primary" icon="EditPen" @click="handleProcess(scope.row)" v-hasPermi="['workflow:process:approval']"></el-button>
            </el-tooltip>
          </template>
        </el-table-column>
      </el-table>

      <pagination v-show="total > 0" :total="total" v-model:page="queryParams.pageNum" v-model:limit="queryParams.pageSize" @pagination="getList" />
    </el-card>
  </div>
</template>

<script setup name="Todo" lang="js">
import { listTodoProcess } from '@/api/workflow/work/process';
import { useTaskList } from './useTaskList';

const router = useRouter();

const {
  rows: todoList,
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
  fetcher: listTodoProcess,
  defaultQuery: { processName: '', category: '' }
});

/** 跳转到处理页面 */
const handleProcess = (row) => {
  router.push({
    path: '/oa/task/process/detail/' + row.procInsId,
    query: {
      taskId: row.taskId,
      processed: true
    }
  })
}
</script>
