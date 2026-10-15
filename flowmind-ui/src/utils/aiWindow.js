import { ref } from 'vue'

// 模块级共享：当前打开的 AI 窗口（'assistant' | 'design' | null）。
// 同一时间只允许一个打开；设计窗口打开时全局助手浮球也一并隐藏。
export const activeAiWindow = ref(null)
