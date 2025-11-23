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
            to="/oa/todo"
            class="flex flex-col items-center justify-center py-2.5 rounded-lg transition-all duration-200 group text-gray-600 hover:bg-gray-100 relative"
            active-class="bg-green-50 !text-green-600 font-medium"
        >
          <div v-if="todoCount > 0" class="absolute top-1 right-3 w-2 h-2 bg-red-500 rounded-full border border-white"></div>
          <el-icon :size="20" class="mb-0.5 group-hover:scale-105 transition-transform"><Finished /></el-icon>
          <span class="text-[11px]">審批</span>
        </router-link>

      </div>

      <div class="mt-auto flex flex-col gap-3 items-center">

        <el-tooltip v-if="isAdmin" content="切換至管理後台" placement="right">
          <div
              @click="goToAdmin"
              class="w-10 h-10 rounded-lg flex items-center justify-center text-gray-500 hover:bg-gray-100 hover:text-green-600 cursor-pointer transition-all"
          >
            <el-icon :size="20"><Monitor /></el-icon>
          </div>
        </el-tooltip>

        <el-dropdown trigger="click">
          <div class="w-10 h-10 rounded-full bg-gray-200 overflow-hidden cursor-pointer border-2 border-transparent hover:border-green-500 transition">
            <img :src="userAvatar" class="w-full h-full object-cover" alt="User Avatar" />
          </div>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="handleLogout">退出登錄</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <div class="flex-1 flex flex-col h-full overflow-hidden">

      <header class="h-14 bg-white border-b border-gray-100 flex items-center justify-between px-6 flex-shrink-0">
        <h2 class="text-base font-semibold text-gray-800">{{ route.meta.title || '工作區' }}</h2>
        <div class="text-sm text-gray-500">
          Admin User
        </div>
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
import {computed, ref} from 'vue'
import {useRoute, useRouter} from 'vue-router'
// 請確保你的路徑正確：'useUserStore' 是一個假設的 Store 模塊
import useUserStore from '@/store/modules/user'
import {Grid, Finished, Monitor} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore() // 假設已初始化並可用

const todoCount = ref(12) // 模擬數據
// 飛書風格通常使用簡潔的圓形頭像
const userAvatar = computed(() => userStore.avatar || 'https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png')

// 判斷是否為管理員
const isAdmin = computed(() => {
  const roles = userStore.roles || []
  return roles.includes('admin')
})

// -------------------
// 邏輯處理函數
// -------------------

// 導航到管理後台
const goToAdmin = () => {
  // 導航到管理後台路徑
  router.push('/admin/index')
}

// 處理登出
const handleLogout = async () => {
  try {
    await userStore.logOut() // 執行登出操作
    router.push('/login') // 重定向到登錄頁面
  } catch (error) {
    console.error("Logout failed:", error)
  }
}
</script>

<style scoped>
/* 如果你在 Tailwind 配置中沒有設置飛書綠色，
可以考慮在 <style> 標籤中定義一個 CSS 變量，但使用 Tailwind 類名更推薦。
*/
</style>