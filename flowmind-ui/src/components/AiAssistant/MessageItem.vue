<template>
  <div :class="['message flex gap-3 mb-4', message.role === 'user' ? 'flex-row-reverse' : '']">
    <div class="message-avatar flex-shrink-0 flex items-center justify-center text-blue-500">
      <el-icon v-if="message.role === 'assistant'" :size="20">
        <ChatDotRound />
      </el-icon>
      <el-avatar v-else size="small" :src="userStore.avatar" />
    </div>
    <div class="message-content max-w-[75%] flex flex-col gap-1">
      <div
        :class="[
          'message-text px-3.5 py-2.5 rounded-3xl text-sm leading-relaxed break-all markdown-content',
          message.role === 'user' ? 'bg-blue-500 text-white' : 'bg-white text-gray-800'
        ]"
        v-html="renderMarkdown(message.content)"
      ></div>
    </div>
  </div>
</template>

<script setup>
import { ChatDotRound } from '@element-plus/icons-vue'
import MarkdownIt from 'markdown-it'
import DOMPurify from 'dompurify'
import useUserStore from '@/store/modules/user'

const userStore = useUserStore()

defineProps({
  message: {
    type: Object,
    required: true
  }
})

// Markdown 渲染配置
const md = new MarkdownIt({
  html: true,
  breaks: true,
  linkify: true,
  typographer: true
})

// 渲染 Markdown 并处理换行
function renderMarkdown(content) {
  if (!content) return ''

  let formattedContent = content
    .replace(/\r\n/g, '\n')
    .replace(/\r/g, '\n')

  return DOMPurify.sanitize(md.render(formattedContent))
}
</script>

<style lang="scss" scoped>
// Markdown 内容样式
.markdown-content {
  word-break: break-word;
  white-space: normal;

  :deep(p) {
    margin: 0.5em 0;
    line-height: 1.6;
    white-space: pre-wrap;
    word-wrap: break-word;
  }

  :deep(p:first-child) {
    margin-top: 0;
  }

  :deep(p:last-child) {
    margin-bottom: 0;
  }

  :deep(code) {
    background-color: rgba(0, 0, 0, 0.06);
    padding: 2px 6px;
    border-radius: 4px;
    font-family: 'Consolas', 'Monaco', monospace;
    font-size: 0.9em;
    white-space: pre;
  }

  :deep(pre) {
    background-color: #f6f8fa;
    padding: 12px;
    border-radius: 6px;
    overflow-x: auto;
    margin: 0.5em 0;

    code {
      background-color: transparent;
      padding: 0;
      white-space: pre;
    }
  }

  :deep(ul), :deep(ol) {
    padding-left: 1.5em;
    margin: 0.5em 0;
  }

  :deep(li) {
    margin: 0.25em 0;
    white-space: normal;
  }

  :deep(li > p) {
    margin: 0;
    display: inline;
  }

  :deep(blockquote) {
    border-left: 4px solid #667eea;
    padding-left: 1em;
    margin: 0.5em 0;
    color: #666;
  }

  :deep(strong) {
    font-weight: 600;
  }

  :deep(em) {
    font-style: italic;
  }

  :deep(h1), :deep(h2), :deep(h3), :deep(h4), :deep(h5), :deep(h6) {
    margin: 0.75em 0 0.5em;
    font-weight: 600;
    line-height: 1.25;
  }

  :deep(h1:first-child), :deep(h2:first-child), :deep(h3:first-child) {
    margin-top: 0;
  }

  :deep(table) {
    border-collapse: collapse;
    width: 100%;
    margin: 0.5em 0;
    display: block;
    overflow-x: auto;
  }

  :deep(th), :deep(td) {
    border: 1px solid #ddd;
    padding: 6px 12px;
    text-align: left;
  }

  :deep(th) {
    background-color: #f6f8fa;
    font-weight: 600;
  }

  :deep(a) {
    color: #667eea;
    text-decoration: none;

    &:hover {
      text-decoration: underline;
    }
  }

  :deep(hr) {
    border: none;
    border-top: 1px solid #ddd;
    margin: 1em 0;
  }
}
</style>
