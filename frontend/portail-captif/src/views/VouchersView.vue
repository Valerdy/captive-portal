<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useVoucherStore } from '@/stores/voucher'
import { useAuthStore } from '@/stores/auth'
import { useNotificationStore } from '@/stores/notification'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import ErrorAlert from '@/components/ErrorAlert.vue'
import DataTable from '@/components/DataTable.vue'

const router = useRouter()
const voucherStore = useVoucherStore()
const authStore = useAuthStore()
const notificationStore = useNotificationStore()

const voucherCode = ref('')
const validationResult = ref<any>(null)
const viewMode = ref<'validate' | 'history'>('validate')

const isAuthenticatedContext = computed(() => authStore.isAuthenticated)

const historyColumns = [
  { key: 'code', label: 'Code', sortable: true },
  { key: 'status', label: 'Statut', sortable: true },
  {
    key: 'duration',
    label: 'Durée',
    sortable: true,
    formatter: (value: number) => formatDuration(value)
  },
  {
    key: 'used_at',
    label: 'Utilisé le',
    sortable: true,
    formatter: (value: string | null) => value ? formatDate(value) : '-'
  },
  {
    key: 'valid_until',
    label: 'Valide jusqu\'au',
    sortable: true,
    formatter: (value: string) => formatDate(value)
  }
]

function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  if (hours > 0) return `${hours}h ${minutes}min`
  if (minutes > 0) return `${minutes} minutes`
  return `${seconds} secondes`
}

function formatDate(value: string): string {
  return new Date(value).toLocaleDateString('fr-FR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}

function formatStatus(value: string): string {
  const statusMap: Record<string, string> = {
    active: 'Actif',
    used: 'Utilisé',
    expired: 'Expiré',
    revoked: 'Révoqué'
  }
  return statusMap[value] || value
}

async function handleValidate() {
  if (!voucherCode.value.trim()) {
    notificationStore.warning('Veuillez entrer un code voucher')
    return
  }

  validationResult.value = null
  try {
    const result = await voucherStore.validateVoucher(voucherCode.value)
    validationResult.value = result

    if (result.valid) {
      notificationStore.success('Code voucher valide !')
    } else {
      notificationStore.error('Code voucher invalide ou expiré')
    }
  } catch (error) {
    notificationStore.error('Erreur lors de la validation du voucher')
  }
}

async function handleRedeem() {
  if (!isAuthenticatedContext.value) {
    notificationStore.warning('Vous devez être connecté pour utiliser un voucher')
    router.push('/login')
    return
  }

  try {
    const result = await voucherStore.redeemVoucher(voucherCode.value)
    notificationStore.success(`Voucher utilisé avec succès ! Durée: ${formatDuration(result.duration)}`)
    voucherCode.value = ''
    validationResult.value = null

    // Refresh history if in authenticated mode
    if (isAuthenticatedContext.value) {
      await voucherStore.fetchVoucherHistory()
    }
  } catch (error) {
    notificationStore.error('Erreur lors de l\'utilisation du voucher')
  }
}

function handleClear() {
  voucherCode.value = ''
  validationResult.value = null
  voucherStore.error = null
}

async function handleLogout() {
  await authStore.logout()
  router.push('/login')
}

onMounted(() => {
  if (isAuthenticatedContext.value) {
    voucherStore.fetchVoucherHistory()
  }
})
</script>

<template>
  <!-- Standalone Voucher Entry (Guest Mode) -->
  <div v-if="!isAuthenticatedContext" class="voucher-container">
    <div class="voucher-card">
      <div class="voucher-header">
        <div class="logo-badge">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M21 10H3M21 6H3M21 14H3M21 18H3" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </div>
        <h1>Codes Voucher</h1>
        <p class="subtitle">Entrez votre code d'accès invité</p>
      </div>

      <div class="form-section">
        <div class="form-group">
          <label for="code">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <rect x="3" y="7" width="18" height="13" rx="2" stroke="currentColor" stroke-width="2"/>
              <path d="M8 7V5a4 4 0 0 1 8 0v2" stroke="currentColor" stroke-width="2"/>
            </svg>
            Code Voucher
          </label>
          <input
            id="code"
            v-model="voucherCode"
            type="text"
            placeholder="Ex: WELCOME2024"
            @keyup.enter="handleValidate"
            :disabled="voucherStore.isLoading"
          />
        </div>

        <div class="button-group">
          <button
            @click="handleValidate"
            :disabled="!voucherCode || voucherStore.isLoading"
            class="btn-secondary"
          >
            <LoadingSpinner v-if="voucherStore.isLoading" size="small" color="currentColor" />
            <span v-else>Valider</span>
          </button>
          <button
            @click="handleRedeem"
            :disabled="!validationResult?.valid || voucherStore.isLoading"
            class="btn-primary"
          >
            <LoadingSpinner v-if="voucherStore.isLoading" size="small" color="white" />
            <span v-else>Utiliser</span>
          </button>
        </div>

        <button
          v-if="voucherCode || validationResult"
          @click="handleClear"
          class="btn-clear"
        >
          Effacer
        </button>

        <ErrorAlert
          v-if="voucherStore.error"
          :message="voucherStore.error"
          dismissible
          @dismiss="voucherStore.error = null"
        />

        <div v-if="validationResult" class="validation-result">
          <div v-if="validationResult.valid" class="valid">
            <div class="result-header">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                <path d="M9 12l2 2 4-4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
              <h3>Voucher Valide</h3>
            </div>
            <div class="voucher-details">
              <div class="detail-item">
                <span class="label">Code</span>
                <span class="value">{{ validationResult.voucher.code }}</span>
              </div>
              <div class="detail-item">
                <span class="label">Durée</span>
                <span class="value">{{ formatDuration(validationResult.voucher.duration) }}</span>
              </div>
              <div class="detail-item">
                <span class="label">Appareils max</span>
                <span class="value">{{ validationResult.voucher.max_devices }}</span>
              </div>
              <div class="detail-item">
                <span class="label">Utilisations</span>
                <span class="value">
                  {{ validationResult.voucher.used_count }} / {{ validationResult.voucher.max_devices }}
                </span>
              </div>
              <div class="detail-item">
                <span class="label">Valide jusqu'au</span>
                <span class="value">
                  {{ new Date(validationResult.voucher.valid_until).toLocaleDateString('fr-FR') }}
                </span>
              </div>
            </div>
          </div>
          <div v-else class="invalid">
            <div class="result-header">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                <path d="M15 9l-6 6M9 9l6 6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
              <h3>Voucher Invalide</h3>
            </div>
            <p>Ce code n'est pas valide ou a expiré</p>
          </div>
        </div>
      </div>

      <div class="footer">
        <router-link to="/login">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4M10 17l5-5-5-5M15 12H3" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
          Se connecter avec un compte
        </router-link>
        <router-link to="/">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" stroke="currentColor" stroke-width="2"/>
            <path d="M9 22V12h6v10" stroke="currentColor" stroke-width="2"/>
          </svg>
          Retour à l'accueil
        </router-link>
      </div>
    </div>
  </div>

  <!-- Authenticated Dashboard Mode -->
  <div v-else class="vouchers-page">
    <!-- Header UCAC-ICAM -->
    <header class="dashboard-header">
      <div class="header-brand">
        <div class="logo-small">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M2 17L12 22L22 17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M2 12L12 17L22 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
        <div class="brand-text">
          <h1>UCAC-ICAM</h1>
          <p>Portail Captif</p>
        </div>
      </div>
      <div class="user-info">
        <div class="user-avatar">
          {{ (authStore.user?.first_name || authStore.user?.username || 'U').charAt(0).toUpperCase() }}
        </div>
        <span class="user-name">{{ authStore.user?.first_name || authStore.user?.username }}</span>
        <button @click="handleLogout" class="btn-logout">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          Déconnexion
        </button>
      </div>
    </header>

    <!-- Navigation -->
    <nav class="nav-menu">
      <router-link to="/dashboard" class="nav-item">
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M9 22V12h6v10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        Tableau de bord
      </router-link>
      <router-link to="/sessions" class="nav-item">
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
          <path d="M12 6v6l4 2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
        Sessions
      </router-link>
      <router-link to="/devices" class="nav-item">
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <rect x="2" y="3" width="20" height="14" rx="2" stroke="currentColor" stroke-width="2"/>
          <path d="M8 21h8M12 17v4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
        Appareils
      </router-link>
      <router-link to="/vouchers" class="nav-item">
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M21 10H3M21 6H3M21 14H3M21 18H3" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
        Vouchers
      </router-link>
      <router-link to="/profile" class="nav-item">
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2"/>
          <circle cx="12" cy="7" r="4" stroke="currentColor" stroke-width="2"/>
        </svg>
        Profil
      </router-link>
    </nav>

    <!-- Main Content -->
    <main class="page-content">
      <h2>
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M21 10H3M21 6H3M21 14H3M21 18H3" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
        Mes Vouchers
      </h2>

      <!-- View Mode Toggle -->
      <div class="view-tabs">
        <button
          @click="viewMode = 'validate'"
          :class="['view-tab', { active: viewMode === 'validate' }]"
        >
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 5v14M5 12l7 7 7-7" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
          Utiliser un voucher
        </button>
        <button
          @click="viewMode = 'history'"
          :class="['view-tab', { active: viewMode === 'history' }]"
        >
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
            <path d="M12 6v6l4 2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
          Historique
        </button>
      </div>

      <!-- Validate View -->
      <div v-if="viewMode === 'validate'" class="validate-section">
        <div class="validate-card">
          <h3>Entrer un code voucher</h3>
          <p class="description">Saisissez votre code d'accès invité pour l'activer</p>

          <div class="form-group">
            <label for="code-auth">Code Voucher</label>
            <input
              id="code-auth"
              v-model="voucherCode"
              type="text"
              placeholder="Ex: WELCOME2024"
              @keyup.enter="handleValidate"
              :disabled="voucherStore.isLoading"
            />
          </div>

          <div class="button-group">
            <button
              @click="handleValidate"
              :disabled="!voucherCode || voucherStore.isLoading"
              class="btn-secondary"
            >
              <LoadingSpinner v-if="voucherStore.isLoading" size="small" color="currentColor" />
              <span v-else>Valider</span>
            </button>
            <button
              @click="handleRedeem"
              :disabled="!validationResult?.valid || voucherStore.isLoading"
              class="btn-primary"
            >
              <LoadingSpinner v-if="voucherStore.isLoading" size="small" color="white" />
              <span v-else>Utiliser</span>
            </button>
          </div>

          <ErrorAlert
            v-if="voucherStore.error"
            :message="voucherStore.error"
            dismissible
            @dismiss="voucherStore.error = null"
          />

          <div v-if="validationResult" class="validation-result">
            <div v-if="validationResult.valid" class="valid">
              <div class="result-header">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                  <path d="M9 12l2 2 4-4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                </svg>
                <h4>Voucher Valide</h4>
              </div>
              <div class="voucher-details">
                <div class="detail-item">
                  <span class="label">Code</span>
                  <span class="value">{{ validationResult.voucher.code }}</span>
                </div>
                <div class="detail-item">
                  <span class="label">Durée</span>
                  <span class="value">{{ formatDuration(validationResult.voucher.duration) }}</span>
                </div>
                <div class="detail-item">
                  <span class="label">Utilisations</span>
                  <span class="value">
                    {{ validationResult.voucher.used_count }} / {{ validationResult.voucher.max_devices }}
                  </span>
                </div>
              </div>
            </div>
            <div v-else class="invalid">
              <div class="result-header">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                  <path d="M15 9l-6 6M9 9l6 6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                </svg>
                <h4>Voucher Invalide</h4>
              </div>
              <p>Ce code n'est pas valide ou a expiré</p>
            </div>
          </div>
        </div>
      </div>

      <!-- History View -->
      <div v-else-if="viewMode === 'history'">
        <DataTable
          :columns="historyColumns"
          :data="voucherStore.voucherHistory"
          :loading="voucherStore.isLoading"
          export-filename="voucher-history-ucac-icam"
        >
          <!-- Custom Status Cell -->
          <template #cell-status="{ value }">
            <span :class="['badge', value]">
              {{ formatStatus(value) }}
            </span>
          </template>
        </DataTable>
      </div>
    </main>
  </div>
</template>

<style scoped>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

/* ========== Standalone Mode (Guest) ========== */
.voucher-container {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #dc2626 0%, #f97316 50%, #ff6b35 100%);
  padding: 1rem;
  animation: gradientShift 15s ease infinite;
  background-size: 200% 200%;
}

@keyframes gradientShift {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}

.voucher-card {
  background: white;
  padding: 2.5rem;
  border-radius: 24px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  width: 100%;
  max-width: 540px;
  animation: fadeInUp 0.6s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.voucher-header {
  text-align: center;
  margin-bottom: 2rem;
}

.logo-badge {
  width: 80px;
  height: 80px;
  margin: 0 auto 1rem;
  background: linear-gradient(135deg, #dc2626 0%, #f97316 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 24px rgba(220, 38, 38, 0.4);
}

.logo-badge svg {
  width: 40px;
  height: 40px;
  color: white;
}

.voucher-header h1 {
  color: #111827;
  font-size: 2rem;
  margin-bottom: 0.5rem;
  font-weight: 800;
}

.subtitle {
  color: #6b7280;
  font-size: 1rem;
}

.form-section {
  margin-bottom: 2rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.625rem;
  color: #111827;
  font-weight: 600;
  font-size: 0.95rem;
}

label svg {
  width: 18px;
  height: 18px;
  color: #f97316;
}

input {
  width: 100%;
  padding: 1rem 1.25rem;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  font-size: 1.1rem;
  text-transform: uppercase;
  letter-spacing: 2px;
  font-weight: 600;
  transition: all 0.3s ease;
  background: #f9fafb;
  text-align: center;
}

input:focus {
  outline: none;
  border-color: #f97316;
  background: white;
  box-shadow: 0 0 0 4px rgba(249, 115, 22, 0.1);
}

input::placeholder {
  text-transform: none;
  letter-spacing: normal;
  font-weight: normal;
  color: #9ca3af;
}

input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.button-group {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-bottom: 1rem;
}

.btn-primary,
.btn-secondary,
.btn-clear {
  padding: 1rem;
  border: none;
  border-radius: 12px;
  font-size: 1rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.btn-primary {
  background: linear-gradient(135deg, #dc2626 0%, #f97316 100%);
  color: white;
  box-shadow: 0 4px 15px rgba(220, 38, 38, 0.3);
}

.btn-secondary {
  background: white;
  color: #f97316;
  border: 2px solid #f97316;
}

.btn-clear {
  background: #f3f4f6;
  color: #6b7280;
  font-weight: 600;
  font-size: 0.9rem;
  padding: 0.75rem;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(220, 38, 38, 0.4);
}

.btn-secondary:hover:not(:disabled) {
  background: #f97316;
  color: white;
  transform: translateY(-2px);
}

.btn-clear:hover {
  background: #e5e7eb;
  color: #374151;
}

.btn-primary:disabled,
.btn-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.validation-result {
  margin-top: 1.5rem;
  padding: 1.75rem;
  border-radius: 16px;
  border: 2px solid;
}

.valid {
  background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
  border-color: #10b981;
}

.invalid {
  background: linear-gradient(135deg, #fef2f2 0%, #fecaca 100%);
  border-color: #dc2626;
}

.result-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1.25rem;
}

.result-header svg {
  width: 32px;
  height: 32px;
}

.valid .result-header svg {
  color: #10b981;
}

.invalid .result-header svg {
  color: #dc2626;
}

.valid h3,
.valid h4 {
  color: #065f46;
  font-size: 1.25rem;
  font-weight: 700;
  margin: 0;
}

.invalid h3,
.invalid h4 {
  color: #991b1b;
  font-size: 1.25rem;
  font-weight: 700;
  margin: 0;
}

.invalid p {
  color: #7f1d1d;
  margin: 0.5rem 0 0 0;
  font-size: 0.95rem;
}

.voucher-details {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: white;
  border-radius: 8px;
  border: 1px solid rgba(0, 0, 0, 0.05);
}

.detail-item .label {
  color: #6b7280;
  font-weight: 600;
  font-size: 0.9rem;
}

.detail-item .value {
  color: #111827;
  font-weight: 700;
  font-size: 0.95rem;
}

.footer {
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 2px solid #e5e7eb;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.footer a {
  color: #f97316;
  text-decoration: none;
  font-weight: 600;
  transition: all 0.3s ease;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.75rem;
  border-radius: 10px;
}

.footer a svg {
  width: 18px;
  height: 18px;
}

.footer a:hover {
  background: #fff7ed;
  color: #dc2626;
  transform: translateX(4px);
}

/* ========== Dashboard Mode (Authenticated) ========== */
.vouchers-page {
  min-height: 100vh;
  background: #f5f7fa;
}

/* Header UCAC-ICAM */
.dashboard-header {
  background: linear-gradient(135deg, #dc2626 0%, #f97316 100%);
  color: white;
  padding: 1.5rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 4px 12px rgba(220, 38, 38, 0.2);
}

.header-brand {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.logo-small {
  width: 50px;
  height: 50px;
  background: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo-small svg {
  width: 26px;
  height: 26px;
  color: #dc2626;
}

.brand-text h1 {
  font-size: 1.5rem;
  font-weight: 800;
  letter-spacing: 1px;
}

.brand-text p {
  font-size: 0.875rem;
  opacity: 0.95;
  font-weight: 300;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.user-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.25);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 1.1rem;
}

.user-name {
  font-weight: 500;
}

.btn-logout {
  background: rgba(255, 255, 255, 0.2);
  border: 1.5px solid rgba(255, 255, 255, 0.5);
  color: white;
  padding: 0.625rem 1.25rem;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
  font-size: 0.9rem;
}

.btn-logout svg {
  width: 18px;
  height: 18px;
}

.btn-logout:hover {
  background: rgba(255, 255, 255, 0.3);
  border-color: white;
  transform: translateY(-1px);
}

/* Navigation */
.nav-menu {
  background: white;
  padding: 0 2rem;
  border-bottom: 2px solid #f0f0f0;
  display: flex;
  gap: 0.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  overflow-x: auto;
}

.nav-item {
  padding: 1rem 1.25rem;
  text-decoration: none;
  color: #666;
  border-bottom: 3px solid transparent;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 500;
  white-space: nowrap;
}

.nav-item svg {
  width: 18px;
  height: 18px;
}

.nav-item:hover {
  color: #f97316;
  background: #fff8f5;
}

.nav-item.router-link-active {
  color: #dc2626;
  border-bottom-color: #dc2626;
  background: #fff5f5;
}

/* Main Content */
.page-content {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.page-content h2 {
  margin-bottom: 2rem;
  color: #111827;
  font-size: 1.75rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.page-content h2 svg {
  width: 32px;
  height: 32px;
  color: #f97316;
}

/* View Tabs */
.view-tabs {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 2rem;
  flex-wrap: wrap;
}

.view-tab {
  padding: 0.75rem 1.5rem;
  background: white;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.95rem;
  color: #6b7280;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.view-tab svg {
  width: 18px;
  height: 18px;
}

.view-tab:hover {
  border-color: #f97316;
  color: #f97316;
  transform: translateY(-2px);
}

.view-tab.active {
  background: linear-gradient(135deg, #dc2626 0%, #f97316 100%);
  border-color: #dc2626;
  color: white;
  box-shadow: 0 4px 12px rgba(220, 38, 38, 0.3);
}

.view-tab.active svg {
  color: white;
}

/* Validate Section */
.validate-section {
  display: flex;
  justify-content: center;
}

.validate-card {
  background: white;
  padding: 2.5rem;
  border-radius: 20px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  width: 100%;
  max-width: 600px;
}

.validate-card h3 {
  color: #111827;
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
}

.description {
  color: #6b7280;
  margin-bottom: 2rem;
  font-size: 0.95rem;
}

/* Badges */
.badge {
  padding: 0.375rem 0.875rem;
  border-radius: 16px;
  font-size: 0.875rem;
  font-weight: 600;
  display: inline-block;
}

.badge.active {
  background: linear-gradient(135deg, #10b981 0%, #34d399 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.3);
}

.badge.used {
  background: linear-gradient(135deg, #6b7280 0%, #9ca3af 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(107, 114, 128, 0.3);
}

.badge.expired {
  background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(220, 38, 38, 0.3);
}

.badge.revoked {
  background: linear-gradient(135deg, #374151 0%, #4b5563 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(55, 65, 81, 0.3);
}

/* Responsive */
@media (max-width: 768px) {
  .dashboard-header {
    padding: 1rem;
  }

  .brand-text h1 {
    font-size: 1.25rem;
  }

  .brand-text p {
    font-size: 0.75rem;
  }

  .user-name {
    display: none;
  }

  .nav-menu {
    padding: 0 1rem;
  }

  .nav-item {
    padding: 0.875rem 1rem;
    font-size: 0.875rem;
  }

  .page-content {
    padding: 1rem;
  }

  .page-content h2 {
    font-size: 1.5rem;
  }
}

@media (max-width: 640px) {
  .voucher-card,
  .validate-card {
    padding: 2rem 1.5rem;
  }

  .button-group {
    grid-template-columns: 1fr;
  }

  .voucher-header h1 {
    font-size: 1.75rem;
  }

  .view-tabs {
    gap: 0.5rem;
  }

  .view-tab {
    padding: 0.625rem 1rem;
    font-size: 0.875rem;
  }
}

@media (max-width: 480px) {
  .logo-small {
    width: 40px;
    height: 40px;
  }

  .logo-small svg {
    width: 20px;
    height: 20px;
  }

  .btn-logout span {
    display: none;
  }

  .page-content h2 {
    font-size: 1.25rem;
  }

  .page-content h2 svg {
    width: 28px;
    height: 28px;
  }
}
</style>
