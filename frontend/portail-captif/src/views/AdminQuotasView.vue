<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useQuotaStore } from '@/stores/quota'
import { useNotificationStore } from '@/stores/notification'

const router = useRouter()
const authStore = useAuthStore()
const quotaStore = useQuotaStore()
const notificationStore = useNotificationStore()

const quotas = computed(() => quotaStore.quotas)
const isLoading = computed(() => quotaStore.isLoading)

const showEditModal = ref(false)
const selectedQuota = ref<any>(null)
const searchQuery = ref('')

// Statistiques
const stats = computed(() => ({
  total: quotas.value.length,
  active: quotas.value.filter(q => q.is_active).length,
  warning: quotas.value.filter(q => q.daily_usage_percent >= 75 && q.daily_usage_percent < 90).length,
  exceeded: quotas.value.filter(q => q.daily_usage_percent >= 90).length
}))

// Filtrage
const filteredQuotas = computed(() => {
  if (!searchQuery.value) return quotas.value
  const query = searchQuery.value.toLowerCase()
  return quotas.value.filter((q: any) =>
    q.user_username?.toLowerCase().includes(query)
  )
})

// Fonction pour obtenir la couleur de la barre de progression
function getProgressColor(percent: number) {
  if (percent >= 90) return '#DC2626' // Rouge
  if (percent >= 75) return '#F97316' // Orange
  return '#10B981' // Vert
}

onMounted(async () => {
  if (!authStore.isAdmin) {
    notificationStore.error('Accès refusé')
    router.push('/')
    return
  }

  try {
    await quotaStore.fetchQuotas()
  } catch (error) {
    notificationStore.error('Erreur lors du chargement des quotas')
  }
})

function handleEdit(quota: any) {
  selectedQuota.value = { ...quota }
  showEditModal.value = true
}

function closeEditModal() {
  showEditModal.value = false
  selectedQuota.value = null
}

async function handleUpdateQuota() {
  if (!selectedQuota.value) return

  try {
    // Convertir les limites GB en bytes pour le backend
    const dailyLimitBytes = Math.round(selectedQuota.value.daily_limit_gb * 1024 * 1024 * 1024)
    const weeklyLimitBytes = Math.round(selectedQuota.value.weekly_limit_gb * 1024 * 1024 * 1024)
    const monthlyLimitBytes = Math.round(selectedQuota.value.monthly_limit_gb * 1024 * 1024 * 1024)

    await quotaStore.updateQuota(selectedQuota.value.id, {
      daily_limit: dailyLimitBytes,
      weekly_limit: weeklyLimitBytes,
      monthly_limit: monthlyLimitBytes,
      is_active: selectedQuota.value.is_active
    })

    notificationStore.success('Quota modifié avec succès')
    closeEditModal()
  } catch (error) {
    notificationStore.error(quotaStore.error || 'Erreur lors de la modification')
  }
}

async function handleToggleStatus(quotaId: number, currentStatus: boolean) {
  const action = currentStatus ? 'désactiver' : 'activer'
  if (confirm(`Voulez-vous vraiment ${action} ce quota ?`)) {
    try {
      await quotaStore.updateQuota(quotaId, {
        is_active: !currentStatus
      })
      notificationStore.success(`Quota ${currentStatus ? 'désactivé' : 'activé'} avec succès`)
    } catch (error) {
      notificationStore.error(quotaStore.error || 'Erreur lors de la modification')
    }
  }
}

async function handleReset(quotaId: number) {
  if (confirm('Voulez-vous vraiment réinitialiser tous les compteurs de ce quota ?')) {
    try {
      await quotaStore.resetAll(quotaId)
      notificationStore.success('Compteurs réinitialisés avec succès')
    } catch (error) {
      notificationStore.error(quotaStore.error || 'Erreur lors de la réinitialisation')
    }
  }
}

function goBack() {
  router.push('/admin/dashboard')
}
</script>

<template>
  <div class="admin-quotas">
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
          <router-link to="/admin/quotas" class="nav-link active">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <line x1="12" y1="1" x2="12" y2="23" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
            Quotas
          </router-link>
          <router-link to="/admin/monitoring" class="nav-link">
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
          <h1>Gestion des quotas</h1>
          <p class="page-subtitle">Configuration des limites de bande passante par utilisateur</p>
        </div>
      </div>

      <!-- Statistiques -->
      <div class="stats-row">
        <div class="stat-box">
          <div class="stat-icon" style="background: #DBEAFE; color: #3B82F6;">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <rect x="3" y="4" width="18" height="18" rx="2" stroke="currentColor" stroke-width="2"/>
              <line x1="3" y1="9" x2="21" y2="9" stroke="currentColor" stroke-width="2"/>
              <line x1="9" y1="9" x2="9" y2="22" stroke="currentColor" stroke-width="2"/>
            </svg>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.total }}</div>
            <div class="stat-label">Total quotas</div>
          </div>
        </div>

        <div class="stat-box success">
          <div class="stat-icon" style="background: #D1FAE5; color: #10B981;">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M22 4L12 14.01l-3-3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.active }}</div>
            <div class="stat-label">Actifs</div>
          </div>
        </div>

        <div class="stat-box warning">
          <div class="stat-icon" style="background: #FED7AA; color: #F97316;">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <line x1="12" y1="9" x2="12" y2="13" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <line x1="12" y1="17" x2="12.01" y2="17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.warning }}</div>
            <div class="stat-label">Attention (>75%)</div>
          </div>
        </div>

        <div class="stat-box danger">
          <div class="stat-icon" style="background: #FEE2E2; color: #DC2626;">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <line x1="15" y1="9" x2="9" y2="15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <line x1="9" y1="9" x2="15" y2="15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.exceeded }}</div>
            <div class="stat-label">Dépassés (>90%)</div>
          </div>
        </div>
      </div>

      <!-- Recherche -->
      <div class="filters-section">
        <div class="search-box">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="11" cy="11" r="8" stroke="currentColor" stroke-width="2"/>
            <path d="m21 21-4.35-4.35" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Rechercher un utilisateur..."
          />
        </div>
      </div>

      <!-- Table des quotas -->
      <div class="content-card">
        <div v-if="isLoading" class="loading">
          <div class="spinner"></div>
          <p>Chargement des quotas...</p>
        </div>

        <div v-else-if="filteredQuotas.length === 0" class="empty-state">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
            <line x1="12" y1="8" x2="12" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            <line x1="12" y1="16" x2="12.01" y2="16" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
          <p>Aucun quota trouvé</p>
        </div>

        <table v-else class="data-table">
          <thead>
            <tr>
              <th>Utilisateur</th>
              <th>Quota jour</th>
              <th>Utilisé aujourd'hui</th>
              <th>Quota semaine</th>
              <th>Quota mois</th>
              <th>Statut</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="quota in filteredQuotas" :key="quota.id">
              <td>
                <div class="user-cell">
                  <div class="user-avatar-sm">
                    {{ quota.user_username.charAt(0).toUpperCase() }}
                  </div>
                  <span class="user-name-text">{{ quota.user_username }}</span>
                </div>
              </td>
              <td><strong>{{ quota.daily_limit_gb?.toFixed(1) }} GB</strong></td>
              <td>
                <div class="usage-cell">
                  <div class="usage-text">
                    <span class="usage-value">{{ quota.used_today_gb?.toFixed(2) }} GB</span>
                    <span class="usage-percent">{{ quota.daily_usage_percent?.toFixed(0) }}%</span>
                  </div>
                  <div class="progress-bar-container">
                    <div
                      class="progress-bar-fill"
                      :style="{
                        width: Math.min(quota.daily_usage_percent, 100) + '%',
                        background: getProgressColor(quota.daily_usage_percent)
                      }"
                    ></div>
                  </div>
                </div>
              </td>
              <td>{{ quota.weekly_limit_gb?.toFixed(1) }} GB</td>
              <td>{{ quota.monthly_limit_gb?.toFixed(1) }} GB</td>
              <td>
                <span v-if="quota.is_active" class="badge badge-success">Actif</span>
                <span v-else class="badge badge-inactive">Inactif</span>
              </td>
              <td>
                <div class="action-buttons">
                  <button @click="handleEdit(quota)" class="action-btn edit" title="Modifier">
                    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                  </button>
                  <button @click="handleReset(quota.id)" class="action-btn reset" title="Réinitialiser">
                    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <polyline points="23 4 23 10 17 10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                  </button>
                  <button @click="handleToggleStatus(quota.id, quota.is_active)" class="action-btn toggle" :title="quota.is_active ? 'Désactiver' : 'Activer'">
                    <svg v-if="quota.is_active" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                      <line x1="15" y1="9" x2="9" y2="15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                      <line x1="9" y1="9" x2="15" y2="15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                    </svg>
                    <svg v-else viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      <path d="M22 4L12 14.01l-3-3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </main>

    <!-- Modal Édition -->
    <Teleport to="body">
      <div v-if="showEditModal && selectedQuota" class="modal-overlay" @click="closeEditModal">
        <div class="modal-content" @click.stop>
          <button @click="closeEditModal" class="modal-close">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </button>

          <div class="modal-header">
            <div class="modal-icon">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <line x1="12" y1="1" x2="12" y2="23" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </div>
            <h2>Modifier les quotas</h2>
            <p class="modal-subtitle">Utilisateur: <strong>{{ selectedQuota.user_username }}</strong></p>
          </div>

          <form @submit.prevent="handleUpdateQuota" class="form">
            <div class="form-group">
              <label>Quota journalier (GB)</label>
              <input v-model.number="selectedQuota.daily_limit_gb" type="number" step="0.1" min="0" required />
            </div>

            <div class="form-group">
              <label>Quota hebdomadaire (GB)</label>
              <input v-model.number="selectedQuota.weekly_limit_gb" type="number" step="0.1" min="0" required />
            </div>

            <div class="form-group">
              <label>Quota mensuel (GB)</label>
              <input v-model.number="selectedQuota.monthly_limit_gb" type="number" step="0.1" min="0" required />
            </div>

            <div class="info-box">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                <line x1="12" y1="16" x2="12" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                <line x1="12" y1="8" x2="12.01" y2="8" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
              <p>Les quotas doivent être cohérents : quota journalier × 7 ≤ quota hebdomadaire ≤ quota mensuel</p>
            </div>

            <div class="form-actions">
              <button type="button" @click="closeEditModal" class="btn-secondary">Annuler</button>
              <button type="submit" class="btn-primary">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z" stroke="currentColor" stroke-width="2"/>
                  <polyline points="17 21 17 13 7 13 7 21" stroke="currentColor" stroke-width="2"/>
                  <polyline points="7 3 7 8 15 8" stroke="currentColor" stroke-width="2"/>
                </svg>
                Enregistrer
              </button>
            </div>
          </form>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

* {
  font-family: 'Inter', sans-serif;
}

.admin-quotas {
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
  align-items: center;
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
  margin: 0.25rem 0 0 0;
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
  border-left: 4px solid #3B82F6;
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

.stat-box.success {
  border-left-color: #10B981;
}

.stat-box.warning {
  border-left-color: #F97316;
}

.stat-box.danger {
  border-left-color: #DC2626;
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

/* Recherche */
.filters-section {
  margin-bottom: 1.5rem;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  background: #FFFFFF;
  border: 1px solid #E5E7EB;
  border-radius: 12px;
  padding: 0.875rem 1.25rem;
  max-width: 400px;
}

.search-box svg {
  width: 20px;
  height: 20px;
  color: #9CA3AF;
}

.search-box input {
  flex: 1;
  border: none;
  outline: none;
  font-size: 0.95rem;
  color: #111827;
  background: transparent;
}

.search-box input::placeholder {
  color: #9CA3AF;
}

/* Table */
.content-card {
  background: #FFFFFF;
  border: 1px solid #E5E7EB;
  border-radius: 12px;
  padding: 1.5rem;
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

.user-cell {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.user-avatar-sm {
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, #DC2626 0%, #F97316 100%);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 700;
  font-size: 0.95rem;
}

.user-name-text {
  font-weight: 600;
  color: #111827;
}

.usage-cell {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  min-width: 180px;
}

.usage-text {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.usage-value {
  font-weight: 600;
  color: #111827;
}

.usage-percent {
  font-weight: 700;
  color: #6B7280;
  font-size: 0.85rem;
}

.progress-bar-container {
  width: 100%;
  height: 8px;
  background: #E5E7EB;
  border-radius: 4px;
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: all 0.5s ease;
}

.badge {
  display: inline-block;
  padding: 0.375rem 0.875rem;
  border-radius: 6px;
  font-size: 0.85rem;
  font-weight: 600;
}

.badge-success {
  background: #D1FAE5;
  color: #059669;
  border: 1px solid #A7F3D0;
}

.badge-inactive {
  background: #F3F4F6;
  color: #6B7280;
  border: 1px solid #E5E7EB;
}

.action-buttons {
  display: flex;
  gap: 0.5rem;
}

.action-btn {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid transparent;
}

.action-btn svg {
  width: 16px;
  height: 16px;
}

.action-btn.edit {
  background: #DBEAFE;
  color: #3B82F6;
  border-color: #BFDBFE;
}

.action-btn.edit:hover {
  background: #BFDBFE;
  transform: translateY(-1px);
}

.action-btn.reset {
  background: #D1FAE5;
  color: #10B981;
  border-color: #A7F3D0;
}

.action-btn.reset:hover {
  background: #A7F3D0;
  transform: translateY(-1px);
}

.action-btn.toggle {
  background: #FED7AA;
  color: #F97316;
  border-color: #FDBA74;
}

.action-btn.toggle:hover {
  background: #FDBA74;
  transform: translateY(-1px);
}

/* Loading & Empty State */
.loading, .empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem;
  color: #9CA3AF;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #E5E7EB;
  border-top-color: #F97316;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-state svg {
  width: 64px;
  height: 64px;
  margin-bottom: 1rem;
  color: #D1D5DB;
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 1rem;
}

.modal-content {
  background: #FFFFFF;
  border: 1px solid #E5E7EB;
  border-radius: 16px;
  padding: 2rem;
  max-width: 600px;
  width: 100%;
  position: relative;
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.15);
}

.modal-close {
  position: absolute;
  top: 1.5rem;
  right: 1.5rem;
  width: 36px;
  height: 36px;
  background: #F3F4F6;
  border: 1px solid #E5E7EB;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  color: #6B7280;
}

.modal-close:hover {
  background: #FEE2E2;
  color: #DC2626;
  border-color: #FECACA;
}

.modal-close svg {
  width: 18px;
  height: 18px;
}

.modal-header {
  text-align: center;
  margin-bottom: 2rem;
}

.modal-icon {
  width: 64px;
  height: 64px;
  background: linear-gradient(135deg, #DC2626 0%, #F97316 100%);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 1rem;
  color: white;
}

.modal-icon svg {
  width: 32px;
  height: 32px;
}

.modal-content h2 {
  color: #111827;
  font-size: 1.75rem;
  font-weight: 800;
  margin: 0 0 0.5rem 0;
}

.modal-subtitle {
  color: #6B7280;
  font-size: 1rem;
  margin: 0;
}

.modal-subtitle strong {
  color: #F97316;
  font-weight: 700;
}

.form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  color: #374151;
  font-weight: 600;
  font-size: 0.95rem;
}

.form-group input {
  width: 100%;
  padding: 0.875rem;
  background: #F9FAFB;
  border: 1px solid #E5E7EB;
  border-radius: 8px;
  color: #111827;
  font-size: 1rem;
  transition: all 0.2s ease;
}

.form-group input:focus {
  outline: none;
  background: #FFFFFF;
  border-color: #F97316;
  box-shadow: 0 0 0 3px rgba(249, 115, 22, 0.1);
}

.info-box {
  display: flex;
  gap: 1rem;
  padding: 1rem;
  background: #EFF6FF;
  border: 1px solid #DBEAFE;
  border-radius: 8px;
  color: #1E40AF;
  font-size: 0.9rem;
}

.info-box svg {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  color: #3B82F6;
}

.form-actions {
  display: flex;
  gap: 1rem;
  margin-top: 1rem;
}

.form-actions button {
  flex: 1;
  padding: 0.875rem 1.5rem;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.95rem;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.form-actions button svg {
  width: 18px;
  height: 18px;
}

.btn-primary {
  background: linear-gradient(135deg, #DC2626 0%, #F97316 100%);
  border: 1px solid #DC2626;
  color: white;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(220, 38, 38, 0.3);
}

.btn-secondary {
  background: #FFFFFF;
  border: 1px solid #E5E7EB;
  color: #6B7280;
}

.btn-secondary:hover {
  background: #F3F4F6;
  color: #111827;
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

  .data-table {
    font-size: 0.85rem;
  }

  .data-table th,
  .data-table td {
    padding: 0.75rem 0.5rem;
  }
}
</style>
