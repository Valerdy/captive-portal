<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useNotificationStore } from '@/stores/notification'
import { monitoringService, type MonitoringMetrics, type RecentActivity } from '@/services/monitoring.service'
import VueApexCharts from 'vue3-apexcharts'

const router = useRouter()
const authStore = useAuthStore()
const notificationStore = useNotificationStore()

const activeConnections = ref(0)
const bandwidth = ref(0)
const cpuUsage = ref(0)
const memoryUsage = ref(0)
const activeDevices = ref(0)
const psutilAvailable = ref(true)
const realtimeActivity = ref<RecentActivity[]>([])
const isLoading = ref(false)
const lastUpdate = ref<string>('')

// Historique pour les graphiques
const cpuHistory = ref<number[]>([0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
const memoryHistory = ref<number[]>([0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
const bandwidthHistory = ref<number[]>([0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
const timestamps = ref<string[]>([])

let updateInterval: any

// Configuration graphique CPU/Memory
const systemChartOptions = computed(() => ({
  chart: {
    type: 'area',
    height: 300,
    toolbar: { show: false },
    fontFamily: 'Inter, sans-serif',
    animations: {
      enabled: true,
      easing: 'easeinout',
      speed: 800
    }
  },
  colors: ['#3B82F6', '#A855F7'],
  dataLabels: { enabled: false },
  stroke: {
    curve: 'smooth',
    width: 3
  },
  fill: {
    type: 'gradient',
    gradient: {
      shadeIntensity: 1,
      opacityFrom: 0.5,
      opacityTo: 0.1,
      stops: [0, 90, 100]
    }
  },
  xaxis: {
    categories: timestamps.value,
    labels: {
      style: {
        colors: '#9CA3AF',
        fontSize: '12px'
      }
    }
  },
  yaxis: {
    min: 0,
    max: 100,
    labels: {
      formatter: (val: number) => `${val.toFixed(0)}%`,
      style: {
        colors: '#9CA3AF',
        fontSize: '12px'
      }
    }
  },
  grid: {
    borderColor: '#E5E7EB',
    strokeDashArray: 4
  },
  tooltip: {
    theme: 'light',
    y: {
      formatter: (val: number) => `${val.toFixed(1)}%`
    }
  },
  legend: {
    position: 'top',
    horizontalAlign: 'right',
    labels: {
      colors: '#6B7280'
    }
  }
}))

const systemChartSeries = computed(() => ([
  {
    name: 'CPU',
    data: cpuHistory.value
  },
  {
    name: 'Mémoire',
    data: memoryHistory.value
  }
]))

// Configuration graphique Bande passante
const bandwidthChartOptions = computed(() => ({
  chart: {
    type: 'area',
    height: 300,
    toolbar: { show: false },
    fontFamily: 'Inter, sans-serif',
    animations: {
      enabled: true,
      easing: 'easeinout',
      speed: 800
    }
  },
  colors: ['#F97316'],
  dataLabels: { enabled: false },
  stroke: {
    curve: 'smooth',
    width: 3
  },
  fill: {
    type: 'gradient',
    gradient: {
      shadeIntensity: 1,
      opacityFrom: 0.7,
      opacityTo: 0.2,
      stops: [0, 90, 100]
    }
  },
  xaxis: {
    categories: timestamps.value,
    labels: {
      style: {
        colors: '#9CA3AF',
        fontSize: '12px'
      }
    }
  },
  yaxis: {
    min: 0,
    labels: {
      formatter: (val: number) => `${val.toFixed(1)} MB/s`,
      style: {
        colors: '#9CA3AF',
        fontSize: '12px'
      }
    }
  },
  grid: {
    borderColor: '#E5E7EB',
    strokeDashArray: 4
  },
  tooltip: {
    theme: 'light',
    y: {
      formatter: (val: number) => `${val.toFixed(2)} MB/s`
    }
  }
}))

const bandwidthChartSeries = computed(() => ([
  {
    name: 'Bande passante',
    data: bandwidthHistory.value
  }
]))

async function fetchMetrics() {
  try {
    isLoading.value = true
    const metrics: MonitoringMetrics = await monitoringService.getMetrics()

    activeConnections.value = metrics.active_connections
    bandwidth.value = metrics.bandwidth
    cpuUsage.value = Math.round(metrics.cpu_usage)
    memoryUsage.value = Math.round(metrics.memory_usage)
    activeDevices.value = metrics.active_devices
    psutilAvailable.value = metrics.psutil_available
    realtimeActivity.value = metrics.recent_activity
    lastUpdate.value = new Date(metrics.timestamp).toLocaleTimeString('fr-FR')

    // Mettre à jour l'historique
    cpuHistory.value.push(cpuUsage.value)
    memoryHistory.value.push(memoryUsage.value)
    bandwidthHistory.value.push(bandwidth.value)

    const now = new Date()
    timestamps.value.push(now.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit', second: '2-digit' }))

    // Garder seulement les 10 dernières valeurs
    if (cpuHistory.value.length > 10) {
      cpuHistory.value.shift()
      memoryHistory.value.shift()
      bandwidthHistory.value.shift()
      timestamps.value.shift()
    }
  } catch (error: any) {
    console.error('Erreur lors de la récupération des métriques:', error)
    if (error.response?.status !== 401) {
      notificationStore.error('Erreur lors de la récupération des métriques')
    }
  } finally {
    isLoading.value = false
  }
}

onMounted(async () => {
  if (!authStore.isAdmin) {
    notificationStore.error('Accès refusé')
    router.push('/')
    return
  }

  // Initialiser les timestamps
  const now = new Date()
  for (let i = 9; i >= 0; i--) {
    const time = new Date(now.getTime() - i * 3000)
    timestamps.value.push(time.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit', second: '2-digit' }))
  }

  // Récupérer les métriques immédiatement
  await fetchMetrics()

  // Mettre à jour toutes les 3 secondes
  updateInterval = setInterval(fetchMetrics, 3000)
})

onUnmounted(() => {
  if (updateInterval) {
    clearInterval(updateInterval)
  }
})

function goBack() {
  router.push('/admin/dashboard')
}
</script>

<template>
  <div class="admin-monitoring">
    <!-- Header professionnel -->
    <header class="dashboard-header">
      <div class="header-container">
        <div class="logo-section">
          <div class="logo-icon">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M2 17L12 22L22 17" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M2 12L12 17L22 12" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <div class="logo-text">
            <div class="logo-title">UCAC-ICAM</div>
            <div class="logo-subtitle">Portail Captif</div>
          </div>
        </div>

        <nav class="nav-menu">
          <router-link to="/admin/dashboard" class="nav-link">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <rect x="3" y="3" width="7" height="7" stroke="currentColor" stroke-width="2"/>
              <rect x="14" y="3" width="7" height="7" stroke="currentColor" stroke-width="2"/>
              <rect x="14" y="14" width="7" height="7" stroke="currentColor" stroke-width="2"/>
              <rect x="3" y="14" width="7" height="7" stroke="currentColor" stroke-width="2"/>
            </svg>
            Dashboard
          </router-link>
          <router-link to="/admin/users" class="nav-link">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2"/>
              <circle cx="9" cy="7" r="4" stroke="currentColor" stroke-width="2"/>
              <path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" stroke="currentColor" stroke-width="2"/>
            </svg>
            Utilisateurs
          </router-link>
          <router-link to="/admin/sites" class="nav-link">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
              <line x1="2" y1="12" x2="22" y2="12" stroke="currentColor" stroke-width="2"/>
              <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" stroke="currentColor" stroke-width="2"/>
            </svg>
            Sites
          </router-link>
          <router-link to="/admin/quotas" class="nav-link">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <line x1="12" y1="1" x2="12" y2="23" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
            Quotas
          </router-link>
          <router-link to="/admin/monitoring" class="nav-link active">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            Monitoring
          </router-link>
        </nav>

        <button @click="authStore.logout" class="btn-logout">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          Déconnexion
        </button>
      </div>
    </header>

    <!-- Page principale -->
    <main class="page-main">
      <div class="page-title-section">
        <button @click="goBack" class="back-btn">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M19 12H5M5 12l7 7m-7-7 7-7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
        <div>
          <h1>Monitoring en temps réel</h1>
          <p class="page-subtitle">Surveillance de l'activité réseau</p>
          <span v-if="lastUpdate" class="last-update">
            <span class="update-dot"></span>
            Dernière mise à jour: {{ lastUpdate }}
          </span>
        </div>
      </div>

      <!-- Warning si psutil non disponible -->
      <div v-if="!psutilAvailable" class="warning-banner">
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <span>Le module psutil n'est pas installé. Les métriques CPU et mémoire ne sont pas disponibles. Exécutez: <code>pip install psutil</code></span>
      </div>

      <!-- Statistiques -->
      <div class="stats-row">
        <div class="stat-box">
          <div class="stat-icon" style="background: #D1FAE5; color: #10B981;">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
              <path d="M12 6v6l4 2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ activeConnections }}</div>
            <div class="stat-label">Connexions actives</div>
          </div>
        </div>

        <div class="stat-box">
          <div class="stat-icon" style="background: #FED7AA; color: #F97316;">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <polyline points="17 6 23 6 23 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ bandwidth.toFixed(2) }}</div>
            <div class="stat-label">MB/s · Bande passante</div>
          </div>
        </div>

        <div class="stat-box">
          <div class="stat-icon" style="background: #DBEAFE; color: #3B82F6;">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <rect x="4" y="4" width="16" height="16" rx="2" stroke="currentColor" stroke-width="2"/>
              <rect x="9" y="9" width="6" height="6" stroke="currentColor" stroke-width="2"/>
            </svg>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ cpuUsage }}%</div>
            <div class="stat-label">CPU utilisé</div>
          </div>
        </div>

        <div class="stat-box">
          <div class="stat-icon" style="background: #E9D5FF; color: #A855F7;">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M2 16.1A5 5 0 0 1 5.9 20M2 12.05A9 9 0 0 1 9.95 20M2 8V6a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ memoryUsage }}%</div>
            <div class="stat-label">Mémoire utilisée</div>
          </div>
        </div>
      </div>

      <!-- Graphiques -->
      <div class="charts-grid">
        <!-- Graphique CPU/Mémoire -->
        <div class="chart-card">
          <div class="chart-header">
            <div class="chart-title">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect x="4" y="4" width="16" height="16" rx="2" stroke="currentColor" stroke-width="2"/>
                <rect x="9" y="9" width="6" height="6" stroke="currentColor" stroke-width="2"/>
              </svg>
              <h3>Ressources système</h3>
            </div>
            <span class="live-badge">
              <span class="pulse-dot"></span>
              En direct
            </span>
          </div>
          <div class="chart-content">
            <VueApexCharts
              type="area"
              height="300"
              :options="systemChartOptions"
              :series="systemChartSeries"
            />
          </div>
        </div>

        <!-- Graphique Bande passante -->
        <div class="chart-card">
          <div class="chart-header">
            <div class="chart-title">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <polyline points="17 6 23 6 23 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              <h3>Bande passante réseau</h3>
            </div>
            <span class="live-badge">
              <span class="pulse-dot"></span>
              En direct
            </span>
          </div>
          <div class="chart-content">
            <VueApexCharts
              type="area"
              height="300"
              :options="bandwidthChartOptions"
              :series="bandwidthChartSeries"
            />
          </div>
        </div>
      </div>

      <!-- Activité récente -->
      <div class="activity-card">
        <div class="activity-header">
          <div class="activity-title">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <h3>Activité récente</h3>
          </div>
          <span class="live-badge">
            <span class="pulse-dot"></span>
            {{ realtimeActivity.length }} événements
          </span>
        </div>

        <div v-if="realtimeActivity.length === 0" class="empty-activity">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
            <line x1="12" y1="8" x2="12" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            <line x1="12" y1="16" x2="12.01" y2="16" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
          <p>Aucune activité récente</p>
        </div>

        <div v-else class="activity-table">
          <table class="data-table">
            <thead>
              <tr>
                <th>Heure</th>
                <th>Utilisateur</th>
                <th>Action</th>
                <th>Adresse IP</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(activity, index) in realtimeActivity" :key="index">
                <td>
                  <span class="activity-time">{{ activity.time }}</span>
                </td>
                <td>
                  <div class="user-cell">
                    <div class="user-avatar-tiny">
                      {{ activity.user.charAt(0).toUpperCase() }}
                    </div>
                    <span class="user-name">{{ activity.user }}</span>
                  </div>
                </td>
                <td>
                  <span class="activity-action">{{ activity.action }}</span>
                </td>
                <td>
                  <span class="activity-ip">{{ activity.ip }}</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

* {
  font-family: 'Inter', sans-serif;
}

.admin-monitoring {
  min-height: 100vh;
  background: #F9FAFB;
}

/* Header professionnel */
.dashboard-header {
  background: #FFFFFF;
  border-bottom: 1px solid #E5E7EB;
  padding: 1rem 2rem;
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-container {
  max-width: 1400px;
  margin: 0 auto;
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
  width: 50px;
  height: 50px;
  background: linear-gradient(135deg, #DC2626 0%, #F97316 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(220, 38, 38, 0.2);
}

.logo-icon svg {
  width: 28px;
  height: 28px;
}

.logo-text {
  display: flex;
  flex-direction: column;
}

.logo-title {
  font-size: 1.25rem;
  font-weight: 800;
  color: #111827;
  letter-spacing: -0.5px;
}

.logo-subtitle {
  font-size: 0.75rem;
  color: #6B7280;
  font-weight: 500;
}

.nav-menu {
  display: flex;
  gap: 0.5rem;
  flex: 1;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.625rem 1rem;
  border-radius: 8px;
  font-size: 0.95rem;
  font-weight: 600;
  color: #6B7280;
  text-decoration: none;
  transition: all 0.2s ease;
}

.nav-link svg {
  width: 18px;
  height: 18px;
}

.nav-link:hover {
  background: #F3F4F6;
  color: #111827;
}

.nav-link.active {
  background: linear-gradient(135deg, #DC2626 0%, #F97316 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(220, 38, 38, 0.2);
}

.btn-logout {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.625rem 1.25rem;
  background: #FEE2E2;
  color: #DC2626;
  border: 1px solid #FECACA;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.95rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-logout:hover {
  background: #FEF2F2;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(220, 38, 38, 0.15);
}

.btn-logout svg {
  width: 18px;
  height: 18px;
}

/* Page principale */
.page-main {
  max-width: 1400px;
  margin: 0 auto;
  padding: 2rem;
}

.page-title-section {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 2rem;
}

.back-btn {
  width: 40px;
  height: 40px;
  background: #FFFFFF;
  border: 1px solid #E5E7EB;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  color: #6B7280;
  flex-shrink: 0;
}

.back-btn:hover {
  background: #F3F4F6;
  color: #111827;
  transform: translateX(-2px);
}

.back-btn svg {
  width: 20px;
  height: 20px;
}

.page-title-section h1 {
  font-size: 2rem;
  font-weight: 800;
  color: #111827;
  margin: 0;
}

.page-subtitle {
  color: #6B7280;
  font-size: 0.95rem;
  margin: 0.25rem 0 0.5rem 0;
}

.last-update {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.375rem 0.875rem;
  background: #D1FAE5;
  border: 1px solid #A7F3D0;
  border-radius: 6px;
  color: #059669;
  font-size: 0.85rem;
  font-weight: 600;
}

.update-dot {
  width: 8px;
  height: 8px;
  background: #10B981;
  border-radius: 50%;
  animation: pulse-dot 2s ease-in-out infinite;
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(0.9); }
}

/* Warning banner */
.warning-banner {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem 1.5rem;
  margin-bottom: 2rem;
  background: #FEF3C7;
  border: 1px solid #FDE68A;
  border-left: 4px solid #F59E0B;
  border-radius: 12px;
  color: #92400E;
}

.warning-banner svg {
  width: 24px;
  height: 24px;
  flex-shrink: 0;
  color: #F59E0B;
}

.warning-banner code {
  background: #FDE68A;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 0.9rem;
}

/* Statistiques */
.stats-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.stat-box {
  background: #FFFFFF;
  border: 1px solid #E5E7EB;
  border-radius: 12px;
  padding: 1.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  transition: all 0.2s ease;
}

.stat-box:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  transform: translateY(-2px);
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-icon svg {
  width: 28px;
  height: 28px;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 2rem;
  font-weight: 800;
  color: #111827;
  line-height: 1;
  margin-bottom: 0.25rem;
}

.stat-label {
  color: #6B7280;
  font-size: 0.9rem;
  font-weight: 500;
}

/* Graphiques */
.charts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.chart-card {
  background: #FFFFFF;
  border: 1px solid #E5E7EB;
  border-radius: 12px;
  padding: 1.5rem;
}

.chart-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.5rem;
}

.chart-title {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.chart-title svg {
  width: 24px;
  height: 24px;
  color: #6B7280;
}

.chart-title h3 {
  font-size: 1.125rem;
  font-weight: 700;
  color: #111827;
  margin: 0;
}

.live-badge {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.375rem 0.875rem;
  background: #D1FAE5;
  border: 1px solid #A7F3D0;
  border-radius: 6px;
  color: #059669;
  font-size: 0.85rem;
  font-weight: 600;
}

.pulse-dot {
  width: 8px;
  height: 8px;
  background: #10B981;
  border-radius: 50%;
  animation: pulse-dot 2s ease-in-out infinite;
}

.chart-content {
  position: relative;
}

/* Activité récente */
.activity-card {
  background: #FFFFFF;
  border: 1px solid #E5E7EB;
  border-radius: 12px;
  padding: 1.5rem;
}

.activity-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.5rem;
}

.activity-title {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.activity-title svg {
  width: 24px;
  height: 24px;
  color: #6B7280;
}

.activity-title h3 {
  font-size: 1.125rem;
  font-weight: 700;
  color: #111827;
  margin: 0;
}

.empty-activity {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem;
  color: #9CA3AF;
}

.empty-activity svg {
  width: 64px;
  height: 64px;
  margin-bottom: 1rem;
  color: #D1D5DB;
}

.activity-table {
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table thead tr {
  border-bottom: 2px solid #E5E7EB;
}

.data-table th {
  text-align: left;
  padding: 1rem;
  font-weight: 700;
  color: #6B7280;
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.data-table tbody tr {
  border-bottom: 1px solid #F3F4F6;
  transition: all 0.2s ease;
}

.data-table tbody tr:hover {
  background: #F9FAFB;
}

.data-table td {
  padding: 1rem;
  color: #374151;
  font-size: 0.95rem;
}

.activity-time {
  color: #6B7280;
  font-size: 0.9rem;
  font-family: 'Courier New', monospace;
}

.user-cell {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.user-avatar-tiny {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #DC2626 0%, #F97316 100%);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 700;
  font-size: 0.85rem;
}

.user-name {
  font-weight: 600;
  color: #111827;
}

.activity-action {
  color: #374151;
}

.activity-ip {
  padding: 0.375rem 0.875rem;
  background: #FED7AA;
  border: 1px solid #FDBA74;
  border-radius: 6px;
  color: #C2410C;
  font-size: 0.85rem;
  font-family: 'Courier New', monospace;
  font-weight: 600;
}

@media (max-width: 768px) {
  .header-container {
    flex-wrap: wrap;
  }

  .nav-menu {
    order: 3;
    width: 100%;
    flex-wrap: wrap;
  }

  .page-main {
    padding: 1rem;
  }

  .stats-row {
    grid-template-columns: 1fr;
  }

  .charts-grid {
    grid-template-columns: 1fr;
  }

  .data-table {
    font-size: 0.85rem;
  }

  .data-table th,
  .data-table td {
    padding: 0.75rem 0.5rem;
  }
}
</style>
