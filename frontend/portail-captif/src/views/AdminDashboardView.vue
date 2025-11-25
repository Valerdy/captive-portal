<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useSessionStore } from '@/stores/session'
import { useDeviceStore } from '@/stores/device'
import { useUserStore } from '@/stores/user'
import { useNotificationStore } from '@/stores/notification'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import VueApexCharts from 'vue3-apexcharts'

const router = useRouter()
const authStore = useAuthStore()
const sessionStore = useSessionStore()
const deviceStore = useDeviceStore()
const userStore = useUserStore()
const notificationStore = useNotificationStore()

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

onMounted(async () => {
  if (!authStore.user?.is_staff && !authStore.user?.is_superuser) {
    notificationStore.error('Accès refusé')
    router.push('/')
    return
  }

  try {
    await Promise.all([
      userStore.fetchUsers(),
      sessionStore.fetchSessions(),
      deviceStore.fetchDevices()
    ])
  } catch (error: any) {
    const message = error?.message || 'Erreur inconnue'
    notificationStore.error(`Erreur lors du chargement des données du dashboard: ${message}`)
    console.error('Erreur chargement dashboard:', error)
  } finally {
    isLoading.value = false
  }
})

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
  <div class="admin-dashboard">
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
        <button @click="navigateTo('/admin/dashboard')" class="nav-item active">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="3" y="3" width="7" height="7" stroke="currentColor" stroke-width="2"/>
            <rect x="14" y="3" width="7" height="7" stroke="currentColor" stroke-width="2"/>
            <rect x="14" y="14" width="7" height="7" stroke="currentColor" stroke-width="2"/>
            <rect x="3" y="14" width="7" height="7" stroke="currentColor" stroke-width="2"/>
          </svg>
          Dashboard
        </button>
        <button @click="navigateTo('/admin/users')" class="nav-item">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2M9 7a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          Utilisateurs
        </button>
        <button @click="navigateTo('/admin/monitoring')" class="nav-item">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          Monitoring
        </button>
        <button @click="navigateTo('/admin/sites')" class="nav-item">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
            <line x1="4.93" y1="4.93" x2="19.07" y2="19.07" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
          Sites bloqués
        </button>
        <button @click="navigateTo('/admin/quotas')" class="nav-item">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <line x1="12" y1="1" x2="12" y2="23" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          Quotas
        </button>
      </nav>
    </header>

    <!-- Contenu principal -->
    <main class="dashboard-content">
      <LoadingSpinner v-if="isLoading" />

      <div v-else class="content-wrapper">
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

.admin-dashboard {
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
  background: #FFFFFF;
  border: 1px solid #E5E7EB;
  border-radius: 12px;
  padding: 1.5rem;
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  transition: all 0.2s;
}

.stat-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
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
  background: #DBEAFE;
  color: #3B82F6;
}

.stat-icon.sessions {
  background: #FEF3C7;
  color: #F59E0B;
}

.stat-icon.devices {
  background: #D1FAE5;
  color: #10B981;
}

.stat-icon.bandwidth {
  background: #FEE2E2;
  color: #DC2626;
}

.stat-content {
  flex: 1;
}

.stat-content h3 {
  font-size: 2rem;
  font-weight: 800;
  color: #1F2937;
  line-height: 1;
  margin-bottom: 0.5rem;
}

.stat-content p {
  font-size: 0.875rem;
  color: #6B7280;
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
  background: #D1FAE5;
  color: #10B981;
}

.stat-badge.info {
  background: #DBEAFE;
  color: #3B82F6;
}

.stat-badge.warning {
  background: #FEF3C7;
  color: #F59E0B;
}

.stat-badge.danger {
  background: #FEE2E2;
  color: #DC2626;
}

/* Graphiques */
.charts-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
  gap: 1.5rem;
}

.chart-card {
  background: #FFFFFF;
  border: 1px solid #E5E7EB;
  border-radius: 12px;
  padding: 1.5rem;
}

.chart-header {
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #E5E7EB;
}

.chart-header h2 {
  font-size: 1.125rem;
  font-weight: 700;
  color: #1F2937;
  margin-bottom: 0.25rem;
}

.chart-subtitle {
  font-size: 0.875rem;
  color: #6B7280;
}

.chart-body {
  margin: 0 -0.5rem;
}

/* Actions rapides */
.quick-actions-section {
  margin-top: 1rem;
}

.section-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #1F2937;
  margin-bottom: 1.5rem;
}

.quick-actions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
}

.action-btn {
  background: #FFFFFF;
  border: 1px solid #E5E7EB;
  border-radius: 12px;
  padding: 1.5rem;
  cursor: pointer;
  transition: all 0.2s;
  text-align: left;
}

.action-btn:hover {
  border-color: #F97316;
  box-shadow: 0 4px 16px rgba(249, 115, 22, 0.1);
  transform: translateY(-2px);
}

.action-icon {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #DC2626 0%, #F97316 100%);
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
  font-size: 1rem;
  font-weight: 600;
  color: #1F2937;
  margin-bottom: 0.25rem;
}

.action-btn p {
  font-size: 0.875rem;
  color: #6B7280;
}

/* Responsive */
@media (max-width: 1024px) {
  .charts-section {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    gap: 1rem;
    padding: 1rem;
  }

  .dashboard-content {
    padding: 1rem;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .main-nav {
    padding: 0 1rem 1rem;
  }
}
</style>
