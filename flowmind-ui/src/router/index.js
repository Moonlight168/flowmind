import { createWebHistory, createRouter } from 'vue-router'
/* Layout */
import Layout from '@/layout'
import UserLayout from '@/layout/portal/index.vue'

/**
 * Note: 路由配置项
 *
 * hidden: true                     // 当设置 true 的时候该路由不会再侧边栏出现 如401，login等页面，或者如一些编辑页面/edit/1
 * alwaysShow: true                 // 当你一个路由下面的 children 声明的路由大于1个时，自动会变成嵌套的模式--如组件页面
 *                                  // 只有一个时，会将那个子路由当做根路由显示在侧边栏--如引导页面
 *                                  // 若你想不管路由下面的 children 声明的个数都显示你的根路由
 *                                  // 你可以设置 alwaysShow: true，这样它就会忽略之前定义的规则，一直显示根路由
 * redirect: noRedirect             // 当设置 noRedirect 的时候该路由在面包屑导航中不可被点击
 * name:'router-name'               // 设定路由的名字，一定要填写不然使用<keep-alive>时会出现各种问题
 * query: '{"id": 1, "name": "ry"}' // 访问路由的默认传递参数
 * roles: ['admin', 'common']       // 访问路由的角色权限
 * permissions: ['a:a:a', 'b:b:b']  // 访问路由的菜单权限
 * meta : {
 noCache: true                   // 如果设置为true，则不会被 <keep-alive> 缓存(默认 false)
 title: 'title'                  // 设置该路由在侧边栏和面包屑中展示的名字
 icon: 'svg-name'                // 设置该路由的图标，对应路径src/assets/icons/svg
 breadcrumb: false               // 如果设置为false，则不会在breadcrumb面包屑中显示
 activeMenu: '/system/user'      // 当路由设置了该属性，则会高亮相对应的侧边栏。
 }
 */

// 公共路由
export const constantRoutes = [
    {
        path: '/redirect',
        component: Layout,
        hidden: true,
        children: [
            {
                path: '/redirect/:path(.*)',
                component: () => import('@/views/redirect/index.vue')
            }
        ]
    },
    {
        path: '/login',
        component: () => import('@/views/login'),
        hidden: true
    },
    {
        path: '/register',
        component: () => import('@/views/register'),
        hidden: true
    },
    {
        path: '/401',
        component: () => import('@/views/error/401'),
        hidden: true
    },
    {
        path: '',
        component: UserLayout,
        redirect: '/oa/workplace',
        children: [
            {
                path: '/oa/workplace',
                component: () => import('@/views/oa/workplace/index.vue'),
                name: 'Workplace',
                meta: { title: '工作台', icon: 'dashboard', affix: true }
            },
        ]
    },
    {
        path: '/user',
        component: Layout,
        hidden: true,
        redirect: 'noredirect',
        children: [
            {
                path: 'profile/:activeTab?',
                component: () => import('@/views/system/user/profile/index'),
                name: 'Profile',
                meta: { title: '个人中心', icon: 'user' }
            }
        ]
    },
]

// 404路由，放在最后以确保其他路由优先匹配
export const notFoundRoute = {
    path: "/:pathMatch(.*)*",
    component: () => import('@/views/error/404'),
    hidden: true
}

// 动态路由，基于用户权限动态去加载
export const dynamicRoutes = [
    {
        path: '/admin',
        component: Layout,
        redirect: '/admin/index',
        children: [
            {
                path: 'index',
                component: () => import('@/views/index'),
                name: 'Index',
                meta: { title: '首页', icon: 'dashboard', affix: true }
            }
        ]
    },
    {
        path: '/system/user-auth',
        component: Layout,
        hidden: true,
        permissions: ['system:user:edit'],
        children: [
            {
                path: 'role/:userId(\\d+)',
                component: () => import('@/views/system/user/authRole'),
                name: 'AuthRole',
                meta: { title: '分配角色', activeMenu: '/system/user' }
            }
        ]
    },
    {
        path: '/system/role-auth',
        component: Layout,
        hidden: true,
        permissions: ['system:role:edit'],
        children: [
            {
                path: 'user/:roleId(\\d+)',
                component: () => import('@/views/system/role/authUser'),
                name: 'AuthUser',
                meta: { title: '分配用户', activeMenu: '/system/role' }
            }
        ]
    },
    {
        path: '/system/dict-data',
        component: Layout,
        hidden: true,
        permissions: ['system:dict:list'],
        children: [
            {
                path: 'index/:dictId(\\d+)',
                component: () => import('@/views/system/dict/data'),
                name: 'Data',
                meta: { title: '字典数据', activeMenu: '/system/dict' }
            }
        ]
    },
    {
        path: '/monitor/job-log',
        component: Layout,
        hidden: true,
        permissions: ['monitor:job:list'],
        children: [
            {
                path: 'index/:jobId(\\d+)',
                component: () => import('@/views/monitor/job/log'),
                name: 'JobLog',
                meta: { title: '调度日志', activeMenu: '/monitor/job' }
            }
        ]
    },
    {
        path: '/tool/gen-edit',
        component: Layout,
        hidden: true,
        permissions: ['tool:gen:edit'],
        children: [
            {
                path: 'index/:tableId(\\d+)',
                component: () => import('@/views/tool/gen/editTable'),
                name: 'GenEdit',
                meta: { title: '修改生成配置', activeMenu: '/tool/gen' }
            }
        ]
    },
    {
        path: '/workflow/process',
        component: Layout,
        hidden: true,
        permissions: ['workflow:process:query'],
        children: [
            {
                path: 'index',
                component: () => import('@/views/workflow/work/index.vue'),
                name: 'WorkProcessIndex',
                meta: { title: '流程列表', activeMenu: '/workflow/process', icon: '' }
            },
            {
                path: 'start/:deployId([\\w|\\-]+)',
                component: () => import('@/views/workflow/work/start.vue'),
                name: 'WorkStart',
                meta: { title: '发起流程', activeMenu: '/workflow/process', icon: '' }
            },
            {
                path: 'detail/:procInsId([\\w|\\-]+)',
                component: () => import('@/views/workflow/work/detail.vue'),
                name: 'WorkDetail',
                meta: { title: '流程详情', activeMenu: '/work/own', icon: '' }
            }
        ]
    },
    {
        path: '/work',
        component: Layout,
        hidden: true,
        permissions: ['workflow:process:query'],
        children: [
            {
                path: 'todo',
                component: () => import('@/views/workflow/work/todo.vue'),
                name: 'WorkTodo',
                meta: { title: '待办任务', activeMenu: '/work/todo', icon: '' }
            },
            {
                path: 'finished',
                component: () => import('@/views/workflow/work/finished.vue'),
                name: 'WorkFinished',
                meta: { title: '已办任务', activeMenu: '/work/finished', icon: '' }
            },
            {
                path: 'own',
                component: () => import('@/views/workflow/work/own.vue'),
                name: 'WorkOwn',
                meta: { title: '我的流程', activeMenu: '/work/own', icon: '' }
            },
            {
                path: 'claim',
                component: () => import('@/views/workflow/work/claim.vue'),
                name: 'WorkClaim',
                meta: { title: '待签收任务', activeMenu: '/work/claim', icon: '' }
            },
            {
                path: 'copy',
                component: () => import('@/views/workflow/work/copy.vue'),
                name: 'WorkCopy',
                meta: { title: '抄送任务', activeMenu: '/work/copy', icon: '' }
            }
        ]
    },
]


export const oaRoutes = [
    // OA工作台路由 - 使用portal布局
    {
        path: '/oa',
        component: UserLayout,
        redirect: '/oa/workplace',
        children: [
            {
                path: 'workplace',
                component: () => import('@/views/oa/workplace/index.vue'),
                name: 'Workplace',
                meta: { title: '工作台', icon: 'dashboard', affix: true },
                children: [
                    {
                        path: 'start/:deployId([\\w|\\-]+)',
                        component: () => import('@/views/oa/workplace/start.vue'),
                        name: 'WorkStart',
                        meta: { title: '发起流程', activeMenu: '/oa/workplace', icon: '' }
                    },
                ]
            },
            {
                path: 'task',
                component: () => import('@/views/oa/task/index.vue'),
                name: 'Task',
                meta: { title: '任务中心', icon: 'todo' },
                redirect: '/oa/task/todo',
                children: [
                    {
                        path: 'todo',
                        component: () => import('@/views/oa/task/todo.vue'),
                        //component: () => import('@/views/workflow/work/todo.vue'),
                        name: 'Todo',
                        meta: { title: '待办事项', icon: 'todo', activeMenu: '/oa/todo' }
                    },
                    {
                        path: 'finished',
                        component: () => import('@/views/oa/task/finished.vue'),
                        //component: () => import('@/views/workflow/work/finished.vue'),
                        name: 'Finished',
                        meta: { title: '已办事项', icon: 'finished', activeMenu: '/oa/finished' }
                    },
                    {
                        path: 'own',
                        component: () => import('@/views/oa/task/own.vue'),
                        //component: () => import('@/views/workflow/work/own.vue'),
                        name: 'Own',
                        meta: { title: '我的流程', icon: 'own', activeMenu: '/oa/own' }
                    },
                    {
                        path: 'copy',
                        component: () => import('@/views/oa/task/copy.vue'),
                        //component: () => import('@/views/workflow/work/copy.vue'),
                        name: 'Copy',
                        meta: { title: '抄送', icon: 'copy', activeMenu: '/oa/copy' }
                    },
                    {
                        path: 'claim',
                        component: () => import('@/views/oa/task/claim.vue'),
                        //component: () => import('@/views/workflow/work/claim.vue'),
                        name: 'Claim',
                        meta: { title: '待签收', icon: 'claim', activeMenu: '/oa/claim' }
                    },
                    {
                        path: 'process/detail/:procInsId',
                        //component: () => import('@/views/oa/task/detail.vue'),
                        component: () => import('@/views/workflow/work/detail.vue'),
                        //component: () => import('@/views/workflow/work/detail.vue'),
                        name: 'ProcessDetail',
                        meta: { title: '流程详情', icon: 'process' }
                    }
                ]
            },
            {
                path: 'profile',
                component: () => import('@/views/system/user/profile/index'),
                name: 'OAProfile',
                meta: { title: '个人信息', icon: 'user' }
            },

        ]
    },
]

const router = createRouter({
    history: createWebHistory(),
    routes: [...constantRoutes, ...oaRoutes, ...dynamicRoutes, notFoundRoute], // 初始路由，确保oaRoutes在应用启动时就被添加
    scrollBehavior(to, from, savedPosition) {
        if (savedPosition) {
            return savedPosition
        }
        return { top: 0 }
    },
})

export default router
