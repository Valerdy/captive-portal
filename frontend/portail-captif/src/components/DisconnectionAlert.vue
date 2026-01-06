<template>
  <div v-if="disconnectionStatus.is_disconnected" class="disconnection-alert">
    <!-- Background effects -->
    <div class="alert-bg">
      <div class="alert-glow"></div>
      <div class="alert-grid"></div>
    </div>

    <div class="alert-content">
      <div class="alert-header">
        <div class="alert-icon">
          <div class="icon-ring"></div>
          <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="8" x2="12" y2="12"></line>
            <line x1="12" y1="16" x2="12.01" y2="16"></line>
          </svg>
        </div>
        <div class="alert-title-section">
          <h3>Accès suspendu</h3>
          <span class="alert-badge">{{ disconnectionStatus.reason_display }}</span>
        </div>
      </div>

      <p class="description">{{ disconnectionStatus.description }}</p>

      <div v-if="disconnectionStatus.quota_used_gb" class="quota-info">
        <div class="quota-header">
          <span class="quota-label">Utilisation du quota</span>
          <span class="quota-value">{{ usagePercent.toFixed(1) }}%</span>
        </div>
        <div class="quota-bar">
          <div class="quota-used" :style="{ width: usagePercent + '%' }">
            <div class="quota-glow"></div>
          </div>
        </div>
        <p class="quota-text">
          <span class="used">{{ disconnectionStatus.quota_used_gb }} Go</span>
          <span class="separator">/</span>
          <span class="limit">{{ disconnectionStatus.quota_limit_gb }} Go</span>
        </p>
      </div>

      <div class="alert-footer">
        <div class="disconnected-time">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
            <path d="M12 6v6l4 2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
          <span>Déconnecté le {{ formatDate(disconnectionStatus.disconnected_at) }}</span>
        </div>
        <div class="contact-info">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span>Pour réactiver votre accès, veuillez contacter l'administrateur réseau.</span>
        </div>
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
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800&family=Rajdhani:wght@400;500;600;700&family=Inter:wght@400;500;600;700&display=swap');

.disconnection-alert {
  background: rgba(15, 15, 25, 0.9);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(229, 50, 18, 0.3);
  border-radius: 20px;
  padding: 2rem;
  margin: 2rem 0;
  position: relative;
  overflow: hidden;
  box-shadow:
    0 20px 60px rgba(0, 0, 0, 0.4),
    0 0 40px rgba(229, 50, 18, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
}

.alert-bg {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
}

.alert-glow {
  position: absolute;
  top: -100px;
  right: -100px;
  width: 300px;
  height: 300px;
  background: radial-gradient(circle, rgba(229, 50, 18, 0.2) 0%, transparent 70%);
}

.alert-grid {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image:
    linear-gradient(rgba(229, 50, 18, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(229, 50, 18, 0.03) 1px, transparent 1px);
  background-size: 30px 30px;
}

.alert-content {
  position: relative;
  z-index: 1;
}

.alert-header {
  display: flex;
  align-items: flex-start;
  gap: 1.25rem;
  margin-bottom: 1.5rem;
}

.alert-icon {
  position: relative;
  width: 56px;
  height: 56px;
  background: linear-gradient(135deg, #e53212 0%, #dc2626 100%);
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
  box-shadow: 0 0 25px rgba(229, 50, 18, 0.4);
}

.icon-ring {
  position: absolute;
  top: -4px;
  left: -4px;
  right: -4px;
  bottom: -4px;
  border: 2px solid rgba(229, 50, 18, 0.3);
  border-radius: 18px;
  animation: pulse-ring 2s ease-in-out infinite;
}

@keyframes pulse-ring {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(1.05); }
}

.alert-title-section {
  flex: 1;
}

.alert-title-section h3 {
  font-family: 'Orbitron', sans-serif;
  font-size: 1.5rem;
  font-weight: 700;
  color: #ffffff;
  margin: 0 0 0.5rem 0;
  letter-spacing: 0.02em;
  text-shadow: 0 0 20px rgba(229, 50, 18, 0.3);
}

.alert-badge {
  display: inline-block;
  font-family: 'Rajdhani', sans-serif;
  font-size: 0.75rem;
  font-weight: 600;
  color: #e53212;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  padding: 0.35rem 0.75rem;
  background: rgba(229, 50, 18, 0.15);
  border: 1px solid rgba(229, 50, 18, 0.3);
  border-radius: 6px;
}

.description {
  font-family: 'Inter', sans-serif;
  font-size: 1rem;
  color: rgba(255, 255, 255, 0.7);
  line-height: 1.6;
  margin: 0 0 1.5rem 0;
}

.quota-info {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 1.25rem;
  margin-bottom: 1.5rem;
}

.quota-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.quota-label {
  font-family: 'Rajdhani', sans-serif;
  font-size: 0.8rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.5);
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.quota-value {
  font-family: 'Orbitron', sans-serif;
  font-size: 1rem;
  font-weight: 700;
  color: #e53212;
}

.quota-bar {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  height: 12px;
  overflow: hidden;
  margin-bottom: 0.75rem;
}

.quota-used {
  background: linear-gradient(90deg, #e53212 0%, #F29400 100%);
  height: 100%;
  border-radius: 10px;
  position: relative;
  transition: width 0.5s ease;
}

.quota-glow {
  position: absolute;
  top: 0;
  right: 0;
  width: 20px;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4));
  animation: shimmer 1.5s ease-in-out infinite;
}

@keyframes shimmer {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 1; }
}

.quota-text {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 0.5rem;
  margin: 0;
  font-family: 'Inter', sans-serif;
}

.quota-text .used {
  font-size: 1.1rem;
  font-weight: 700;
  color: #e53212;
}

.quota-text .separator {
  color: rgba(255, 255, 255, 0.3);
}

.quota-text .limit {
  font-size: 1rem;
  color: rgba(255, 255, 255, 0.6);
}

.alert-footer {
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  padding-top: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.disconnected-time,
.contact-info {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  font-family: 'Inter', sans-serif;
}

.disconnected-time svg,
.contact-info svg {
  width: 18px;
  height: 18px;
  color: rgba(255, 255, 255, 0.4);
  flex-shrink: 0;
  margin-top: 2px;
}

.disconnected-time span {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.5);
}

.contact-info {
  background: rgba(0, 142, 207, 0.1);
  border: 1px solid rgba(0, 142, 207, 0.2);
  border-radius: 10px;
  padding: 1rem;
}

.contact-info svg {
  color: #008ecf;
}

.contact-info span {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.8);
  line-height: 1.5;
}

@media (max-width: 768px) {
  .disconnection-alert {
    padding: 1.5rem;
  }

  .alert-header {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }

  .alert-title-section h3 {
    font-size: 1.25rem;
  }

  .description {
    text-align: center;
  }
}
</style>
