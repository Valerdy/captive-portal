<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useSessionStore } from '@/stores/session'
import { useDeviceStore } from '@/stores/device'

const router = useRouter()
const authStore = useAuthStore()
const sessionStore = useSessionStore()
const deviceStore = useDeviceStore()

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

async function handleLogout() {
  await authStore.logout()
  router.push('/login')
}

onMounted(async () => {
  await Promise.all([
    sessionStore.fetchStatistics(),
    sessionStore.fetchActiveSessions(),
    deviceStore.fetchActiveDevices()
  ])
})
</script>

<template>
  <div class="dashboard">
    <!-- Header UCAC-ICAM -->
    <header class="dashboard-header">
      <div class="header-brand">
        <div class="logo-small">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M2 17L12 22L22 17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M2 12L12 17L22 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
        <div class="brand-text">
          <h1>UCAC-ICAM</h1>
          <p>Portail Captif</p>
        </div>
      </div>
      <div class="user-info">
        <div class="user-avatar">
          {{ (authStore.user?.first_name || authStore.user?.username || 'U').charAt(0).toUpperCase() }}
        </div>
        <span class="user-name">{{ authStore.user?.first_name || authStore.user?.username }}</span>
        <button @click="handleLogout" class="btn-logout">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          Déconnexion
        </button>
      </div>
    </header>

    <!-- Navigation -->
    <nav class="nav-menu">
      <router-link to="/dashboard" class="nav-item">
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M9 22V12h6v10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        Tableau de bord
      </router-link>
      <router-link to="/sessions" class="nav-item">
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
          <path d="M12 6v6l4 2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
        Sessions
      </router-link>
      <router-link to="/devices" class="nav-item">
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <rect x="2" y="3" width="20" height="14" rx="2" stroke="currentColor" stroke-width="2"/>
          <path d="M8 21h8M12 17v4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
        Appareils
      </router-link>
      <router-link to="/vouchers" class="nav-item">
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M21 10H3M21 6H3M21 14H3M21 18H3" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
        Vouchers
      </router-link>
      <router-link to="/profile" class="nav-item">
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2"/>
          <circle cx="12" cy="7" r="4" stroke="currentColor" stroke-width="2"/>
        </svg>
        Profil
      </router-link>
    </nav>

    <!-- Contenu Principal -->
    <main class="dashboard-content">
      <h2>Tableau de bord</h2>

      <!-- Grille de statistiques -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-icon sessions">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
              <path d="M12 6v6l4 2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </div>
          <div class="stat-info">
            <h3>Sessions totales</h3>
            <p class="stat-value">{{ sessionStore.statistics?.total_sessions || 0 }}</p>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon active">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M22 12h-4l-3 9L9 3l-3 9H2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <div class="stat-info">
            <h3>Sessions actives</h3>
            <p class="stat-value active">{{ sessionStore.statistics?.active_sessions || 0 }}</p>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon data">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" stroke="currentColor" stroke-width="2"/>
            </svg>
          </div>
          <div class="stat-info">
            <h3>Données transférées</h3>
            <p class="stat-value">
              {{ formatBytes(sessionStore.statistics?.total_data_transferred || 0) }}
            </p>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon devices">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <rect x="2" y="3" width="20" height="14" rx="2" stroke="currentColor" stroke-width="2"/>
              <path d="M8 21h8M12 17v4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </div>
          <div class="stat-info">
            <h3>Appareils actifs</h3>
            <p class="stat-value">{{ deviceStore.activeDevices.length }}</p>
          </div>
        </div>
      </div>

      <!-- Section Sessions actives -->
      <div class="section">
        <h3>
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
            <path d="M12 6v6l4 2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
          Sessions actives
        </h3>
        <div v-if="sessionStore.activeSessions.length > 0" class="table-container">
          <table>
            <thead>
              <tr>
                <th>Adresse IP</th>
                <th>Début</th>
                <th>Données</th>
                <th>Statut</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="session in sessionStore.activeSessions" :key="session.id">
                <td>{{ session.ip_address }}</td>
                <td>{{ new Date(session.start_time).toLocaleString() }}</td>
                <td>{{ formatBytes(session.total_bytes) }}</td>
                <td><span class="badge active">Actif</span></td>
              </tr>
            </tbody>
          </table>
        </div>
        <p v-else class="no-data">Aucune session active</p>
      </div>
    </main>
  </div>
</template>

<style scoped>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.dashboard {
  min-height: 100vh;
  background: #f5f7fa;
}

/* Header UCAC-ICAM */
.dashboard-header {
  background: linear-gradient(135deg, #dc2626 0%, #f97316 100%);
  color: white;
  padding: 1.5rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 4px 12px rgba(220, 38, 38, 0.2);
}

.header-brand {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.logo-small {
  width: 50px;
  height: 50px;
  background: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo-small svg {
  width: 26px;
  height: 26px;
  color: #dc2626;
}

.brand-text h1 {
  font-size: 1.5rem;
  font-weight: 800;
  letter-spacing: 1px;
}

.brand-text p {
  font-size: 0.875rem;
  opacity: 0.95;
  font-weight: 300;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.user-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.25);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 1.1rem;
}

.user-name {
  font-weight: 500;
}

.btn-logout {
  background: rgba(255, 255, 255, 0.2);
  border: 1.5px solid rgba(255, 255, 255, 0.5);
  color: white;
  padding: 0.625rem 1.25rem;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
  font-size: 0.9rem;
}

.btn-logout svg {
  width: 18px;
  height: 18px;
}

.btn-logout:hover {
  background: rgba(255, 255, 255, 0.3);
  border-color: white;
  transform: translateY(-1px);
}

/* Navigation */
.nav-menu {
  background: white;
  padding: 0 2rem;
  border-bottom: 2px solid #f0f0f0;
  display: flex;
  gap: 0.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  overflow-x: auto;
}

.nav-item {
  padding: 1rem 1.25rem;
  text-decoration: none;
  color: #666;
  border-bottom: 3px solid transparent;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 500;
  white-space: nowrap;
}

.nav-item svg {
  width: 18px;
  height: 18px;
}

.nav-item:hover {
  color: #f97316;
  background: #fff8f5;
}

.nav-item.router-link-active {
  color: #dc2626;
  border-bottom-color: #dc2626;
  background: #fff5f5;
}

/* Contenu Principal */
.dashboard-content {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.dashboard-content h2 {
  margin-bottom: 2rem;
  color: #333;
  font-size: 1.75rem;
  font-weight: 700;
}

/* Grille de statistiques */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 1.5rem;
  margin-bottom: 3rem;
}

.stat-card {
  background: white;
  padding: 1.75rem;
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  display: flex;
  gap: 1.25rem;
  align-items: center;
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-icon svg {
  width: 28px;
  height: 28px;
}

.stat-icon.sessions {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.stat-icon.active {
  background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
  color: white;
}

.stat-icon.data {
  background: linear-gradient(135deg, #dc2626 0%, #f97316 100%);
  color: white;
}

.stat-icon.devices {
  background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
  color: white;
}

.stat-info h3 {
  font-size: 0.875rem;
  color: #888;
  margin-bottom: 0.5rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.stat-value {
  font-size: 2.25rem;
  font-weight: 800;
  color: #333;
  line-height: 1;
}

.stat-value.active {
  background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* Section */
.section {
  background: white;
  padding: 2rem;
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  margin-bottom: 2rem;
}

.section h3 {
  margin-bottom: 1.5rem;
  color: #333;
  font-size: 1.25rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.section h3 svg {
  width: 24px;
  height: 24px;
  color: #f97316;
}

.table-container {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  background: #f8f9fa;
  border-radius: 8px;
}

th,
td {
  padding: 1rem;
  text-align: left;
  border-bottom: 1px solid #e8e8e8;
}

th {
  font-weight: 600;
  color: #666;
  font-size: 0.875rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

tbody tr {
  transition: background 0.2s;
}

tbody tr:hover {
  background: #f8f9fa;
}

.badge {
  padding: 0.375rem 0.875rem;
  border-radius: 16px;
  font-size: 0.875rem;
  font-weight: 600;
  display: inline-block;
}

.badge.active {
  background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
  color: white;
}

.no-data {
  color: #999;
  text-align: center;
  padding: 3rem;
  font-style: italic;
}

/* Responsive */
@media (max-width: 768px) {
  .dashboard-header {
    padding: 1rem;
  }

  .brand-text h1 {
    font-size: 1.25rem;
  }

  .brand-text p {
    font-size: 0.75rem;
  }

  .user-name {
    display: none;
  }

  .nav-menu {
    padding: 0 1rem;
  }

  .nav-item {
    padding: 0.875rem 1rem;
    font-size: 0.875rem;
  }

  .dashboard-content {
    padding: 1rem;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  table {
    font-size: 0.875rem;
  }

  th,
  td {
    padding: 0.75rem 0.5rem;
  }
}

@media (max-width: 480px) {
  .logo-small {
    width: 40px;
    height: 40px;
  }

  .logo-small svg {
    width: 20px;
    height: 20px;
  }

  .btn-logout span {
    display: none;
  }

  .stat-card {
    padding: 1.25rem;
  }

  .stat-icon {
    width: 50px;
    height: 50px;
  }

  .stat-icon svg {
    width: 24px;
    height: 24px;
  }

  .stat-value {
    font-size: 1.75rem;
  }
}
</style>
