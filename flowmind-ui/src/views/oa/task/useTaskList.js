/**
 * OA 任务列表的公共逻辑。
 *
 * 待办 / 已办 / 抄送 / 待签收 / 我的流程五个页面只有接口、查询字段和表格列不同，
 * 脚本部分逐字相同，抽到这里。各页模板保持原样，避免动到版式。
 */
import { getCurrentInstance, onMounted, ref } from 'vue'

import { listAllCategory } from '@/api/workflow/category'
import useOaCounts from '@/store/modules/oaCounts'

export function useTaskList({
  fetcher,
  defaultQuery = {},
  // 抄送页没有日期筛选，且直接传 queryParams（不包 addDateRange）
  hasDateRange = true,
  // 抄送页的分类字段是 categoryId，其余页面是 category
  categoryField = 'category'
}) {
  const { proxy } = getCurrentInstance()
  const counts = useOaCounts()

  const rows = ref([])
  const loading = ref(true)
  const showSearch = ref(true)
  const total = ref(0)
  const dateRange = ref(['', ''])
  const queryFormRef = ref()
  const categoryOptions = ref([])
  const queryParams = ref({ pageNum: 1, pageSize: 10, ...defaultQuery })

  const getList = async () => {
    loading.value = true
    try {
      const params = hasDateRange
        ? proxy.addDateRange(queryParams.value, dateRange.value)
        : queryParams.value
      const res = await fetcher(params)
      rows.value = res.rows
      total.value = res.total
      counts.refresh()
    } finally {
      loading.value = false
    }
  }

  const handleQuery = () => {
    queryParams.value.pageNum = 1
    getList()
  }

  const resetQuery = () => {
    queryFormRef.value.resetFields()
    handleQuery()
  }

  /** 分类编码 → 名称。find 可能返回 undefined，这里必须兜住，否则整格渲染会抛错 */
  const categoryFormat = (row) => {
    const matched = categoryOptions.value.find((item) => item.code === row[categoryField])
    return matched?.categoryName || ''
  }

  onMounted(async () => {
    const res = await listAllCategory()
    categoryOptions.value = res.data
    getList()
  })

  return {
    rows,
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
  }
}
