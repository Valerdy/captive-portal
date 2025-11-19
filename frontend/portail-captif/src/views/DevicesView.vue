<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useDeviceStore } from '@/stores/device'

const router = useRouter()
const authStore = useAuthStore()
const deviceStore = useDeviceStore()

async function handleDeactivate(deviceId: number) {
  if (confirm('Voulez-vous vraiment désactiver cet appareil ?')) {
    await deviceStore.deactivateDevice(deviceId)
  }
}

function getDeviceIcon(type: string): string {
  const icons: Record<string, string> = {
    mobile: '📱',
    desktop: '💻',
    tablet: '📲',
    other: '🖥️'
  }
  return icons[type] || '🖥️'
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
      <h2>
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <rect x="2" y="3" width="20" height="14" rx="2" stroke="currentColor" stroke-width="2"/>
          <path d="M8 21h8M12 17v4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
        Mes Appareils
      </h2>

      <div v-if="deviceStore.isLoading" class="loading">
        <div class="spinner"></div>
        Chargement des appareils...
      </div>

      <div v-else-if="deviceStore.devices.length > 0" class="devices-grid">
        <div v-for="device in deviceStore.devices" :key="device.id" class="device-card">
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
                <rect x="2" y="3" width="20" height="14" rx="2" stroke="currentColor" stroke-width="2"/>
                <path d="M8 21h8M12 17v4" stroke="currentColor" stroke-width="2"/>
              </svg>
              <span class="device-type">{{ device.device_type }}</span>
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
                <p>{{ new Date(device.first_seen).toLocaleDateString() }}</p>
              </div>
            </div>
            <div class="date-item">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                <path d="M12 6v6l4 2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
              <div>
                <small>Dernier accès</small>
                <p>{{ new Date(device.last_seen).toLocaleDateString() }}</p>
              </div>
            </div>
          </div>

          <div class="device-actions">
            <button
              v-if="device.is_active"
              @click="handleDeactivate(device.id)"
              class="btn-danger"
            >
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
              Désactiver
            </button>
          </div>
        </div>
      </div>

      <div v-else class="empty-state">
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <rect x="2" y="3" width="20" height="14" rx="2" stroke="currentColor" stroke-width="2"/>
          <path d="M8 21h8M12 17v4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
        <h3>Aucun appareil trouvé</h3>
        <p>Vous n'avez pas encore d'appareils enregistrés.</p>
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

/* Header UCAC-ICAM (Réutilisé du Dashboard) */
.dashboard-header {
  background: linear-gradient(135deg, #c31432 0%, #e85d04 100%);
  color: white;
  padding: 1.5rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 4px 12px rgba(195, 20, 50, 0.2);
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
  color: #c31432;
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

/* Navigation (Réutilisé du Dashboard) */
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
  color: #e85d04;
  background: #fff8f5;
}

.nav-item.router-link-active {
  color: #c31432;
  border-bottom-color: #c31432;
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
  color: #333;
  font-size: 1.75rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.page-content h2 svg {
  width: 32px;
  height: 32px;
  color: #e85d04;
}

.loading {
  text-align: center;
  padding: 4rem 2rem;
  color: #666;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  font-size: 1.1rem;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f0f0f0;
  border-top: 4px solid #e85d04;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Grille d'appareils */
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
  color: #333;
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
  color: #e85d04;
  flex-shrink: 0;
}

.mac-address {
  font-family: 'Courier New', monospace;
  color: #666;
  font-size: 0.9rem;
  background: #f8f9fa;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
}

.device-type {
  color: #666;
  text-transform: capitalize;
  font-weight: 500;
}

.device-dates {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #f0f0f0;
}

.date-item {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
}

.date-item svg {
  width: 20px;
  height: 20px;
  color: #999;
  margin-top: 0.25rem;
  flex-shrink: 0;
}

.date-item small {
  color: #999;
  font-size: 0.75rem;
  display: block;
  margin-bottom: 0.25rem;
}

.date-item p {
  color: #555;
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
  background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
  color: white;
}

.badge.inactive {
  background: linear-gradient(135deg, #f44336 0%, #e91e63 100%);
  color: white;
}

.device-actions {
  margin-top: 0.5rem;
}

.btn-danger {
  width: 100%;
  background: linear-gradient(135deg, #f44336 0%, #e91e63 100%);
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 10px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  transition: all 0.3s ease;
}

.btn-danger svg {
  width: 18px;
  height: 18px;
}

.btn-danger:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(244, 67, 54, 0.4);
}

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
  color: #e0e0e0;
  margin-bottom: 1.5rem;
}

.empty-state h3 {
  color: #666;
  font-size: 1.5rem;
  margin-bottom: 0.75rem;
}

.empty-state p {
  color: #999;
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

  .page-content h2 {
    font-size: 1.5rem;
  }

  .page-content h2 svg {
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
