<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useQuotaStore } from '@/stores/quota'
import { useNotificationStore } from '@/stores/notification'
import AdminLayout from '@/layouts/AdminLayout.vue'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import DataTable from '@/components/DataTable.vue'

const router = useRouter()
const authStore = useAuthStore()
const quotaStore = useQuotaStore()
const notificationStore = useNotificationStore()

const quotas = computed(() => quotaStore.quotas)
const isLoading = computed(() => quotaStore.isLoading)

const showEditModal = ref(false)
const selectedQuota = ref<any>(null)

const columns = [
  { key: 'user_username', label: 'Utilisateur', sortable: true },
  { key: 'daily_limit_gb', label: 'Quota jour (GB)', sortable: true },
  { key: 'used_today_gb', label: 'Utilisé (GB)', sortable: true },
  { key: 'weekly_limit_gb', label: 'Quota semaine (GB)', sortable: true },
  { key: 'monthly_limit_gb', label: 'Quota mois (GB)', sortable: true },
  { key: 'is_active', label: 'Statut', sortable: true },
  { key: 'actions', label: 'Actions', sortable: false }
]

// Fonction pour obtenir la couleur de la barre de progression
function getProgressColor(percent: number) {
  if (percent >= 90) return 'linear-gradient(90deg, #DC2626, #EF4444)' // Rouge
  if (percent >= 75) return 'linear-gradient(90deg, #F97316, #FB923C)' // Orange
  return 'linear-gradient(90deg, #10B981, #34D399)' // Vert
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
</script>

<template>
  <AdminLayout activePage="quotas">
      <LoadingSpinner v-if="isLoading" />

      <div v-else class="content-card">
        <DataTable
          :columns="columns"
          :data="quotas"
          :loading="isLoading"
          export-filename="quotas-ucac-icam"
        >
          <template #cell-used_today_gb="{ value, row }">
            <div class="usage-cell">
              <div class="usage-text">
                <span class="usage-value">{{ value?.toFixed(2) }} GB</span>
                <span class="usage-percent">{{ row.daily_usage_percent?.toFixed(0) }}%</span>
              </div>
              <div class="progress-bar-container">
                <div
                  class="progress-bar-fill"
                  :style="{
                    width: Math.min(row.daily_usage_percent, 100) + '%',
                    background: getProgressColor(row.daily_usage_percent)
                  }"
                ></div>
              </div>
            </div>
          </template>
          <template #cell-is_active="{ value }">
            <span :class="['status-badge', value ? 'active' : 'inactive']">
              {{ value ? 'Actif' : 'Inactif' }}
            </span>
          </template>
          <template #cell-actions="{ row }">
            <div class="action-buttons">
              <button @click="handleEdit(row)" class="action-btn edit" title="Modifier">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </button>
              <button @click="handleReset(row.id)" class="action-btn reset" title="Réinitialiser">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <polyline points="23 4 23 10 17 10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </button>
              <button @click="handleToggleStatus(row.id, row.is_active)" class="action-btn toggle" :title="row.is_active ? 'Désactiver' : 'Activer'">
                <svg v-if="row.is_active" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
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
          </template>
        </DataTable>
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
  </AdminLayout>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* Contenu spécifique à la page quotas */


.content-card {
  background: #FFFFFF;
  border: 1px solid #E5E7EB;
  border-radius: 16px;
  padding: 2rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
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
  font-size: 0.95rem;
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

.status-badge {
  display: inline-block;
  padding: 0.375rem 0.875rem;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 600;
}

.status-badge.active {
  background: #D1FAE5;
  color: #059669;
  border: 1px solid #A7F3D0;
}

.status-badge.inactive {
  background: #FEE2E2;
  color: #DC2626;
  border: 1px solid #FECACA;
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
  transition: all 0.3s ease;
  border: 1px solid transparent;
}

.action-btn svg {
  width: 18px;
  height: 18px;
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

/* Responsive */
@media (max-width: 1024px) {
  .charts-section {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
}
</style>
