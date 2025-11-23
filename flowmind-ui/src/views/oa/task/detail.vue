<template>
  <div class="max-w-5xl mx-auto bg-white rounded-xl shadow-sm border border-gray-100 min-h-[80vh] flex flex-col">
    <div class="h-12 border-b border-gray-100 flex items-center px-4">
      <button @click="$router.back()" class="flex items-center text-sm text-gray-500 hover:text-blue-600 transition">
        <el-icon class="mr-1"><ArrowLeft /></el-icon> 返回
      </button>
      <div class="ml-4 h-4 w-px bg-gray-200"></div>
      <span class="ml-4 text-sm font-bold text-gray-800">流程处理</span>
    </div>

    <div class="p-6 flex-1">
      <div class="text-center py-10">
        <el-alert type="info" show-icon :closable="false">
          <template #title>
            <div class="font-bold text-base">开发提示</div>
          </template>
          <template #default>
            <div class="mt-2 text-sm">
              为了完整显示表单，请在 <b>src/views/oa/task/detail.vue</b> 中引入原有的 Flowable 表单组件。<br/>
              通常位于 <code>src/components/Process/Form</code> 或 <code>src/views/flowable/task/todo/detail</code>。
              <br/><br/>
              当前接收到的参数：
              <pre class="bg-gray-100 p-2 rounded mt-2 text-left">{{ $route.query }}</pre>
            </div>
          </template>
        </el-alert>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRoute } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'

const route = useRoute()
// const deployId = route.query.deployId
// const taskId = route.query.taskId
</script>