import MarkdownIt from 'markdown-it'
import DOMPurify from 'dompurify'

// Markdown 渲染配置（全局单例，MessageItem 等组件共用）
const md = new MarkdownIt({
  html: true,
  breaks: true,
  linkify: true,
  typographer: true
})

export function renderMarkdown(content) {
  if (!content) return ''
  const formatted = content.replace(/\r\n/g, '\n').replace(/\r/g, '\n')
  return DOMPurify.sanitize(md.render(formatted))
}
