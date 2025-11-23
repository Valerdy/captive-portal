<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useSiteStore } from '@/stores/site'
import { useNotificationStore } from '@/stores/notification'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import DataTable from '@/components/DataTable.vue'

const router = useRouter()
const authStore = useAuthStore()
const siteStore = useSiteStore()
const notificationStore = useNotificationStore()

const blockedSites = computed(() => siteStore.sites)
const isLoading = computed(() => siteStore.isLoading)

const showAddModal = ref(false)
const newSite = ref({
  url: '',
  type: 'blacklist' as 'blacklist' | 'whitelist',
  reason: ''
})

const columns = [
  { key: 'url', label: 'URL', sortable: true },
  { key: 'type', label: 'Type', sortable: true, formatter: (value: string) => value === 'blacklist' ? 'Liste noire' : 'Liste blanche' },
  { key: 'reason', label: 'Raison', sortable: false },
  { key: 'added_date', label: 'Ajouté le', sortable: true, formatter: (value: string) => new Date(value).toLocaleDateString('fr-FR') },
  { key: 'is_active', label: 'Statut', sortable: true },
  { key: 'actions', label: 'Actions', sortable: false }
]

onMounted(async () => {
  if (!authStore.isAdmin) {
    notificationStore.error('Accès refusé')
    router.push('/')
    return
  }

  try {
    await siteStore.fetchSites()
  } catch (error) {
    notificationStore.error('Erreur lors du chargement des sites')
  }
})

function openAddModal() {
  newSite.value = {
    url: '',
    type: 'blacklist',
    reason: ''
  }
  showAddModal.value = true
}

function closeAddModal() {
  showAddModal.value = false
}

async function handleAddSite() {
  if (!newSite.value.url) {
    notificationStore.warning('Veuillez entrer une URL')
    return
  }

  try {
    await siteStore.createSite({
      url: newSite.value.url,
      type: newSite.value.type,
      reason: newSite.value.reason || null,
      is_active: true
    })

    notificationStore.success('Site ajouté avec succès')
    closeAddModal()
  } catch (error) {
    notificationStore.error(siteStore.error || 'Erreur lors de l\'ajout')
  }
}

async function handleToggleStatus(siteId: number, currentStatus: boolean) {
  const action = currentStatus ? 'désactiver' : 'activer'
  if (confirm(`Voulez-vous vraiment ${action} ce site ?`)) {
    try {
      await siteStore.updateSite(siteId, {
        is_active: !currentStatus
      })
      notificationStore.success(`Site ${currentStatus ? 'désactivé' : 'activé'} avec succès`)
    } catch (error) {
      notificationStore.error(siteStore.error || 'Erreur lors de la modification')
    }
  }
}

async function handleDelete(siteId: number) {
  if (confirm('Voulez-vous vraiment supprimer ce site ?')) {
    try {
      await siteStore.deleteSite(siteId)
      notificationStore.success('Site supprimé avec succès')
    } catch (error) {
      notificationStore.error(siteStore.error || 'Erreur lors de la suppression')
    }
  }
}

function goBack() {
  router.push('/admin/dashboard')
}
</script>

<template>
  <div class="admin-sites">
    <header class="page-header">
      <button @click="goBack" class="back-btn">
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M19 12H5M5 12l7 7m-7-7 7-7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        Retour
      </button>

      <div class="header-content">
        <div class="header-info">
          <h1>Gestion des sites</h1>
          <p>Blacklist et Whitelist - {{ blockedSites.length }} sites configurés</p>
        </div>
        <button @click="openAddModal" class="add-btn">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
            <line x1="12" y1="8" x2="12" y2="16" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            <line x1="8" y1="12" x2="16" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
          Ajouter un site
        </button>
      </div>
    </header>

    <main class="page-content">
      <LoadingSpinner v-if="isLoading" />

      <div v-else class="content-card">
        <DataTable
          :columns="columns"
          :data="blockedSites"
          :loading="isLoading"
          export-filename="sites-bloques-ucac-icam"
        >
          <template #cell-type="{ value }">
            <span :class="['type-badge', value]">
              {{ value === 'blacklist' ? 'Liste noire' : 'Liste blanche' }}
            </span>
          </template>
          <template #cell-is_active="{ value }">
            <span :class="['status-badge', value ? 'active' : 'inactive']">
              {{ value ? 'Actif' : 'Inactif' }}
            </span>
          </template>
          <template #cell-actions="{ row }">
            <div class="action-buttons">
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
              <button @click="handleDelete(row.id)" class="action-btn delete" title="Supprimer">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <polyline points="3 6 5 6 21 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </button>
            </div>
          </template>
        </DataTable>
      </div>
    </main>

    <!-- Modal Ajout -->
    <Teleport to="body">
      <div v-if="showAddModal" class="modal-overlay" @click="closeAddModal">
        <div class="modal-content" @click.stop>
          <button @click="closeAddModal" class="modal-close">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </button>

          <h2>Ajouter un site</h2>

          <form @submit.prevent="handleAddSite" class="form">
            <div class="form-group">
              <label>URL du site *</label>
              <input v-model="newSite.url" type="text" placeholder="exemple.com" required />
            </div>

            <div class="form-group">
              <label>Type *</label>
              <select v-model="newSite.type" required>
                <option value="blacklist">Liste noire (bloquer)</option>
                <option value="whitelist">Liste blanche (autoriser)</option>
              </select>
            </div>

            <div class="form-group">
              <label>Raison</label>
              <textarea v-model="newSite.reason" placeholder="Raison du blocage/autorisation..." rows="3"></textarea>
            </div>

            <div class="form-actions">
              <button type="button" @click="closeAddModal" class="btn-secondary">Annuler</button>
              <button type="submit" class="btn-primary">Ajouter</button>
            </div>
          </form>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.admin-sites {
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

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 2rem;
}

.header-info h1 {
  font-size: 2rem;
  font-weight: 800;
  margin-bottom: 0.5rem;
}

.header-info p {
  color: rgba(255, 255, 255, 0.6);
}

.add-btn {
  background: linear-gradient(135deg, #dc2626 0%, #f97316 100%);
  border: 2px solid rgba(220, 38, 38, 0.5);
  border-radius: 12px;
  padding: 1rem 1.5rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  cursor: pointer;
  transition: all 0.3s ease;
  color: white;
  font-weight: 600;
  box-shadow: 0 4px 12px rgba(220, 38, 38, 0.3);
}

.add-btn svg {
  width: 20px;
  height: 20px;
}

.add-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(220, 38, 38, 0.4);
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

.type-badge {
  display: inline-block;
  padding: 0.375rem 0.875rem;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 600;
}

.type-badge.blacklist {
  background: rgba(220, 38, 38, 0.15);
  color: #f87171;
  border: 1px solid rgba(220, 38, 38, 0.3);
}

.type-badge.whitelist {
  background: rgba(16, 185, 129, 0.15);
  color: #34d399;
  border: 1px solid rgba(16, 185, 129, 0.3);
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
  background: rgba(107, 114, 128, 0.15);
  color: #9ca3af;
  border: 1px solid rgba(107, 114, 128, 0.3);
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

.action-btn.toggle {
  background: rgba(245, 158, 11, 0.1);
  color: #fbbf24;
  border-color: rgba(245, 158, 11, 0.2);
}

.action-btn.toggle:hover {
  background: rgba(245, 158, 11, 0.2);
  border-color: rgba(245, 158, 11, 0.4);
}

.action-btn.delete {
  background: rgba(220, 38, 38, 0.1);
  color: #f87171;
  border-color: rgba(220, 38, 38, 0.2);
}

.action-btn.delete:hover {
  background: rgba(220, 38, 38, 0.2);
  border-color: rgba(220, 38, 38, 0.4);
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
  margin-bottom: 2rem;
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

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 0.875rem;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  color: white;
  font-size: 1rem;
  transition: all 0.3s ease;
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  outline: none;
  background: rgba(255, 255, 255, 0.08);
  border-color: #f97316;
}

.form-group textarea {
  resize: vertical;
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
  .admin-sites {
    padding: 1rem;
  }

  .header-content {
    flex-direction: column;
    align-items: flex-start;
  }

  .add-btn {
    width: 100%;
    justify-content: center;
  }
}
</style>
