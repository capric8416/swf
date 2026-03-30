import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import type { RouteRecordRaw } from 'vue-router'

// 布局组件
const TechLayout = () => import('@/layouts/TechLayout.vue')

// 页面组件
const LoginView = () => import('@/views/login/index.vue')
const DashboardView = () => import('@/views/dashboard/index.vue')
const PersonalStatsView = () => import('@/views/personal-stats/index.vue')
const ProjectStatsView = () => import('@/views/project-stats/index.vue')
const SyncView = () => import('@/views/sync/index.vue')
const UsersManageView = () => import('@/views/admin/users.vue')
const ProjectsManageView = () => import('@/views/admin/projects.vue')
const SettingsView = () => import('@/views/admin/settings.vue')

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: LoginView,
    meta: { public: true, title: '登录' },
  },
  {
    path: '/',
    component: TechLayout,
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: DashboardView,
        meta: { title: '仪表盘', icon: 'Odometer' },
      },
      {
        path: 'personal-stats',
        name: 'PersonalStats',
        component: PersonalStatsView,
        meta: { title: '个人统计', icon: 'User' },
      },
      {
        path: 'project-stats',
        name: 'ProjectStats',
        component: ProjectStatsView,
        meta: { title: '项目统计', icon: 'DataLine' },
      },
      {
        path: 'trends',
        name: 'Trends',
        component: () => import('@/views/dashboard/index.vue'), // 临时使用仪表盘
        meta: { title: '趋势分析', icon: 'TrendCharts' },
      },
      {
        path: 'sync',
        name: 'Sync',
        component: SyncView,
        meta: { title: '数据同步', icon: 'Refresh' },
      },
      {
        path: 'admin/users',
        name: 'UserManagement',
        component: UsersManageView,
        meta: { title: '用户管理', icon: 'Users', requiresAdmin: true },
      },
      {
        path: 'admin/projects',
        name: 'ProjectManagement',
        component: ProjectsManageView,
        meta: { title: '项目管理', icon: 'Folder', requiresAdmin: true },
      },
      {
        path: 'admin/settings',
        name: 'SystemSettings',
        component: SettingsView,
        meta: { title: '系统设置', icon: 'Setting', requiresAdmin: true },
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue'),
    meta: { title: '页面未找到' },
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior() {
    return { top: 0 }
  },
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()

  // 设置页面标题
  document.title = to.meta.title ? `${to.meta.title} - DevMetrics` : 'DevMetrics'

  // 公开路由直接通过
  if (to.meta.public) {
    // 已登录用户访问登录页，重定向到仪表盘
    if (to.path === '/login' && authStore.isAuthenticated) {
      return next('/dashboard')
    }
    return next()
  }

  // 检查是否已登录
  if (!authStore.isAuthenticated) {
    return next('/login')
  }

  // 获取当前用户信息（如果还没有）
  if (!authStore.user) {
    try {
      await authStore.fetchCurrentUser()
    } catch {
      return next('/login')
    }
  }

  // 检查管理员权限
  if (to.meta.requiresAdmin && !authStore.isAdmin) {
    return next('/dashboard')
  }

  next()
})

export default router
