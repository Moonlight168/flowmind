<template>
  <div class="space-y-4">
    <div v-if="drafts.length === 0" class="text-center py-12">
      <div class="text-6xl mb-4 text-gray-300">
        <el-icon><Document /></el-icon>
      </div>
      <p class="text-gray-500">暂无草稿</p>
    </div>
    
    <div v-else class="space-y-3">
      <div 
        v-for="draft in drafts" 
        :key="draft.draftId"
        class="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow"
      >
        <div class="flex items-start justify-between">
          <div class="flex-1">
            <h4 class="font-medium text-gray-900 mb-1">{{ draft.processName }}</h4>
            <p class="text-sm text-gray-500 mb-2">{{ draft.description }}</p>
            <div class="flex items-center gap-4 text-xs text-gray-400">
              <span>{{ formatDate(draft.createTime) }}</span>
              <span>{{ formatDate(draft.updateTime) }}</span>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <el-button 
              type="primary" 
              size="small"
              @click="handleEditDraft(draft)"
            >
              继续编辑
            </el-button>
            <el-button 
              type="danger" 
              size="small"
              @click="handleDeleteDraft(draft)"
            >
              删除
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Document } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import { delDraft } from '@/api/workflow/work/draft'

// 接收父组件传递的props和emits
const props = defineProps({
  drafts: {
    type: Array,
    required: true
  }
})

const emit = defineEmits(['refresh-drafts'])

const router = useRouter()

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

// 处理编辑草稿
const handleEditDraft = (draft) => {
  router.push({
    path: '/oa/workplace/start/'+draft.deployId,
    query: { 
      definitionId: draft.definitionId,
    }
  })
}

// 处理删除草稿
const handleDeleteDraft = (draft) => {
  ElMessageBox.confirm(
    `确定要删除草稿"${draft.processName}"吗？删除后将无法恢复。`,
    '删除确认',
    {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(() => {
    // 调用删除API
    delDraft(draft.definitionId).then(res => {
      if (res.code === 200) {
        ElMessage.success('删除草稿成功');
        // 通知父组件刷新草稿列表
        emit('refresh-drafts');
      } else {
        ElMessage.error('删除草稿失败：' + (res.msg || '未知错误'));
      }
    }).catch(error => {
      console.error('删除草稿失败:', error);
      ElMessage.error('删除草稿失败，请稍后重试');
    });
  }).catch(() => {
    // 用户取消删除
    ElMessage.info('已取消删除');
  });
}
</script>