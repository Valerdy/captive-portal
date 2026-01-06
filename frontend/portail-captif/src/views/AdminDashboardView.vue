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

// Navigation helper
function navigateTo(path: string) {
  router.push(path)
}

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

// Graphique de répartition des sessions
const sessionsPieChartOptions = computed(() => ({
  chart: {
    type: 'donut',
    fontFamily: 'Inter, sans-serif'
  },
  colors: ['#10B981', '#F97316', '#DC2626'],
  labels: ['Actives', 'Expirées', 'Terminées'],
  legend: {
    position: 'bottom',
    fontSize: '14px',
    fontWeight: 500
  },
  plotOptions: {
    pie: {
      donut: {
        size: '70%',
        labels: {
          show: true,
          total: {
            show: true,
            label: 'Total',
            fontSize: '16px',
            fontWeight: 600,
            color: '#1F2937'
          }
        }
      }
    }
  },
  dataLabels: { enabled: false },
  tooltip: {
    theme: 'light',
    y: { formatter: (val: number) => `${val} sessions` }
  }
}))

const sessionsPieChartSeries = computed(() => {
  const active = sessionStore.sessions.filter(s => s.status === 'active').length
  const expired = sessionStore.sessions.filter(s => s.status === 'expired').length
  const terminated = sessionStore.sessions.filter(s => s.status === 'terminated').length
  return [active, expired, terminated]
})

// Graphique Top 5 profils les plus utilisés
const topProfilesChartOptions = computed(() => ({
  chart: {
    type: 'bar',
    height: 350,
    toolbar: { show: false },
    fontFamily: 'Inter, sans-serif'
  },
  colors: ['#10B981'],
  plotOptions: {
    bar: {
      borderRadius: 8,
      columnWidth: '70%',
      distributed: false
    }
  },
  dataLabels: { enabled: false },
  xaxis: {
    categories: topProfiles.value.map(p => p.profile_name),
    labels: {
      style: { colors: '#6B7280', fontSize: '12px' },
      rotate: -45,
      rotateAlways: true
    }
  },
  yaxis: {
    title: { text: 'Nombre d\'utilisateurs' },
    labels: {
      style: { colors: '#6B7280', fontSize: '12px' },
      formatter: (val: number) => `${Math.round(val)}`
    }
  },
  grid: { borderColor: '#E5E7EB' },
  tooltip: {
    theme: 'light',
    y: { formatter: (val: number) => `${val} utilisateurs` }
  }
}))

const topProfilesChartSeries = computed(() => {
  return [{
    name: 'Utilisateurs',
    data: topProfiles.value.map(p => p.total_users)
  }]
})

// Graphique de répartition des types de quotas
const quotaTypesPieChartOptions = computed(() => ({
  chart: {
    type: 'donut',
    fontFamily: 'Inter, sans-serif'
  },
  colors: ['#3B82F6', '#F59E0B'],
  labels: ['Quotas Limités', 'Quotas Illimités'],
  legend: {
    position: 'bottom',
    fontSize: '14px',
    fontWeight: 500
  },
  plotOptions: {
    pie: {
      donut: {
        size: '70%',
        labels: {
          show: true,
          total: {
            show: true,
            label: 'Total',
            fontSize: '16px',
            fontWeight: 600,
            color: '#1F2937'
          }
        }
      }
    }
  },
  dataLabels: { enabled: false },
  tooltip: {
    theme: 'light',
    y: { formatter: (val: number) => `${val} profils` }
  }
}))

const quotaTypesPieChartSeries = computed(() => {
  if (!profileStats.value) return [0, 0]
  return [
    profileStats.value.limited_profiles || 0,
    profileStats.value.unlimited_profiles || 0
  ]
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

          <div class="chart-card">
            <div class="chart-header">
              <h2>Répartition des sessions</h2>
              <p class="chart-subtitle">Distribution par statut</p>
            </div>
            <div class="chart-body">
              <VueApexCharts
                type="donut"
                height="350"
                :options="sessionsPieChartOptions"
                :series="sessionsPieChartSeries"
              />
            </div>
          </div>

          <div class="chart-card">
            <div class="chart-header">
              <h2>Top 5 Profils les Plus Utilisés</h2>
              <p class="chart-subtitle">Nombre d'utilisateurs par profil</p>
            </div>
            <div class="chart-body">
              <VueApexCharts
                v-if="topProfiles.length > 0"
                type="bar"
                height="350"
                :options="topProfilesChartOptions"
                :series="topProfilesChartSeries"
              />
              <div v-else class="no-data">
                <p>Aucune donnée disponible</p>
              </div>
            </div>
          </div>

          <div class="chart-card">
            <div class="chart-header">
              <h2>Répartition des Types de Quotas</h2>
              <p class="chart-subtitle">Limités vs Illimités</p>
            </div>
            <div class="chart-body">
              <VueApexCharts
                v-if="profileStats"
                type="donut"
                height="350"
                :options="quotaTypesPieChartOptions"
                :series="quotaTypesPieChartSeries"
              />
              <div v-else class="no-data">
                <p>Aucune donnée disponible</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Actions rapides -->
        <div class="quick-actions-section">
          <h2 class="section-title">Actions rapides</h2>
          <div class="quick-actions-grid">
            <button @click="navigateTo('/admin/users')" class="action-btn">
              <div class="action-icon">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2"/>
                  <circle cx="8.5" cy="7" r="4" stroke="currentColor" stroke-width="2"/>
                  <line x1="20" y1="8" x2="20" y2="14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                  <line x1="23" y1="11" x2="17" y2="11" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                </svg>
              </div>
              <h3>Ajouter un utilisateur</h3>
              <p>Créer un nouveau compte</p>
            </button>

            <button @click="navigateTo('/admin/sites')" class="action-btn">
              <div class="action-icon">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                  <line x1="4.93" y1="4.93" x2="19.07" y2="19.07" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                </svg>
              </div>
              <h3>Bloquer un site</h3>
              <p>Gérer les restrictions</p>
            </button>

            <button @click="navigateTo('/admin/quotas')" class="action-btn">
              <div class="action-icon">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                  <line x1="12" y1="8" x2="12" y2="16" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                  <line x1="8" y1="12" x2="16" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                </svg>
              </div>
              <h3>Configurer quotas</h3>
              <p>Définir les limites</p>
            </button>

            <button @click="navigateTo('/admin/profiles')" class="action-btn">
              <div class="action-icon">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                  <path d="M12 8v8" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                  <path d="M8 12h8" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                </svg>
              </div>
              <h3>Gérer les profils</h3>
              <p>Créer et configurer des profils</p>
            </button>

            <button @click="navigateTo('/admin/monitoring')" class="action-btn">
              <div class="action-icon">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </div>
              <h3>Monitoring temps réel</h3>
              <p>Surveiller le système</p>
            </button>
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

/* Actions rapides */
.quick-actions-section {
  margin-top: 1rem;
}

.section-title {
  font-family: 'Orbitron', monospace;
  font-size: 1.25rem;
  font-weight: 700;
  color: #F29400;
  margin-bottom: 1.5rem;
  text-shadow: 0 0 15px rgba(242, 148, 0, 0.3);
}

.quick-actions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
}

.action-btn {
  background: rgba(15, 15, 25, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 1.5rem;
  cursor: pointer;
  transition: all 0.3s;
  text-align: left;
}

.action-btn:hover {
  border-color: rgba(0, 142, 207, 0.5);
  box-shadow: 0 8px 32px rgba(0, 142, 207, 0.2);
  transform: translateY(-2px);
}

.action-icon {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #F29400 0%, #008ecf 100%);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  margin-bottom: 1rem;
}

.action-icon svg {
  width: 24px;
  height: 24px;
}

.action-btn h3 {
  font-family: 'Rajdhani', sans-serif;
  font-size: 1rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.95);
  margin-bottom: 0.25rem;
}

.action-btn p {
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.5);
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
