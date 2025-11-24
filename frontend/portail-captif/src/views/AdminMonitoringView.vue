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
    <header class="page-header">
      <button @click="goBack" class="back-btn">
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M19 12H5M5 12l7 7m-7-7 7-7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        Retour
      </button>

      <div class="header-info">
        <h1>Monitoring en temps réel</h1>
        <p>Surveillance de l'activité réseau</p>
        <span v-if="lastUpdate" class="last-update">
          <span class="update-dot"></span>
          Dernière mise à jour: {{ lastUpdate }}
        </span>
      </div>
    </header>

    <main class="page-content">
      <!-- Warning if psutil not available -->
      <div v-if="!psutilAvailable" class="warning-banner">
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <span>Le module psutil n'est pas installé. Les métriques CPU et mémoire ne sont pas disponibles. Exécutez: <code>pip install psutil</code></span>
      </div>

      <!-- Métriques en temps réel -->
      <div class="metrics-grid">
        <div class="metric-card">
          <div class="metric-icon pulse">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
              <path d="M12 6v6l4 2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </div>
          <div class="metric-info">
            <h3>{{ activeConnections }}</h3>
            <p>Connexions actives</p>
          </div>
        </div>

        <div class="metric-card">
          <div class="metric-icon bandwidth">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <polyline points="17 6 23 6 23 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <div class="metric-info">
            <h3>{{ bandwidth.toFixed(2) }} MB/s</h3>
            <p>Bande passante</p>
          </div>
        </div>

        <div class="metric-card">
          <div class="metric-icon cpu">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <rect x="4" y="4" width="16" height="16" rx="2" stroke="currentColor" stroke-width="2"/>
              <rect x="9" y="9" width="6" height="6" stroke="currentColor" stroke-width="2"/>
            </svg>
          </div>
          <div class="metric-info">
            <h3>{{ cpuUsage }}%</h3>
            <p>CPU</p>
          </div>
          <div class="progress-bar">
            <div class="progress" :style="{ width: cpuUsage + '%' }"></div>
          </div>
        </div>

        <div class="metric-card">
          <div class="metric-icon memory">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M2 16.1A5 5 0 0 1 5.9 20M2 12.05A9 9 0 0 1 9.95 20M2 8V6a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </div>
          <div class="metric-info">
            <h3>{{ memoryUsage }}%</h3>
            <p>Mémoire</p>
          </div>
          <div class="progress-bar">
            <div class="progress memory-progress" :style="{ width: memoryUsage + '%' }"></div>
          </div>
        </div>
      </div>

      <!-- Graphiques -->
      <div class="charts-section">
        <div class="chart-card">
          <div class="chart-header">
            <h3>Ressources système (CPU / Mémoire)</h3>
            <span class="live-indicator">
              <span class="pulse-dot"></span>
              En direct
            </span>
          </div>
          <VueApexCharts
            type="area"
            height="300"
            :options="systemChartOptions"
            :series="systemChartSeries"
          />
        </div>

        <div class="chart-card">
          <div class="chart-header">
            <h3>Bande passante réseau</h3>
            <span class="live-indicator">
              <span class="pulse-dot"></span>
              En direct
            </span>
          </div>
          <VueApexCharts
            type="area"
            height="300"
            :options="bandwidthChartOptions"
            :series="bandwidthChartSeries"
          />
        </div>
      </div>

      <!-- Activité en temps réel -->
      <div class="activity-card">
        <div class="activity-header">
          <h2>Activité récente</h2>
          <span class="live-indicator">
            <span class="pulse-dot"></span>
            En direct
          </span>
        </div>

        <div v-if="realtimeActivity.length === 0" class="no-activity">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
            <line x1="12" y1="8" x2="12" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            <line x1="12" y1="16" x2="12.01" y2="16" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
          <p>Aucune activité récente</p>
        </div>

        <div v-else class="activity-list">
          <div v-for="(activity, index) in realtimeActivity" :key="index" class="activity-item">
            <div class="activity-time">{{ activity.time }}</div>
            <div class="activity-content">
              <span class="activity-user">{{ activity.user }}</span>
              <span class="activity-action">{{ activity.action }}</span>
              <span class="activity-ip">{{ activity.ip }}</span>
            </div>
          </div>
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
  padding: 2rem;
}

.page-header {
  max-width: 1400px;
  margin: 0 auto 2rem;
}

.back-btn {
  background: #FFFFFF;
  border: 1px solid #E5E7EB;
  border-radius: 12px;
  padding: 0.75rem 1.25rem;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  transition: all 0.3s ease;
  color: #6B7280;
  margin-bottom: 1.5rem;
}

.back-btn:hover {
  background: #F3F4F6;
  color: #111827;
  transform: translateX(-4px);
}

.back-btn svg {
  width: 20px;
  height: 20px;
}

.header-info h1 {
  font-size: 2rem;
  font-weight: 800;
  margin-bottom: 0.5rem;
  color: #111827;
}

.header-info p {
  color: #6B7280;
  margin-bottom: 0.5rem;
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

.page-content {
  max-width: 1400px;
  margin: 0 auto;
}

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

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.metric-card {
  background: #FFFFFF;
  border: 1px solid #E5E7EB;
  border-radius: 16px;
  padding: 1.75rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  position: relative;
  overflow: hidden;
}

.metric-icon {
  width: 60px;
  height: 60px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 1rem;
}

.metric-icon svg {
  width: 30px;
  height: 30px;
}

.metric-icon.pulse {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    box-shadow: 0 0 20px rgba(16, 185, 129, 0.3);
  }
  50% {
    box-shadow: 0 0 40px rgba(16, 185, 129, 0.6);
  }
}

.metric-icon.bandwidth {
  background: rgba(249, 115, 22, 0.1);
  color: #f97316;
}

.metric-icon.cpu {
  background: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
}

.metric-icon.memory {
  background: rgba(168, 85, 247, 0.1);
  color: #a855f7;
}

.metric-info h3 {
  font-size: 2rem;
  font-weight: 800;
  margin-bottom: 0.25rem;
  color: #111827;
}

.metric-info p {
  color: #6B7280;
  font-size: 0.9rem;
}

.progress-bar {
  margin-top: 1rem;
  height: 6px;
  background: #E5E7EB;
  border-radius: 3px;
  overflow: hidden;
}

.progress {
  height: 100%;
  background: linear-gradient(90deg, #3b82f6, #60a5fa);
  transition: width 0.5s ease;
  border-radius: 3px;
}

.memory-progress {
  background: linear-gradient(90deg, #a855f7, #c084fc);
}

.charts-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.chart-card {
  background: #FFFFFF;
  border: 1px solid #E5E7EB;
  border-radius: 16px;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.chart-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.5rem;
}

.chart-header h3 {
  font-size: 1.125rem;
  font-weight: 700;
  color: #111827;
  margin: 0;
}

.live-indicator {
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

.activity-card {
  background: #FFFFFF;
  border: 1px solid #E5E7EB;
  border-radius: 16px;
  padding: 2rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.activity-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.5rem;
}

.activity-header h2 {
  font-size: 1.5rem;
  font-weight: 800;
  color: #111827;
}

.no-activity {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem;
  color: #9CA3AF;
}

.no-activity svg {
  width: 64px;
  height: 64px;
  margin-bottom: 1rem;
  color: #D1D5DB;
}

.activity-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.activity-item {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  padding: 1.25rem;
  background: #F9FAFB;
  border: 1px solid #E5E7EB;
  border-radius: 12px;
  transition: all 0.3s ease;
}

.activity-item:hover {
  background: #F3F4F6;
  border-color: #F97316;
}

.activity-time {
  font-size: 0.85rem;
  color: #6B7280;
  min-width: 100px;
  font-family: monospace;
}

.activity-content {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex: 1;
}

.activity-user {
  font-weight: 600;
  color: #3B82F6;
}

.activity-action {
  color: #111827;
}

.activity-ip {
  margin-left: auto;
  padding: 0.375rem 0.875rem;
  background: #FED7AA;
  border: 1px solid #FDBA74;
  border-radius: 8px;
  color: #C2410C;
  font-size: 0.85rem;
  font-family: monospace;
  font-weight: 600;
}

@media (max-width: 768px) {
  .admin-monitoring {
    padding: 1rem;
  }

  .metrics-grid {
    grid-template-columns: 1fr;
  }

  .charts-section {
    grid-template-columns: 1fr;
  }

  .activity-item {
    flex-direction: column;
    align-items: flex-start;
  }

  .activity-content {
    flex-direction: column;
    align-items: flex-start;
  }

  .activity-ip {
    margin-left: 0;
  }
}
</style>
