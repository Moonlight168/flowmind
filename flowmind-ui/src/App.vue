<template>
  <router-view />
  <template>
  <div class="text-2xl font-bold text-red-500 mt-10 text-center">
    Tailwind CSS 在 RuoYi-Vite 项目中集成成功！
  </div>
</template>
</template>

<script setup>
import useSettingsStore from '@/store/modules/settings'
import { handleThemeStyle } from '@/utils/theme'


onMounted(() => {
  nextTick(() => {
    // 初始化主题样式
    handleThemeStyle(useSettingsStore().theme)
  })
})
</script>
