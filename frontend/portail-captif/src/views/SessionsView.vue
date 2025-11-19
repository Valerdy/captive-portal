<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useSessionStore } from '@/stores/session'
import { useNotificationStore } from '@/stores/notification'
import DataTable from '@/components/DataTable.vue'
import LoadingSpinner from '@/components/LoadingSpinner.vue'

const router = useRouter()
const authStore = useAuthStore()
const sessionStore = useSessionStore()
const notificationStore = useNotificationStore()

const statusFilter = ref<string>('all')

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

function formatDate(value: string): string {
  return new Date(value).toLocaleString('fr-FR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function formatStatus(value: string): string {
  const statusMap: Record<string, string> = {
    active: 'Actif',
    expired: 'Expiré',
    terminated: 'Terminé'
  }
  return statusMap[value] || value
}

const columns = [
  { key: 'ip_address', label: 'Adresse IP', sortable: true },
  { key: 'mac_address', label: 'MAC Address', sortable: true },
  {
    key: 'start_time',
    label: 'Début',
    sortable: true,
    formatter: (value: string) => formatDate(value)
  },
  {
    key: 'end_time',
    label: 'Fin',
    sortable: true,
    formatter: (value: string | null) => value ? formatDate(value) : '-'
  },
  {
    key: 'total_bytes',
    label: 'Données',
    sortable: true,
    formatter: (value: number) => formatBytes(value)
  },
  {
    key: 'status',
    label: 'Statut',
    sortable: true,
    formatter: (value: string) => formatStatus(value)
  },
  { key: 'actions', label: 'Actions', sortable: false }
]

const filteredSessions = computed(() => {
  if (statusFilter.value === 'all') {
    return sessionStore.sessions
  }
  return sessionStore.sessions.filter(session => session.status === statusFilter.value)
})

async function handleTerminate(sessionId: number) {
  if (confirm('Voulez-vous vraiment terminer cette session ?')) {
    try {
      await sessionStore.terminateSession(sessionId)
      notificationStore.success('Session terminée avec succès')
    } catch (error) {
      notificationStore.error('Erreur lors de la terminaison de la session')
    }
  }
}

async function handleLogout() {
  await authStore.logout()
  router.push('/login')
}

onMounted(() => {
  sessionStore.fetchSessions()
})
</script>

<template>
  <div class="sessions-page">
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
    <main class="page-content">
      <h2>
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
          <path d="M12 6v6l4 2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
        Mes Sessions
      </h2>

      <!-- Status Filter Tabs -->
      <div class="filter-tabs">
        <button
          @click="statusFilter = 'all'"
          :class="['filter-tab', { active: statusFilter === 'all' }]"
        >
          Tous
          <span class="count">{{ sessionStore.sessions.length }}</span>
        </button>
        <button
          @click="statusFilter = 'active'"
          :class="['filter-tab', { active: statusFilter === 'active' }]"
        >
          Actifs
          <span class="count active">
            {{ sessionStore.sessions.filter(s => s.status === 'active').length }}
          </span>
        </button>
        <button
          @click="statusFilter = 'expired'"
          :class="['filter-tab', { active: statusFilter === 'expired' }]"
        >
          Expirés
          <span class="count expired">
            {{ sessionStore.sessions.filter(s => s.status === 'expired').length }}
          </span>
        </button>
        <button
          @click="statusFilter = 'terminated'"
          :class="['filter-tab', { active: statusFilter === 'terminated' }]"
        >
          Terminés
          <span class="count terminated">
            {{ sessionStore.sessions.filter(s => s.status === 'terminated').length }}
          </span>
        </button>
      </div>

      <!-- Data Table -->
      <DataTable
        :columns="columns"
        :data="filteredSessions"
        :loading="sessionStore.isLoading"
        export-filename="sessions-ucac-icam"
      >
        <!-- Custom IP Address Cell -->
        <template #cell-ip_address="{ value }">
          <span class="ip-address">{{ value }}</span>
        </template>

        <!-- Custom MAC Address Cell -->
        <template #cell-mac_address="{ value }">
          <span class="mac-address">{{ value }}</span>
        </template>

        <!-- Custom Total Bytes Cell -->
        <template #cell-total_bytes="{ value }">
          <span class="data-badge">{{ formatBytes(value) }}</span>
        </template>

        <!-- Custom Status Cell -->
        <template #cell-status="{ value }">
          <span :class="['badge', value]">
            {{ formatStatus(value) }}
          </span>
        </template>

        <!-- Custom Actions Cell -->
        <template #cell-actions="{ row }">
          <button
            v-if="row.status === 'active'"
            @click="handleTerminate(row.id)"
            class="btn-danger"
          >
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
              <path d="M15 9l-6 6M9 9l6 6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
            Terminer
          </button>
          <span v-else class="action-disabled">—</span>
        </template>
      </DataTable>
    </main>
  </div>
</template>

<style scoped>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.sessions-page {
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

/* Contenu */
.page-content {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.page-content h2 {
  margin-bottom: 2rem;
  color: #111827;
  font-size: 1.75rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.page-content h2 svg {
  width: 32px;
  height: 32px;
  color: #f97316;
}

/* Filter Tabs */
.filter-tabs {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
}

.filter-tab {
  padding: 0.75rem 1.5rem;
  background: white;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.95rem;
  color: #6b7280;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.filter-tab:hover {
  border-color: #f97316;
  color: #f97316;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(249, 115, 22, 0.15);
}

.filter-tab.active {
  background: linear-gradient(135deg, #dc2626 0%, #f97316 100%);
  border-color: #dc2626;
  color: white;
  box-shadow: 0 4px 12px rgba(220, 38, 38, 0.3);
}

.filter-tab .count {
  background: rgba(0, 0, 0, 0.1);
  padding: 0.25rem 0.5rem;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 700;
  min-width: 24px;
  text-align: center;
}

.filter-tab.active .count {
  background: rgba(255, 255, 255, 0.25);
}

/* Custom Cell Styles */
.ip-address,
.mac-address {
  font-family: 'Courier New', monospace;
  font-size: 0.9rem;
  color: #111827;
  background: #f9fafb;
  padding: 0.375rem 0.625rem;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
  font-weight: 500;
}

.data-badge {
  background: linear-gradient(135deg, #dc2626 0%, #f97316 100%);
  color: white;
  padding: 0.375rem 0.75rem;
  border-radius: 12px;
  font-size: 0.875rem;
  font-weight: 600;
  display: inline-block;
}

.badge {
  padding: 0.375rem 0.875rem;
  border-radius: 16px;
  font-size: 0.875rem;
  font-weight: 600;
  display: inline-block;
  text-transform: capitalize;
}

.badge.active {
  background: linear-gradient(135deg, #10b981 0%, #34d399 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.3);
}

.badge.expired {
  background: linear-gradient(135deg, #f59e0b 0%, #fbbf24 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(245, 158, 11, 0.3);
}

.badge.terminated {
  background: linear-gradient(135deg, #6b7280 0%, #9ca3af 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(107, 114, 128, 0.3);
}

.btn-danger {
  background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.875rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(220, 38, 38, 0.3);
}

.btn-danger svg {
  width: 16px;
  height: 16px;
}

.btn-danger:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(220, 38, 38, 0.4);
}

.action-disabled {
  color: #d1d5db;
  font-size: 1.25rem;
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

  .page-content {
    padding: 1rem;
  }

  .page-content h2 {
    font-size: 1.5rem;
  }

  .filter-tabs {
    gap: 0.5rem;
  }

  .filter-tab {
    padding: 0.625rem 1rem;
    font-size: 0.875rem;
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

  .page-content h2 {
    font-size: 1.25rem;
  }

  .page-content h2 svg {
    width: 28px;
    height: 28px;
  }
}
</style>
