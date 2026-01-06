<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useSessionStore } from '@/stores/session'
import { useDeviceStore } from '@/stores/device'
import DisconnectionAlert from '@/components/DisconnectionAlert.vue'

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
    <!-- Header -->
    <header class="dashboard-header">
      <div class="header-brand">
        <router-link to="/" class="home-button" title="Retour a l'accueil">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M9 22V12h6v10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </router-link>
        <div class="logo-icon">
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
          <span>Deconnexion</span>
        </button>
      </div>
    </header>

    <!-- Navigation -->
    <nav class="nav-menu">
      <router-link to="/dashboard" class="nav-item">
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <rect x="3" y="3" width="7" height="7" stroke="currentColor" stroke-width="2"/>
          <rect x="14" y="3" width="7" height="7" stroke="currentColor" stroke-width="2"/>
          <rect x="14" y="14" width="7" height="7" stroke="currentColor" stroke-width="2"/>
          <rect x="3" y="14" width="7" height="7" stroke="currentColor" stroke-width="2"/>
        </svg>
        Dashboard
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
          <rect x="2" y="5" width="20" height="14" rx="2" stroke="currentColor" stroke-width="2"/>
          <line x1="2" y1="10" x2="22" y2="10" stroke="currentColor" stroke-width="2"/>
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

    <!-- Main Content -->
    <main class="dashboard-content">
      <div class="page-title">
        <h2>Tableau de bord</h2>
        <div class="status-indicator">
          <span class="status-dot"></span>
          <span>En ligne</span>
        </div>
      </div>

      <!-- Disconnection Alert -->
      <DisconnectionAlert />

      <!-- Stats Grid -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-icon orange">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
              <path d="M12 6v6l4 2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </div>
          <div class="stat-info">
            <h3>Sessions totales</h3>
            <p class="stat-value">{{ sessionStore.statistics?.total_sessions || 0 }}</p>
          </div>
          <div class="stat-glow orange"></div>
        </div>

        <div class="stat-card">
          <div class="stat-icon green">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M22 12h-4l-3 9L9 3l-3 9H2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <div class="stat-info">
            <h3>Sessions actives</h3>
            <p class="stat-value green">{{ sessionStore.statistics?.active_sessions || 0 }}</p>
          </div>
          <div class="stat-glow green"></div>
        </div>

        <div class="stat-card">
          <div class="stat-icon blue">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" stroke="currentColor" stroke-width="2"/>
            </svg>
          </div>
          <div class="stat-info">
            <h3>Donnees transferees</h3>
            <p class="stat-value">{{ formatBytes(sessionStore.statistics?.total_data_transferred || 0) }}</p>
          </div>
          <div class="stat-glow blue"></div>
        </div>

        <div class="stat-card">
          <div class="stat-icon magenta">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <rect x="2" y="3" width="20" height="14" rx="2" stroke="currentColor" stroke-width="2"/>
              <path d="M8 21h8M12 17v4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </div>
          <div class="stat-info">
            <h3>Appareils actifs</h3>
            <p class="stat-value">{{ deviceStore.activeDevices.length }}</p>
          </div>
          <div class="stat-glow magenta"></div>
        </div>
      </div>

      <!-- Active Sessions Section -->
      <div class="section">
        <div class="section-header">
          <h3>
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
              <path d="M12 6v6l4 2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
            Sessions actives
          </h3>
          <router-link to="/sessions" class="view-all">
            Voir tout
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M5 12h14M12 5l7 7-7 7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </router-link>
        </div>
        <div v-if="sessionStore.activeSessions.length > 0" class="table-container">
          <table>
            <thead>
              <tr>
                <th>Adresse IP</th>
                <th>Debut</th>
                <th>Donnees</th>
                <th>Statut</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="session in sessionStore.activeSessions" :key="session.id">
                <td class="ip-cell">{{ session.ip_address }}</td>
                <td>{{ new Date(session.start_time).toLocaleString() }}</td>
                <td>{{ formatBytes(session.total_bytes) }}</td>
                <td><span class="badge success">Actif</span></td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-else class="no-data">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
            <path d="M12 8v4M12 16h.01" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
          <p>Aucune session active</p>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.dashboard {
  min-height: 100vh;
  background: #050508;
}

/* Header */
.dashboard-header {
  background: linear-gradient(135deg, rgba(20, 20, 30, 0.95) 0%, rgba(10, 10, 15, 0.98) 100%);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(242, 148, 0, 0.2);
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-brand {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.home-button {
  width: 44px;
  height: 44px;
  background: rgba(242, 148, 0, 0.1);
  border: 1px solid rgba(242, 148, 0, 0.3);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  text-decoration: none;
  transition: all 0.3s ease;
  color: #F29400;
}

.home-button svg {
  width: 20px;
  height: 20px;
}

.home-button:hover {
  background: rgba(242, 148, 0, 0.2);
  border-color: #F29400;
  box-shadow: 0 0 20px rgba(242, 148, 0, 0.3);
}

.logo-icon {
  width: 45px;
  height: 45px;
  background: linear-gradient(135deg, #F29400 0%, #cc7a00 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 0 20px rgba(242, 148, 0, 0.3);
}

.logo-icon svg {
  width: 24px;
  height: 24px;
  color: white;
}

.brand-text h1 {
  font-family: 'Orbitron', sans-serif;
  font-size: 1.25rem;
  font-weight: 700;
  color: white;
  letter-spacing: 0.1em;
}

.brand-text p {
  font-family: 'Rajdhani', sans-serif;
  font-size: 0.8rem;
  color: #008ecf;
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.user-avatar {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: linear-gradient(135deg, #008ecf 0%, #006699 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: 'Rajdhani', sans-serif;
  font-weight: 700;
  font-size: 1.1rem;
  color: white;
}

.user-name {
  font-family: 'Rajdhani', sans-serif;
  font-weight: 600;
  color: white;
}

.btn-logout {
  background: rgba(229, 50, 18, 0.1);
  border: 1px solid rgba(229, 50, 18, 0.3);
  color: #e53212;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-family: 'Rajdhani', sans-serif;
  font-weight: 600;
  font-size: 0.9rem;
  text-transform: uppercase;
}

.btn-logout svg {
  width: 18px;
  height: 18px;
}

.btn-logout:hover {
  background: rgba(229, 50, 18, 0.2);
  border-color: #e53212;
  box-shadow: 0 0 20px rgba(229, 50, 18, 0.3);
}

/* Navigation */
.nav-menu {
  background: rgba(15, 15, 20, 0.9);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  padding: 0 2rem;
  display: flex;
  gap: 0.25rem;
  overflow-x: auto;
}

.nav-item {
  padding: 1rem 1.5rem;
  text-decoration: none;
  color: #636362;
  border-bottom: 2px solid transparent;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-family: 'Rajdhani', sans-serif;
  font-weight: 600;
  font-size: 0.9rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  white-space: nowrap;
}

.nav-item svg {
  width: 18px;
  height: 18px;
}

.nav-item:hover {
  color: #F29400;
  background: rgba(242, 148, 0, 0.05);
}

.nav-item.router-link-active {
  color: #F29400;
  border-bottom-color: #F29400;
  background: rgba(242, 148, 0, 0.1);
}

/* Main Content */
.dashboard-content {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.page-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 2rem;
}

.page-title h2 {
  font-family: 'Rajdhani', sans-serif;
  font-size: 2rem;
  font-weight: 700;
  color: white;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: rgba(0, 207, 93, 0.1);
  border: 1px solid rgba(0, 207, 93, 0.3);
  border-radius: 20px;
  font-family: 'Rajdhani', sans-serif;
  font-size: 0.85rem;
  color: #00cf5d;
  text-transform: uppercase;
}

.status-dot {
  width: 8px;
  height: 8px;
  background: #00cf5d;
  border-radius: 50%;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(0.8); }
}

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.stat-card {
  background: rgba(20, 20, 30, 0.6);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 1.5rem;
  display: flex;
  align-items: center;
  gap: 1.25rem;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.stat-card::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: linear-gradient(180deg, #F29400, #a23882);
}

.stat-card:hover {
  transform: translateY(-4px);
  border-color: rgba(242, 148, 0, 0.3);
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
}

.stat-glow {
  position: absolute;
  bottom: -50%;
  right: -20%;
  width: 150px;
  height: 150px;
  border-radius: 50%;
  filter: blur(60px);
  opacity: 0.2;
  transition: opacity 0.3s ease;
}

.stat-card:hover .stat-glow {
  opacity: 0.4;
}

.stat-glow.orange { background: #F29400; }
.stat-glow.green { background: #00cf5d; }
.stat-glow.blue { background: #008ecf; }
.stat-glow.magenta { background: #a23882; }

.stat-icon {
  width: 55px;
  height: 55px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  z-index: 1;
}

.stat-icon svg {
  width: 26px;
  height: 26px;
  color: white;
}

.stat-icon.orange {
  background: linear-gradient(135deg, #F29400 0%, #cc7a00 100%);
  box-shadow: 0 0 20px rgba(242, 148, 0, 0.4);
}

.stat-icon.green {
  background: linear-gradient(135deg, #00cf5d 0%, #00a648 100%);
  box-shadow: 0 0 20px rgba(0, 207, 93, 0.4);
}

.stat-icon.blue {
  background: linear-gradient(135deg, #008ecf 0%, #006699 100%);
  box-shadow: 0 0 20px rgba(0, 142, 207, 0.4);
}

.stat-icon.magenta {
  background: linear-gradient(135deg, #a23882 0%, #7a2962 100%);
  box-shadow: 0 0 20px rgba(162, 56, 130, 0.4);
}

.stat-info {
  position: relative;
  z-index: 1;
}

.stat-info h3 {
  font-family: 'Rajdhani', sans-serif;
  font-size: 0.8rem;
  font-weight: 500;
  color: #636362;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.25rem;
}

.stat-value {
  font-family: 'Orbitron', sans-serif;
  font-size: 1.75rem;
  font-weight: 700;
  color: white;
  line-height: 1;
}

.stat-value.green {
  color: #00cf5d;
}

/* Section */
.section {
  background: rgba(20, 20, 30, 0.6);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.section-header h3 {
  font-family: 'Rajdhani', sans-serif;
  font-size: 1.1rem;
  font-weight: 700;
  color: white;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.section-header h3 svg {
  width: 22px;
  height: 22px;
  color: #F29400;
}

.view-all {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #008ecf;
  text-decoration: none;
  font-family: 'Rajdhani', sans-serif;
  font-weight: 600;
  font-size: 0.85rem;
  text-transform: uppercase;
  transition: all 0.3s ease;
}

.view-all svg {
  width: 16px;
  height: 16px;
}

.view-all:hover {
  color: #33aee8;
}

/* Table */
.table-container {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  background: rgba(242, 148, 0, 0.1);
}

th, td {
  padding: 1rem;
  text-align: left;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

th {
  font-family: 'Rajdhani', sans-serif;
  font-size: 0.8rem;
  font-weight: 600;
  color: #F29400;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

td {
  font-family: 'Inter', sans-serif;
  font-size: 0.9rem;
  color: #ccc;
}

.ip-cell {
  font-family: 'Orbitron', sans-serif;
  color: #008ecf;
}

tbody tr {
  transition: all 0.2s ease;
}

tbody tr:hover {
  background: rgba(242, 148, 0, 0.05);
}

.badge {
  padding: 0.35rem 0.75rem;
  border-radius: 20px;
  font-family: 'Rajdhani', sans-serif;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.badge.success {
  background: rgba(0, 207, 93, 0.2);
  color: #00cf5d;
  border: 1px solid rgba(0, 207, 93, 0.3);
}

.no-data {
  text-align: center;
  padding: 3rem;
  color: #636362;
}

.no-data svg {
  width: 48px;
  height: 48px;
  margin-bottom: 1rem;
  opacity: 0.5;
}

.no-data p {
  font-family: 'Rajdhani', sans-serif;
  font-size: 1rem;
}

/* Responsive */
@media (max-width: 768px) {
  .dashboard-header {
    padding: 1rem;
    flex-wrap: wrap;
    gap: 1rem;
  }

  .brand-text h1 {
    font-size: 1rem;
  }

  .user-name {
    display: none;
  }

  .btn-logout span {
    display: none;
  }

  .nav-menu {
    padding: 0 1rem;
  }

  .nav-item {
    padding: 0.875rem 1rem;
    font-size: 0.8rem;
  }

  .dashboard-content {
    padding: 1rem;
  }

  .page-title {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }

  .page-title h2 {
    font-size: 1.5rem;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  table {
    font-size: 0.85rem;
  }

  th, td {
    padding: 0.75rem 0.5rem;
  }
}

@media (max-width: 480px) {
  .home-button {
    width: 38px;
    height: 38px;
  }

  .logo-icon {
    width: 38px;
    height: 38px;
  }

  .logo-icon svg {
    width: 20px;
    height: 20px;
  }

  .stat-card {
    padding: 1.25rem;
  }

  .stat-icon {
    width: 45px;
    height: 45px;
  }

  .stat-icon svg {
    width: 22px;
    height: 22px;
  }

  .stat-value {
    font-size: 1.5rem;
  }
}
</style>
