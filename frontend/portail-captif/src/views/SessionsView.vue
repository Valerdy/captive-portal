<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useSessionStore } from '@/stores/session'

const sessionStore = useSessionStore()

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

async function handleTerminate(sessionId: number) {
  if (confirm('Voulez-vous vraiment terminer cette session ?')) {
    await sessionStore.terminateSession(sessionId)
  }
}

onMounted(() => {
  sessionStore.fetchSessions()
})
</script>

<template>
  <div class="page">
    <h2>Mes Sessions</h2>

    <div v-if="sessionStore.isLoading" class="loading">Chargement...</div>

    <div v-else-if="sessionStore.sessions.length > 0" class="table-container">
      <table>
        <thead>
          <tr>
            <th>Adresse IP</th>
            <th>MAC Address</th>
            <th>Début</th>
            <th>Fin</th>
            <th>Données</th>
            <th>Statut</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="session in sessionStore.sessions" :key="session.id">
            <td>{{ session.ip_address }}</td>
            <td>{{ session.mac_address }}</td>
            <td>{{ new Date(session.start_time).toLocaleString() }}</td>
            <td>{{ session.end_time ? new Date(session.end_time).toLocaleString() : '-' }}</td>
            <td>{{ formatBytes(session.total_bytes) }}</td>
            <td>
              <span :class="['badge', session.status]">{{ session.status }}</span>
            </td>
            <td>
              <button
                v-if="session.status === 'active'"
                @click="handleTerminate(session.id)"
                class="btn-danger"
              >
                Terminer
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <p v-else class="no-data">Aucune session trouvée</p>
  </div>
</template>

<style scoped>
.page {
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
}

h2 {
  margin-bottom: 2rem;
  color: #333;
}

.loading {
  text-align: center;
  padding: 3rem;
  color: #666;
}

.table-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  background: #f8f8f8;
}

th,
td {
  padding: 1rem;
  text-align: left;
  border-bottom: 1px solid #e0e0e0;
}

th {
  font-weight: 600;
  color: #666;
}

.badge {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.875rem;
  font-weight: 500;
}

.badge.active {
  background: #e8f5e9;
  color: #4caf50;
}

.badge.expired {
  background: #fff3e0;
  color: #f57c00;
}

.badge.terminated {
  background: #fce4ec;
  color: #e91e63;
}

.btn-danger {
  background: #f44336;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.875rem;
}

.btn-danger:hover {
  background: #d32f2f;
}

.no-data {
  text-align: center;
  padding: 3rem;
  color: #999;
}
</style>
