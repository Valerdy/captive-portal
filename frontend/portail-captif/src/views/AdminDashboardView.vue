<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useSessionStore } from '@/stores/session'
import { useDeviceStore } from '@/stores/device'
import { useUserStore } from '@/stores/user'
import { useNotificationStore } from '@/stores/notification'
import { useProfileStore } from '@/stores/profile'
import AdminLayout from '@/layouts/AdminLayout.vue'
import VueApexCharts from 'vue3-apexcharts'

const router = useRouter()
const authStore = useAuthStore()
const sessionStore = useSessionStore()
const deviceStore = useDeviceStore()
const userStore = useUserStore()
const notificationStore = useNotificationStore()
const profileStore = useProfileStore()

const isLoading = ref(true)

// Calculer les statistiques en temps réel
const activeSessions = computed(() =>
  sessionStore.sessions.filter(s => s.status === 'active').length
)

const activeDevices = computed(() =>
  deviceStore.devices.filter(d => d.is_active).length
)

const activeUsers = computed(() =>
  userStore.users.filter(u => u.is_active).length
)

// Calculer la bande passante totale à partir des sessions (en GB)
const totalBandwidth = computed(() => {
  const totalBytes = sessionStore.sessions.reduce((sum, session) => {
    const sessionBytes = (session.bytes_in || 0) + (session.bytes_out || 0)
    return sum + sessionBytes
  }, 0)
  return Math.round(totalBytes / (1024 * 1024 * 1024)) // Convertir en GB
})

// Calculer la bande passante d'aujourd'hui
const todayBandwidth = computed(() => {
  const today = new Date()
  today.setHours(0, 0, 0, 0)

  const todayBytes = sessionStore.sessions
    .filter(session => {
      const sessionDate = new Date(session.start_time)
      return sessionDate >= today
    })
    .reduce((sum, session) => {
      const sessionBytes = (session.bytes_in || 0) + (session.bytes_out || 0)
      return sum + sessionBytes
    }, 0)

  return Math.round(todayBytes / (1024 * 1024 * 1024)) // Convertir en GB
})

// Stats calculées
const stats = computed(() => ({
  totalUsers: userStore.users.length,
  activeUsers: activeUsers.value,
  totalSessions: sessionStore.sessions.length,
  activeSessions: activeSessions.value,
  totalDevices: deviceStore.devices.length,
  activeDevices: activeDevices.value,
  totalBandwidth: totalBandwidth.value,
  todayBandwidth: todayBandwidth.value
}))

// Stats de profils
const profileStats = computed(() => {
  if (!profileStore.statistics) return null
  return profileStore.statistics.summary
})

const topProfiles = computed(() => {
  if (!profileStore.statistics) return []
  return profileStore.statistics.top_profiles || []
})

// Graphique de bande passante (24h)
const bandwidthChartOptions = computed(() => ({
  chart: {
    type: 'area',
    height: 350,
    toolbar: { show: false },
    fontFamily: 'Inter, sans-serif'
  },
  colors: ['#F97316'],
  dataLabels: { enabled: false },
  stroke: { curve: 'smooth', width: 3 },
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
    categories: Array.from({ length: 7 }, (_, i) => `${i * 4}h`),
    labels: { style: { colors: '#6B7280', fontSize: '12px' } }
  },
  yaxis: {
    labels: {
      style: { colors: '#6B7280', fontSize: '12px' },
      formatter: (val: number) => `${val} MB`
    }
  },
  grid: { borderColor: '#E5E7EB' },
  tooltip: {
    theme: 'light',
    y: { formatter: (val: number) => `${val} MB` }
  }
}))

const bandwidthChartSeries = computed(() => {
  const hours = Array.from({ length: 7 }, (_, i) => i * 4)
  const data = hours.map(hour => {
    const hourStart = new Date()
    hourStart.setHours(hour, 0, 0, 0)
    const hourEnd = new Date()
    hourEnd.setHours(hour + 4, 0, 0, 0)

    const hourBytes = sessionStore.sessions
      .filter(session => {
        const sessionDate = new Date(session.start_time)
        return sessionDate >= hourStart && sessionDate < hourEnd
      })
      .reduce((sum, session) => {
        return sum + (session.bytes_in || 0) + (session.bytes_out || 0)
      }, 0)

    return Math.round(hourBytes / (1024 * 1024))
  })

  return [{ name: 'Bande passante', data }]
})

// Graphique d'activité utilisateur (7 jours)
const userActivityChartOptions = computed(() => ({
  chart: {
    type: 'bar',
    height: 350,
    toolbar: { show: false },
    fontFamily: 'Inter, sans-serif'
  },
  colors: ['#DC2626'],
  plotOptions: {
    bar: {
      borderRadius: 8,
      columnWidth: '60%'
    }
  },
  dataLabels: { enabled: false },
  xaxis: {
    categories: ['Dim', 'Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam'],
    labels: { style: { colors: '#6B7280', fontSize: '12px' } }
  },
  yaxis: {
    labels: {
      style: { colors: '#6B7280', fontSize: '12px' },
      formatter: (val: number) => `${val}`
    }
  },
  grid: { borderColor: '#E5E7EB' },
  tooltip: {
    theme: 'light',
    y: { formatter: (val: number) => `${val} utilisateurs` }
  }
}))

const userActivityChartSeries = computed(() => {
  const last7Days = Array.from({ length: 7 }, (_, i) => {
    const date = new Date()
    date.setDate(date.getDate() - (6 - i))
    return date
  })

  const data = last7Days.map((date) => {
    const dayStart = new Date(date)
    dayStart.setHours(0, 0, 0, 0)
    const dayEnd = new Date(date)
    dayEnd.setHours(23, 59, 59, 999)

    const uniqueUsers = new Set(
      sessionStore.sessions
        .filter(session => {
          const sessionDate = new Date(session.start_time)
          return sessionDate >= dayStart && sessionDate <= dayEnd
        })
        .map(session => session.user)
    )

    return uniqueUsers.size
  })

  return [{ name: 'Utilisateurs actifs', data }]
})


onMounted(async () => {
  if (!authStore.isAdmin) {
    notificationStore.error('Accès refusé')
    router.push('/')
    return
  }

  try {
    await Promise.all([
      userStore.fetchUsers(),
      sessionStore.fetchSessions(),
      deviceStore.fetchDevices(),
      profileStore.fetchStatistics()
    ])
  } catch (error: any) {
    const message = error?.message || 'Erreur inconnue'
    notificationStore.error(`Erreur lors du chargement des données du dashboard: ${message}`)
    console.error('Erreur chargement dashboard:', error)
  } finally {
    isLoading.value = false
  }
})
</script>

<template>
  <AdminLayout activePage="dashboard">
      <div class="content-wrapper">
        <!-- Cartes de statistiques -->
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-icon users">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2M9 7a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" stroke="currentColor" stroke-width="2"/>
              </svg>
            </div>
            <div class="stat-content">
              <h3>{{ stats.totalUsers }}</h3>
              <p>Utilisateurs totaux</p>
              <span class="stat-badge success">{{ stats.activeUsers }} actifs</span>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-icon sessions">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                <polyline points="12 6 12 12 16 14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </div>
            <div class="stat-content">
              <h3>{{ stats.totalSessions }}</h3>
              <p>Sessions totales</p>
              <span class="stat-badge info">{{ stats.activeSessions }} en cours</span>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-icon devices">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect x="5" y="2" width="14" height="20" rx="2" ry="2" stroke="currentColor" stroke-width="2"/>
                <line x1="12" y1="18" x2="12.01" y2="18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </div>
            <div class="stat-content">
              <h3>{{ stats.totalDevices }}</h3>
              <p>Appareils enregistrés</p>
              <span class="stat-badge warning">{{ stats.activeDevices }} connectés</span>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-icon bandwidth">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <polyline points="17 6 23 6 23 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
            <div class="stat-content">
              <h3>{{ stats.todayBandwidth }} GB</h3>
              <p>Bande passante (aujourd'hui)</p>
              <span class="stat-badge danger">Total: {{ stats.totalBandwidth }} GB</span>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-icon profiles">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2"/>
                <circle cx="12" cy="7" r="4" stroke="currentColor" stroke-width="2"/>
              </svg>
            </div>
            <div class="stat-content">
              <h3>{{ profileStats?.total_profiles || 0 }}</h3>
              <p>Profils créés</p>
              <span class="stat-badge success">{{ profileStats?.active_profiles || 0 }} actifs</span>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-icon quota">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                <path d="M12 6v6l4 2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </div>
            <div class="stat-content">
              <h3>{{ profileStats?.limited_profiles || 0 }}</h3>
              <p>Profils avec quota limité</p>
              <span class="stat-badge warning">{{ profileStats?.unlimited_profiles || 0 }} illimités</span>
            </div>
          </div>
        </div>

        <!-- Graphiques -->
        <div class="charts-section">
          <div class="chart-card">
            <div class="chart-header">
              <h2>Bande passante sur 24h</h2>
              <p class="chart-subtitle">Consommation par période de 4 heures</p>
            </div>
            <div class="chart-body">
              <VueApexCharts
                type="area"
                height="350"
                :options="bandwidthChartOptions"
                :series="bandwidthChartSeries"
              />
            </div>
          </div>

          <div class="chart-card">
            <div class="chart-header">
              <h2>Activité utilisateurs (7 jours)</h2>
              <p class="chart-subtitle">Nombre d'utilisateurs actifs par jour</p>
            </div>
            <div class="chart-body">
              <VueApexCharts
                type="bar"
                height="350"
                :options="userActivityChartOptions"
                :series="userActivityChartSeries"
              />
            </div>
          </div>

        </div>
      </div>
  </AdminLayout>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Rajdhani:wght@300;400;500;600;700&family:Inter:wght@300;400;500;600;700;800&display=swap');

/* Contenu spécifique au dashboard - Dark Theme */
.content-wrapper {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

/* Statistiques */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.5rem;
}

.stat-card {
  background: rgba(15, 15, 25, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 1.5rem;
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  transition: all 0.3s;
}

.stat-card:hover {
  border-color: rgba(0, 142, 207, 0.3);
  box-shadow: 0 8px 32px rgba(0, 142, 207, 0.15);
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

.stat-icon.users {
  background: rgba(0, 142, 207, 0.2);
  color: #008ecf;
}

.stat-icon.sessions {
  background: rgba(242, 148, 0, 0.2);
  color: #F29400;
}

.stat-icon.devices {
  background: rgba(16, 185, 129, 0.2);
  color: #10B981;
}

.stat-icon.bandwidth {
  background: rgba(229, 50, 18, 0.2);
  color: #e53212;
}

.stat-icon.profiles {
  background: rgba(162, 56, 130, 0.2);
  color: #a23882;
}

.stat-icon.quota {
  background: rgba(162, 56, 130, 0.2);
  color: #a23882;
}

.stat-content {
  flex: 1;
}

.stat-content h3 {
  font-family: 'Orbitron', monospace;
  font-size: 2rem;
  font-weight: 800;
  color: #F29400;
  line-height: 1;
  margin-bottom: 0.5rem;
  text-shadow: 0 0 15px rgba(242, 148, 0, 0.3);
}

.stat-content p {
  font-family: 'Rajdhani', sans-serif;
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.6);
  font-weight: 500;
  margin-bottom: 0.75rem;
}

.stat-badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
}

.stat-badge.success {
  background: rgba(16, 185, 129, 0.2);
  color: #10B981;
}

.stat-badge.info {
  background: rgba(0, 142, 207, 0.2);
  color: #008ecf;
}

.stat-badge.warning {
  background: rgba(242, 148, 0, 0.2);
  color: #F29400;
}

.stat-badge.danger {
  background: rgba(229, 50, 18, 0.2);
  color: #e53212;
}

/* Graphiques */
.charts-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
  gap: 1.5rem;
}

.chart-card {
  background: rgba(15, 15, 25, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 1.5rem;
}

.chart-header {
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.chart-header h2 {
  font-family: 'Orbitron', monospace;
  font-size: 1.125rem;
  font-weight: 700;
  color: #008ecf;
  margin-bottom: 0.25rem;
}

.chart-subtitle {
  font-family: 'Rajdhani', sans-serif;
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.5);
}

.chart-body {
  margin: 0 -0.5rem;
}

.no-data {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 350px;
  color: rgba(255, 255, 255, 0.4);
  font-size: 1rem;
}

/* Responsive */
@media (max-width: 1024px) {
  .charts-section {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
