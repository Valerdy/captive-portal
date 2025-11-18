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
    <header class="dashboard-header">
      <h1>Portail Captif</h1>
      <div class="user-info">
        <span>{{ authStore.user?.first_name || authStore.user?.username }}</span>
        <button @click="handleLogout" class="btn-logout">Déconnexion</button>
      </div>
    </header>

    <nav class="nav-menu">
      <router-link to="/" class="nav-item">Tableau de bord</router-link>
      <router-link to="/sessions" class="nav-item">Sessions</router-link>
      <router-link to="/devices" class="nav-item">Appareils</router-link>
      <router-link to="/vouchers" class="nav-item">Vouchers</router-link>
      <router-link to="/profile" class="nav-item">Profil</router-link>
    </nav>

    <main class="dashboard-content">
      <h2>Tableau de bord</h2>

      <div class="stats-grid">
        <div class="stat-card">
          <h3>Sessions totales</h3>
          <p class="stat-value">{{ sessionStore.statistics?.total_sessions || 0 }}</p>
        </div>
        <div class="stat-card">
          <h3>Sessions actives</h3>
          <p class="stat-value active">{{ sessionStore.statistics?.active_sessions || 0 }}</p>
        </div>
        <div class="stat-card">
          <h3>Données transférées</h3>
          <p class="stat-value">
            {{ formatBytes(sessionStore.statistics?.total_data_transferred || 0) }}
          </p>
        </div>
        <div class="stat-card">
          <h3>Appareils actifs</h3>
          <p class="stat-value">{{ deviceStore.activeDevices.length }}</p>
        </div>
      </div>

      <div class="section">
        <h3>Sessions actives</h3>
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
.dashboard {
  min-height: 100vh;
  background: #f5f5f5;
}

.dashboard-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 1.5rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dashboard-header h1 {
  font-size: 1.5rem;
  margin: 0;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.btn-logout {
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid white;
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-logout:hover {
  background: rgba(255, 255, 255, 0.3);
}

.nav-menu {
  background: white;
  padding: 0 2rem;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  gap: 0.5rem;
}

.nav-item {
  padding: 1rem 1.5rem;
  text-decoration: none;
  color: #666;
  border-bottom: 3px solid transparent;
  transition: all 0.2s;
}

.nav-item:hover {
  color: #667eea;
}

.nav-item.router-link-active {
  color: #667eea;
  border-bottom-color: #667eea;
}

.dashboard-content {
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
}

.dashboard-content h2 {
  margin-bottom: 2rem;
  color: #333;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 1.5rem;
  margin-bottom: 3rem;
}

.stat-card {
  background: white;
  padding: 1.5rem;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.stat-card h3 {
  font-size: 0.9rem;
  color: #666;
  margin-bottom: 0.5rem;
}

.stat-value {
  font-size: 2rem;
  font-weight: bold;
  color: #333;
}

.stat-value.active {
  color: #4caf50;
}

.section {
  background: white;
  padding: 2rem;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  margin-bottom: 2rem;
}

.section h3 {
  margin-bottom: 1rem;
  color: #333;
}

.table-container {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  background: #f8f8f8;
}

th,
td {
  padding: 0.875rem;
  text-align: left;
  border-bottom: 1px solid #e0e0e0;
}

th {
  font-weight: 600;
  color: #666;
}

.badge {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.875rem;
  font-weight: 500;
}

.badge.active {
  background: #e8f5e9;
  color: #4caf50;
}

.no-data {
  color: #999;
  text-align: center;
  padding: 2rem;
}
</style>
