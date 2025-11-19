<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const formData = ref({
  username: '',
  email: '',
  password: '',
  first_name: '',
  last_name: '',
  phone_number: ''
})
const errorMessage = ref('')

async function handleRegister() {
  errorMessage.value = ''

  try {
    await authStore.register(formData.value)
    router.push('/dashboard')
  } catch (error) {
    errorMessage.value = authStore.error || 'Erreur lors de l\'inscription'
  }
}
</script>

<template>
  <div class="register-page">
    <div class="register-container">
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
        <p class="subtitle">Créez votre compte d'accès</p>
      </div>

      <!-- Carte d'inscription -->
      <div class="register-card">
        <h3>Inscription</h3>

        <form @submit.prevent="handleRegister">
          <div class="form-row">
            <div class="form-group">
              <label for="first_name">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <circle cx="12" cy="7" r="4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                Prénom
              </label>
              <input
                id="first_name"
                v-model="formData.first_name"
                type="text"
                placeholder="Votre prénom"
                autocomplete="given-name"
              />
            </div>
            <div class="form-group">
              <label for="last_name">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <circle cx="12" cy="7" r="4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                Nom
              </label>
              <input
                id="last_name"
                v-model="formData.last_name"
                type="text"
                placeholder="Votre nom"
                autocomplete="family-name"
              />
            </div>
          </div>

          <div class="form-group">
            <label for="username">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                <path d="M12 16v-4M12 8h.01" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
              Nom d'utilisateur *
            </label>
            <input
              id="username"
              v-model="formData.username"
              type="text"
              required
              placeholder="Choisissez un nom d'utilisateur"
              autocomplete="username"
            />
          </div>

          <div class="form-group">
            <label for="email">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M22 6l-10 7L2 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              Email *
            </label>
            <input
              id="email"
              v-model="formData.email"
              type="email"
              required
              placeholder="votre.email@exemple.com"
              autocomplete="email"
            />
          </div>

          <div class="form-group">
            <label for="phone_number">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              Téléphone
            </label>
            <input
              id="phone_number"
              v-model="formData.phone_number"
              type="tel"
              placeholder="+237 6XX XX XX XX"
              autocomplete="tel"
            />
          </div>

          <div class="form-group">
            <label for="password">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M7 11V7a5 5 0 0 1 10 0v4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              Mot de passe *
            </label>
            <input
              id="password"
              v-model="formData.password"
              type="password"
              required
              placeholder="Choisissez un mot de passe"
              autocomplete="new-password"
            />
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
            <span v-if="authStore.isLoading">Inscription en cours...</span>
            <span v-else>S'inscrire</span>
          </button>
        </form>

        <div class="divider">
          <span>OU</span>
        </div>

        <div class="footer">
          <router-link to="/login" class="link-button">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4M10 17l5-5-5-5M15 12H3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            Déjà un compte ? Se connecter
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

.register-page {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #c31432 0%, #e85d04 50%, #ff6b35 100%);
  padding: 1rem;
}

.register-container {
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
  color: #c31432;
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

/* Carte d'inscription */
.register-card {
  background: white;
  padding: 2.5rem;
  border-radius: 20px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  margin-bottom: 1.5rem;
}

.register-card h3 {
  color: #c31432;
  font-size: 1.5rem;
  margin-bottom: 2rem;
  text-align: center;
  font-weight: 700;
}

/* Formulaire */
.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

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
  background: linear-gradient(135deg, #c31432 0%, #e85d04 100%);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 1.1rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(195, 20, 50, 0.3);
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
  width: 42%;
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

/* Footer */
.footer {
  text-align: center;
}

.link-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.875rem 1.5rem;
  border: 2px solid #e85d04;
  border-radius: 12px;
  color: #e85d04;
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
  background: #e85d04;
  color: white;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(232, 93, 4, 0.3);
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
  .register-page {
    padding: 0.5rem;
  }

  .header h1 {
    font-size: 2rem;
  }

  .header h2 {
    font-size: 1.2rem;
  }

  .register-card {
    padding: 2rem 1.5rem;
  }

  .form-row {
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

  .register-card {
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
