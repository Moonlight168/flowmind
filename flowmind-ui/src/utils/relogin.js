import { ElMessageBox } from 'element-plus'

// 是否显示重新登录（同时被 permission.js 用作"用户信息加载中"标志）
export const isRelogin = { show: false }

/**
 * 弹出"登录状态已过期"确认框，确认后登出并跳转登录页。
 * request.js（axios 401）与 sse.js（fetch 401）共用，避免两处维护同一段弹窗逻辑。
 * useUserStore 动态导入：本模块被 sse.js 静态引用，避免把 store 模块图
 * 拉进 SSE 单元测试环境。
 */
export function promptRelogin() {
  if (isRelogin.show) return
  isRelogin.show = true
  ElMessageBox.confirm('登录状态已过期，您可以继续留在该页面，或者重新登录', '系统提示', { confirmButtonText: '重新登录', cancelButtonText: '取消', type: 'warning' }).then(async () => {
    isRelogin.show = false
    const { default: useUserStore } = await import('@/store/modules/user')
    useUserStore().logOut().then(() => {
      location.href = '/index'
    })
  }).catch(() => {
    isRelogin.show = false
  })
}
