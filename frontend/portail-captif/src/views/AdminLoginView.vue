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
    <!-- Animated Background -->
    <div class="bg-animation">
      <div class="grid-overlay"></div>
      <div class="glow-orb orb-1"></div>
      <div class="glow-orb orb-2"></div>
      <div class="glow-orb orb-3"></div>
      <div class="scan-line"></div>
    </div>

    <!-- Bouton retour -->
    <button @click="goBack" class="back-btn" title="Retour">
      <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M19 12H5M5 12l7 7m-7-7 7-7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
      <span>Retour</span>
    </button>

    <div class="login-container">
      <!-- Logo animé -->
      <div class="logo-section">
        <div class="logo-container">
          <div class="logo-ring outer"></div>
          <div class="logo-ring middle"></div>
          <div class="logo-ring inner"></div>
          <div class="logo-icon">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z" stroke="currentColor" stroke-width="2"/>
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" stroke="currentColor" stroke-width="2"/>
            </svg>
          </div>
        </div>
        <h1 class="title">ADMIN</h1>
        <p class="subtitle">Espace Administrateur</p>
      </div>

      <!-- Carte de connexion -->
      <div class="login-card">
        <div class="card-header">
          <div class="header-icon">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M9 12l2 2 4-4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <div>
            <h2>Connexion Sécurisée</h2>
            <p>UCAC-ICAM Portail Captif</p>
          </div>
        </div>

        <!-- Formulaire -->
        <form @submit.prevent="handleLogin" class="form">
          <div class="form-group">
            <label for="username">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2"/>
                <circle cx="12" cy="7" r="4" stroke="currentColor" stroke-width="2"/>
              </svg>
              Identifiant
            </label>
            <div class="input-wrapper">
              <input
                id="username"
                v-model="username"
                type="text"
                placeholder="Nom d'utilisateur"
                autocomplete="username"
                :disabled="isLoading"
                required
              />
              <div class="input-glow"></div>
            </div>
          </div>

          <div class="form-group">
            <label for="password">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2" stroke="currentColor" stroke-width="2"/>
                <path d="M7 11V7a5 5 0 0 1 10 0v4" stroke="currentColor" stroke-width="2"/>
              </svg>
              Mot de passe
            </label>
            <div class="input-wrapper password-wrapper">
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
              <div class="input-glow"></div>
            </div>
          </div>

          <button type="submit" :disabled="isLoading" class="submit-btn">
            <LoadingSpinner v-if="isLoading" size="small" color="white" />
            <template v-else>
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4M10 17l5-5-5-5M15 12H3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              <span>Accéder au panneau</span>
            </template>
          </button>
        </form>

        <!-- Footer sécurité -->
        <div class="security-notice">
          <div class="security-icon">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <div class="security-text">
            <span class="security-label">Zone sécurisée</span>
            <span class="security-desc">Accès réservé aux administrateurs autorisés</span>
          </div>
          <div class="security-indicator">
            <span class="indicator-dot"></span>
            <span class="indicator-dot"></span>
            <span class="indicator-dot"></span>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="page-footer">
        <p>&copy; 2024 UCAC-ICAM - Système de gestion du portail captif</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Rajdhani:wght@300;400;500;600;700&family=Inter:wght@300;400;500;600;700&display=swap');

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
  background: linear-gradient(135deg, #0a0a12 0%, #0f0f1a 50%, #1a1a2e 100%);
}

/* Animated Background */
.bg-animation {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
}

.grid-overlay {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(242, 148, 0, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(242, 148, 0, 0.03) 1px, transparent 1px);
  background-size: 50px 50px;
  animation: gridMove 20s linear infinite;
}

@keyframes gridMove {
  0% { transform: translate(0, 0); }
  100% { transform: translate(50px, 50px); }
}

.glow-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.5;
  animation: float 10s ease-in-out infinite;
}

.orb-1 {
  width: 500px;
  height: 500px;
  background: radial-gradient(circle, rgba(242, 148, 0, 0.4) 0%, transparent 70%);
  top: -150px;
  right: -150px;
  animation-delay: 0s;
}

.orb-2 {
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, rgba(229, 50, 18, 0.3) 0%, transparent 70%);
  bottom: -100px;
  left: -100px;
  animation-delay: -3s;
}

.orb-3 {
  width: 300px;
  height: 300px;
  background: radial-gradient(circle, rgba(0, 142, 207, 0.3) 0%, transparent 70%);
  top: 50%;
  left: 30%;
  transform: translate(-50%, -50%);
  animation-delay: -6s;
}

@keyframes float {
  0%, 100% { transform: translateY(0) scale(1); }
  50% { transform: translateY(-40px) scale(1.1); }
}

.scan-line {
  position: absolute;
  width: 100%;
  height: 2px;
  background: linear-gradient(90deg, transparent, rgba(242, 148, 0, 0.5), transparent);
  top: 0;
  animation: scan 4s linear infinite;
}

@keyframes scan {
  0% { top: 0; opacity: 1; }
  100% { top: 100%; opacity: 0; }
}

/* Bouton retour */
.back-btn {
  position: fixed;
  top: 1.5rem;
  left: 1.5rem;
  z-index: 10;
  background: rgba(15, 15, 25, 0.8);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(242, 148, 0, 0.3);
  border-radius: 12px;
  padding: 0.75rem 1.25rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  transition: all 0.3s ease;
  color: #F29400;
  font-family: 'Rajdhani', sans-serif;
  font-weight: 600;
  font-size: 0.95rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.back-btn svg {
  width: 18px;
  height: 18px;
}

.back-btn:hover {
  background: rgba(242, 148, 0, 0.1);
  border-color: #F29400;
  box-shadow: 0 0 20px rgba(242, 148, 0, 0.3);
  transform: translateX(-4px);
}

/* Container */
.login-container {
  position: relative;
  z-index: 1;
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

/* Logo Section */
.logo-section {
  text-align: center;
  margin-bottom: 2rem;
}

.logo-container {
  width: 100px;
  height: 100px;
  margin: 0 auto 1.5rem;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo-ring {
  position: absolute;
  border: 2px solid transparent;
  border-radius: 50%;
}

.logo-ring.outer {
  width: 100%;
  height: 100%;
  border-top-color: #F29400;
  border-right-color: #F29400;
  animation: spin 3s linear infinite;
}

.logo-ring.middle {
  width: 80%;
  height: 80%;
  border-top-color: #e53212;
  border-bottom-color: #e53212;
  animation: spin 2.5s linear infinite reverse;
}

.logo-ring.inner {
  width: 60%;
  height: 60%;
  border-top-color: #008ecf;
  border-left-color: #008ecf;
  animation: spin 2s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.logo-icon {
  width: 45px;
  height: 45px;
  background: linear-gradient(135deg, rgba(242, 148, 0, 0.3) 0%, rgba(229, 50, 18, 0.2) 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(242, 148, 0, 0.4);
  box-shadow: 0 0 20px rgba(242, 148, 0, 0.3);
}

.logo-icon svg {
  width: 26px;
  height: 26px;
  color: #F29400;
  animation: pulse-icon 2s ease-in-out infinite;
}

@keyframes pulse-icon {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

.title {
  font-family: 'Orbitron', sans-serif;
  font-size: 2.5rem;
  font-weight: 900;
  color: white;
  letter-spacing: 8px;
  text-shadow: 0 0 40px rgba(242, 148, 0, 0.5);
  margin-bottom: 0.25rem;
}

.subtitle {
  font-family: 'Rajdhani', sans-serif;
  font-size: 1.1rem;
  font-weight: 500;
  color: #F29400;
  letter-spacing: 3px;
  text-transform: uppercase;
}

/* Login Card */
.login-card {
  background: rgba(15, 15, 25, 0.85);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  border: 1px solid rgba(242, 148, 0, 0.2);
  padding: 2rem;
  box-shadow:
    0 25px 50px rgba(0, 0, 0, 0.5),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
  margin-bottom: 1.5rem;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 2rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.header-icon {
  width: 50px;
  height: 50px;
  background: linear-gradient(135deg, rgba(242, 148, 0, 0.2) 0%, rgba(229, 50, 18, 0.1) 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(242, 148, 0, 0.3);
  flex-shrink: 0;
}

.header-icon svg {
  width: 24px;
  height: 24px;
  color: #F29400;
}

.card-header h2 {
  font-family: 'Rajdhani', sans-serif;
  color: white;
  font-size: 1.3rem;
  font-weight: 600;
  margin-bottom: 0.25rem;
}

.card-header p {
  color: rgba(255, 255, 255, 0.5);
  font-family: 'Inter', sans-serif;
  font-size: 0.85rem;
}

/* Form */
.form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: rgba(255, 255, 255, 0.8);
  font-family: 'Rajdhani', sans-serif;
  font-weight: 600;
  font-size: 0.9rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.form-group label svg {
  width: 16px;
  height: 16px;
  color: #F29400;
}

.input-wrapper {
  position: relative;
}

.input-wrapper input {
  width: 100%;
  padding: 1rem 1.25rem;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  font-family: 'Inter', sans-serif;
  font-size: 1rem;
  color: white;
  transition: all 0.3s ease;
}

.input-wrapper input::placeholder {
  color: rgba(255, 255, 255, 0.3);
}

.input-wrapper input:focus {
  outline: none;
  border-color: #F29400;
  background: rgba(242, 148, 0, 0.05);
  box-shadow: 0 0 25px rgba(242, 148, 0, 0.2);
}

.input-wrapper input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.input-glow {
  position: absolute;
  inset: 0;
  border-radius: 12px;
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.3s ease;
  background: linear-gradient(135deg, rgba(242, 148, 0, 0.1) 0%, transparent 50%);
}

.input-wrapper:focus-within .input-glow {
  opacity: 1;
}

/* Password */
.password-wrapper input {
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
  color: rgba(255, 255, 255, 0.4);
  transition: all 0.3s ease;
  z-index: 2;
}

.toggle-password svg {
  width: 18px;
  height: 18px;
}

.toggle-password:hover {
  color: #F29400;
}

.toggle-password:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

/* Submit Button */
.submit-btn {
  width: 100%;
  padding: 1rem 1.5rem;
  background: linear-gradient(135deg, #F29400 0%, #e53212 100%);
  border: none;
  border-radius: 12px;
  font-family: 'Rajdhani', sans-serif;
  font-size: 1.1rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: white;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  box-shadow: 0 4px 20px rgba(242, 148, 0, 0.3);
  margin-top: 0.5rem;
}

.submit-btn svg {
  width: 20px;
  height: 20px;
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 30px rgba(242, 148, 0, 0.5);
}

.submit-btn:active:not(:disabled) {
  transform: translateY(0);
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Security Notice */
.security-notice {
  margin-top: 1.5rem;
  padding: 1rem;
  background: linear-gradient(135deg, rgba(0, 142, 207, 0.1) 0%, rgba(0, 142, 207, 0.05) 100%);
  border: 1px solid rgba(0, 142, 207, 0.3);
  border-radius: 12px;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.security-icon {
  width: 40px;
  height: 40px;
  background: rgba(0, 142, 207, 0.2);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.security-icon svg {
  width: 20px;
  height: 20px;
  color: #008ecf;
}

.security-text {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.security-label {
  font-family: 'Rajdhani', sans-serif;
  font-weight: 600;
  font-size: 0.9rem;
  color: #008ecf;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.security-desc {
  font-family: 'Inter', sans-serif;
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
}

.security-indicator {
  display: flex;
  gap: 0.25rem;
}

.indicator-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #008ecf;
  animation: blink 1.5s ease-in-out infinite;
}

.indicator-dot:nth-child(2) {
  animation-delay: 0.2s;
}

.indicator-dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes blink {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 1; }
}

/* Footer */
.page-footer {
  text-align: center;
  color: rgba(255, 255, 255, 0.4);
  font-family: 'Inter', sans-serif;
  font-size: 0.8rem;
}

/* Responsive */
@media (max-width: 600px) {
  .admin-login-page {
    padding: 1rem;
  }

  .back-btn {
    top: 1rem;
    left: 1rem;
    padding: 0.6rem 1rem;
    font-size: 0.85rem;
  }

  .logo-container {
    width: 80px;
    height: 80px;
  }

  .logo-icon {
    width: 38px;
    height: 38px;
  }

  .logo-icon svg {
    width: 22px;
    height: 22px;
  }

  .title {
    font-size: 2rem;
    letter-spacing: 5px;
  }

  .subtitle {
    font-size: 0.95rem;
    letter-spacing: 2px;
  }

  .login-card {
    padding: 1.5rem;
  }

  .card-header {
    flex-direction: column;
    text-align: center;
  }

  .security-notice {
    flex-direction: column;
    text-align: center;
    gap: 0.75rem;
  }

  .security-indicator {
    justify-content: center;
  }
}

@media (max-width: 380px) {
  .title {
    font-size: 1.75rem;
    letter-spacing: 4px;
  }

  .login-card {
    padding: 1.25rem;
  }

  .input-wrapper input {
    padding: 0.875rem 1rem;
  }

  .submit-btn {
    padding: 0.875rem;
    font-size: 1rem;
  }
}
</style>
