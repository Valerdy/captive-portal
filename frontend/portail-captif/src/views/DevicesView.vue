<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useDeviceStore } from '@/stores/device'

const deviceStore = useDeviceStore()

async function handleDeactivate(deviceId: number) {
  if (confirm('Voulez-vous vraiment désactiver cet appareil ?')) {
    await deviceStore.deactivateDevice(deviceId)
  }
}

function getDeviceIcon(type: string): string {
  const icons: Record<string, string> = {
    mobile: '📱',
    desktop: '💻',
    tablet: '📲',
    other: '🖥️'
  }
  return icons[type] || '🖥️'
}

onMounted(() => {
  deviceStore.fetchDevices()
})
</script>

<template>
  <div class="page">
    <h2>Mes Appareils</h2>

    <div v-if="deviceStore.isLoading" class="loading">Chargement...</div>

    <div v-else-if="deviceStore.devices.length > 0" class="devices-grid">
      <div v-for="device in deviceStore.devices" :key="device.id" class="device-card">
        <div class="device-icon">{{ getDeviceIcon(device.device_type) }}</div>
        <div class="device-info">
          <h3>{{ device.hostname || 'Appareil sans nom' }}</h3>
          <p class="mac-address">{{ device.mac_address }}</p>
          <p class="device-type">{{ device.device_type }}</p>
          <div class="device-dates">
            <small>Premier accès: {{ new Date(device.first_seen).toLocaleDateString() }}</small>
            <small>Dernier accès: {{ new Date(device.last_seen).toLocaleDateString() }}</small>
          </div>
        </div>
        <div class="device-status">
          <span :class="['badge', device.is_active ? 'active' : 'inactive']">
            {{ device.is_active ? 'Actif' : 'Inactif' }}
          </span>
        </div>
        <div class="device-actions">
          <button
            v-if="device.is_active"
            @click="handleDeactivate(device.id)"
            class="btn-danger"
          >
            Désactiver
          </button>
        </div>
      </div>
    </div>

    <p v-else class="no-data">Aucun appareil trouvé</p>
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

.devices-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
}

.device-card {
  background: white;
  padding: 1.5rem;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.device-icon {
  font-size: 3rem;
  text-align: center;
}

.device-info h3 {
  margin: 0 0 0.5rem 0;
  color: #333;
}

.mac-address {
  font-family: monospace;
  color: #666;
  font-size: 0.9rem;
}

.device-type {
  color: #999;
  text-transform: capitalize;
  font-size: 0.85rem;
}

.device-dates {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  margin-top: 0.5rem;
}

.device-dates small {
  color: #999;
}

.device-status {
  text-align: center;
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

.badge.inactive {
  background: #ffebee;
  color: #f44336;
}

.device-actions {
  text-align: center;
}

.btn-danger {
  background: #f44336;
  color: white;
  border: none;
  padding: 0.5rem 1.5rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.875rem;
  width: 100%;
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
