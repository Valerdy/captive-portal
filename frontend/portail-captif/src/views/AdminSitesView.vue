<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useSiteStore } from '@/stores/site'
import { useNotificationStore } from '@/stores/notification'
import AdminLayout from '@/layouts/AdminLayout.vue'

const router = useRouter()
const authStore = useAuthStore()
const siteStore = useSiteStore()
const notificationStore = useNotificationStore()

const blockedSites = computed(() => siteStore.sites)
const isLoading = computed(() => siteStore.isLoading)

const showAddModal = ref(false)
const showEditModal = ref(false)
const selectedSite = ref<any>(null)
const searchQuery = ref('')
const filterType = ref('all')
const filterStatus = ref('all')
const isDeleting = ref(false)

const newSite = ref({
  url: '',
  type: 'blacklist' as 'blacklist' | 'whitelist',
  reason: ''
})

// Filtrage
const filteredSites = computed(() => {
  let filtered = blockedSites.value

  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(s => s.url.toLowerCase().includes(query))
  }

  if (filterType.value !== 'all') {
    filtered = filtered.filter(s => s.type === filterType.value)
  }

  if (filterStatus.value !== 'all') {
    if (filterStatus.value === 'active') {
      filtered = filtered.filter(s => s.is_active)
    } else {
      filtered = filtered.filter(s => !s.is_active)
    }
  }

  return filtered
})

// Statistiques
const stats = computed(() => ({
  total: blockedSites.value.length,
  blacklist: blockedSites.value.filter(s => s.type === 'blacklist').length,
  whitelist: blockedSites.value.filter(s => s.type === 'whitelist').length,
  active: blockedSites.value.filter(s => s.is_active).length
}))

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

function handleEdit(site: any) {
  selectedSite.value = { ...site }
  showEditModal.value = true
}

function closeEditModal() {
  showEditModal.value = false
  selectedSite.value = null
}

async function handleUpdateSite() {
  if (!selectedSite.value) return

  if (!selectedSite.value.url) {
    notificationStore.warning('Veuillez entrer une URL')
    return
  }

  try {
    await siteStore.updateSite(selectedSite.value.id, {
      url: selectedSite.value.url,
      type: selectedSite.value.type,
      reason: selectedSite.value.reason || null,
      is_active: selectedSite.value.is_active
    })
    notificationStore.success('Site modifié avec succès')
    closeEditModal()
  } catch (error) {
    notificationStore.error(siteStore.error || 'Erreur lors de la modification')
  }
}

async function handleToggleActive(site: any) {
  try {
    await siteStore.updateSite(site.id, {
      is_active: !site.is_active
    })
    notificationStore.success(`Site ${site.is_active ? 'désactivé' : 'activé'}`)
  } catch (error) {
    notificationStore.error('Erreur lors de la modification')
  }
}

async function handleDelete(site: any) {
  // Protection contre les double-clics
  if (isDeleting.value) {
    return
  }

  if (!confirm(`Voulez-vous vraiment supprimer ${site.url} ?`)) {
    return
  }

  isDeleting.value = true
  try {
    await siteStore.deleteSite(site.id)
    notificationStore.success('Site supprimé avec succès')
  } catch (error) {
    notificationStore.error('Erreur lors de la suppression')
  } finally {
    isDeleting.value = false
  }
}
</script>

<template>
  <AdminLayout activePage="sites">
    <div class="content-header">
      <div>
          <h2 class="page-title">Sites bloqués</h2>
          <p class="page-subtitle">Gérer les listes noires et blanches</p>
        </div>
        <button @click="openAddModal" class="btn-primary">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
            <line x1="12" y1="8" x2="12" y2="16" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            <line x1="8" y1="12" x2="16" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
          Ajouter un site
        </button>
      </div>

      <!-- Statistiques -->
      <div class="stats-row">
        <div class="stat-box">
          <div class="stat-value">{{ stats.total }}</div>
          <div class="stat-label">Total sites</div>
        </div>
        <div class="stat-box danger">
          <div class="stat-value">{{ stats.blacklist }}</div>
          <div class="stat-label">Liste noire</div>
        </div>
        <div class="stat-box success">
          <div class="stat-value">{{ stats.whitelist }}</div>
          <div class="stat-label">Liste blanche</div>
        </div>
        <div class="stat-box info">
          <div class="stat-value">{{ stats.active }}</div>
          <div class="stat-label">Actifs</div>
        </div>
      </div>

      <!-- Filtres -->
      <div class="filters-section">
        <div class="search-box">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="11" cy="11" r="8" stroke="currentColor" stroke-width="2"/>
            <path d="m21 21-4.35-4.35" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Rechercher un site..."
            class="search-input"
          />
        </div>

        <div class="filter-group">
          <select v-model="filterType" class="filter-select">
            <option value="all">Tous les types</option>
            <option value="blacklist">Liste noire</option>
            <option value="whitelist">Liste blanche</option>
          </select>

          <select v-model="filterStatus" class="filter-select">
            <option value="all">Tous les statuts</option>
            <option value="active">Actifs</option>
            <option value="inactive">Inactifs</option>
          </select>
        </div>
      </div>

      <!-- Table -->
      <div class="table-container">
        <table class="data-table">
          <thead>
            <tr>
              <th>URL</th>
              <th>Type</th>
              <th>Raison</th>
              <th>Statut</th>
              <th>Date d'ajout</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="site in filteredSites" :key="site.id">
              <td>
                <div class="url-cell">
                  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                    <path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" stroke="currentColor" stroke-width="2"/>
                  </svg>
                  <span>{{ site.url }}</span>
                </div>
              </td>
              <td>
                <span v-if="site.type === 'blacklist'" class="badge badge-danger">Liste noire</span>
                <span v-else class="badge badge-success">Liste blanche</span>
              </td>
              <td>
                <span class="reason-text">{{ site.reason || '-' }}</span>
              </td>
              <td>
                <span v-if="site.is_active" class="badge badge-success">Actif</span>
                <span v-else class="badge badge-gray">Inactif</span>
              </td>
              <td>{{ new Date(site.added_date).toLocaleDateString('fr-FR') }}</td>
              <td>
                <div class="action-buttons">
                  <button @click="handleEdit(site)" class="action-btn edit" title="Modifier">
                    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                  </button>
                  <button @click="handleToggleActive(site)" :class="['action-btn', site.is_active ? 'danger' : 'success']" :title="site.is_active ? 'Désactiver' : 'Activer'">
                    <svg v-if="site.is_active" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                      <line x1="4.93" y1="4.93" x2="19.07" y2="19.07" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                    </svg>
                    <svg v-else viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      <polyline points="22 4 12 14.01 9 11.01" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                  </button>
                  <button @click="handleDelete(site)" class="action-btn delete" title="Supprimer">
                    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <polyline points="3 6 5 6 21 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>

        <div v-if="filteredSites.length === 0" class="empty-state">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
            <line x1="4.93" y1="4.93" x2="19.07" y2="19.07" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
          <h3>Aucun site trouvé</h3>
          <p>Aucun site ne correspond à vos critères de recherche</p>
        </div>
      </div>

    <!-- Modal Ajout -->
    <div v-if="showAddModal" class="modal-overlay" @click.self="closeAddModal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>Ajouter un site</h3>
          <button @click="closeAddModal" class="modal-close">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <line x1="18" y1="6" x2="6" y2="18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              <line x1="6" y1="6" x2="18" y2="18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </button>
        </div>

        <div class="modal-body">
          <div class="form-group">
            <label>URL du site *</label>
            <input v-model="newSite.url" type="text" placeholder="example.com" />
            <small>Entrez le domaine sans http:// ou https://</small>
          </div>

          <div class="form-group">
            <label>Type de liste *</label>
            <select v-model="newSite.type" class="form-select">
              <option value="blacklist">Liste noire (bloquer)</option>
              <option value="whitelist">Liste blanche (autoriser)</option>
            </select>
          </div>

          <div class="form-group">
            <label>Raison (optionnel)</label>
            <textarea v-model="newSite.reason" rows="3" placeholder="Expliquez pourquoi ce site est ajouté..."></textarea>
          </div>
        </div>

        <div class="modal-footer">
          <button @click="closeAddModal" class="btn-secondary">Annuler</button>
          <button @click="handleAddSite" class="btn-primary">Ajouter</button>
        </div>
      </div>
    </div>

    <!-- Modal Édition -->
    <div v-if="showEditModal && selectedSite" class="modal-overlay" @click.self="closeEditModal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>Modifier le site</h3>
          <button @click="closeEditModal" class="modal-close">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <line x1="18" y1="6" x2="6" y2="18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              <line x1="6" y1="6" x2="18" y2="18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </button>
        </div>

        <div class="modal-body">
          <div class="form-group">
            <label>URL du site *</label>
            <input v-model="selectedSite.url" type="text" placeholder="example.com" />
            <small>Entrez le domaine sans http:// ou https://</small>
          </div>

          <div class="form-group">
            <label>Type de liste *</label>
            <select v-model="selectedSite.type" class="form-select">
              <option value="blacklist">Liste noire (bloquer)</option>
              <option value="whitelist">Liste blanche (autoriser)</option>
            </select>
          </div>

          <div class="form-group">
            <label>Raison (optionnel)</label>
            <textarea v-model="selectedSite.reason" rows="3" placeholder="Expliquez pourquoi ce site est ajouté..."></textarea>
          </div>

          <div class="form-group checkbox-group">
            <label class="checkbox-label">
              <input v-model="selectedSite.is_active" type="checkbox" />
              <span class="checkbox-text">
                <strong>Site actif</strong>
                <small>Si désactivé, le blocage/autorisation ne sera pas appliqué</small>
              </span>
            </label>
          </div>
        </div>

        <div class="modal-footer">
          <button @click="closeEditModal" class="btn-secondary">Annuler</button>
          <button @click="handleUpdateSite" class="btn-primary">Enregistrer</button>
        </div>
      </div>
    </div>
  </AdminLayout>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* Contenu spécifique à la page sites */

.content-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 2rem;
}

.page-title {
  font-family: 'Orbitron', monospace;
  font-size: 1.875rem;
  font-weight: 800;
  color: #F29400;
  margin-bottom: 0.5rem;
  text-shadow: 0 0 20px rgba(242, 148, 0, 0.3);
}

.page-subtitle {
  font-family: 'Rajdhani', sans-serif;
  font-size: 1rem;
  color: rgba(255, 255, 255, 0.6);
}

.btn-primary {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  background: linear-gradient(135deg, #F29400 0%, #008ecf 100%);
  color: white;
  border: none;
  border-radius: 10px;
  font-family: 'Rajdhani', sans-serif;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 4px 15px rgba(242, 148, 0, 0.3);
}

.btn-primary svg {
  width: 20px;
  height: 20px;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(242, 148, 0, 0.4);
}

/* Statistiques */
.stats-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.stat-box {
  background: rgba(15, 15, 25, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 1.5rem;
  border-left: 4px solid #636362;
  transition: all 0.3s;
}

.stat-box:hover {
  border-color: rgba(0, 142, 207, 0.3);
  box-shadow: 0 8px 32px rgba(0, 142, 207, 0.15);
}

.stat-box.success {
  border-left-color: #10B981;
}

.stat-box.danger {
  border-left-color: #e53212;
}

.stat-box.info {
  border-left-color: #008ecf;
}

.stat-value {
  font-family: 'Orbitron', monospace;
  font-size: 2rem;
  font-weight: 800;
  color: #F29400;
  margin-bottom: 0.25rem;
  text-shadow: 0 0 15px rgba(242, 148, 0, 0.3);
}

.stat-label {
  font-family: 'Rajdhani', sans-serif;
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.6);
  font-weight: 500;
}

/* Filtres */
.filters-section {
  background: rgba(15, 15, 25, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  display: flex;
  gap: 1rem;
  align-items: center;
}

.search-box {
  flex: 1;
  position: relative;
  display: flex;
  align-items: center;
}

.search-box svg {
  position: absolute;
  left: 1rem;
  width: 20px;
  height: 20px;
  color: rgba(255, 255, 255, 0.4);
}

.search-input {
  width: 100%;
  padding: 0.75rem 1rem 0.75rem 3rem;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  font-size: 0.875rem;
  background: rgba(0, 0, 0, 0.3);
  color: rgba(255, 255, 255, 0.9);
  transition: all 0.3s;
}

.search-input::placeholder {
  color: rgba(255, 255, 255, 0.4);
}

.search-input:focus {
  outline: none;
  border-color: #008ecf;
  box-shadow: 0 0 15px rgba(0, 142, 207, 0.2);
}

.filter-group {
  display: flex;
  gap: 0.75rem;
}

.filter-select {
  padding: 0.75rem 1rem;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.9);
  background: rgba(0, 0, 0, 0.3);
  cursor: pointer;
  transition: all 0.3s;
}

.filter-select:focus {
  outline: none;
  border-color: #008ecf;
  box-shadow: 0 0 15px rgba(0, 142, 207, 0.2);
}

/* Table */
.table-container {
  background: rgba(15, 15, 25, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  overflow: hidden;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table thead {
  background: rgba(0, 142, 207, 0.1);
  border-bottom: 1px solid rgba(0, 142, 207, 0.2);
}

.data-table th {
  padding: 1rem 1.5rem;
  text-align: left;
  font-family: 'Orbitron', monospace;
  font-size: 0.75rem;
  font-weight: 600;
  color: #008ecf;
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.data-table td {
  padding: 1rem 1.5rem;
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.9);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.data-table tbody tr:last-child td {
  border-bottom: none;
}

.data-table tbody tr:hover {
  background: rgba(0, 142, 207, 0.05);
}

.url-cell {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.url-cell svg {
  width: 20px;
  height: 20px;
  color: rgba(255, 255, 255, 0.4);
  flex-shrink: 0;
}

.url-cell span {
  font-weight: 500;
  color: rgba(255, 255, 255, 0.95);
}

.reason-text {
  color: rgba(255, 255, 255, 0.5);
  font-style: italic;
}

.badge {
  display: inline-block;
  padding: 0.375rem 0.75rem;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
}

.badge-success {
  background: rgba(16, 185, 129, 0.2);
  color: #10B981;
}

.badge-danger {
  background: rgba(229, 50, 18, 0.2);
  color: #e53212;
}

.badge-info {
  background: rgba(0, 142, 207, 0.2);
  color: #008ecf;
}

.badge-gray {
  background: rgba(99, 99, 98, 0.3);
  color: rgba(255, 255, 255, 0.6);
}

.action-buttons {
  display: flex;
  gap: 0.5rem;
}

.action-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  background: rgba(0, 0, 0, 0.3);
  cursor: pointer;
  transition: all 0.3s;
}

.action-btn svg {
  width: 16px;
  height: 16px;
  color: rgba(255, 255, 255, 0.6);
}

.action-btn.success:hover {
  background: rgba(16, 185, 129, 0.2);
  border-color: #10B981;
}

.action-btn.success:hover svg {
  color: #10B981;
}

.action-btn.danger:hover {
  background: rgba(229, 50, 18, 0.2);
  border-color: #e53212;
}

.action-btn.danger:hover svg {
  color: #e53212;
}

.action-btn.edit:hover {
  background: rgba(0, 142, 207, 0.2);
  border-color: #008ecf;
}

.action-btn.edit:hover svg {
  color: #008ecf;
}

.action-btn.delete:hover {
  background: rgba(229, 50, 18, 0.2);
  border-color: #e53212;
}

.action-btn.delete:hover svg {
  color: #e53212;
}

.empty-state {
  padding: 4rem 2rem;
  text-align: center;
}

.empty-state svg {
  width: 64px;
  height: 64px;
  color: rgba(255, 255, 255, 0.2);
  margin-bottom: 1rem;
}

.empty-state h3 {
  font-family: 'Orbitron', monospace;
  font-size: 1.125rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  margin-bottom: 0.5rem;
}

.empty-state p {
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.5);
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.modal-content {
  background: rgba(15, 15, 25, 0.95);
  border: 1px solid rgba(0, 142, 207, 0.2);
  border-radius: 16px;
  max-width: 600px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 50px rgba(0, 142, 207, 0.2);
}

.modal-header {
  padding: 1.5rem 2rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h3 {
  font-family: 'Orbitron', monospace;
  font-size: 1.25rem;
  font-weight: 700;
  color: #008ecf;
}

.modal-close {
  width: 36px;
  height: 36px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(0, 0, 0, 0.3);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s;
}

.modal-close svg {
  width: 20px;
  height: 20px;
  color: rgba(255, 255, 255, 0.6);
}

.modal-close:hover {
  background: rgba(229, 50, 18, 0.2);
  border-color: #e53212;
}

.modal-close:hover svg {
  color: #e53212;
}

.modal-body {
  padding: 2rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  font-family: 'Rajdhani', sans-serif;
  font-size: 0.875rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 0.5rem;
}

.form-group small {
  display: block;
  margin-top: 0.5rem;
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
}

.form-group input[type="text"],
.form-group textarea,
.form-select {
  width: 100%;
  padding: 0.75rem 1rem;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  font-size: 0.875rem;
  background: rgba(0, 0, 0, 0.3);
  color: rgba(255, 255, 255, 0.9);
  transition: all 0.3s;
}

.form-group input:focus,
.form-group textarea:focus,
.form-select:focus {
  outline: none;
  border-color: #F97316;
  box-shadow: 0 0 0 3px rgba(249, 115, 22, 0.1);
}

.form-group textarea {
  resize: vertical;
  font-family: inherit;
}

.checkbox-group {
  margin-top: 1rem;
}

.checkbox-label {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  cursor: pointer;
}

.checkbox-label input[type="checkbox"] {
  width: 20px;
  height: 20px;
  margin-top: 2px;
  cursor: pointer;
  accent-color: #F29400;
}

.checkbox-text {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.checkbox-text strong {
  font-size: 0.875rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

.checkbox-text small {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
}

.modal-footer {
  padding: 1.5rem 2rem;
  border-top: 1px solid #E5E7EB;
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
}

.btn-secondary {
  padding: 0.75rem 1.5rem;
  background: #F3F4F6;
  color: #374151;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-secondary:hover {
  background: #E5E7EB;
}

.loading-container {
  padding: 4rem 0;
  display: flex;
  justify-content: center;
}

/* Responsive */
@media (max-width: 768px) {
  .content-header {
    flex-direction: column;
    gap: 1rem;
  }

  .btn-primary {
    width: 100%;
    justify-content: center;
  }

  .filters-section {
    flex-direction: column;
  }

  .filter-group {
    width: 100%;
    flex-direction: column;
  }

  .filter-select {
    width: 100%;
  }

  .stats-row {
    grid-template-columns: 1fr;
  }

  .table-container {
    overflow-x: auto;
  }

  .data-table {
    min-width: 800px;
  }
}
</style>
