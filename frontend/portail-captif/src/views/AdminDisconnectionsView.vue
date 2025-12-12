<template>
  <div class="admin-disconnections">
    <div class="page-header">
      <h1>Déconnexions automatiques</h1>
      <p class="page-description">
        Gérer les utilisateurs déconnectés automatiquement pour dépassement de quota
      </p>
    </div>

    <!-- Filtres -->
    <div class="filters">
      <div class="filter-group">
        <label>Statut</label>
        <select v-model="filters.status">
          <option value="all">Tous</option>
          <option value="active">Déconnectés (actifs)</option>
          <option value="reconnected">Réactivés</option>
        </select>
      </div>

      <div class="filter-group">
        <label>Raison</label>
        <select v-model="filters.reason">
          <option value="">Toutes</option>
          <option value="quota_exceeded">Quota dépassé</option>
          <option value="daily_limit">Limite journalière</option>
          <option value="weekly_limit">Limite hebdomadaire</option>
          <option value="monthly_limit">Limite mensuelle</option>
          <option value="validity_expired">Validité expirée</option>
        </select>
      </div>

      <div class="filter-group">
        <label>Recherche</label>
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Username, nom..."
          class="search-input"
        />
      </div>

      <button @click="refreshData" class="btn-refresh">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2"/>
        </svg>
        Actualiser
      </button>
    </div>

    <!-- Statistiques -->
    <div class="stats-cards">
      <div class="stat-card">
        <div class="stat-value">{{ stats.total_active }}</div>
        <div class="stat-label">Déconnectés actuellement</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats.today }}</div>
        <div class="stat-label">Aujourd'hui</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats.week }}</div>
        <div class="stat-label">Cette semaine</div>
      </div>
      <div class="stat-card success">
        <div class="stat-value">{{ stats.reconnected }}</div>
        <div class="stat-label">Réactivés</div>
      </div>
    </div>

    <!-- Liste des déconnexions -->
    <div class="disconnections-table">
      <table>
        <thead>
          <tr>
            <th>Utilisateur</th>
            <th>Raison</th>
            <th>Détails</th>
            <th>Déconnecté le</th>
            <th>Statut</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="log in filteredLogs" :key="log.id" :class="{ inactive: !log.is_active }">
            <td>
              <div class="user-info">
                <div class="user-name">{{ log.user_full_name }}</div>
                <div class="user-username">{{ log.user_username }}</div>
              </div>
            </td>
            <td>
              <span class="reason-badge" :class="'reason-' + log.reason">
                {{ log.reason_display }}
              </span>
            </td>
            <td>
              <div class="details">
                {{ log.description }}
                <div v-if="log.quota_used_gb" class="quota-details">
                  {{ log.quota_used_gb }} Go / {{ log.quota_limit_gb }} Go
                </div>
              </div>
            </td>
            <td>
              <div class="date-info">
                {{ formatDate(log.disconnected_at) }}
              </div>
            </td>
            <td>
              <span v-if="log.is_active" class="status-badge active">
                🔴 Déconnecté
              </span>
              <span v-else class="status-badge reconnected">
                ✅ Réactivé
                <div class="reconnected-info">
                  {{ formatDate(log.reconnected_at) }}
                  <br>
                  par {{ log.reconnected_by_username || 'Système' }}
                </div>
              </span>
            </td>
            <td>
              <button
                v-if="log.is_active"
                @click="reactivateUser(log)"
                class="btn-reactivate"
                :disabled="loading"
              >
                Réactiver
              </button>
              <span v-else class="already-reconnected">—</span>
            </td>
          </tr>
        </tbody>
      </table>

      <div v-if="filteredLogs.length === 0" class="empty-state">
        <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
          <circle cx="12" cy="12" r="10"></circle>
          <path d="M12 6v6l4 2"></path>
        </svg>
        <p>Aucune déconnexion trouvée</p>
      </div>
    </div>

    <!-- Pagination -->
    <div v-if="pagination.total > pagination.pageSize" class="pagination">
      <button
        @click="changePage(pagination.currentPage - 1)"
        :disabled="pagination.currentPage === 1"
        class="btn-page"
      >
        Précédent
      </button>
      <span class="page-info">
        Page {{ pagination.currentPage }} / {{ pagination.totalPages }}
      </span>
      <button
        @click="changePage(pagination.currentPage + 1)"
        :disabled="pagination.currentPage === pagination.totalPages"
        class="btn-page"
      >
        Suivant
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

interface DisconnectionLog {
  id: number
  user_username: string
  user_full_name: string
  reason: string
  reason_display: string
  description: string
  disconnected_at: string
  reconnected_at: string | null
  is_active: boolean
  quota_used_gb: number | null
  quota_limit_gb: number | null
  reconnected_by_username: string | null
}

const logs = ref<DisconnectionLog[]>([])
const loading = ref(false)
const searchQuery = ref('')
const filters = ref({
  status: 'active',
  reason: ''
})

const pagination = ref({
  currentPage: 1,
  pageSize: 20,
  total: 0,
  totalPages: 0
})

const stats = ref({
  total_active: 0,
  today: 0,
  week: 0,
  reconnected: 0
})

const filteredLogs = computed(() => {
  let result = logs.value

  // Filtre par statut
  if (filters.value.status === 'active') {
    result = result.filter(log => log.is_active)
  } else if (filters.value.status === 'reconnected') {
    result = result.filter(log => !log.is_active)
  }

  // Filtre par raison
  if (filters.value.reason) {
    result = result.filter(log => log.reason === filters.value.reason)
  }

  // Recherche
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(log =>
      log.user_username.toLowerCase().includes(query) ||
      log.user_full_name.toLowerCase().includes(query)
    )
  }

  return result
})

const fetchLogs = async () => {
  loading.value = true
  try {
    const response = await axios.get('/api/core/disconnection-logs/', {
      params: {
        page: pagination.value.currentPage,
        page_size: pagination.value.pageSize
      }
    })

    logs.value = response.data.results
    pagination.value.total = response.data.count
    pagination.value.totalPages = Math.ceil(response.data.count / pagination.value.pageSize)

    calculateStats()
  } catch (error) {
    console.error('Erreur lors du chargement des logs:', error)
    alert('Erreur lors du chargement des déconnexions')
  } finally {
    loading.value = false
  }
}

const calculateStats = () => {
  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)

  stats.value = {
    total_active: logs.value.filter(log => log.is_active).length,
    today: logs.value.filter(log => {
      const disconnectedAt = new Date(log.disconnected_at)
      return disconnectedAt >= today && log.is_active
    }).length,
    week: logs.value.filter(log => {
      const disconnectedAt = new Date(log.disconnected_at)
      return disconnectedAt >= weekAgo && log.is_active
    }).length,
    reconnected: logs.value.filter(log => !log.is_active).length
  }
}

const reactivateUser = async (log: DisconnectionLog) => {
  if (!confirm(`Voulez-vous réactiver l'utilisateur ${log.user_full_name} (${log.user_username}) ?`)) {
    return
  }

  loading.value = true
  try {
    const response = await axios.post(`/api/core/disconnection-logs/${log.id}/reactivate/`)

    alert(`✅ ${response.data.message}`)

    // Rafraîchir les données
    await fetchLogs()
  } catch (error: any) {
    console.error('Erreur lors de la réactivation:', error)
    const errorMsg = error.response?.data?.error || 'Erreur lors de la réactivation'
    alert(`❌ ${errorMsg}`)
  } finally {
    loading.value = false
  }
}

const changePage = (page: number) => {
  pagination.value.currentPage = page
  fetchLogs()
}

const refreshData = () => {
  fetchLogs()
}

const formatDate = (dateString: string | null) => {
  if (!dateString) return '—'
  const date = new Date(dateString)
  return date.toLocaleString('fr-FR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

onMounted(() => {
  fetchLogs()
})
</script>

<style scoped>
.admin-disconnections {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 2rem;
}

.page-header h1 {
  font-size: 2rem;
  margin: 0 0 0.5rem 0;
  color: #2c3e50;
}

.page-description {
  color: #7f8c8d;
  margin: 0;
}

.filters {
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
  padding: 1.5rem;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  flex-wrap: wrap;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  flex: 1;
  min-width: 200px;
}

.filter-group label {
  font-size: 0.85rem;
  font-weight: 600;
  color: #2c3e50;
}

.filter-group select,
.search-input {
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 0.95rem;
}

.btn-refresh {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: #3498db;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  align-self: flex-end;
}

.btn-refresh:hover {
  background: #2980b9;
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.stat-card {
  background: white;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border-left: 4px solid #e74c3c;
}

.stat-card.success {
  border-left-color: #27ae60;
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  color: #2c3e50;
}

.stat-label {
  font-size: 0.9rem;
  color: #7f8c8d;
  margin-top: 0.5rem;
}

.disconnections-table {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  background: #f8f9fa;
}

th {
  padding: 1rem;
  text-align: left;
  font-weight: 600;
  color: #2c3e50;
  border-bottom: 2px solid #dee2e6;
}

td {
  padding: 1rem;
  border-bottom: 1px solid #dee2e6;
}

tr.inactive {
  opacity: 0.6;
}

.user-info {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.user-name {
  font-weight: 600;
  color: #2c3e50;
}

.user-username {
  font-size: 0.85rem;
  color: #7f8c8d;
}

.reason-badge {
  display: inline-block;
  padding: 0.35rem 0.75rem;
  border-radius: 12px;
  font-size: 0.85rem;
  font-weight: 600;
  background: #e74c3c;
  color: white;
}

.reason-quota_exceeded {
  background: #e74c3c;
}

.reason-daily_limit,
.reason-weekly_limit,
.reason-monthly_limit {
  background: #f39c12;
}

.reason-validity_expired {
  background: #95a5a6;
}

.details {
  font-size: 0.9rem;
  color: #555;
}

.quota-details {
  font-size: 0.8rem;
  color: #7f8c8d;
  margin-top: 0.25rem;
}

.date-info {
  font-size: 0.9rem;
  color: #555;
}

.status-badge {
  display: inline-block;
  padding: 0.35rem 0.75rem;
  border-radius: 12px;
  font-size: 0.85rem;
  font-weight: 600;
}

.status-badge.active {
  background: #ffe5e5;
  color: #e74c3c;
}

.status-badge.reconnected {
  background: #d4edda;
  color: #27ae60;
}

.reconnected-info {
  font-size: 0.75rem;
  margin-top: 0.25rem;
  opacity: 0.8;
}

.btn-reactivate {
  padding: 0.5rem 1rem;
  background: #27ae60;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: background 0.2s;
}

.btn-reactivate:hover {
  background: #229954;
}

.btn-reactivate:disabled {
  background: #95a5a6;
  cursor: not-allowed;
}

.already-reconnected {
  color: #bdc3c7;
}

.empty-state {
  padding: 4rem 2rem;
  text-align: center;
  color: #95a5a6;
}

.empty-state svg {
  margin-bottom: 1rem;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  margin-top: 2rem;
}

.btn-page {
  padding: 0.5rem 1rem;
  background: white;
  border: 1px solid #ddd;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
}

.btn-page:hover:not(:disabled) {
  background: #f8f9fa;
}

.btn-page:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  font-weight: 500;
  color: #2c3e50;
}
</style>
