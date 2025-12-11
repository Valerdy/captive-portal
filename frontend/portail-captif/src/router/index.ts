import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('../views/HomeView.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
      meta: { requiresGuest: true }
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('../views/RegisterView.vue'),
      meta: { requiresGuest: true }
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: () => import('../views/DashboardView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/devices',
      name: 'devices',
      component: () => import('../views/DevicesView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/sessions',
      name: 'sessions',
      component: () => import('../views/SessionsView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/vouchers',
      name: 'vouchers',
      component: () => import('../views/VouchersView.vue'),
      meta: { requiresAuth: true } // Auth requise pour utiliser un voucher
    },
    {
      path: '/profile',
      name: 'profile',
      component: () => import('../views/ProfileView.vue'),
      meta: { requiresAuth: true }
    },
    // Routes Admin
    {
      path: '/admin/login',
      name: 'admin-login',
      component: () => import('../views/AdminLoginView.vue'),
      meta: { requiresGuest: true }
    },
    {
      path: '/admin/dashboard',
      name: 'admin-dashboard',
      component: () => import('../views/AdminDashboardView.vue'),
      meta: { requiresAuth: true, requiresAdmin: true }
    },
    {
      path: '/admin/users',
      name: 'admin-users',
      component: () => import('../views/AdminUsersView.vue'),
      meta: { requiresAuth: true, requiresAdmin: true }
    },
    {
      path: '/admin/monitoring',
      name: 'admin-monitoring',
      component: () => import('../views/AdminMonitoringView.vue'),
      meta: { requiresAuth: true, requiresAdmin: true }
    },
    {
      path: '/admin/sites',
      name: 'admin-sites',
      component: () => import('../views/AdminSitesView.vue'),
      meta: { requiresAuth: true, requiresAdmin: true }
    },
    {
      path: '/admin/quotas',
      name: 'admin-quotas',
      component: () => import('../views/AdminQuotasView.vue'),
      meta: { requiresAuth: true, requiresAdmin: true }
    },
    {
      path: '/admin/promotions',
      name: 'admin-promotions',
      component: () => import('../views/AdminPromotionsView.vue'),
      meta: { requiresAuth: true, requiresAdmin: true }
    },
    {
      path: '/admin/profiles',
      name: 'admin-profiles',
      component: () => import('../views/AdminProfilesView.vue'),
      meta: { requiresAuth: true, requiresAdmin: true }
    }
  ]
})

// Navigation Guard
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  // Toujours initialiser l'auth depuis localStorage au début
  // Cela garantit que l'état d'authentification est à jour avant les vérifications
  authStore.initializeAuth()

  const requiresAuth = to.matched.some((record) => record.meta.requiresAuth)
  const requiresGuest = to.matched.some((record) => record.meta.requiresGuest)
  const requiresAdmin = to.matched.some((record) => record.meta.requiresAdmin)

  if (requiresAuth && !authStore.isAuthenticated) {
    // Rediriger vers login si auth requise et pas connecté
    const redirectRoute = requiresAdmin ? 'admin-login' : 'login'
    next({ name: redirectRoute, query: { redirect: to.fullPath } })
  } else if (requiresAdmin && !authStore.isAdmin) {
    // Rediriger si droits admin requis mais pas admin
    next({ name: 'home' })
  } else if (requiresGuest && authStore.isAuthenticated) {
    // Rediriger vers dashboard si déjà connecté
    const redirectRoute = authStore.isAdmin ? 'admin-dashboard' : 'dashboard'
    next({ name: redirectRoute })
  } else {
    next()
  }
})

export default router
