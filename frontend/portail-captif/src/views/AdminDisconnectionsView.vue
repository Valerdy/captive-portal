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
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Rajdhani:wght@300;400;500;600;700&family=Inter:wght@300;400;500;600;700;800&display=swap');

.admin-disconnections {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 2rem;
}

.page-header h1 {
  font-family: 'Orbitron', monospace;
  font-size: 2rem;
  margin: 0 0 0.5rem 0;
  color: #F29400;
  text-shadow: 0 0 20px rgba(242, 148, 0, 0.3);
}

.page-description {
  font-family: 'Rajdhani', sans-serif;
  color: rgba(255, 255, 255, 0.6);
  margin: 0;
}

.filters {
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
  padding: 1.5rem;
  background: rgba(15, 15, 25, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
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
  font-family: 'Rajdhani', sans-serif;
  font-size: 0.85rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.7);
}

.filter-group select,
.search-input {
  padding: 0.5rem;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  font-size: 0.95rem;
  background: rgba(0, 0, 0, 0.3);
  color: rgba(255, 255, 255, 0.9);
  transition: all 0.3s;
}

.filter-group select:focus,
.search-input:focus {
  outline: none;
  border-color: #008ecf;
  box-shadow: 0 0 15px rgba(0, 142, 207, 0.2);
}

.btn-refresh {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: linear-gradient(135deg, #008ecf 0%, #00b4e6 100%);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-family: 'Rajdhani', sans-serif;
  font-weight: 600;
  align-self: flex-end;
  transition: all 0.3s;
}

.btn-refresh:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(0, 142, 207, 0.3);
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.stat-card {
  background: rgba(15, 15, 25, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 1.5rem;
  border-radius: 16px;
  border-left: 4px solid #e53212;
  transition: all 0.3s;
}

.stat-card:hover {
  border-color: rgba(0, 142, 207, 0.3);
  box-shadow: 0 8px 32px rgba(0, 142, 207, 0.15);
}

.stat-card.success {
  border-left-color: #10B981;
}

.stat-value {
  font-family: 'Orbitron', monospace;
  font-size: 2rem;
  font-weight: 700;
  color: #F29400;
  text-shadow: 0 0 15px rgba(242, 148, 0, 0.3);
}

.stat-label {
  font-family: 'Rajdhani', sans-serif;
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.6);
  margin-top: 0.5rem;
}

.disconnections-table {
  background: rgba(15, 15, 25, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  overflow: hidden;
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  background: rgba(0, 142, 207, 0.1);
}

th {
  padding: 1rem;
  text-align: left;
  font-family: 'Orbitron', monospace;
  font-weight: 600;
  color: #008ecf;
  border-bottom: 1px solid rgba(0, 142, 207, 0.2);
  text-transform: uppercase;
  font-size: 0.75rem;
  letter-spacing: 0.1em;
}

td {
  padding: 1rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  color: rgba(255, 255, 255, 0.9);
}

tr.inactive {
  opacity: 0.6;
}

tr:hover {
  background: rgba(0, 142, 207, 0.05);
}

.user-info {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.user-name {
  font-weight: 600;
  color: rgba(255, 255, 255, 0.95);
}

.user-username {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.5);
}

.reason-badge {
  display: inline-block;
  padding: 0.35rem 0.75rem;
  border-radius: 12px;
  font-size: 0.85rem;
  font-weight: 600;
  background: rgba(229, 50, 18, 0.8);
  color: white;
}

.reason-quota_exceeded {
  background: rgba(229, 50, 18, 0.8);
}

.reason-daily_limit,
.reason-weekly_limit,
.reason-monthly_limit {
  background: rgba(242, 148, 0, 0.8);
}

.reason-validity_expired {
  background: rgba(99, 99, 98, 0.8);
}

.details {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.7);
}

.quota-details {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.5);
  margin-top: 0.25rem;
}

.date-info {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.7);
}

.status-badge {
  display: inline-block;
  padding: 0.35rem 0.75rem;
  border-radius: 12px;
  font-size: 0.85rem;
  font-weight: 600;
}

.status-badge.active {
  background: rgba(229, 50, 18, 0.2);
  color: #e53212;
}

.status-badge.reconnected {
  background: rgba(16, 185, 129, 0.2);
  color: #10B981;
}

.reconnected-info {
  font-size: 0.75rem;
  margin-top: 0.25rem;
  opacity: 0.8;
  color: rgba(255, 255, 255, 0.5);
}

.btn-reactivate {
  padding: 0.5rem 1rem;
  background: linear-gradient(135deg, #10B981 0%, #059669 100%);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-family: 'Rajdhani', sans-serif;
  font-weight: 600;
  transition: all 0.3s;
}

.btn-reactivate:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);
}

.btn-reactivate:disabled {
  background: rgba(99, 99, 98, 0.5);
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.already-reconnected {
  color: rgba(255, 255, 255, 0.3);
}

.empty-state {
  padding: 4rem 2rem;
  text-align: center;
  color: rgba(255, 255, 255, 0.4);
}

.empty-state svg {
  margin-bottom: 1rem;
  color: rgba(255, 255, 255, 0.2);
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
  background: rgba(15, 15, 25, 0.8);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  cursor: pointer;
  font-family: 'Rajdhani', sans-serif;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.7);
  transition: all 0.3s;
}

.btn-page:hover:not(:disabled) {
  background: rgba(0, 142, 207, 0.2);
  border-color: #008ecf;
  color: #008ecf;
}

.btn-page:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  font-family: 'Rajdhani', sans-serif;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.7);
}
</style>
