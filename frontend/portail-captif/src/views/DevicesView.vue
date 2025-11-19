<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useDeviceStore } from '@/stores/device'
import { useNotificationStore } from '@/stores/notification'
import DataTable from '@/components/DataTable.vue'

const router = useRouter()
const authStore = useAuthStore()
const deviceStore = useDeviceStore()
const notificationStore = useNotificationStore()

const viewMode = ref<'grid' | 'table'>('grid')
const statusFilter = ref<string>('all')

function formatDate(value: string): string {
  return new Date(value).toLocaleString('fr-FR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function formatStatus(value: boolean): string {
  return value ? 'Actif' : 'Inactif'
}

function formatDeviceType(value: string): string {
  const types: Record<string, string> = {
    mobile: 'Mobile',
    desktop: 'Ordinateur',
    tablet: 'Tablette',
    other: 'Autre'
  }
  return types[value] || value
}

const columns = [
  { key: 'hostname', label: 'Nom', sortable: true },
  { key: 'mac_address', label: 'Adresse MAC', sortable: true },
  { key: 'ip_address', label: 'Adresse IP', sortable: true },
  {
    key: 'device_type',
    label: 'Type',
    sortable: true,
    formatter: (value: string) => formatDeviceType(value)
  },
  {
    key: 'first_seen',
    label: 'Premier accès',
    sortable: true,
    formatter: (value: string) => formatDate(value)
  },
  {
    key: 'last_seen',
    label: 'Dernier accès',
    sortable: true,
    formatter: (value: string) => formatDate(value)
  },
  {
    key: 'is_active',
    label: 'Statut',
    sortable: true,
    formatter: (value: boolean) => formatStatus(value)
  },
  { key: 'actions', label: 'Actions', sortable: false }
]

const filteredDevices = computed(() => {
  if (statusFilter.value === 'all') {
    return deviceStore.devices
  }
  const isActive = statusFilter.value === 'active'
  return deviceStore.devices.filter(device => device.is_active === isActive)
})

function getDeviceIcon(type: string): string {
  const icons: Record<string, string> = {
    mobile: '📱',
    desktop: '💻',
    tablet: '📲',
    other: '🖥️'
  }
  return icons[type] || '🖥️'
}

async function handleToggleStatus(deviceId: number, isActive: boolean) {
  const action = isActive ? 'désactiver' : 'activer'
  if (confirm(`Voulez-vous vraiment ${action} cet appareil ?`)) {
    try {
      if (isActive) {
        await deviceStore.deactivateDevice(deviceId)
        notificationStore.success('Appareil désactivé avec succès')
      } else {
        // Assuming there's an activateDevice method
        await deviceStore.activateDevice(deviceId)
        notificationStore.success('Appareil activé avec succès')
      }
    } catch (error) {
      notificationStore.error(`Erreur lors de la modification de l'appareil`)
    }
  }
}

async function handleDelete(deviceId: number) {
  if (confirm('Voulez-vous vraiment supprimer cet appareil ? Cette action est irréversible.')) {
    try {
      await deviceStore.deleteDevice(deviceId)
      notificationStore.success('Appareil supprimé avec succès')
    } catch (error) {
      notificationStore.error('Erreur lors de la suppression de l\'appareil')
    }
  }
}

async function handleLogout() {
  await authStore.logout()
  router.push('/login')
}

onMounted(() => {
  deviceStore.fetchDevices()
})
</script>

<template>
  <div class="devices-page">
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
      <div class="page-header">
        <h2>
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="2" y="3" width="20" height="14" rx="2" stroke="currentColor" stroke-width="2"/>
            <path d="M8 21h8M12 17v4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
          Mes Appareils
        </h2>

        <!-- View Mode Toggle -->
        <div class="view-toggle">
          <button
            @click="viewMode = 'grid'"
            :class="['toggle-btn', { active: viewMode === 'grid' }]"
            title="Vue Grille"
          >
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <rect x="3" y="3" width="7" height="7" rx="1" stroke="currentColor" stroke-width="2"/>
              <rect x="14" y="3" width="7" height="7" rx="1" stroke="currentColor" stroke-width="2"/>
              <rect x="3" y="14" width="7" height="7" rx="1" stroke="currentColor" stroke-width="2"/>
              <rect x="14" y="14" width="7" height="7" rx="1" stroke="currentColor" stroke-width="2"/>
            </svg>
          </button>
          <button
            @click="viewMode = 'table'"
            :class="['toggle-btn', { active: viewMode === 'table' }]"
            title="Vue Tableau"
          >
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M3 6h18M3 12h18M3 18h18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </button>
        </div>
      </div>

      <!-- Status Filter Tabs -->
      <div class="filter-tabs">
        <button
          @click="statusFilter = 'all'"
          :class="['filter-tab', { active: statusFilter === 'all' }]"
        >
          Tous
          <span class="count">{{ deviceStore.devices.length }}</span>
        </button>
        <button
          @click="statusFilter = 'active'"
          :class="['filter-tab', { active: statusFilter === 'active' }]"
        >
          Actifs
          <span class="count active">
            {{ deviceStore.devices.filter(d => d.is_active).length }}
          </span>
        </button>
        <button
          @click="statusFilter = 'inactive'"
          :class="['filter-tab', { active: statusFilter === 'inactive' }]"
        >
          Inactifs
          <span class="count inactive">
            {{ deviceStore.devices.filter(d => !d.is_active).length }}
          </span>
        </button>
      </div>

      <!-- Grid View -->
      <div v-if="viewMode === 'grid' && !deviceStore.isLoading && filteredDevices.length > 0" class="devices-grid">
        <div v-for="device in filteredDevices" :key="device.id" class="device-card">
          <div class="device-header">
            <div class="device-icon">{{ getDeviceIcon(device.device_type) }}</div>
            <span :class="['badge', device.is_active ? 'active' : 'inactive']">
              {{ device.is_active ? 'Actif' : 'Inactif' }}
            </span>
          </div>

          <div class="device-info">
            <h3>{{ device.hostname || 'Appareil sans nom' }}</h3>
            <div class="info-row">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M21 10H3M21 6H3M21 14H3M21 18H3" stroke="currentColor" stroke-width="2"/>
              </svg>
              <span class="mac-address">{{ device.mac_address }}</span>
            </div>
            <div class="info-row">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="2"/>
                <path d="M12 1v6m0 6v6M1 12h6m6 0h6" stroke="currentColor" stroke-width="2"/>
              </svg>
              <span class="ip-address">{{ device.ip_address || 'N/A' }}</span>
            </div>
            <div class="info-row">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect x="2" y="3" width="20" height="14" rx="2" stroke="currentColor" stroke-width="2"/>
                <path d="M8 21h8M12 17v4" stroke="currentColor" stroke-width="2"/>
              </svg>
              <span class="device-type">{{ formatDeviceType(device.device_type) }}</span>
            </div>
          </div>

          <div class="device-dates">
            <div class="date-item">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                <path d="M12 6v6l4 2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
              <div>
                <small>Premier accès</small>
                <p>{{ new Date(device.first_seen).toLocaleDateString('fr-FR') }}</p>
              </div>
            </div>
            <div class="date-item">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                <path d="M12 6v6l4 2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
              <div>
                <small>Dernier accès</small>
                <p>{{ new Date(device.last_seen).toLocaleDateString('fr-FR') }}</p>
              </div>
            </div>
          </div>

          <div class="device-actions">
            <button
              @click="handleToggleStatus(device.id, device.is_active)"
              :class="device.is_active ? 'btn-warning' : 'btn-success'"
            >
              <svg v-if="device.is_active" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
              <svg v-else viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M5 13l4 4L19 7" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
              {{ device.is_active ? 'Désactiver' : 'Activer' }}
            </button>
            <button @click="handleDelete(device.id)" class="btn-danger-outline">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
              Supprimer
            </button>
          </div>
        </div>
      </div>

      <!-- Table View -->
      <div v-else-if="viewMode === 'table'">
        <DataTable
          :columns="columns"
          :data="filteredDevices"
          :loading="deviceStore.isLoading"
          export-filename="devices-ucac-icam"
        >
          <!-- Custom Hostname Cell -->
          <template #cell-hostname="{ value, row }">
            <div class="hostname-cell">
              <span class="device-icon-small">{{ getDeviceIcon(row.device_type) }}</span>
              <span>{{ value || 'Appareil sans nom' }}</span>
            </div>
          </template>

          <!-- Custom MAC Address Cell -->
          <template #cell-mac_address="{ value }">
            <span class="mac-address">{{ value }}</span>
          </template>

          <!-- Custom IP Address Cell -->
          <template #cell-ip_address="{ value }">
            <span class="ip-address">{{ value || 'N/A' }}</span>
          </template>

          <!-- Custom Status Cell -->
          <template #cell-is_active="{ value }">
            <span :class="['badge', value ? 'active' : 'inactive']">
              {{ value ? 'Actif' : 'Inactif' }}
            </span>
          </template>

          <!-- Custom Actions Cell -->
          <template #cell-actions="{ row }">
            <div class="table-actions">
              <button
                @click="handleToggleStatus(row.id, row.is_active)"
                :class="['btn-icon', row.is_active ? 'warning' : 'success']"
                :title="row.is_active ? 'Désactiver' : 'Activer'"
              >
                <svg v-if="row.is_active" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                </svg>
                <svg v-else viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M5 13l4 4L19 7" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                </svg>
              </button>
              <button
                @click="handleDelete(row.id)"
                class="btn-icon danger"
                title="Supprimer"
              >
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                </svg>
              </button>
            </div>
          </template>
        </DataTable>
      </div>

      <!-- Empty State -->
      <div v-if="!deviceStore.isLoading && filteredDevices.length === 0" class="empty-state">
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <rect x="2" y="3" width="20" height="14" rx="2" stroke="currentColor" stroke-width="2"/>
          <path d="M8 21h8M12 17v4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
        <h3>Aucun appareil trouvé</h3>
        <p>{{ statusFilter === 'all' ? 'Vous n\'avez pas encore d\'appareils enregistrés.' : `Aucun appareil ${statusFilter === 'active' ? 'actif' : 'inactif'} trouvé.` }}</p>
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

.devices-page {
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

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.page-header h2 {
  color: #111827;
  font-size: 1.75rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin: 0;
}

.page-header h2 svg {
  width: 32px;
  height: 32px;
  color: #f97316;
}

/* View Toggle */
.view-toggle {
  display: flex;
  gap: 0.5rem;
  background: white;
  padding: 0.375rem;
  border-radius: 12px;
  border: 2px solid #e5e7eb;
}

.toggle-btn {
  padding: 0.5rem;
  background: transparent;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.toggle-btn svg {
  width: 20px;
  height: 20px;
  color: #6b7280;
}

.toggle-btn:hover {
  background: #f9fafb;
}

.toggle-btn.active {
  background: linear-gradient(135deg, #dc2626 0%, #f97316 100%);
}

.toggle-btn.active svg {
  color: white;
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

/* Grid View */
.devices-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 1.5rem;
}

.device-card {
  background: white;
  padding: 1.75rem;
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  transition: all 0.3s ease;
}

.device-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.device-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.device-icon {
  font-size: 3.5rem;
  text-align: center;
}

.device-info h3 {
  margin-bottom: 0.875rem;
  color: #111827;
  font-size: 1.25rem;
  font-weight: 700;
}

.info-row {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  margin-bottom: 0.5rem;
}

.info-row svg {
  width: 18px;
  height: 18px;
  color: #f97316;
  flex-shrink: 0;
}

.mac-address,
.ip-address {
  font-family: 'Courier New', monospace;
  font-size: 0.9rem;
  color: #111827;
  background: #f9fafb;
  padding: 0.375rem 0.625rem;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
  font-weight: 500;
}

.device-type {
  color: #6b7280;
  text-transform: capitalize;
  font-weight: 500;
}

.device-dates {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #e5e7eb;
}

.date-item {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
}

.date-item svg {
  width: 20px;
  height: 20px;
  color: #9ca3af;
  margin-top: 0.25rem;
  flex-shrink: 0;
}

.date-item small {
  color: #9ca3af;
  font-size: 0.75rem;
  display: block;
  margin-bottom: 0.25rem;
}

.date-item p {
  color: #111827;
  font-size: 0.875rem;
  font-weight: 600;
}

.badge {
  padding: 0.375rem 0.875rem;
  border-radius: 16px;
  font-size: 0.875rem;
  font-weight: 600;
  display: inline-block;
}

.badge.active {
  background: linear-gradient(135deg, #10b981 0%, #34d399 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.3);
}

.badge.inactive {
  background: linear-gradient(135deg, #6b7280 0%, #9ca3af 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(107, 114, 128, 0.3);
}

.device-actions {
  display: flex;
  gap: 0.75rem;
  margin-top: 0.5rem;
}

.btn-warning,
.btn-success,
.btn-danger-outline {
  flex: 1;
  padding: 0.75rem 1rem;
  border-radius: 10px;
  cursor: pointer;
  font-size: 0.875rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  transition: all 0.3s ease;
  border: none;
}

.btn-warning {
  background: linear-gradient(135deg, #f59e0b 0%, #fbbf24 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(245, 158, 11, 0.3);
}

.btn-success {
  background: linear-gradient(135deg, #10b981 0%, #34d399 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.3);
}

.btn-danger-outline {
  background: white;
  color: #dc2626;
  border: 2px solid #dc2626;
  box-shadow: 0 2px 8px rgba(220, 38, 38, 0.1);
}

.btn-warning:hover,
.btn-success:hover,
.btn-danger-outline:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.btn-warning svg,
.btn-success svg,
.btn-danger-outline svg {
  width: 16px;
  height: 16px;
}

/* Table View Custom Cells */
.hostname-cell {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.device-icon-small {
  font-size: 1.5rem;
}

.table-actions {
  display: flex;
  gap: 0.5rem;
}

.btn-icon {
  padding: 0.5rem;
  border-radius: 8px;
  cursor: pointer;
  border: none;
  background: white;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-icon svg {
  width: 18px;
  height: 18px;
}

.btn-icon.warning {
  color: #f59e0b;
  border: 2px solid #f59e0b;
}

.btn-icon.success {
  color: #10b981;
  border: 2px solid #10b981;
}

.btn-icon.danger {
  color: #dc2626;
  border: 2px solid #dc2626;
}

.btn-icon:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.btn-icon.warning:hover {
  background: #f59e0b;
  color: white;
}

.btn-icon.success:hover {
  background: #10b981;
  color: white;
}

.btn-icon.danger:hover {
  background: #dc2626;
  color: white;
}

/* Empty State */
.empty-state {
  background: white;
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  padding: 4rem 2rem;
  text-align: center;
}

.empty-state svg {
  width: 80px;
  height: 80px;
  color: #e5e7eb;
  margin-bottom: 1.5rem;
}

.empty-state h3 {
  color: #6b7280;
  font-size: 1.5rem;
  margin-bottom: 0.75rem;
}

.empty-state p {
  color: #9ca3af;
  font-size: 1.1rem;
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

  .page-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .page-header h2 {
    font-size: 1.5rem;
  }

  .filter-tabs {
    gap: 0.5rem;
  }

  .filter-tab {
    padding: 0.625rem 1rem;
    font-size: 0.875rem;
  }

  .devices-grid {
    grid-template-columns: 1fr;
  }

  .device-dates {
    grid-template-columns: 1fr;
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

  .page-header h2 {
    font-size: 1.25rem;
  }

  .page-header h2 svg {
    width: 28px;
    height: 28px;
  }

  .device-card {
    padding: 1.25rem;
  }

  .device-icon {
    font-size: 2.5rem;
  }
}
</style>
