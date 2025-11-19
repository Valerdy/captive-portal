<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useNotificationStore } from '@/stores/notification'
import DataTable from '@/components/DataTable.vue'

const router = useRouter()
const authStore = useAuthStore()
const notificationStore = useNotificationStore()

const quotas = ref([
  { id: 1, user: 'john_doe', daily_limit: 5, weekly_limit: 30, monthly_limit: 120, used_today: 3.2, used_week: 18.5, used_month: 75.3, is_active: true },
  { id: 2, user: 'jane_smith', daily_limit: 10, weekly_limit: 50, monthly_limit: 200, used_today: 7.8, used_week: 42.1, used_month: 168.9, is_active: true },
  { id: 3, user: 'user123', daily_limit: 3, weekly_limit: 20, monthly_limit: 80, used_today: 2.1, used_week: 12.3, used_month: 45.7, is_active: true }
])

const showEditModal = ref(false)
const selectedQuota = ref<any>(null)

const columns = [
  { key: 'user', label: 'Utilisateur', sortable: true },
  { key: 'daily_limit', label: 'Quota jour (GB)', sortable: true },
  { key: 'used_today', label: 'Utilisé (GB)', sortable: true },
  { key: 'weekly_limit', label: 'Quota semaine (GB)', sortable: true },
  { key: 'monthly_limit', label: 'Quota mois (GB)', sortable: true },
  { key: 'is_active', label: 'Statut', sortable: true },
  { key: 'actions', label: 'Actions', sortable: false }
]

onMounted(() => {
  if (!authStore.isAdmin) {
    router.push('/')
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
    const index = quotas.value.findIndex(q => q.id === selectedQuota.value.id)
    if (index !== -1) {
      quotas.value[index] = { ...selectedQuota.value }
    }

    notificationStore.success('Quota modifié avec succès')
    closeEditModal()
  } catch (error) {
    notificationStore.error('Erreur lors de la modification')
  }
}

async function handleToggleStatus(quotaId: number, currentStatus: boolean) {
  const action = currentStatus ? 'désactiver' : 'activer'
  if (confirm(`Voulez-vous vraiment ${action} ce quota ?`)) {
    try {
      const quota = quotas.value.find(q => q.id === quotaId)
      if (quota) {
        quota.is_active = !currentStatus
      }
      notificationStore.success(`Quota ${currentStatus ? 'désactivé' : 'activé'} avec succès`)
    } catch (error) {
      notificationStore.error('Erreur lors de la modification')
    }
  }
}

async function handleReset(quotaId: number) {
  if (confirm('Voulez-vous vraiment réinitialiser les compteurs de ce quota ?')) {
    try {
      const quota = quotas.value.find(q => q.id === quotaId)
      if (quota) {
        quota.used_today = 0
        quota.used_week = 0
        quota.used_month = 0
      }
      notificationStore.success('Compteurs réinitialisés avec succès')
    } catch (error) {
      notificationStore.error('Erreur lors de la réinitialisation')
    }
  }
}

function goBack() {
  router.push('/admin/dashboard')
}
</script>

<template>
  <div class="admin-quotas">
    <header class="page-header">
      <button @click="goBack" class="back-btn">
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M19 12H5M5 12l7 7m-7-7 7-7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        Retour
      </button>

      <div class="header-info">
        <h1>Gestion des quotas</h1>
        <p>Configuration des limites de bande passante par utilisateur</p>
      </div>
    </header>

    <main class="page-content">
      <div class="content-card">
        <DataTable
          :columns="columns"
          :data="quotas"
          export-filename="quotas-ucac-icam"
        >
          <template #cell-used_today="{ value, row }">
            <div class="usage-cell">
              <span>{{ value.toFixed(1) }} GB</span>
              <div class="progress-mini">
                <div class="progress-fill" :style="{ width: (value / row.daily_limit * 100) + '%' }"></div>
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

          <h2>Modifier les quotas</h2>
          <p class="modal-subtitle">Utilisateur: <strong>{{ selectedQuota.user }}</strong></p>

          <form @submit.prevent="handleUpdateQuota" class="form">
            <div class="form-group">
              <label>Quota journalier (GB)</label>
              <input v-model.number="selectedQuota.daily_limit" type="number" step="0.1" min="0" required />
            </div>

            <div class="form-group">
              <label>Quota hebdomadaire (GB)</label>
              <input v-model.number="selectedQuota.weekly_limit" type="number" step="0.1" min="0" required />
            </div>

            <div class="form-group">
              <label>Quota mensuel (GB)</label>
              <input v-model.number="selectedQuota.monthly_limit" type="number" step="0.1" min="0" required />
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
              <button type="submit" class="btn-primary">Enregistrer</button>
            </div>
          </form>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.admin-quotas {
  min-height: 100vh;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
  padding: 2rem;
  color: white;
}

.page-header {
  max-width: 1400px;
  margin: 0 auto 2rem;
}

.back-btn {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 0.75rem 1.25rem;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  transition: all 0.3s ease;
  color: white;
  margin-bottom: 1.5rem;
}

.back-btn:hover {
  background: rgba(255, 255, 255, 0.1);
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
}

.header-info p {
  color: rgba(255, 255, 255, 0.6);
}

.page-content {
  max-width: 1400px;
  margin: 0 auto;
}

.content-card {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 2rem;
}

.usage-cell {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.progress-mini {
  width: 100px;
  height: 6px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #10b981, #34d399);
  transition: width 0.5s ease;
  border-radius: 3px;
}

.status-badge {
  display: inline-block;
  padding: 0.375rem 0.875rem;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 600;
}

.status-badge.active {
  background: rgba(16, 185, 129, 0.15);
  color: #34d399;
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.status-badge.inactive {
  background: rgba(220, 38, 38, 0.15);
  color: #f87171;
  border: 1px solid rgba(220, 38, 38, 0.3);
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
  background: rgba(59, 130, 246, 0.1);
  color: #60a5fa;
  border-color: rgba(59, 130, 246, 0.2);
}

.action-btn.edit:hover {
  background: rgba(59, 130, 246, 0.2);
  border-color: rgba(59, 130, 246, 0.4);
}

.action-btn.reset {
  background: rgba(16, 185, 129, 0.1);
  color: #34d399;
  border-color: rgba(16, 185, 129, 0.2);
}

.action-btn.reset:hover {
  background: rgba(16, 185, 129, 0.2);
  border-color: rgba(16, 185, 129, 0.4);
}

.action-btn.toggle {
  background: rgba(245, 158, 11, 0.1);
  color: #fbbf24;
  border-color: rgba(245, 158, 11, 0.2);
}

.action-btn.toggle:hover {
  background: rgba(245, 158, 11, 0.2);
  border-color: rgba(245, 158, 11, 0.4);
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.75);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 1rem;
}

.modal-content {
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 24px;
  padding: 2.5rem;
  max-width: 600px;
  width: 100%;
  position: relative;
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.5);
}

.modal-close {
  position: absolute;
  top: 1.5rem;
  right: 1.5rem;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  color: rgba(255, 255, 255, 0.6);
}

.modal-close:hover {
  background: rgba(220, 38, 38, 0.2);
  color: #f87171;
  transform: rotate(90deg);
}

.modal-content h2 {
  color: white;
  font-size: 1.75rem;
  font-weight: 800;
  margin-bottom: 0.5rem;
}

.modal-subtitle {
  color: rgba(255, 255, 255, 0.7);
  font-size: 1rem;
  margin-bottom: 2rem;
}

.modal-subtitle strong {
  color: #f97316;
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
  color: rgba(255, 255, 255, 0.9);
  font-weight: 600;
  font-size: 0.95rem;
}

.form-group input {
  width: 100%;
  padding: 0.875rem;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  color: white;
  font-size: 1rem;
  transition: all 0.3s ease;
}

.form-group input:focus {
  outline: none;
  background: rgba(255, 255, 255, 0.08);
  border-color: #f97316;
}

.info-box {
  display: flex;
  gap: 1rem;
  padding: 1rem;
  background: rgba(59, 130, 246, 0.1);
  border: 1px solid rgba(59, 130, 246, 0.2);
  border-radius: 12px;
  color: #60a5fa;
  font-size: 0.9rem;
}

.info-box svg {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

.form-actions {
  display: flex;
  gap: 1rem;
  margin-top: 1rem;
}

.form-actions button {
  flex: 1;
  padding: 1rem;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-primary {
  background: linear-gradient(135deg, #dc2626 0%, #f97316 100%);
  border: 2px solid rgba(220, 38, 38, 0.5);
  color: white;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(220, 38, 38, 0.4);
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: white;
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.1);
}

@media (max-width: 768px) {
  .admin-quotas {
    padding: 1rem;
  }
}
</style>
