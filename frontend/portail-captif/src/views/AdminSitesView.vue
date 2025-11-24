<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useSiteStore } from '@/stores/site'
import { useNotificationStore } from '@/stores/notification'
import LoadingSpinner from '@/components/LoadingSpinner.vue'

const router = useRouter()
const authStore = useAuthStore()
const siteStore = useSiteStore()
const notificationStore = useNotificationStore()

const blockedSites = computed(() => siteStore.sites)
const isLoading = computed(() => siteStore.isLoading)

const showAddModal = ref(false)
const searchQuery = ref('')
const filterType = ref('all')
const filterStatus = ref('all')

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
  if (!confirm(`Voulez-vous vraiment supprimer ${site.url} ?`)) {
    return
  }

  try {
    await siteStore.deleteSite(site.id)
    notificationStore.success('Site supprimé avec succès')
  } catch (error) {
    notificationStore.error('Erreur lors de la suppression')
  }
}

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
  <div class="admin-sites">
    <!-- Header -->
    <header class="page-header">
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
        <button @click="navigateTo('/admin/dashboard')" class="nav-item">
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
        <button @click="navigateTo('/admin/sites')" class="nav-item active">
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

    <!-- Contenu -->
    <main class="page-content">
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
      <div v-if="isLoading" class="loading-container">
        <LoadingSpinner />
      </div>

      <div v-else class="table-container">
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
    </main>

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

.admin-sites {
  min-height: 100vh;
  background: #F9FAFB;
}

/* Header - réutilisation du même style */
.page-header {
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
.page-content {
  max-width: 1600px;
  margin: 0 auto;
  padding: 2rem;
}

.content-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 2rem;
}

.page-title {
  font-size: 1.875rem;
  font-weight: 800;
  color: #1F2937;
  margin-bottom: 0.5rem;
}

.page-subtitle {
  font-size: 1rem;
  color: #6B7280;
}

.btn-primary {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  background: linear-gradient(135deg, #DC2626 0%, #F97316 100%);
  color: white;
  border: none;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 2px 8px rgba(220, 38, 38, 0.2);
}

.btn-primary svg {
  width: 20px;
  height: 20px;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(220, 38, 38, 0.3);
}

/* Statistiques */
.stats-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.stat-box {
  background: #FFFFFF;
  border: 1px solid #E5E7EB;
  border-radius: 12px;
  padding: 1.5rem;
  border-left: 4px solid #6B7280;
}

.stat-box.success {
  border-left-color: #10B981;
}

.stat-box.danger {
  border-left-color: #DC2626;
}

.stat-box.info {
  border-left-color: #3B82F6;
}

.stat-value {
  font-size: 2rem;
  font-weight: 800;
  color: #1F2937;
  margin-bottom: 0.25rem;
}

.stat-label {
  font-size: 0.875rem;
  color: #6B7280;
  font-weight: 500;
}

/* Filtres */
.filters-section {
  background: #FFFFFF;
  border: 1px solid #E5E7EB;
  border-radius: 12px;
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
  color: #9CA3AF;
}

.search-input {
  width: 100%;
  padding: 0.75rem 1rem 0.75rem 3rem;
  border: 1px solid #E5E7EB;
  border-radius: 8px;
  font-size: 0.875rem;
  transition: all 0.2s;
}

.search-input:focus {
  outline: none;
  border-color: #F97316;
  box-shadow: 0 0 0 3px rgba(249, 115, 22, 0.1);
}

.filter-group {
  display: flex;
  gap: 0.75rem;
}

.filter-select {
  padding: 0.75rem 1rem;
  border: 1px solid #E5E7EB;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  color: #1F2937;
  background: white;
  cursor: pointer;
  transition: all 0.2s;
}

.filter-select:focus {
  outline: none;
  border-color: #F97316;
  box-shadow: 0 0 0 3px rgba(249, 115, 22, 0.1);
}

/* Table */
.table-container {
  background: #FFFFFF;
  border: 1px solid #E5E7EB;
  border-radius: 12px;
  overflow: hidden;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table thead {
  background: #F9FAFB;
  border-bottom: 1px solid #E5E7EB;
}

.data-table th {
  padding: 1rem 1.5rem;
  text-align: left;
  font-size: 0.75rem;
  font-weight: 700;
  color: #6B7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.data-table td {
  padding: 1rem 1.5rem;
  font-size: 0.875rem;
  color: #1F2937;
  border-bottom: 1px solid #F3F4F6;
}

.data-table tbody tr:last-child td {
  border-bottom: none;
}

.data-table tbody tr:hover {
  background: #F9FAFB;
}

.url-cell {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.url-cell svg {
  width: 20px;
  height: 20px;
  color: #9CA3AF;
  flex-shrink: 0;
}

.url-cell span {
  font-weight: 500;
  color: #1F2937;
}

.reason-text {
  color: #6B7280;
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
  background: #D1FAE5;
  color: #10B981;
}

.badge-danger {
  background: #FEE2E2;
  color: #DC2626;
}

.badge-info {
  background: #DBEAFE;
  color: #3B82F6;
}

.badge-gray {
  background: #F3F4F6;
  color: #6B7280;
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
  border: 1px solid #E5E7EB;
  border-radius: 6px;
  background: white;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn svg {
  width: 16px;
  height: 16px;
  color: #6B7280;
}

.action-btn.success:hover {
  background: #D1FAE5;
  border-color: #10B981;
}

.action-btn.success:hover svg {
  color: #10B981;
}

.action-btn.danger:hover {
  background: #FEE2E2;
  border-color: #DC2626;
}

.action-btn.danger:hover svg {
  color: #DC2626;
}

.action-btn.delete:hover {
  background: #FEE2E2;
  border-color: #DC2626;
}

.action-btn.delete:hover svg {
  color: #DC2626;
}

.empty-state {
  padding: 4rem 2rem;
  text-align: center;
}

.empty-state svg {
  width: 64px;
  height: 64px;
  color: #D1D5DB;
  margin-bottom: 1rem;
}

.empty-state h3 {
  font-size: 1.125rem;
  font-weight: 600;
  color: #1F2937;
  margin-bottom: 0.5rem;
}

.empty-state p {
  font-size: 0.875rem;
  color: #6B7280;
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.modal-content {
  background: white;
  border-radius: 16px;
  max-width: 500px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.2);
}

.modal-header {
  padding: 1.5rem 2rem;
  border-bottom: 1px solid #E5E7EB;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h3 {
  font-size: 1.25rem;
  font-weight: 700;
  color: #1F2937;
}

.modal-close {
  width: 36px;
  height: 36px;
  border: none;
  background: #F3F4F6;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

.modal-close svg {
  width: 20px;
  height: 20px;
  color: #6B7280;
}

.modal-close:hover {
  background: #FEE2E2;
}

.modal-close:hover svg {
  color: #DC2626;
}

.modal-body {
  padding: 2rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  font-size: 0.875rem;
  font-weight: 600;
  color: #374151;
  margin-bottom: 0.5rem;
}

.form-group small {
  display: block;
  margin-top: 0.5rem;
  font-size: 0.75rem;
  color: #6B7280;
}

.form-group input[type="text"],
.form-group textarea,
.form-select {
  width: 100%;
  padding: 0.75rem 1rem;
  border: 1px solid #E5E7EB;
  border-radius: 8px;
  font-size: 0.875rem;
  transition: all 0.2s;
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
  .header-content {
    flex-direction: column;
    gap: 1rem;
    padding: 1rem;
  }

  .page-content {
    padding: 1rem;
  }

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

  .main-nav {
    padding: 0 1rem 1rem;
  }
}
</style>
