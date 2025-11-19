<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useNotificationStore } from '@/stores/notification'
import ErrorAlert from '@/components/ErrorAlert.vue'
import LoadingSpinner from '@/components/LoadingSpinner.vue'

const router = useRouter()
const authStore = useAuthStore()
const notificationStore = useNotificationStore()

const username = ref('')
const password = ref('')
const errorMessage = ref('')

async function handleLogin() {
  errorMessage.value = ''

  try {
    await authStore.login({
      username: username.value,
      password: password.value
    })

    // Notification de succès
    notificationStore.success('Connexion réussie ! Bienvenue.')

    // Redirection vers le dashboard ou l'URL d'origine
    const redirect = router.currentRoute.value.query.redirect as string
    router.push(redirect || '/dashboard')
  } catch (error) {
    errorMessage.value = authStore.error || 'Erreur de connexion'
    notificationStore.error(errorMessage.value)
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-container">
      <!-- Logo et Header -->
      <div class="header">
        <div class="logo-circle">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M2 17L12 22L22 17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M2 12L12 17L22 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
        <h1>UCAC-ICAM</h1>
        <h2>Portail Captif</h2>
        <p class="subtitle">Bienvenue sur votre espace de connexion</p>
      </div>

      <!-- Formulaire de Connexion -->
      <div class="login-card">
        <h3>Connexion</h3>

        <form @submit.prevent="handleLogin">
          <div class="form-group">
            <label for="username">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <circle cx="12" cy="7" r="4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              Nom d'utilisateur
            </label>
            <input
              id="username"
              v-model="username"
              type="text"
              required
              placeholder="Entrez votre nom d'utilisateur"
              autocomplete="username"
            />
          </div>

          <div class="form-group">
            <label for="password">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M7 11V7a5 5 0 0 1 10 0v4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              Mot de passe
            </label>
            <input
              id="password"
              v-model="password"
              type="password"
              required
              placeholder="Entrez votre mot de passe"
              autocomplete="current-password"
            />
          </div>

          <ErrorAlert
            v-if="errorMessage"
            :message="errorMessage"
            dismissible
            @dismiss="errorMessage = ''"
          />

          <button type="submit" :disabled="authStore.isLoading" class="btn-primary">
            <LoadingSpinner v-if="authStore.isLoading" size="small" color="white" />
            <span v-else>Se connecter</span>
          </button>
        </form>

        <div class="divider">
          <span>OU</span>
        </div>

        <div class="footer-links">
          <router-link to="/register" class="link-button">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <circle cx="8.5" cy="7" r="4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <line x1="20" y1="8" x2="20" y2="14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <line x1="23" y1="11" x2="17" y2="11" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            Créer un compte
          </router-link>

          <router-link to="/vouchers" class="link-button">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M21 10H3M21 6H3M21 14H3M21 18H3" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
            Code invité
          </router-link>
        </div>
      </div>

      <!-- Footer -->
      <div class="page-footer">
        <p>&copy; 2024 UCAC-ICAM - Tous droits réservés</p>
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

.login-page {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #dc2626 0%, #111827 50%, #f97316 100%);
  padding: 1rem;
}

.login-container {
  width: 100%;
  max-width: 440px;
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

/* Header avec Logo */
.header {
  text-align: center;
  margin-bottom: 2rem;
  color: white;
}

.logo-circle {
  width: 80px;
  height: 80px;
  margin: 0 auto 1.5rem;
  background: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
  }
}

.logo-circle svg {
  width: 40px;
  height: 40px;
  color: #dc2626;
}

.header h1 {
  font-size: 2.5rem;
  font-weight: 800;
  margin-bottom: 0.5rem;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
  letter-spacing: 2px;
}

.header h2 {
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
  opacity: 0.95;
}

.subtitle {
  font-size: 1rem;
  opacity: 0.9;
  font-weight: 300;
}

/* Carte de Login */
.login-card {
  background: white;
  padding: 2.5rem;
  border-radius: 20px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  margin-bottom: 1.5rem;
}

.login-card h3 {
  color: #dc2626;
  font-size: 1.5rem;
  margin-bottom: 2rem;
  text-align: center;
  font-weight: 700;
}

/* Formulaire */
.form-group {
  margin-bottom: 1.5rem;
}

label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
  color: #333;
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
  padding: 1rem;
  border: 2px solid #e0e0e0;
  border-radius: 12px;
  font-size: 1rem;
  transition: all 0.3s ease;
  background: #f8f8f8;
}

input:focus {
  outline: none;
  border-color: #f97316;
  background: white;
  box-shadow: 0 0 0 3px rgba(249, 115, 22, 0.1);
}

input::placeholder {
  color: #999;
}

/* Message d'erreur */
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

/* Bouton principal */
.btn-primary {
  width: 100%;
  padding: 1rem;
  background: linear-gradient(135deg, #dc2626 0%, #f97316 100%);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 1.1rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(220, 38, 38, 0.3);
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(220, 38, 38, 0.4);
}

.btn-primary:active:not(:disabled) {
  transform: translateY(0);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Divider */
.divider {
  text-align: center;
  margin: 2rem 0;
  position: relative;
}

.divider::before,
.divider::after {
  content: '';
  position: absolute;
  top: 50%;
  width: 40%;
  height: 1px;
  background: #e0e0e0;
}

.divider::before {
  left: 0;
}

.divider::after {
  right: 0;
}

.divider span {
  background: white;
  padding: 0 1rem;
  color: #999;
  font-size: 0.9rem;
  font-weight: 600;
}

/* Liens du footer */
.footer-links {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.link-button {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.875rem 1rem;
  border: 2px solid #f97316;
  border-radius: 12px;
  color: #f97316;
  text-decoration: none;
  font-weight: 600;
  font-size: 0.95rem;
  transition: all 0.3s ease;
}

.link-button svg {
  width: 18px;
  height: 18px;
}

.link-button:hover {
  background: #f97316;
  color: white;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(249, 115, 22, 0.3);
}

/* Footer de la page */
.page-footer {
  text-align: center;
  color: white;
  font-size: 0.9rem;
  opacity: 0.9;
}

/* Responsive */
@media (max-width: 640px) {
  .login-page {
    padding: 0.5rem;
  }

  .header h1 {
    font-size: 2rem;
  }

  .header h2 {
    font-size: 1.2rem;
  }

  .login-card {
    padding: 2rem 1.5rem;
  }

  .footer-links {
    grid-template-columns: 1fr;
  }

  .logo-circle {
    width: 70px;
    height: 70px;
  }

  .logo-circle svg {
    width: 35px;
    height: 35px;
  }
}

@media (max-width: 380px) {
  .header h1 {
    font-size: 1.75rem;
  }

  .login-card {
    padding: 1.5rem 1rem;
  }

  input {
    padding: 0.875rem;
  }

  .btn-primary {
    padding: 0.875rem;
    font-size: 1rem;
  }
}
</style>
