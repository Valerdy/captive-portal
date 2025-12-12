<template>
  <div v-if="disconnectionStatus.is_disconnected" class="disconnection-alert">
    <div class="alert-icon">
      <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"></circle>
        <line x1="12" y1="8" x2="12" y2="12"></line>
        <line x1="12" y1="16" x2="12.01" y2="16"></line>
      </svg>
    </div>

    <div class="alert-content">
      <h3>Accès suspendu</h3>
      <p class="reason">{{ disconnectionStatus.reason_display }}</p>
      <p class="description">{{ disconnectionStatus.description }}</p>

      <div v-if="disconnectionStatus.quota_used_gb" class="quota-info">
        <div class="quota-bar">
          <div class="quota-used" :style="{ width: usagePercent + '%' }"></div>
        </div>
        <p class="quota-text">
          {{ disconnectionStatus.quota_used_gb }} Go utilisés / {{ disconnectionStatus.quota_limit_gb }} Go
        </p>
      </div>

      <div class="alert-footer">
        <p class="disconnected-time">
          Déconnecté le {{ formatDate(disconnectionStatus.disconnected_at) }}
        </p>
        <p class="contact-info">
          Pour réactiver votre accès, veuillez contacter l'administrateur réseau.
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

interface DisconnectionStatus {
  is_disconnected: boolean
  reason: string
  reason_display: string
  description: string
  disconnected_at: string
  quota_used_gb: number | null
  quota_limit_gb: number | null
}

const disconnectionStatus = ref<DisconnectionStatus>({
  is_disconnected: false,
  reason: '',
  reason_display: '',
  description: '',
  disconnected_at: '',
  quota_used_gb: null,
  quota_limit_gb: null
})

const usagePercent = computed(() => {
  if (!disconnectionStatus.value.quota_used_gb || !disconnectionStatus.value.quota_limit_gb) {
    return 0
  }
  return Math.min(
    100,
    (disconnectionStatus.value.quota_used_gb / disconnectionStatus.value.quota_limit_gb) * 100
  )
})

const checkDisconnectionStatus = async () => {
  try {
    const response = await axios.get('/api/core/disconnection-logs/current/')
    if (response.data.is_disconnected !== false) {
      disconnectionStatus.value = {
        is_disconnected: true,
        ...response.data
      }
    }
  } catch (error) {
    console.error('Erreur lors de la vérification du statut:', error)
  }
}

const formatDate = (dateString: string) => {
  if (!dateString) return ''
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
  checkDisconnectionStatus()
})
</script>

<style scoped>
.disconnection-alert {
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
  color: white;
  border-radius: 12px;
  padding: 2rem;
  margin: 2rem 0;
  box-shadow: 0 10px 40px rgba(255, 107, 107, 0.3);
  display: flex;
  gap: 1.5rem;
  align-items: flex-start;
}

.alert-icon {
  flex-shrink: 0;
}

.alert-icon svg {
  filter: drop-shadow(0 2px 8px rgba(0, 0, 0, 0.2));
}

.alert-content {
  flex: 1;
}

.alert-content h3 {
  margin: 0 0 0.5rem 0;
  font-size: 1.5rem;
  font-weight: 700;
}

.reason {
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0.5rem 0;
  opacity: 0.95;
}

.description {
  font-size: 0.95rem;
  margin: 0.5rem 0 1rem 0;
  opacity: 0.9;
  line-height: 1.5;
}

.quota-info {
  background: rgba(255, 255, 255, 0.15);
  border-radius: 8px;
  padding: 1rem;
  margin: 1rem 0;
}

.quota-bar {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 10px;
  height: 20px;
  overflow: hidden;
  margin-bottom: 0.5rem;
}

.quota-used {
  background: white;
  height: 100%;
  border-radius: 10px;
  transition: width 0.3s ease;
  box-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
}

.quota-text {
  margin: 0;
  font-size: 0.9rem;
  text-align: center;
  font-weight: 600;
}

.alert-footer {
  margin-top: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid rgba(255, 255, 255, 0.2);
}

.disconnected-time {
  font-size: 0.85rem;
  opacity: 0.8;
  margin: 0 0 0.5rem 0;
}

.contact-info {
  font-size: 0.9rem;
  font-weight: 500;
  margin: 0;
  padding: 0.75rem;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  border-left: 3px solid white;
}

@media (max-width: 768px) {
  .disconnection-alert {
    flex-direction: column;
    text-align: center;
  }

  .alert-icon {
    margin: 0 auto;
  }
}
</style>
