<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useNotificationStore } from '@/stores/notification'

interface Props {
  activePage?: 'dashboard' | 'users' | 'monitoring' | 'sites' | 'quotas' | 'promotions' | 'profiles'
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
    <!-- Animated Background -->
    <div class="bg-animation">
      <div class="gradient-orb orb-1"></div>
      <div class="gradient-orb orb-2"></div>
      <div class="gradient-orb orb-3"></div>
      <div class="grid-overlay"></div>
    </div>

    <!-- Sidebar -->
    <aside class="sidebar">
      <div class="sidebar-header">
        <router-link to="/" class="logo-link">
          <div class="logo-container">
            <div class="logo-rings">
              <div class="ring ring-1"></div>
              <div class="ring ring-2"></div>
            </div>
            <div class="logo-icon">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
          </div>
          <div class="logo-text">
            <span class="logo-title">UCAC-ICAM</span>
            <span class="logo-subtitle">Administration</span>
          </div>
        </router-link>
      </div>

      <nav class="sidebar-nav">
        <div class="nav-section">
          <span class="nav-label">Principal</span>
          <button
            @click="navigateTo('/admin/dashboard')"
            class="nav-item"
            :class="{ active: activePage === 'dashboard' }"
          >
            <div class="nav-icon">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect x="3" y="3" width="7" height="7" rx="1" stroke="currentColor" stroke-width="2"/>
                <rect x="14" y="3" width="7" height="7" rx="1" stroke="currentColor" stroke-width="2"/>
                <rect x="14" y="14" width="7" height="7" rx="1" stroke="currentColor" stroke-width="2"/>
                <rect x="3" y="14" width="7" height="7" rx="1" stroke="currentColor" stroke-width="2"/>
              </svg>
            </div>
            <span>Dashboard</span>
            <div class="nav-indicator"></div>
          </button>
          <button
            @click="navigateTo('/admin/monitoring')"
            class="nav-item"
            :class="{ active: activePage === 'monitoring' }"
          >
            <div class="nav-icon">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
            <span>Monitoring</span>
            <div class="nav-indicator"></div>
          </button>
        </div>

        <div class="nav-section">
          <span class="nav-label">Gestion</span>
          <button
            @click="navigateTo('/admin/users')"
            class="nav-item"
            :class="{ active: activePage === 'users' }"
          >
            <div class="nav-icon">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2M9 7a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
            <span>Utilisateurs</span>
            <div class="nav-indicator"></div>
          </button>
          <button
            @click="navigateTo('/admin/profiles')"
            class="nav-item"
            :class="{ active: activePage === 'profiles' }"
          >
            <div class="nav-icon">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <circle cx="12" cy="7" r="4" stroke="currentColor" stroke-width="2"/>
              </svg>
            </div>
            <span>Profils</span>
            <div class="nav-indicator"></div>
          </button>
          <button
            @click="navigateTo('/admin/promotions')"
            class="nav-item"
            :class="{ active: activePage === 'promotions' }"
          >
            <div class="nav-icon">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect x="3" y="3" width="18" height="18" rx="2" stroke="currentColor" stroke-width="2"/>
                <line x1="9" y1="9" x2="15" y2="9" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                <line x1="9" y1="15" x2="15" y2="15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </div>
            <span>Promotions</span>
            <div class="nav-indicator"></div>
          </button>
        </div>

        <div class="nav-section">
          <span class="nav-label">Contrôle</span>
          <button
            @click="navigateTo('/admin/quotas')"
            class="nav-item"
            :class="{ active: activePage === 'quotas' }"
          >
            <div class="nav-icon">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <line x1="12" y1="1" x2="12" y2="23" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
            <span>Quotas</span>
            <div class="nav-indicator"></div>
          </button>
          <button
            @click="navigateTo('/admin/sites')"
            class="nav-item"
            :class="{ active: activePage === 'sites' }"
          >
            <div class="nav-icon">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                <line x1="4.93" y1="4.93" x2="19.07" y2="19.07" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </div>
            <span>Sites bloqués</span>
            <div class="nav-indicator"></div>
          </button>
        </div>
      </nav>

      <!-- User Section -->
      <div class="sidebar-footer">
        <div class="user-card">
          <div class="user-avatar">
            <span>{{ authStore.user?.username?.charAt(0).toUpperCase() }}</span>
            <div class="avatar-ring"></div>
          </div>
          <div class="user-info">
            <span class="user-name">{{ authStore.user?.username }}</span>
            <span class="user-role">Administrateur</span>
          </div>
          <button @click="handleLogout" class="logout-btn" title="Déconnexion">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
        </div>
      </div>
    </aside>

    <!-- Main Content -->
    <main class="main-content">
      <div class="content-wrapper">
        <slot />
      </div>
    </main>
  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Rajdhani:wght@400;500;600;700&family=Inter:wght@400;500;600;700&display=swap');

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.admin-layout {
  min-height: 100vh;
  display: flex;
  background: #0a0a0f;
  position: relative;
  overflow: hidden;
}

/* Animated Background */
.bg-animation {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 0;
  pointer-events: none;
}

.gradient-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.4;
}

.orb-1 {
  width: 600px;
  height: 600px;
  background: linear-gradient(135deg, #F29400 0%, #e53212 100%);
  top: -200px;
  right: -100px;
  animation: float 20s ease-in-out infinite;
}

.orb-2 {
  width: 500px;
  height: 500px;
  background: linear-gradient(135deg, #008ecf 0%, #a23882 100%);
  bottom: -150px;
  left: 20%;
  animation: float 25s ease-in-out infinite reverse;
}

.orb-3 {
  width: 400px;
  height: 400px;
  background: linear-gradient(135deg, #a23882 0%, #F29400 100%);
  top: 50%;
  right: 30%;
  animation: float 18s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  25% { transform: translate(30px, -30px) scale(1.05); }
  50% { transform: translate(-20px, 20px) scale(0.95); }
  75% { transform: translate(-30px, -20px) scale(1.02); }
}

.grid-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image:
    linear-gradient(rgba(242, 148, 0, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(242, 148, 0, 0.03) 1px, transparent 1px);
  background-size: 50px 50px;
}

/* Sidebar */
.sidebar {
  width: 280px;
  min-height: 100vh;
  background: rgba(15, 15, 25, 0.8);
  backdrop-filter: blur(20px);
  border-right: 1px solid rgba(242, 148, 0, 0.1);
  display: flex;
  flex-direction: column;
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  z-index: 100;
}

.sidebar-header {
  padding: 1.5rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.logo-link {
  display: flex;
  align-items: center;
  gap: 1rem;
  text-decoration: none;
  padding: 0.5rem;
  border-radius: 12px;
  transition: all 0.3s ease;
}

.logo-link:hover {
  background: rgba(242, 148, 0, 0.1);
}

.logo-container {
  position: relative;
  width: 48px;
  height: 48px;
}

.logo-rings {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
}

.ring {
  position: absolute;
  border-radius: 50%;
  border: 2px solid transparent;
}

.ring-1 {
  top: -4px;
  left: -4px;
  right: -4px;
  bottom: -4px;
  border-color: rgba(242, 148, 0, 0.3);
  animation: rotate 8s linear infinite;
}

.ring-2 {
  top: -8px;
  left: -8px;
  right: -8px;
  bottom: -8px;
  border-color: rgba(0, 142, 207, 0.2);
  animation: rotate 12s linear infinite reverse;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.logo-icon {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #F29400 0%, #e53212 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  position: relative;
  z-index: 1;
  box-shadow: 0 0 20px rgba(242, 148, 0, 0.4);
}

.logo-icon svg {
  width: 26px;
  height: 26px;
}

.logo-text {
  display: flex;
  flex-direction: column;
}

.logo-title {
  font-family: 'Orbitron', sans-serif;
  font-size: 1.1rem;
  font-weight: 700;
  color: #ffffff;
  letter-spacing: 0.05em;
}

.logo-subtitle {
  font-family: 'Rajdhani', sans-serif;
  font-size: 0.75rem;
  color: #F29400;
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

/* Navigation */
.sidebar-nav {
  flex: 1;
  padding: 1rem 0;
  overflow-y: auto;
}

.nav-section {
  padding: 0.5rem 1rem;
  margin-bottom: 0.5rem;
}

.nav-label {
  display: block;
  font-family: 'Rajdhani', sans-serif;
  font-size: 0.7rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.3);
  text-transform: uppercase;
  letter-spacing: 0.15em;
  padding: 0.5rem 0.75rem;
  margin-bottom: 0.25rem;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  width: 100%;
  padding: 0.875rem 1rem;
  background: transparent;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
  color: rgba(255, 255, 255, 0.6);
  font-family: 'Inter', sans-serif;
  font-weight: 500;
  font-size: 0.9rem;
  text-align: left;
  position: relative;
  overflow: hidden;
}

.nav-icon {
  width: 36px;
  height: 36px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.nav-icon svg {
  width: 18px;
  height: 18px;
}

.nav-indicator {
  position: absolute;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 0;
  background: linear-gradient(180deg, #F29400 0%, #e53212 100%);
  border-radius: 3px 0 0 3px;
  transition: height 0.3s ease;
}

.nav-item:hover {
  background: rgba(242, 148, 0, 0.08);
  color: rgba(255, 255, 255, 0.9);
}

.nav-item:hover .nav-icon {
  background: rgba(242, 148, 0, 0.15);
}

.nav-item.active {
  background: linear-gradient(90deg, rgba(242, 148, 0, 0.15) 0%, rgba(242, 148, 0, 0.05) 100%);
  color: #F29400;
}

.nav-item.active .nav-icon {
  background: linear-gradient(135deg, #F29400 0%, #e53212 100%);
  color: white;
  box-shadow: 0 0 15px rgba(242, 148, 0, 0.4);
}

.nav-item.active .nav-indicator {
  height: 24px;
}

/* Sidebar Footer */
.sidebar-footer {
  padding: 1rem;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}

.user-card {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.user-avatar {
  position: relative;
  width: 42px;
  height: 42px;
  background: linear-gradient(135deg, #008ecf 0%, #a23882 100%);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-family: 'Orbitron', sans-serif;
  font-weight: 700;
  font-size: 1rem;
}

.avatar-ring {
  position: absolute;
  top: -2px;
  left: -2px;
  right: -2px;
  bottom: -2px;
  border: 2px solid rgba(0, 142, 207, 0.3);
  border-radius: 12px;
  animation: pulse-ring 2s ease-in-out infinite;
}

@keyframes pulse-ring {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(1.05); }
}

.user-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.user-name {
  font-family: 'Inter', sans-serif;
  font-size: 0.875rem;
  font-weight: 600;
  color: #ffffff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-role {
  font-family: 'Rajdhani', sans-serif;
  font-size: 0.7rem;
  color: #008ecf;
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.logout-btn {
  width: 36px;
  height: 36px;
  background: rgba(229, 50, 18, 0.1);
  border: 1px solid rgba(229, 50, 18, 0.2);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  color: #e53212;
}

.logout-btn svg {
  width: 18px;
  height: 18px;
}

.logout-btn:hover {
  background: #e53212;
  border-color: #e53212;
  color: white;
  box-shadow: 0 0 15px rgba(229, 50, 18, 0.4);
  transform: translateX(2px);
}

/* Main Content */
.main-content {
  flex: 1;
  margin-left: 280px;
  min-height: 100vh;
  position: relative;
  z-index: 1;
}

.content-wrapper {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

/* Scrollbar */
.sidebar-nav::-webkit-scrollbar {
  width: 4px;
}

.sidebar-nav::-webkit-scrollbar-track {
  background: transparent;
}

.sidebar-nav::-webkit-scrollbar-thumb {
  background: rgba(242, 148, 0, 0.3);
  border-radius: 4px;
}

.sidebar-nav::-webkit-scrollbar-thumb:hover {
  background: rgba(242, 148, 0, 0.5);
}

/* Responsive */
@media (max-width: 1024px) {
  .sidebar {
    width: 240px;
  }

  .main-content {
    margin-left: 240px;
  }
}

@media (max-width: 768px) {
  .sidebar {
    width: 70px;
    padding: 0;
  }

  .sidebar-header {
    padding: 1rem 0.5rem;
  }

  .logo-link {
    justify-content: center;
    padding: 0.25rem;
  }

  .logo-text {
    display: none;
  }

  .logo-container {
    width: 40px;
    height: 40px;
  }

  .logo-icon {
    width: 40px;
    height: 40px;
  }

  .nav-section {
    padding: 0.5rem;
  }

  .nav-label {
    display: none;
  }

  .nav-item {
    justify-content: center;
    padding: 0.75rem;
  }

  .nav-item span {
    display: none;
  }

  .nav-indicator {
    display: none;
  }

  .sidebar-footer {
    padding: 0.5rem;
  }

  .user-card {
    flex-direction: column;
    padding: 0.5rem;
    gap: 0.5rem;
  }

  .user-info {
    display: none;
  }

  .main-content {
    margin-left: 70px;
  }

  .content-wrapper {
    padding: 1rem;
  }
}
</style>
