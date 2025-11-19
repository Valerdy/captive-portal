<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useSessionStore } from '@/stores/session'
import { useDeviceStore } from '@/stores/device'
import { useNotificationStore } from '@/stores/notification'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import ErrorAlert from '@/components/ErrorAlert.vue'

const router = useRouter()
const authStore = useAuthStore()
const sessionStore = useSessionStore()
const deviceStore = useDeviceStore()
const notificationStore = useNotificationStore()

const formData = ref({
  first_name: '',
  last_name: '',
  email: '',
  phone_number: ''
})

const passwordData = ref({
  current_password: '',
  new_password: '',
  confirm_password: ''
})

const showPasswordForm = ref(false)
const formErrors = ref<Record<string, string>>({})

const hasChanges = computed(() => {
  if (!authStore.user) return false
  return (
    formData.value.first_name !== (authStore.user.first_name || '') ||
    formData.value.last_name !== (authStore.user.last_name || '') ||
    formData.value.email !== (authStore.user.email || '') ||
    formData.value.phone_number !== (authStore.user.phone_number || '')
  )
})

const activeSessionsCount = computed(() => {
  return sessionStore.sessions.filter(s => s.status === 'active').length
})

const activeDevicesCount = computed(() => {
  return deviceStore.devices.filter(d => d.is_active).length
})

function validateProfileForm(): boolean {
  formErrors.value = {}

  if (!formData.value.email) {
    formErrors.value.email = 'L\'email est requis'
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.value.email)) {
    formErrors.value.email = 'Email invalide'
  }

  if (formData.value.phone_number && !/^[+]?[\d\s-()]+$/.test(formData.value.phone_number)) {
    formErrors.value.phone_number = 'Numéro de téléphone invalide'
  }

  return Object.keys(formErrors.value).length === 0
}

function validatePasswordForm(): boolean {
  formErrors.value = {}

  if (!passwordData.value.current_password) {
    formErrors.value.current_password = 'Le mot de passe actuel est requis'
  }

  if (!passwordData.value.new_password) {
    formErrors.value.new_password = 'Le nouveau mot de passe est requis'
  } else if (passwordData.value.new_password.length < 8) {
    formErrors.value.new_password = 'Le mot de passe doit contenir au moins 8 caractères'
  }

  if (passwordData.value.new_password !== passwordData.value.confirm_password) {
    formErrors.value.confirm_password = 'Les mots de passe ne correspondent pas'
  }

  return Object.keys(formErrors.value).length === 0
}

async function handleUpdate() {
  if (!validateProfileForm()) {
    notificationStore.error('Veuillez corriger les erreurs dans le formulaire')
    return
  }

  try {
    await authStore.updateProfile(formData.value)
    notificationStore.success('Profil mis à jour avec succès !')
  } catch (error) {
    notificationStore.error(authStore.error || 'Erreur lors de la mise à jour du profil')
  }
}

async function handlePasswordChange() {
  if (!validatePasswordForm()) {
    notificationStore.error('Veuillez corriger les erreurs dans le formulaire')
    return
  }

  try {
    await authStore.changePassword(passwordData.value)
    notificationStore.success('Mot de passe modifié avec succès !')

    // Reset password form
    passwordData.value = {
      current_password: '',
      new_password: '',
      confirm_password: ''
    }
    showPasswordForm.value = false
  } catch (error) {
    notificationStore.error(authStore.error || 'Erreur lors du changement de mot de passe')
  }
}

function handleCancel() {
  if (authStore.user) {
    formData.value = {
      first_name: authStore.user.first_name || '',
      last_name: authStore.user.last_name || '',
      email: authStore.user.email || '',
      phone_number: authStore.user.phone_number || ''
    }
  }
  formErrors.value = {}
  notificationStore.info('Modifications annulées')
}

async function handleLogout() {
  await authStore.logout()
  router.push('/login')
}

onMounted(() => {
  if (authStore.user) {
    formData.value = {
      first_name: authStore.user.first_name || '',
      last_name: authStore.user.last_name || '',
      email: authStore.user.email || '',
      phone_number: authStore.user.phone_number || ''
    }
  }

  // Load user stats
  sessionStore.fetchSessions()
  deviceStore.fetchDevices()
})
</script>

<template>
  <div class="profile-page">
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

    <!-- Contenu Principal -->
    <main class="page-content">
      <h2>
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2"/>
          <circle cx="12" cy="7" r="4" stroke="currentColor" stroke-width="2"/>
        </svg>
        Mon Profil
      </h2>

      <!-- Account Statistics -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-icon sessions">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
              <path d="M12 6v6l4 2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ activeSessionsCount }}</div>
            <div class="stat-label">Sessions actives</div>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon devices">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <rect x="2" y="3" width="20" height="14" rx="2" stroke="currentColor" stroke-width="2"/>
              <path d="M8 21h8M12 17v4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ activeDevicesCount }}</div>
            <div class="stat-label">Appareils actifs</div>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon total">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" stroke="currentColor" stroke-width="2"/>
              <path d="M9 22V12h6v10" stroke="currentColor" stroke-width="2"/>
            </svg>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ sessionStore.sessions.length }}</div>
            <div class="stat-label">Total sessions</div>
          </div>
        </div>
      </div>

      <div class="profile-container">
        <!-- Profile Header -->
        <div class="profile-header">
          <div class="avatar-large">
            {{ (authStore.user?.username || 'U').charAt(0).toUpperCase() }}
          </div>
          <div class="profile-info">
            <h3>{{ authStore.user?.username }}</h3>
            <p class="member-since">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect x="3" y="4" width="18" height="18" rx="2" stroke="currentColor" stroke-width="2"/>
                <path d="M16 2v4M8 2v4M3 10h18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
              Membre depuis {{ new Date(authStore.user?.date_joined || '').toLocaleDateString('fr-FR') }}
            </p>
            <div class="account-details">
              <div class="detail-item" v-if="authStore.user?.mac_address">
                <span class="detail-label">MAC Address:</span>
                <span class="detail-value">{{ authStore.user.mac_address }}</span>
              </div>
              <div class="detail-item" v-if="authStore.user?.ip_address">
                <span class="detail-label">Adresse IP:</span>
                <span class="detail-value">{{ authStore.user.ip_address }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Profile Form -->
        <form @submit.prevent="handleUpdate" class="profile-form">
          <h4 class="form-section-title">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" stroke="currentColor" stroke-width="2"/>
              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" stroke="currentColor" stroke-width="2"/>
            </svg>
            Informations personnelles
          </h4>

          <div class="form-row">
            <div class="form-group">
              <label for="first_name">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2"/>
                  <circle cx="12" cy="7" r="4" stroke="currentColor" stroke-width="2"/>
                </svg>
                Prénom
              </label>
              <input
                id="first_name"
                v-model="formData.first_name"
                type="text"
                placeholder="Votre prénom"
                :disabled="authStore.isLoading"
              />
            </div>

            <div class="form-group">
              <label for="last_name">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2"/>
                  <circle cx="12" cy="7" r="4" stroke="currentColor" stroke-width="2"/>
                </svg>
                Nom
              </label>
              <input
                id="last_name"
                v-model="formData.last_name"
                type="text"
                placeholder="Votre nom"
                :disabled="authStore.isLoading"
              />
            </div>
          </div>

          <div class="form-group">
            <label for="email">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" stroke="currentColor" stroke-width="2"/>
                <path d="M22 6l-10 7L2 6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
              Email *
            </label>
            <input
              id="email"
              v-model="formData.email"
              type="email"
              placeholder="votre.email@exemple.com"
              :disabled="authStore.isLoading"
              required
            />
            <span v-if="formErrors.email" class="field-error">{{ formErrors.email }}</span>
          </div>

          <div class="form-group">
            <label for="phone_number">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
              Téléphone
            </label>
            <input
              id="phone_number"
              v-model="formData.phone_number"
              type="tel"
              placeholder="+237 6XX XX XX XX"
              :disabled="authStore.isLoading"
            />
            <span v-if="formErrors.phone_number" class="field-error">{{ formErrors.phone_number }}</span>
          </div>

          <div class="form-actions">
            <button
              type="button"
              @click="handleCancel"
              class="btn-secondary"
              :disabled="!hasChanges || authStore.isLoading"
            >
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
              Annuler
            </button>

            <button
              type="submit"
              class="btn-primary"
              :disabled="!hasChanges || authStore.isLoading"
            >
              <LoadingSpinner v-if="authStore.isLoading" size="small" color="white" />
              <template v-else>
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z" stroke="currentColor" stroke-width="2"/>
                  <path d="M17 21v-8H7v8M7 3v5h8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                Enregistrer les modifications
              </template>
            </button>
          </div>
        </form>

        <!-- Password Change Section -->
        <div class="password-section">
          <button
            @click="showPasswordForm = !showPasswordForm"
            class="password-toggle"
          >
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <rect x="3" y="11" width="18" height="11" rx="2" stroke="currentColor" stroke-width="2"/>
              <path d="M7 11V7a5 5 0 0 1 10 0v4" stroke="currentColor" stroke-width="2"/>
            </svg>
            {{ showPasswordForm ? 'Masquer' : 'Modifier le mot de passe' }}
            <svg
              :class="['chevron', { open: showPasswordForm }]"
              viewBox="0 0 24 24"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path d="M6 9l6 6 6-6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </button>

          <Transition name="expand">
            <form v-if="showPasswordForm" @submit.prevent="handlePasswordChange" class="password-form">
              <div class="form-group">
                <label for="current_password">
                  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <rect x="3" y="11" width="18" height="11" rx="2" stroke="currentColor" stroke-width="2"/>
                    <path d="M7 11V7a5 5 0 0 1 10 0v4" stroke="currentColor" stroke-width="2"/>
                  </svg>
                  Mot de passe actuel *
                </label>
                <input
                  id="current_password"
                  v-model="passwordData.current_password"
                  type="password"
                  placeholder="Votre mot de passe actuel"
                  :disabled="authStore.isLoading"
                  required
                />
                <span v-if="formErrors.current_password" class="field-error">{{ formErrors.current_password }}</span>
              </div>

              <div class="form-group">
                <label for="new_password">
                  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <rect x="3" y="11" width="18" height="11" rx="2" stroke="currentColor" stroke-width="2"/>
                    <path d="M7 11V7a5 5 0 0 1 10 0v4" stroke="currentColor" stroke-width="2"/>
                  </svg>
                  Nouveau mot de passe *
                </label>
                <input
                  id="new_password"
                  v-model="passwordData.new_password"
                  type="password"
                  placeholder="Minimum 8 caractères"
                  :disabled="authStore.isLoading"
                  required
                />
                <span v-if="formErrors.new_password" class="field-error">{{ formErrors.new_password }}</span>
              </div>

              <div class="form-group">
                <label for="confirm_password">
                  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                    <path d="M22 4L12 14.01l-3-3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                  Confirmer le mot de passe *
                </label>
                <input
                  id="confirm_password"
                  v-model="passwordData.confirm_password"
                  type="password"
                  placeholder="Répétez le nouveau mot de passe"
                  :disabled="authStore.isLoading"
                  required
                />
                <span v-if="formErrors.confirm_password" class="field-error">{{ formErrors.confirm_password }}</span>
              </div>

              <button
                type="submit"
                class="btn-primary"
                :disabled="authStore.isLoading"
              >
                <LoadingSpinner v-if="authStore.isLoading" size="small" color="white" />
                <template v-else>
                  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                    <path d="M22 4L12 14.01l-3-3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                  Modifier le mot de passe
                </template>
              </button>
            </form>
          </Transition>
        </div>
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

.profile-page {
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

/* Content */
.page-content {
  padding: 2rem;
  max-width: 1000px;
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

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.stat-card {
  background: white;
  padding: 1.5rem;
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  display: flex;
  align-items: center;
  gap: 1.25rem;
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-icon svg {
  width: 28px;
  height: 28px;
  color: white;
}

.stat-icon.sessions {
  background: linear-gradient(135deg, #10b981 0%, #34d399 100%);
}

.stat-icon.devices {
  background: linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%);
}

.stat-icon.total {
  background: linear-gradient(135deg, #f59e0b 0%, #fbbf24 100%);
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 2rem;
  font-weight: 800;
  color: #111827;
  line-height: 1;
  margin-bottom: 0.25rem;
}

.stat-label {
  color: #6b7280;
  font-size: 0.875rem;
  font-weight: 500;
}

/* Profile Container */
.profile-container {
  background: white;
  padding: 2.5rem;
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.profile-header {
  display: flex;
  align-items: center;
  gap: 2rem;
  padding: 2rem;
  background: linear-gradient(135deg, #fff8f5 0%, #fff5f5 100%);
  border-radius: 12px;
  margin-bottom: 2.5rem;
  border: 2px solid #ffe8e0;
}

.avatar-large {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  background: linear-gradient(135deg, #dc2626 0%, #f97316 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 3rem;
  font-weight: 800;
  box-shadow: 0 8px 24px rgba(220, 38, 38, 0.3);
  flex-shrink: 0;
}

.profile-info {
  flex: 1;
}

.profile-info h3 {
  margin: 0 0 0.75rem 0;
  color: #111827;
  font-size: 1.75rem;
  font-weight: 700;
}

.member-since {
  margin: 0 0 1rem 0;
  color: #6b7280;
  font-size: 0.95rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.member-since svg {
  width: 18px;
  height: 18px;
  color: #f97316;
}

.account-details {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.detail-item {
  display: flex;
  gap: 0.5rem;
  font-size: 0.875rem;
}

.detail-label {
  color: #6b7280;
  font-weight: 600;
}

.detail-value {
  color: #111827;
  font-family: 'Courier New', monospace;
  font-weight: 500;
}

/* Form */
.profile-form {
  margin-bottom: 2.5rem;
}

.form-section-title {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #e5e7eb;
  color: #111827;
  font-size: 1.25rem;
  font-weight: 700;
}

.form-section-title svg {
  width: 24px;
  height: 24px;
  color: #f97316;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

.form-group {
  margin-bottom: 1.75rem;
}

label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.625rem;
  color: #374151;
  font-weight: 600;
  font-size: 0.95rem;
}

label svg {
  width: 18px;
  height: 18px;
  color: #f97316;
  flex-shrink: 0;
}

input {
  width: 100%;
  padding: 1rem;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  font-size: 1rem;
  transition: all 0.3s ease;
  background: #f9fafb;
}

input:focus {
  outline: none;
  border-color: #f97316;
  background: white;
  box-shadow: 0 0 0 4px rgba(249, 115, 22, 0.1);
}

input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

input::placeholder {
  color: #9ca3af;
}

.field-error {
  display: block;
  margin-top: 0.375rem;
  color: #dc2626;
  font-size: 0.875rem;
  font-weight: 500;
}

.form-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
}

.btn-primary,
.btn-secondary {
  padding: 1rem 2rem;
  border: none;
  border-radius: 12px;
  font-size: 1rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.625rem;
}

.btn-primary {
  background: linear-gradient(135deg, #dc2626 0%, #f97316 100%);
  color: white;
  box-shadow: 0 4px 15px rgba(220, 38, 38, 0.3);
  flex: 1;
}

.btn-secondary {
  background: white;
  color: #6b7280;
  border: 2px solid #e5e7eb;
}

.btn-primary svg,
.btn-secondary svg {
  width: 20px;
  height: 20px;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(220, 38, 38, 0.4);
}

.btn-secondary:hover:not(:disabled) {
  border-color: #f97316;
  color: #f97316;
  background: #fff7ed;
}

.btn-primary:disabled,
.btn-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

/* Password Section */
.password-section {
  border-top: 2px solid #e5e7eb;
  padding-top: 2rem;
}

.password-toggle {
  width: 100%;
  padding: 1rem 1.5rem;
  background: #f9fafb;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  color: #374151;
  font-weight: 600;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.password-toggle svg:first-child {
  width: 20px;
  height: 20px;
  color: #f97316;
}

.password-toggle .chevron {
  width: 20px;
  height: 20px;
  margin-left: auto;
  transition: transform 0.3s ease;
}

.password-toggle .chevron.open {
  transform: rotate(180deg);
}

.password-toggle:hover {
  background: white;
  border-color: #f97316;
  color: #f97316;
}

.password-form {
  margin-top: 1.5rem;
  padding: 1.5rem;
  background: #f9fafb;
  border-radius: 12px;
  border: 2px solid #e5e7eb;
}

/* Transitions */
.expand-enter-active,
.expand-leave-active {
  transition: all 0.3s ease;
  overflow: hidden;
}

.expand-enter-from,
.expand-leave-to {
  max-height: 0;
  opacity: 0;
  margin-top: 0;
  padding-top: 0;
  padding-bottom: 0;
}

.expand-enter-to,
.expand-leave-from {
  max-height: 1000px;
  opacity: 1;
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

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .profile-container {
    padding: 1.5rem;
  }

  .profile-header {
    flex-direction: column;
    text-align: center;
    padding: 1.5rem;
  }

  .form-row {
    grid-template-columns: 1fr;
  }

  .form-actions {
    flex-direction: column;
  }

  .btn-primary,
  .btn-secondary {
    width: 100%;
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

  .avatar-large {
    width: 80px;
    height: 80px;
    font-size: 2.5rem;
  }

  .profile-info h3 {
    font-size: 1.5rem;
  }
}
</style>
