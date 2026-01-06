<script setup lang="ts">
import ErrorAlert from '@/components/ErrorAlert.vue'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import { useAuthStore } from '@/stores/auth'
import { useNotificationStore } from '@/stores/notification'
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const authStore = useAuthStore()
const notificationStore = useNotificationStore()

const username = ref('')
const password = ref('')
const errorMessage = ref('')
const showPassword = ref(false)

async function handleLogin() {
  errorMessage.value = ''

  try {
    await authStore.login({
      username: username.value,
      password: password.value
    })

    notificationStore.success('Connexion reussie ! Bienvenue.')
    const redirect = router.currentRoute.value.query.redirect as string
    router.push(redirect || '/devices')
  } catch {
    errorMessage.value = authStore.error || 'Erreur de connexion'
    notificationStore.error(errorMessage.value)
  }
}

function togglePassword() {
  showPassword.value = !showPassword.value
}
</script>

<template>
  <div class="login-page">
    <!-- Animated Background -->
    <div class="bg-animated">
      <div class="grid-overlay"></div>
      <div class="gradient-orb orb-1"></div>
      <div class="gradient-orb orb-2"></div>
      <div class="cyber-lines"></div>
    </div>

    <!-- Home Button -->
    <router-link to="/" class="home-button" title="Retour a l'accueil">
      <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M9 22V12h6v10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    </router-link>

    <div class="login-container animate-fadeInUp">
      <!-- Header -->
      <div class="header">
        <div class="logo-container">
          <div class="logo-ring"></div>
          <div class="logo-icon">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M2 17L12 22L22 17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M2 12L12 17L22 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
        </div>
        <h1>UCAC-ICAM</h1>
        <h2>Portail Captif</h2>
        <p class="subtitle">Connectez-vous a votre espace</p>
      </div>

      <!-- Login Card -->
      <div class="login-card">
        <div class="card-header">
          <div class="card-icon">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4M10 17l5-5-5-5M15 12H3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <h3>Connexion</h3>
        </div>

        <form @submit.prevent="handleLogin">
          <div class="form-group">
            <label for="username">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <circle cx="12" cy="7" r="4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              Nom d'utilisateur
            </label>
            <div class="input-wrapper">
              <input
                id="username"
                v-model="username"
                type="text"
                required
                placeholder="Entrez votre identifiant"
                autocomplete="username"
              />
              <span class="input-glow"></span>
            </div>
          </div>

          <div class="form-group">
            <label for="password">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M7 11V7a5 5 0 0 1 10 0v4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              Mot de passe
            </label>
            <div class="input-wrapper password-input">
              <input
                id="password"
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
                required
                placeholder="Entrez votre mot de passe"
                autocomplete="current-password"
              />
              <button type="button" @click="togglePassword" class="toggle-password">
                <svg v-if="showPassword" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <line x1="1" y1="1" x2="23" y2="23" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                <svg v-else viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </button>
              <span class="input-glow"></span>
            </div>
          </div>

          <ErrorAlert
            v-if="errorMessage"
            :message="errorMessage"
            dismissible
            @dismiss="errorMessage = ''"
          />

          <button type="submit" :disabled="authStore.isLoading" class="btn-submit">
            <LoadingSpinner v-if="authStore.isLoading" size="small" color="white" />
            <span v-else>
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4M10 17l5-5-5-5M15 12H3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              Se connecter
            </span>
          </button>
        </form>

        <div class="divider">
          <span>OU</span>
        </div>

        <div class="footer-links">
          <router-link to="/register" class="link-button blue">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <circle cx="8.5" cy="7" r="4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <line x1="20" y1="8" x2="20" y2="14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <line x1="23" y1="11" x2="17" y2="11" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            Creer un compte
          </router-link>

          <router-link to="/vouchers" class="link-button magenta">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <rect x="2" y="5" width="20" height="14" rx="2" stroke="currentColor" stroke-width="2"/>
              <line x1="2" y1="10" x2="22" y2="10" stroke="currentColor" stroke-width="2"/>
            </svg>
            Code invite
          </router-link>
        </div>
      </div>

      <!-- Footer -->
      <div class="page-footer">
        <p>&copy; 2024 UCAC-ICAM - Tous droits reserves</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: #050508;
  padding: 1rem;
  position: relative;
  overflow: hidden;
}

/* Animated Background */
.bg-animated {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  overflow: hidden;
}

.grid-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image:
    linear-gradient(rgba(242, 148, 0, 0.02) 1px, transparent 1px),
    linear-gradient(90deg, rgba(242, 148, 0, 0.02) 1px, transparent 1px);
  background-size: 40px 40px;
}

.gradient-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(100px);
  opacity: 0.3;
  animation: orbPulse 8s ease-in-out infinite;
}

.orb-1 {
  width: 500px;
  height: 500px;
  background: radial-gradient(circle, #F29400 0%, transparent 70%);
  top: -150px;
  right: -100px;
}

.orb-2 {
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, #008ecf 0%, transparent 70%);
  bottom: -100px;
  left: -100px;
  animation-delay: 4s;
}

@keyframes orbPulse {
  0%, 100% { transform: scale(1); opacity: 0.3; }
  50% { transform: scale(1.2); opacity: 0.5; }
}

.cyber-lines {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background:
    linear-gradient(90deg, transparent 49.5%, rgba(242, 148, 0, 0.03) 50%, transparent 50.5%),
    linear-gradient(transparent 49.5%, rgba(242, 148, 0, 0.03) 50%, transparent 50.5%);
  background-size: 100px 100px;
}

/* Home Button */
.home-button {
  position: fixed;
  top: 1.5rem;
  left: 1.5rem;
  width: 50px;
  height: 50px;
  background: rgba(20, 20, 30, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(242, 148, 0, 0.3);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  text-decoration: none;
  transition: all 0.3s ease;
  z-index: 100;
  color: #F29400;
}

.home-button svg {
  width: 24px;
  height: 24px;
}

.home-button:hover {
  background: rgba(242, 148, 0, 0.1);
  border-color: #F29400;
  box-shadow: 0 0 30px rgba(242, 148, 0, 0.3);
  transform: scale(1.05);
}

/* Login Container */
.login-container {
  width: 100%;
  max-width: 440px;
  position: relative;
  z-index: 1;
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

.animate-fadeInUp {
  animation: fadeInUp 0.6s ease-out forwards;
}

/* Header */
.header {
  text-align: center;
  margin-bottom: 2rem;
  color: white;
}

.logo-container {
  position: relative;
  width: 100px;
  height: 100px;
  margin: 0 auto 1.5rem;
}

.logo-ring {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  border: 2px solid rgba(242, 148, 0, 0.3);
  border-radius: 50%;
  animation: ringRotate 10s linear infinite;
}

@keyframes ringRotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.logo-icon {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 70px;
  height: 70px;
  background: linear-gradient(135deg, rgba(242, 148, 0, 0.2) 0%, rgba(0, 142, 207, 0.2) 100%);
  backdrop-filter: blur(10px);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(242, 148, 0, 0.3);
}

.logo-icon svg {
  width: 35px;
  height: 35px;
  color: #F29400;
}

.header h1 {
  font-family: 'Orbitron', sans-serif;
  font-size: 2.5rem;
  font-weight: 900;
  letter-spacing: 0.1em;
  margin-bottom: 0.25rem;
  background: linear-gradient(135deg, #ffffff 0%, #F29400 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.header h2 {
  font-family: 'Rajdhani', sans-serif;
  font-size: 1.25rem;
  font-weight: 600;
  color: #008ecf;
  text-transform: uppercase;
  letter-spacing: 0.15em;
  margin-bottom: 0.5rem;
}

.subtitle {
  font-size: 0.95rem;
  color: #636362;
}

/* Login Card */
.login-card {
  background: linear-gradient(135deg, rgba(20, 20, 30, 0.8) 0%, rgba(10, 10, 15, 0.9) 100%);
  backdrop-filter: blur(30px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 2.5rem;
  border-radius: 24px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
  margin-bottom: 1.5rem;
  position: relative;
  overflow: hidden;
}

.login-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, #F29400, #008ecf, transparent);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.card-icon {
  width: 50px;
  height: 50px;
  background: linear-gradient(135deg, #F29400 0%, #cc7a00 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 0 20px rgba(242, 148, 0, 0.3);
}

.card-icon svg {
  width: 24px;
  height: 24px;
  color: white;
}

.card-header h3 {
  font-family: 'Rajdhani', sans-serif;
  font-size: 1.5rem;
  font-weight: 700;
  color: white;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* Form */
.form-group {
  margin-bottom: 1.5rem;
}

label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
  font-family: 'Rajdhani', sans-serif;
  font-size: 0.9rem;
  font-weight: 600;
  color: #636362;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

label svg {
  width: 18px;
  height: 18px;
  color: #F29400;
}

.input-wrapper {
  position: relative;
}

.input-wrapper input {
  width: 100%;
  padding: 1rem 1.25rem;
  font-family: 'Inter', sans-serif;
  font-size: 1rem;
  color: white;
  background: rgba(255, 255, 255, 0.05);
  border: 2px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  outline: none;
  transition: all 0.3s ease;
}

.input-wrapper input::placeholder {
  color: #636362;
}

.input-wrapper input:focus {
  border-color: #F29400;
  background: rgba(242, 148, 0, 0.05);
}

.input-wrapper input:focus + .input-glow,
.password-input input:focus ~ .input-glow {
  opacity: 1;
}

.input-glow {
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 80%;
  height: 2px;
  background: linear-gradient(90deg, transparent, #F29400, transparent);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.password-input {
  position: relative;
}

.password-input input {
  padding-right: 3.5rem;
}

.toggle-password {
  position: absolute;
  top: 50%;
  right: 1rem;
  transform: translateY(-50%);
  background: none;
  border: none;
  cursor: pointer;
  color: #636362;
  transition: color 0.3s ease;
  padding: 0.25rem;
}

.toggle-password:hover {
  color: #F29400;
}

.toggle-password svg {
  width: 20px;
  height: 20px;
}

/* Submit Button */
.btn-submit {
  width: 100%;
  padding: 1rem 2rem;
  font-family: 'Rajdhani', sans-serif;
  font-size: 1.1rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: white;
  background: linear-gradient(135deg, #F29400 0%, #cc7a00 100%);
  border: none;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  position: relative;
  overflow: hidden;
}

.btn-submit::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s ease;
}

.btn-submit:hover::before {
  left: 100%;
}

.btn-submit:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 0 30px rgba(242, 148, 0, 0.5);
}

.btn-submit:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-submit svg {
  width: 20px;
  height: 20px;
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
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1));
}

.divider::before {
  left: 0;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1));
}

.divider::after {
  right: 0;
  background: linear-gradient(90deg, rgba(255, 255, 255, 0.1), transparent);
}

.divider span {
  background: transparent;
  padding: 0 1rem;
  color: #636362;
  font-family: 'Rajdhani', sans-serif;
  font-size: 0.85rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

/* Footer Links */
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
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  color: white;
  text-decoration: none;
  font-family: 'Rajdhani', sans-serif;
  font-weight: 600;
  font-size: 0.9rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  transition: all 0.3s ease;
}

.link-button svg {
  width: 18px;
  height: 18px;
}

.link-button.blue {
  border-color: rgba(0, 142, 207, 0.3);
  color: #008ecf;
}

.link-button.blue:hover {
  background: rgba(0, 142, 207, 0.1);
  border-color: #008ecf;
  box-shadow: 0 0 20px rgba(0, 142, 207, 0.3);
}

.link-button.magenta {
  border-color: rgba(162, 56, 130, 0.3);
  color: #a23882;
}

.link-button.magenta:hover {
  background: rgba(162, 56, 130, 0.1);
  border-color: #a23882;
  box-shadow: 0 0 20px rgba(162, 56, 130, 0.3);
}

/* Page Footer */
.page-footer {
  text-align: center;
  color: #636362;
  font-size: 0.85rem;
}

/* Responsive */
@media (max-width: 640px) {
  .login-page {
    padding: 0.5rem;
  }

  .home-button {
    top: 1rem;
    left: 1rem;
    width: 44px;
    height: 44px;
  }

  .home-button svg {
    width: 20px;
    height: 20px;
  }

  .header h1 {
    font-size: 2rem;
  }

  .header h2 {
    font-size: 1rem;
  }

  .login-card {
    padding: 2rem 1.5rem;
  }

  .footer-links {
    grid-template-columns: 1fr;
  }

  .logo-container {
    width: 80px;
    height: 80px;
  }

  .logo-icon {
    width: 55px;
    height: 55px;
  }

  .logo-icon svg {
    width: 28px;
    height: 28px;
  }
}

@media (max-width: 380px) {
  .header h1 {
    font-size: 1.75rem;
  }

  .login-card {
    padding: 1.5rem 1rem;
  }

  .input-wrapper input {
    padding: 0.875rem;
  }

  .btn-submit {
    padding: 0.875rem;
    font-size: 1rem;
  }
}
</style>
