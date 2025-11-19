<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useNotificationStore } from '@/stores/notification'
import LoadingSpinner from '@/components/LoadingSpinner.vue'

const router = useRouter()
const authStore = useAuthStore()
const notificationStore = useNotificationStore()

const username = ref('')
const password = ref('')
const showPassword = ref(false)
const isLoading = ref(false)

async function handleLogin() {
  if (!username.value || !password.value) {
    notificationStore.warning('Veuillez remplir tous les champs')
    return
  }

  isLoading.value = true
  try {
    // Appel API pour connexion admin
    await authStore.adminLogin(username.value, password.value)

    // Vérifier si l'utilisateur est bien admin
    if (authStore.user?.is_staff || authStore.user?.is_superuser) {
      notificationStore.success('Connexion administrateur réussie !')
      router.push('/admin/dashboard')
    } else {
      notificationStore.error('Accès refusé : droits administrateur requis')
      await authStore.logout()
    }
  } catch (error: any) {
    notificationStore.error(error.response?.data?.detail || 'Identifiants invalides')
  } finally {
    isLoading.value = false
  }
}

function goBack() {
  router.push('/')
}
</script>

<template>
  <div class="admin-login-page">
    <!-- Fond animé -->
    <div class="animated-background">
      <div class="gradient-orb orb-1"></div>
      <div class="gradient-orb orb-2"></div>
      <div class="gradient-orb orb-3"></div>
    </div>

    <!-- Bouton retour -->
    <button @click="goBack" class="back-btn" title="Retour">
      <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M19 12H5M5 12l7 7m-7-7 7-7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
      <span>Retour</span>
    </button>

    <!-- Carte de connexion -->
    <div class="login-card">
      <!-- Badge Admin -->
      <div class="admin-badge">
        <div class="badge-icon">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z" stroke="currentColor" stroke-width="2"/>
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" stroke="currentColor" stroke-width="2"/>
          </svg>
        </div>
      </div>

      <!-- En-tête -->
      <div class="header">
        <h1>Espace Administrateur</h1>
        <p class="subtitle">UCAC-ICAM Portail Captif</p>
      </div>

      <!-- Formulaire -->
      <form @submit.prevent="handleLogin" class="form">
        <div class="form-group">
          <label for="username">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2"/>
              <circle cx="12" cy="7" r="4" stroke="currentColor" stroke-width="2"/>
            </svg>
            Nom d'utilisateur
          </label>
          <input
            id="username"
            v-model="username"
            type="text"
            placeholder="admin"
            autocomplete="username"
            :disabled="isLoading"
            required
          />
        </div>

        <div class="form-group">
          <label for="password">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2" stroke="currentColor" stroke-width="2"/>
              <path d="M7 11V7a5 5 0 0 1 10 0v4" stroke="currentColor" stroke-width="2"/>
            </svg>
            Mot de passe
          </label>
          <div class="password-input">
            <input
              id="password"
              v-model="password"
              :type="showPassword ? 'text' : 'password'"
              placeholder="••••••••"
              autocomplete="current-password"
              :disabled="isLoading"
              required
            />
            <button
              type="button"
              @click="showPassword = !showPassword"
              class="toggle-password"
              :disabled="isLoading"
              tabindex="-1"
            >
              <svg v-if="!showPassword" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" stroke="currentColor" stroke-width="2"/>
                <circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="2"/>
              </svg>
              <svg v-else viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" stroke="currentColor" stroke-width="2"/>
                <line x1="1" y1="1" x2="23" y2="23" stroke="currentColor" stroke-width="2"/>
              </svg>
            </button>
          </div>
        </div>

        <button type="submit" :disabled="isLoading" class="submit-btn">
          <LoadingSpinner v-if="isLoading" size="small" />
          <span v-else>
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4M10 17l5-5-5-5M15 12H3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            Se connecter
          </span>
        </button>
      </form>

      <!-- Footer sécurité -->
      <div class="security-notice">
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <span>Connexion sécurisée - Accès réservé aux administrateurs</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.admin-login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  position: relative;
  overflow: hidden;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
}

/* Fond animé */
.animated-background {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  overflow: hidden;
  z-index: 0;
}

.gradient-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.3;
  animation: float 20s ease-in-out infinite;
}

.orb-1 {
  width: 500px;
  height: 500px;
  background: radial-gradient(circle, #dc2626, transparent);
  top: -10%;
  left: -10%;
  animation-delay: 0s;
}

.orb-2 {
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, #f97316, transparent);
  bottom: -10%;
  right: -10%;
  animation-delay: 5s;
}

.orb-3 {
  width: 300px;
  height: 300px;
  background: radial-gradient(circle, #991b1b, transparent);
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  animation-delay: 10s;
}

@keyframes float {
  0%, 100% {
    transform: translate(0, 0) scale(1);
  }
  33% {
    transform: translate(30px, -30px) scale(1.1);
  }
  66% {
    transform: translate(-20px, 20px) scale(0.9);
  }
}

/* Bouton retour */
.back-btn {
  position: absolute;
  top: 2rem;
  left: 2rem;
  z-index: 10;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  padding: 0.75rem 1.25rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  transition: all 0.3s ease;
  color: white;
  font-weight: 500;
}

.back-btn svg {
  width: 20px;
  height: 20px;
}

.back-btn:hover {
  background: rgba(255, 255, 255, 0.15);
  border-color: rgba(255, 255, 255, 0.3);
  transform: translateX(-4px);
}

/* Carte de connexion */
.login-card {
  position: relative;
  z-index: 1;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 24px;
  padding: 3rem;
  max-width: 480px;
  width: 100%;
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.5);
  animation: slideUp 0.6s ease-out;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(40px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Badge Admin */
.admin-badge {
  position: absolute;
  top: -40px;
  left: 50%;
  transform: translateX(-50%);
  width: 80px;
  height: 80px;
}

.badge-icon {
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #dc2626 0%, #f97316 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 4px solid rgba(15, 23, 42, 0.9);
  box-shadow:
    0 0 30px rgba(220, 38, 38, 0.6),
    0 10px 25px rgba(0, 0, 0, 0.4);
  animation: pulse 3s ease-in-out infinite;
}

.badge-icon svg {
  width: 40px;
  height: 40px;
  color: white;
  animation: rotate 8s linear infinite;
}

@keyframes pulse {
  0%, 100% {
    box-shadow:
      0 0 30px rgba(220, 38, 38, 0.6),
      0 10px 25px rgba(0, 0, 0, 0.4);
  }
  50% {
    box-shadow:
      0 0 50px rgba(249, 115, 22, 0.8),
      0 15px 35px rgba(0, 0, 0, 0.5);
  }
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* En-tête */
.header {
  text-align: center;
  margin-top: 2.5rem;
  margin-bottom: 2.5rem;
}

.header h1 {
  color: white;
  font-size: 2rem;
  font-weight: 800;
  margin-bottom: 0.5rem;
  background: linear-gradient(135deg, #fff 0%, #f97316 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.subtitle {
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.95rem;
  font-weight: 500;
}

/* Formulaire */
.form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.form-group label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: rgba(255, 255, 255, 0.9);
  font-weight: 600;
  font-size: 0.95rem;
}

.form-group label svg {
  width: 18px;
  height: 18px;
  color: #f97316;
}

.form-group input {
  width: 100%;
  padding: 1rem 1.25rem;
  background: rgba(255, 255, 255, 0.1);
  border: 2px solid rgba(255, 255, 255, 0.15);
  border-radius: 12px;
  color: white;
  font-size: 1rem;
  transition: all 0.3s ease;
}

.form-group input::placeholder {
  color: rgba(255, 255, 255, 0.4);
}

.form-group input:focus {
  outline: none;
  background: rgba(255, 255, 255, 0.15);
  border-color: #f97316;
  box-shadow: 0 0 0 4px rgba(249, 115, 22, 0.1);
}

.form-group input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Champ mot de passe */
.password-input {
  position: relative;
}

.password-input input {
  padding-right: 3.5rem;
}

.toggle-password {
  position: absolute;
  right: 1rem;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(255, 255, 255, 0.6);
  transition: all 0.3s ease;
}

.toggle-password svg {
  width: 20px;
  height: 20px;
}

.toggle-password:hover {
  color: #f97316;
}

.toggle-password:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* Bouton submit */
.submit-btn {
  margin-top: 1rem;
  width: 100%;
  padding: 1.125rem 2rem;
  background: linear-gradient(135deg, #dc2626 0%, #f97316 100%);
  border: 2px solid rgba(220, 38, 38, 0.5);
  border-radius: 12px;
  color: white;
  font-size: 1.1rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  box-shadow:
    0 4px 12px rgba(0, 0, 0, 0.3),
    inset 0 -4px 8px rgba(0, 0, 0, 0.25),
    inset 0 2px 8px rgba(255, 255, 255, 0.15);
}

.submit-btn svg {
  width: 20px;
  height: 20px;
}

.submit-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #ef4444 0%, #fb923c 100%);
  border-color: rgba(239, 68, 68, 0.8);
  transform: translateY(-2px);
  box-shadow:
    0 0 20px rgba(220, 38, 38, 0.5),
    0 0 40px rgba(220, 38, 38, 0.3),
    0 6px 16px rgba(0, 0, 0, 0.4),
    inset 0 -3px 6px rgba(0, 0, 0, 0.3),
    inset 0 3px 6px rgba(255, 255, 255, 0.2);
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Notice de sécurité */
.security-notice {
  margin-top: 2rem;
  padding: 1rem;
  background: rgba(249, 115, 22, 0.1);
  border: 1px solid rgba(249, 115, 22, 0.3);
  border-radius: 12px;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  color: rgba(255, 255, 255, 0.8);
  font-size: 0.85rem;
}

.security-notice svg {
  width: 20px;
  height: 20px;
  color: #f97316;
  flex-shrink: 0;
}

/* Responsive */
@media (max-width: 600px) {
  .admin-login-page {
    padding: 1rem;
  }

  .back-btn {
    top: 1rem;
    left: 1rem;
    padding: 0.65rem 1rem;
    font-size: 0.9rem;
  }

  .login-card {
    padding: 2.5rem 1.5rem;
  }

  .header h1 {
    font-size: 1.65rem;
  }

  .subtitle {
    font-size: 0.85rem;
  }

  .admin-badge {
    width: 70px;
    height: 70px;
    top: -35px;
  }

  .badge-icon svg {
    width: 35px;
    height: 35px;
  }

  .security-notice {
    font-size: 0.8rem;
    flex-direction: column;
    text-align: center;
  }
}
</style>
