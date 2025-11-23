<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useSessionStore } from '@/stores/session'
import { useDeviceStore } from '@/stores/device'
import { useUserStore } from '@/stores/user'
import { useNotificationStore } from '@/stores/notification'
import LoadingSpinner from '@/components/LoadingSpinner.vue'

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
  todayBandwidth: todayBandwidth.value,
  blockedSites: 0, // Pas de backend pour l'instant
  alerts: 0 // Pas de backend pour l'instant
}))

// Générer les données de graphique de bande passante (24h)
const bandwidthData = computed(() => {
  const hours = Array.from({ length: 7 }, (_, i) => i * 4)
  return hours.map(hour => {
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

    const hourMB = Math.round(hourBytes / (1024 * 1024))
    return {
      time: `${hour.toString().padStart(2, '0')}:00`,
      value: hourMB
    }
  })
})

// Générer les données d'activité utilisateur (7 derniers jours)
const userActivityData = computed(() => {
  const days = ['Dim', 'Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam']
  const last7Days = Array.from({ length: 7 }, (_, i) => {
    const date = new Date()
    date.setDate(date.getDate() - (6 - i))
    return date
  })

  return last7Days.map((date, index) => {
    const dayStart = new Date(date)
    dayStart.setHours(0, 0, 0, 0)
    const dayEnd = new Date(date)
    dayEnd.setHours(23, 59, 59, 999)

    // Compter les sessions uniques de ce jour
    const uniqueUsers = new Set(
      sessionStore.sessions
        .filter(session => {
          const sessionDate = new Date(session.start_time)
          return sessionDate >= dayStart && sessionDate <= dayEnd
        })
        .map(session => session.user)
    )

    return {
      day: days[date.getDay()],
      users: uniqueUsers.size
    }
  })
})

onMounted(async () => {
  // Vérifier si l'utilisateur est admin
  if (!authStore.user?.is_staff && !authStore.user?.is_superuser) {
    notificationStore.error('Accès refusé')
    router.push('/')
    return
  }

  try {
    // Charger toutes les données en parallèle
    await Promise.all([
      userStore.fetchUsers(),
      sessionStore.fetchSessions(),
      deviceStore.fetchDevices()
    ])
    // Les stats sont automatiquement calculées via computed properties
  } catch (error) {
    notificationStore.error('Erreur lors du chargement des données')
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

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
}
</script>

<template>
  <div class="admin-dashboard">
    <!-- Header avec navigation -->
    <header class="dashboard-header">
      <div class="header-content">
        <div class="logo-section">
          <div class="logo-badge">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z" stroke="currentColor" stroke-width="2"/>
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" stroke="currentColor" stroke-width="2"/>
            </svg>
          </div>
          <div class="logo-text">
            <h1>Admin Dashboard</h1>
            <p>UCAC-ICAM Portail Captif</p>
          </div>
        </div>

        <div class="header-actions">
          <div class="user-info">
            <div class="user-avatar">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2"/>
                <circle cx="12" cy="7" r="4" stroke="currentColor" stroke-width="2"/>
              </svg>
            </div>
            <div class="user-details">
              <span class="user-name">{{ authStore.user?.username || 'Admin' }}</span>
              <span class="user-role">Administrateur</span>
            </div>
          </div>
          <button @click="handleLogout" class="logout-btn" title="Déconnexion">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
        </div>
      </div>
    </header>

    <!-- Navigation principale -->
    <nav class="main-nav">
      <button @click="navigateTo('/admin/dashboard')" class="nav-item active">
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <rect x="3" y="3" width="7" height="7" stroke="currentColor" stroke-width="2"/>
          <rect x="14" y="3" width="7" height="7" stroke="currentColor" stroke-width="2"/>
          <rect x="14" y="14" width="7" height="7" stroke="currentColor" stroke-width="2"/>
          <rect x="3" y="14" width="7" height="7" stroke="currentColor" stroke-width="2"/>
        </svg>
        <span>Dashboard</span>
      </button>
      <button @click="navigateTo('/admin/users')" class="nav-item">
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2"/>
          <circle cx="9" cy="7" r="4" stroke="currentColor" stroke-width="2"/>
          <path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" stroke="currentColor" stroke-width="2"/>
        </svg>
        <span>Utilisateurs</span>
      </button>
      <button @click="navigateTo('/admin/monitoring')" class="nav-item">
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <span>Monitoring</span>
      </button>
      <button @click="navigateTo('/admin/sites')" class="nav-item">
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
          <line x1="4.93" y1="4.93" x2="19.07" y2="19.07" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
        <span>Sites bloqués</span>
      </button>
      <button @click="navigateTo('/admin/quotas')" class="nav-item">
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <line x1="12" y1="1" x2="12" y2="23" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <span>Quotas</span>
      </button>
    </nav>

    <!-- Contenu principal -->
    <main class="dashboard-content">
      <LoadingSpinner v-if="isLoading" />

      <div v-else class="content-wrapper">
        <!-- Cartes de statistiques -->
        <div class="stats-grid">
          <!-- Utilisateurs -->
          <div class="stat-card users">
            <div class="stat-header">
              <div class="stat-icon">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2"/>
                  <circle cx="9" cy="7" r="4" stroke="currentColor" stroke-width="2"/>
                  <path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" stroke="currentColor" stroke-width="2"/>
                </svg>
              </div>
              <span class="stat-label">Utilisateurs</span>
            </div>
            <div class="stat-values">
              <div class="stat-main">{{ stats.totalUsers }}</div>
              <div class="stat-sub">{{ stats.activeUsers }} actifs</div>
            </div>
            <div class="stat-badge success">+12% ce mois</div>
          </div>

          <!-- Sessions -->
          <div class="stat-card sessions">
            <div class="stat-header">
              <div class="stat-icon">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                  <polyline points="12 6 12 12 16 14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                </svg>
              </div>
              <span class="stat-label">Sessions</span>
            </div>
            <div class="stat-values">
              <div class="stat-main">{{ stats.totalSessions }}</div>
              <div class="stat-sub">{{ stats.activeSessions }} actives</div>
            </div>
            <div class="stat-badge info">En temps réel</div>
          </div>

          <!-- Appareils -->
          <div class="stat-card devices">
            <div class="stat-header">
              <div class="stat-icon">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <rect x="5" y="2" width="14" height="20" rx="2" ry="2" stroke="currentColor" stroke-width="2"/>
                  <line x1="12" y1="18" x2="12.01" y2="18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                </svg>
              </div>
              <span class="stat-label">Appareils</span>
            </div>
            <div class="stat-values">
              <div class="stat-main">{{ stats.totalDevices }}</div>
              <div class="stat-sub">{{ stats.activeDevices }} connectés</div>
            </div>
            <div class="stat-badge warning">Limite: 500</div>
          </div>

          <!-- Bande passante -->
          <div class="stat-card bandwidth">
            <div class="stat-header">
              <div class="stat-icon">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <polyline points="17 6 23 6 23 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </div>
              <span class="stat-label">Bande passante</span>
            </div>
            <div class="stat-values">
              <div class="stat-main">{{ stats.todayBandwidth }} GB</div>
              <div class="stat-sub">Total: {{ stats.totalBandwidth }} GB</div>
            </div>
            <div class="stat-badge danger">85% utilisé</div>
          </div>
        </div>

        <!-- Graphiques et tableaux -->
        <div class="charts-grid">
          <!-- Graphique Bande passante -->
          <div class="chart-card">
            <div class="chart-header">
              <h3>Bande passante (24h)</h3>
              <button class="chart-action">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <circle cx="12" cy="12" r="1" fill="currentColor"/>
                  <circle cx="12" cy="5" r="1" fill="currentColor"/>
                  <circle cx="12" cy="19" r="1" fill="currentColor"/>
                </svg>
              </button>
            </div>
            <div class="chart-content">
              <!-- Graphique simplifié en CSS -->
              <div class="simple-chart">
                <div v-for="(data, index) in bandwidthData" :key="index" class="chart-bar">
                  <div class="bar" :style="{ height: (data.value / 450 * 100) + '%' }"></div>
                  <span class="bar-label">{{ data.time.split(':')[0] }}h</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Graphique Activité -->
          <div class="chart-card">
            <div class="chart-header">
              <h3>Activité utilisateurs (7j)</h3>
              <button class="chart-action">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <circle cx="12" cy="12" r="1" fill="currentColor"/>
                  <circle cx="12" cy="5" r="1" fill="currentColor"/>
                  <circle cx="12" cy="19" r="1" fill="currentColor"/>
                </svg>
              </button>
            </div>
            <div class="chart-content">
              <div class="simple-chart">
                <div v-for="(data, index) in userActivityData" :key="index" class="chart-bar">
                  <div class="bar activity-bar" :style="{ height: (data.users / 210 * 100) + '%' }"></div>
                  <span class="bar-label">{{ data.day }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Actions rapides -->
        <div class="quick-actions">
          <h2>Actions rapides</h2>
          <div class="actions-grid">
            <button @click="navigateTo('/admin/users')" class="action-card">
              <div class="action-icon">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2"/>
                  <circle cx="8.5" cy="7" r="4" stroke="currentColor" stroke-width="2"/>
                  <line x1="20" y1="8" x2="20" y2="14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                  <line x1="23" y1="11" x2="17" y2="11" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                </svg>
              </div>
              <h3>Ajouter utilisateur</h3>
              <p>Créer un nouveau compte utilisateur</p>
            </button>

            <button @click="navigateTo('/admin/sites')" class="action-card">
              <div class="action-icon">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                  <line x1="4.93" y1="4.93" x2="19.07" y2="19.07" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                </svg>
              </div>
              <h3>Bloquer un site</h3>
              <p>Ajouter à la liste noire</p>
            </button>

            <button @click="navigateTo('/admin/quotas')" class="action-card">
              <div class="action-icon">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                  <line x1="12" y1="8" x2="12" y2="16" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                  <line x1="8" y1="12" x2="16" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                </svg>
              </div>
              <h3>Définir quotas</h3>
              <p>Configurer les limites</p>
            </button>

            <button @click="navigateTo('/admin/monitoring')" class="action-card">
              <div class="action-icon">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" stroke="currentColor" stroke-width="2"/>
                  <circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="2"/>
                </svg>
              </div>
              <h3>Monitoring</h3>
              <p>Voir l'activité en temps réel</p>
            </button>
          </div>
        </div>

        <!-- Alertes -->
        <div v-if="stats.alerts > 0" class="alerts-section">
          <div class="alerts-header">
            <h2>
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" stroke="currentColor" stroke-width="2"/>
                <line x1="12" y1="9" x2="12" y2="13" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                <line x1="12" y1="17" x2="12.01" y2="17" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
              Alertes système ({{ stats.alerts }})
            </h2>
          </div>
          <div class="alert-item warning">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
              <line x1="12" y1="8" x2="12" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              <line x1="12" y1="16" x2="12.01" y2="16" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
            <div class="alert-content">
              <h4>Bande passante élevée</h4>
              <p>85% de la bande passante totale est utilisée</p>
              <span class="alert-time">Il y a 5 minutes</span>
            </div>
          </div>
          <div class="alert-item danger">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
              <line x1="15" y1="9" x2="9" y2="15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              <line x1="9" y1="9" x2="15" y2="15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
            <div class="alert-content">
              <h4>Tentative d'accès suspect</h4>
              <p>3 tentatives de connexion échouées depuis 192.168.1.105</p>
              <span class="alert-time">Il y a 12 minutes</span>
            </div>
          </div>
          <div class="alert-item info">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
              <line x1="12" y1="16" x2="12" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              <line x1="12" y1="8" x2="12.01" y2="8" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
            <div class="alert-content">
              <h4>Mise à jour disponible</h4>
              <p>Une nouvelle version du système est disponible</p>
              <span class="alert-time">Il y a 1 heure</span>
            </div>
          </div>
        </div>
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

.admin-dashboard {
  min-height: 100vh;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
  color: white;
}

/* Header */
.dashboard-header {
  background: rgba(17, 24, 39, 0.8);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  padding: 1.5rem 2rem;
  position: sticky;
  top: 0;
  z-index: 50;
}

.header-content {
  max-width: 1600px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.logo-section {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.logo-badge {
  width: 50px;
  height: 50px;
  background: linear-gradient(135deg, #dc2626 0%, #f97316 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 0 20px rgba(220, 38, 38, 0.4);
}

.logo-badge svg {
  width: 28px;
  height: 28px;
  color: white;
  animation: rotate 8s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.logo-text h1 {
  font-size: 1.5rem;
  font-weight: 800;
  background: linear-gradient(135deg, #fff 0%, #f97316 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.logo-text p {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.6);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem 1.25rem;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.user-avatar {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #f97316 0%, #fb923c 100%);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.user-avatar svg {
  width: 20px;
  height: 20px;
  color: white;
}

.user-details {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.user-name {
  font-weight: 600;
  font-size: 0.95rem;
}

.user-role {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.6);
}

.logout-btn {
  width: 45px;
  height: 45px;
  background: rgba(220, 38, 38, 0.1);
  border: 1px solid rgba(220, 38, 38, 0.3);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  color: #dc2626;
}

.logout-btn svg {
  width: 20px;
  height: 20px;
}

.logout-btn:hover {
  background: rgba(220, 38, 38, 0.2);
  border-color: rgba(220, 38, 38, 0.5);
  transform: translateY(-2px);
}

/* Navigation */
.main-nav {
  max-width: 1600px;
  margin: 0 auto;
  padding: 1.5rem 2rem;
  display: flex;
  gap: 1rem;
  overflow-x: auto;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.875rem 1.5rem;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  color: rgba(255, 255, 255, 0.7);
  font-weight: 500;
  white-space: nowrap;
}

.nav-item svg {
  width: 20px;
  height: 20px;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.1);
  color: white;
  border-color: rgba(249, 115, 22, 0.3);
}

.nav-item.active {
  background: linear-gradient(135deg, #dc2626 0%, #f97316 100%);
  color: white;
  border-color: transparent;
  box-shadow: 0 4px 12px rgba(220, 38, 38, 0.3);
}

/* Contenu principal */
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

/* Grille de stats */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.5rem;
}

.stat-card {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 1.75rem;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 3px;
  background: linear-gradient(90deg, #dc2626, #f97316);
}

.stat-card.users::before {
  background: linear-gradient(90deg, #10b981, #34d399);
}

.stat-card.sessions::before {
  background: linear-gradient(90deg, #3b82f6, #60a5fa);
}

.stat-card.devices::before {
  background: linear-gradient(90deg, #f59e0b, #fbbf24);
}

.stat-card:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(249, 115, 22, 0.3);
  transform: translateY(-4px);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
}

.stat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.5rem;
}

.stat-icon {
  width: 48px;
  height: 48px;
  background: rgba(249, 115, 22, 0.1);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-icon svg {
  width: 24px;
  height: 24px;
  color: #f97316;
}

.stat-card.users .stat-icon {
  background: rgba(16, 185, 129, 0.1);
}

.stat-card.users .stat-icon svg {
  color: #10b981;
}

.stat-card.sessions .stat-icon {
  background: rgba(59, 130, 246, 0.1);
}

.stat-card.sessions .stat-icon svg {
  color: #3b82f6;
}

.stat-card.devices .stat-icon {
  background: rgba(245, 158, 11, 0.1);
}

.stat-card.devices .stat-icon svg {
  color: #f59e0b;
}

.stat-label {
  color: rgba(255, 255, 255, 0.6);
  font-size: 0.9rem;
  font-weight: 500;
}

.stat-values {
  margin-bottom: 1rem;
}

.stat-main {
  font-size: 2.5rem;
  font-weight: 800;
  line-height: 1;
  margin-bottom: 0.5rem;
}

.stat-sub {
  color: rgba(255, 255, 255, 0.6);
  font-size: 0.95rem;
}

.stat-badge {
  display: inline-block;
  padding: 0.375rem 0.875rem;
  border-radius: 8px;
  font-size: 0.8rem;
  font-weight: 600;
}

.stat-badge.success {
  background: rgba(16, 185, 129, 0.15);
  color: #34d399;
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.stat-badge.info {
  background: rgba(59, 130, 246, 0.15);
  color: #60a5fa;
  border: 1px solid rgba(59, 130, 246, 0.3);
}

.stat-badge.warning {
  background: rgba(245, 158, 11, 0.15);
  color: #fbbf24;
  border: 1px solid rgba(245, 158, 11, 0.3);
}

.stat-badge.danger {
  background: rgba(220, 38, 38, 0.15);
  color: #f87171;
  border: 1px solid rgba(220, 38, 38, 0.3);
}

/* Graphiques */
.charts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 1.5rem;
}

.chart-card {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 1.75rem;
}

.chart-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.5rem;
}

.chart-header h3 {
  font-size: 1.1rem;
  font-weight: 700;
}

.chart-action {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  color: rgba(255, 255, 255, 0.6);
}

.chart-action:hover {
  background: rgba(255, 255, 255, 0.1);
  color: white;
}

.simple-chart {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 0.75rem;
  height: 200px;
  padding-top: 1rem;
}

.chart-bar {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  height: 100%;
}

.bar {
  width: 100%;
  background: linear-gradient(to top, #dc2626, #f97316);
  border-radius: 6px 6px 0 0;
  transition: all 0.3s ease;
  min-height: 20px;
}

.activity-bar {
  background: linear-gradient(to top, #3b82f6, #60a5fa);
}

.bar-label {
  color: rgba(255, 255, 255, 0.6);
  font-size: 0.75rem;
  font-weight: 500;
}

.chart-bar:hover .bar {
  opacity: 0.8;
  transform: scaleY(1.05);
}

/* Actions rapides */
.quick-actions h2 {
  font-size: 1.5rem;
  font-weight: 800;
  margin-bottom: 1.5rem;
}

.actions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
}

.action-card {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 2rem;
  cursor: pointer;
  transition: all 0.3s ease;
  text-align: left;
}

.action-card:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(249, 115, 22, 0.3);
  transform: translateY(-4px);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
}

.action-icon {
  width: 56px;
  height: 56px;
  background: linear-gradient(135deg, #dc2626 0%, #f97316 100%);
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 1.25rem;
}

.action-icon svg {
  width: 28px;
  height: 28px;
  color: white;
}

.action-card h3 {
  font-size: 1.1rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
}

.action-card p {
  color: rgba(255, 255, 255, 0.6);
  font-size: 0.9rem;
}

/* Alertes */
.alerts-section {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 1.75rem;
}

.alerts-header h2 {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 1.25rem;
  font-weight: 700;
  margin-bottom: 1.5rem;
}

.alerts-header svg {
  width: 24px;
  height: 24px;
  color: #f59e0b;
}

.alert-item {
  display: flex;
  gap: 1rem;
  padding: 1.25rem;
  border-radius: 12px;
  margin-bottom: 1rem;
  border-left: 4px solid;
}

.alert-item:last-child {
  margin-bottom: 0;
}

.alert-item svg {
  width: 24px;
  height: 24px;
  flex-shrink: 0;
}

.alert-item.warning {
  background: rgba(245, 158, 11, 0.1);
  border-left-color: #f59e0b;
  color: #fbbf24;
}

.alert-item.danger {
  background: rgba(220, 38, 38, 0.1);
  border-left-color: #dc2626;
  color: #f87171;
}

.alert-item.info {
  background: rgba(59, 130, 246, 0.1);
  border-left-color: #3b82f6;
  color: #60a5fa;
}

.alert-content h4 {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 0.25rem;
  color: white;
}

.alert-content p {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 0.5rem;
}

.alert-time {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.5);
}

/* Responsive */
@media (max-width: 1024px) {
  .charts-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .dashboard-header {
    padding: 1rem;
  }

  .header-content {
    flex-direction: column;
    gap: 1rem;
  }

  .main-nav {
    padding: 1rem;
  }

  .dashboard-content {
    padding: 1rem;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .user-info span {
    display: none;
  }
}
</style>
