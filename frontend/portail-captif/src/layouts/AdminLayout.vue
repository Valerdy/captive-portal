<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useNotificationStore } from '@/stores/notification'

interface Props {
  activePage?: 'dashboard' | 'users' | 'monitoring' | 'sites' | 'quotas' | 'promotions'
}

const props = withDefaults(defineProps<Props>(), {
  activePage: 'dashboard'
})

const router = useRouter()
const authStore = useAuthStore()
const notificationStore = useNotificationStore()

function handleLogout() {
  authStore.logout()
  notificationStore.success('Déconnexion réussie')
  router.push('/')
}

function navigateTo(route: string) {
  router.push(route)
}
</script>

<template>
  <div class="admin-layout">
    <!-- Header professionnel -->
    <header class="dashboard-header">
      <div class="header-content">
        <div class="header-left">
          <div class="logo-section">
            <div class="logo-icon">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
            <div class="logo-text">
              <h1>UCAC-ICAM</h1>
              <p>Administration</p>
            </div>
          </div>
        </div>

        <div class="header-right">
          <div class="user-menu">
            <div class="user-avatar">{{ authStore.user?.username?.charAt(0).toUpperCase() }}</div>
            <div class="user-info">
              <span class="user-name">{{ authStore.user?.username }}</span>
              <span class="user-role">Administrateur</span>
            </div>
          </div>
          <button @click="handleLogout" class="logout-btn">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
        </div>
      </div>

      <!-- Navigation -->
      <nav class="main-nav">
        <button
          @click="navigateTo('/admin/dashboard')"
          class="nav-item"
          :class="{ active: activePage === 'dashboard' }"
        >
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="3" y="3" width="7" height="7" stroke="currentColor" stroke-width="2"/>
            <rect x="14" y="3" width="7" height="7" stroke="currentColor" stroke-width="2"/>
            <rect x="14" y="14" width="7" height="7" stroke="currentColor" stroke-width="2"/>
            <rect x="3" y="14" width="7" height="7" stroke="currentColor" stroke-width="2"/>
          </svg>
          Dashboard
        </button>
        <button
          @click="navigateTo('/admin/users')"
          class="nav-item"
          :class="{ active: activePage === 'users' }"
        >
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2M9 7a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          Utilisateurs
        </button>
        <button
          @click="navigateTo('/admin/monitoring')"
          class="nav-item"
          :class="{ active: activePage === 'monitoring' }"
        >
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          Monitoring
        </button>
        <button
          @click="navigateTo('/admin/sites')"
          class="nav-item"
          :class="{ active: activePage === 'sites' }"
        >
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
            <line x1="4.93" y1="4.93" x2="19.07" y2="19.07" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
          Sites bloqués
        </button>
        <button
          @click="navigateTo('/admin/quotas')"
          class="nav-item"
          :class="{ active: activePage === 'quotas' }"
        >
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <line x1="12" y1="1" x2="12" y2="23" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          Quotas
        </button>
        <button
          @click="navigateTo('/admin/promotions')"
          class="nav-item"
          :class="{ active: activePage === 'promotions' }"
        >
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="3" y="3" width="18" height="18" rx="2" stroke="currentColor" stroke-width="2"/>
            <line x1="9" y1="9" x2="15" y2="9" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            <line x1="9" y1="15" x2="15" y2="15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
          Promotions
        </button>
      </nav>
    </header>

    <!-- Contenu de la page (slot) -->
    <main class="dashboard-content">
      <slot />
    </main>
  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
  font-family: 'Inter', sans-serif;
}

.admin-layout {
  min-height: 100vh;
  background: #F9FAFB;
}

/* Header */
.dashboard-header {
  background: #FFFFFF;
  border-bottom: 1px solid #E5E7EB;
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.header-content {
  max-width: 1600px;
  margin: 0 auto;
  padding: 1.25rem 2rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 2rem;
}

.logo-section {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.logo-icon {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #DC2626 0%, #F97316 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.logo-icon svg {
  width: 28px;
  height: 28px;
}

.logo-text h1 {
  font-size: 1.25rem;
  font-weight: 800;
  color: #1F2937;
  letter-spacing: -0.02em;
}

.logo-text p {
  font-size: 0.875rem;
  color: #6B7280;
  font-weight: 500;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.user-menu {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem 1rem;
  background: #F9FAFB;
  border-radius: 10px;
  border: 1px solid #E5E7EB;
}

.user-avatar {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #DC2626 0%, #F97316 100%);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 700;
  font-size: 1rem;
}

.user-info {
  display: flex;
  flex-direction: column;
}

.user-name {
  font-size: 0.875rem;
  font-weight: 600;
  color: #1F2937;
}

.user-role {
  font-size: 0.75rem;
  color: #6B7280;
}

.logout-btn {
  width: 44px;
  height: 44px;
  background: #FEF2F2;
  border: 1px solid #FEE2E2;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  color: #DC2626;
}

.logout-btn svg {
  width: 20px;
  height: 20px;
}

.logout-btn:hover {
  background: #DC2626;
  border-color: #DC2626;
  color: white;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(220, 38, 38, 0.2);
}

/* Navigation */
.main-nav {
  max-width: 1600px;
  margin: 0 auto;
  padding: 0 2rem 1rem;
  display: flex;
  gap: 0.5rem;
  overflow-x: auto;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.25rem;
  background: transparent;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  color: #6B7280;
  font-weight: 500;
  font-size: 0.875rem;
  white-space: nowrap;
}

.nav-item svg {
  width: 18px;
  height: 18px;
}

.nav-item:hover {
  background: #F9FAFB;
  color: #1F2937;
}

.nav-item.active {
  background: linear-gradient(135deg, #DC2626 0%, #F97316 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(220, 38, 38, 0.2);
}

/* Contenu */
.dashboard-content {
  max-width: 1600px;
  margin: 0 auto;
  padding: 2rem;
}

/* Responsive */
@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    gap: 1rem;
    padding: 1rem;
  }

  .dashboard-content {
    padding: 1rem;
  }

  .main-nav {
    padding: 0 1rem 1rem;
  }
}
</style>
