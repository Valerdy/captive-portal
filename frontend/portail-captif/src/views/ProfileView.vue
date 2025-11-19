<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const formData = ref({
  first_name: '',
  last_name: '',
  email: '',
  phone_number: ''
})

const successMessage = ref('')
const errorMessage = ref('')

async function handleUpdate() {
  successMessage.value = ''
  errorMessage.value = ''

  try {
    await authStore.updateProfile(formData.value)
    successMessage.value = 'Profil mis à jour avec succès !'
  } catch (error) {
    errorMessage.value = authStore.error || 'Erreur lors de la mise à jour'
  }
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
      <router-link to="/" class="nav-item">
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

      <div class="profile-container">
        <!-- En-tête profil -->
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
              Membre depuis {{ new Date(authStore.user?.date_joined || '').toLocaleDateString() }}
            </p>
          </div>
        </div>

        <!-- Formulaire de mise à jour -->
        <form @submit.prevent="handleUpdate" class="profile-form">
          <div class="form-row">
            <div class="form-group">
              <label for="first_name">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2"/>
                  <circle cx="12" cy="7" r="4" stroke="currentColor" stroke-width="2"/>
                </svg>
                Prénom
              </label>
              <input id="first_name" v-model="formData.first_name" type="text" placeholder="Votre prénom" />
            </div>
            <div class="form-group">
              <label for="last_name">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2"/>
                  <circle cx="12" cy="7" r="4" stroke="currentColor" stroke-width="2"/>
                </svg>
                Nom
              </label>
              <input id="last_name" v-model="formData.last_name" type="text" placeholder="Votre nom" />
            </div>
          </div>

          <div class="form-group">
            <label for="email">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" stroke="currentColor" stroke-width="2"/>
                <path d="M22 6l-10 7L2 6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
              Email
            </label>
            <input id="email" v-model="formData.email" type="email" placeholder="votre.email@exemple.com" />
          </div>

          <div class="form-group">
            <label for="phone_number">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
              Téléphone
            </label>
            <input id="phone_number" v-model="formData.phone_number" type="tel" placeholder="+237 6XX XX XX XX" />
          </div>

          <div v-if="successMessage" class="success-message">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              <path d="M22 4L12 14.01l-3-3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            {{ successMessage }}
          </div>

          <div v-if="errorMessage" class="error-message">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
              <line x1="12" y1="8" x2="12" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              <line x1="12" y1="16" x2="12.01" y2="16" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
            {{ errorMessage }}
          </div>

          <button type="submit" :disabled="authStore.isLoading" class="btn-primary">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z" stroke="currentColor" stroke-width="2"/>
              <path d="M17 21v-8H7v8M7 3v5h8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            {{ authStore.isLoading ? 'Enregistrement...' : 'Enregistrer les modifications' }}
          </button>
        </form>
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

/* Header UCAC-ICAM (Réutilisé) */
.dashboard-header {
  background: linear-gradient(135deg, #c31432 0%, #e85d04 100%);
  color: white;
  padding: 1.5rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 4px 12px rgba(195, 20, 50, 0.2);
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
  color: #c31432;
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

/* Navigation (Réutilisé) */
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
  color: #e85d04;
  background: #fff8f5;
}

.nav-item.router-link-active {
  color: #c31432;
  border-bottom-color: #c31432;
  background: #fff5f5;
}

/* Contenu */
.page-content {
  padding: 2rem;
  max-width: 900px;
  margin: 0 auto;
}

.page-content h2 {
  margin-bottom: 2rem;
  color: #333;
  font-size: 1.75rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.page-content h2 svg {
  width: 32px;
  height: 32px;
  color: #e85d04;
}

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
  background: linear-gradient(135deg, #c31432 0%, #e85d04 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 3rem;
  font-weight: 800;
  box-shadow: 0 8px 24px rgba(195, 20, 50, 0.3);
  flex-shrink: 0;
}

.profile-info h3 {
  margin: 0 0 0.75rem 0;
  color: #333;
  font-size: 1.75rem;
  font-weight: 700;
}

.member-since {
  margin: 0;
  color: #666;
  font-size: 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.member-since svg {
  width: 18px;
  height: 18px;
  color: #e85d04;
}

.profile-form {
  margin-top: 2rem;
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
  color: #333;
  font-weight: 600;
  font-size: 0.95rem;
}

label svg {
  width: 18px;
  height: 18px;
  color: #e85d04;
  flex-shrink: 0;
}

input {
  width: 100%;
  padding: 1rem;
  border: 2px solid #e0e0e0;
  border-radius: 12px;
  font-size: 1rem;
  transition: all 0.3s ease;
  background: #f8f8f8;
}

input:focus {
  outline: none;
  border-color: #e85d04;
  background: white;
  box-shadow: 0 0 0 3px rgba(232, 93, 4, 0.1);
}

input::placeholder {
  color: #999;
}

.success-message {
  background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
  border: 1px solid #81c784;
  color: #2e7d32;
  padding: 1rem;
  border-radius: 12px;
  margin-bottom: 1.5rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-weight: 600;
}

.success-message svg {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

.error-message {
  background: #fff5f5;
  border: 1px solid #feb2b2;
  color: #c53030;
  padding: 1rem;
  border-radius: 12px;
  margin-bottom: 1.5rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.9rem;
}

.error-message svg {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

.btn-primary {
  width: 100%;
  padding: 1.125rem;
  background: linear-gradient(135deg, #c31432 0%, #e85d04 100%);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 1.1rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(195, 20, 50, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.625rem;
}

.btn-primary svg {
  width: 20px;
  height: 20px;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(195, 20, 50, 0.4);
}

.btn-primary:active:not(:disabled) {
  transform: translateY(0);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
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
    font-size: 1.5rem;
  }

  .page-content h2 svg {
    width: 28px;
    height: 28px;
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
