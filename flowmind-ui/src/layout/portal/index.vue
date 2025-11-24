<template>
  <div class="flex h-screen w-full bg-gray-50 overflow-hidden font-sans text-gray-700">

    <div class="w-20 bg-white flex flex-col items-center py-6 border-r border-gray-200 shadow-sm z-20 flex-shrink-0">

      <div class="w-10 h-10 bg-green-500 rounded-lg flex items-center justify-center text-white font-bold text-lg mb-8 shadow-green-200 shadow-md cursor-pointer hover:opacity-90 transition">
        OA
      </div>

      <div class="flex-1 flex flex-col gap-2 w-full px-2">

        <router-link
            to="/oa/workplace"
            class="flex flex-col items-center justify-center py-2.5 rounded-lg transition-all duration-200 group text-gray-600 hover:bg-gray-100"
            active-class="bg-green-50 !text-green-600 font-medium"
        >
          <el-icon :size="20" class="mb-0.5 group-hover:scale-105 transition-transform"><Grid /></el-icon>
          <span class="text-[11px]">工作台</span>
        </router-link>

        <router-link
            to="/oa/task"
            class="flex flex-col items-center justify-center py-2.5 rounded-lg transition-all duration-200 group text-gray-600 hover:bg-gray-100 relative"
            active-class="bg-green-50 !text-green-600 font-medium"
        >
          <div v-if="todoCount > 0" class="absolute -top-1 -right-1 min-w-[18px] h-[18px] bg-red-500 text-white text-xs rounded-full flex items-center justify-center border border-white">
            {{ todoCount > 99 ? '99+' : todoCount }}
          </div>
          <el-icon :size="20" class="mb-0.5 group-hover:scale-105 transition-transform"><Finished /></el-icon>
          <span class="text-[11px]">审批</span>
        </router-link>

      </div>

      <div class="mt-auto flex flex-col gap-3 items-center">

        <el-tooltip v-if="isAdmin" content="切换至管理后台" placement="right">
          <div
              @click="goToAdmin"
              class="w-10 h-10 rounded-lg flex items-center justify-center text-gray-500 hover:bg-gray-100 hover:text-green-600 cursor-pointer transition-all"
          >
            <el-icon :size="20"><Monitor /></el-icon>
          </div>
        </el-tooltip>

        <el-dropdown trigger="click">
          <div class="w-10 h-10 rounded-full bg-gray-200 overflow-hidden cursor-pointer border-2 border-transparent hover:border-green-500 transition">
            <img :src="userAvatar" class="w-full h-full object-cover" alt="用户头像" />
          </div>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="goToProfile">
                <el-icon><User /></el-icon>个人信息
              </el-dropdown-item>
              <el-dropdown-item divided @click="handleLogout">
                <el-icon><SwitchButton /></el-icon>退出登录
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <div class="flex-1 flex flex-col h-full overflow-hidden">

      <header class="h-14 bg-white border-b border-gray-100 flex items-center justify-between px-6 flex-shrink-0">
        <h2 class="text-base font-semibold text-gray-800">{{ route.meta.title || '工作区' }}</h2>
      </header>

      <main class="flex-1 overflow-y-auto">
        <div class="p-6 h-full">
          <router-view v-slot="{ Component }">
            <transition name="el-fade-in-linear" mode="out-in">
              <component :is="Component" />
            </transition>
          </router-view>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import {computed, ref, onMounted} from 'vue'
import {useRoute, useRouter} from 'vue-router'
import useUserStore from '@/store/modules/user'
import usePermissionStore from '@/store/modules/permission'
import {isHttp} from '@/utils/validate'
import {Grid, Finished, Monitor, User, SwitchButton} from '@element-plus/icons-vue'
import {listTodoProcess} from '@/api/workflow/work/process'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const todoCount = ref(0) // 待办任务数量
const userAvatar = computed(() => userStore.avatar || 'https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png')

// 判断是否为管理员
const isAdmin = computed(() => {
  const roles = userStore.roles || []
  return roles.includes('admin')
})

// 获取待办任务数量
const getTodoCount = async () => {
  try {
    const res = await listTodoProcess({ pageNum: 1, pageSize: 1 })
    todoCount.value = res.total || 0
  } catch (error) {
    console.error('获取待办任务数量失败:', error)
    todoCount.value = 0
  }
}

// 导航到管理后台
const goToAdmin = async () => {
  // 确保用户信息和权限路由已加载
  if (userStore.roles.length === 0) {
    await userStore.getInfo()
  }
  
  // 确保菜单已加载
  const permissionStore = usePermissionStore()
  if (permissionStore.sidebarRouters.length === 0) {
    const accessRoutes = await permissionStore.generateRoutes()
    accessRoutes.forEach(route => { 
      if (!isHttp(route.path)) {
        router.addRoute(route)
      }
    })
  }
  
  await router.push('/admin/index')
}

// 导航到个人信息页面
const goToProfile = () => {
  router.push('/oa/profile')
}

// 处理登出
const handleLogout = async () => {
  try {
    await userStore.logOut()
    router.push('/login')
  } catch (error) {
    console.error("退出登录失败:", error)
  }
}

// 组件挂载时获取待办任务数量
onMounted(() => {
  // 确保用户信息已加载
  if (!userStore.name) {
    userStore.getInfo().then(() => {
      getTodoCount()
    })
  } else {
    getTodoCount()
  }
})
</script>

<style scoped>
/* 如果你在 Tailwind 配置中没有设置飞书绿色，
可以考虑在 <style> 标签中定义一个 CSS 变量，但使用 Tailwind 类名更推荐。
*/
</style>