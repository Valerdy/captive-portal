<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { usePromotionStore } from '@/stores/promotion'
import { useNotificationStore } from '@/stores/notification'
import ErrorAlert from '@/components/ErrorAlert.vue'
import LoadingSpinner from '@/components/LoadingSpinner.vue'

const router = useRouter()
const authStore = useAuthStore()
const promotionStore = usePromotionStore()
const notificationStore = useNotificationStore()

const formData = ref({
  first_name: '',
  last_name: '',
  promotion: '' as number | string,
  matricule: '',
  password: '',
  password2: ''
})
const errorMessage = ref('')
const showPassword = ref(false)
const showPassword2 = ref(false)

const promotions = ref<{ id: number; name: string }[]>([])

async function loadPromotions() {
  try {
    // Utiliser l'endpoint public pour les promotions actives
    const list = await promotionStore.fetchActivePromotions()
    promotions.value = list.map(p => ({ id: p.id, name: p.name }))
  } catch (error) {
    // en cas d'échec, on laisse la saisie libre via fallback
    promotions.value = []
  }
}

async function handleRegister() {
  errorMessage.value = ''

  // Validation côté client
  if (!formData.value.first_name || !formData.value.last_name ||
      !formData.value.promotion || !formData.value.matricule ||
      !formData.value.password || !formData.value.password2) {
    errorMessage.value = 'Tous les champs sont requis'
    notificationStore.error(errorMessage.value)
    return
  }

  if (formData.value.password !== formData.value.password2) {
    errorMessage.value = 'Les mots de passe ne correspondent pas'
    notificationStore.error(errorMessage.value)
    return
  }

  try {
    await authStore.register(formData.value)

    // Notification de succès
    notificationStore.success('Inscription réussie ! Bienvenue.')

    router.push('/dashboard')
  } catch (error) {
    errorMessage.value = authStore.error || 'Erreur lors de l\'inscription'
    notificationStore.error(errorMessage.value)
  }
}

onMounted(() => {
  loadPromotions()
})
</script>

<template>
  <div class="register-page">
    <!-- Animated Background -->
    <div class="bg-animation">
      <div class="grid-overlay"></div>
      <div class="glow-orb orb-1"></div>
      <div class="glow-orb orb-2"></div>
      <div class="glow-orb orb-3"></div>
    </div>

    <!-- Bouton Accueil -->
    <router-link to="/" class="home-button" title="Retour à l'accueil">
      <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M9 22V12h6v10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    </router-link>

    <div class="register-container">
      <!-- Logo et Header -->
      <div class="header">
        <div class="logo-container">
          <div class="logo-ring outer"></div>
          <div class="logo-ring inner"></div>
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
        <p class="subtitle">Créez votre compte étudiant</p>
      </div>

      <!-- Carte d'inscription -->
      <div class="register-card">
        <div class="card-header">
          <div class="header-icon">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2"/>
              <circle cx="8.5" cy="7" r="4" stroke="currentColor" stroke-width="2"/>
              <line x1="20" y1="8" x2="20" y2="14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              <line x1="23" y1="11" x2="17" y2="11" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </div>
          <div>
            <h3>Inscription</h3>
            <p class="info-text">Utilisez les informations fournies par l'administration</p>
          </div>
        </div>

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
              <div class="input-wrapper">
                <input
                  id="first_name"
                  v-model="formData.first_name"
                  type="text"
                  required
                  placeholder="Votre prénom"
                  autocomplete="given-name"
                />
              </div>
            </div>
            <div class="form-group">
              <label for="last_name">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <circle cx="12" cy="7" r="4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                Nom
              </label>
              <div class="input-wrapper">
                <input
                  id="last_name"
                  v-model="formData.last_name"
                  type="text"
                  required
                  placeholder="Votre nom"
                  autocomplete="family-name"
                />
              </div>
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label for="promotion">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M22 10v6M2 10l10-5 10 5-10 5z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M6 12v5c3 3 9 3 12 0v-5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                Promotion
              </label>
              <div class="input-wrapper select-wrapper">
                <select
                  id="promotion"
                  v-model="formData.promotion"
                  required
                >
                  <option value="" disabled>Choisir une promotion</option>
                  <option v-for="promo in promotions" :key="promo.id" :value="promo.id">
                    {{ promo.name }}
                  </option>
                </select>
                <svg class="select-arrow" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <polyline points="6 9 12 15 18 9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </div>
            </div>
            <div class="form-group">
              <label for="matricule">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <rect x="3" y="4" width="18" height="18" rx="2" ry="2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <line x1="16" y1="2" x2="16" y2="6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <line x1="8" y1="2" x2="8" y2="6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <line x1="3" y1="10" x2="21" y2="10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                Matricule
              </label>
              <div class="input-wrapper">
                <input
                  id="matricule"
                  v-model="formData.matricule"
                  type="text"
                  required
                  placeholder="Ex: 2024XXXX"
                  autocomplete="off"
                />
              </div>
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
            <div class="input-wrapper password-wrapper">
              <input
                id="password"
                v-model="formData.password"
                :type="showPassword ? 'text' : 'password'"
                required
                placeholder="Choisissez un mot de passe fort"
                autocomplete="new-password"
              />
              <button
                type="button"
                class="toggle-password"
                @click="showPassword = !showPassword"
                aria-label="Afficher/Masquer le mot de passe"
              >
                <svg v-if="!showPassword" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                <svg v-else viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <line x1="1" y1="1" x2="23" y2="23" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </button>
            </div>
          </div>

          <div class="form-group">
            <label for="password2">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M7 11V7a5 5 0 0 1 10 0v4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <circle cx="12" cy="16" r="1" fill="currentColor"/>
              </svg>
              Confirmer le mot de passe
            </label>
            <div class="input-wrapper password-wrapper">
              <input
                id="password2"
                v-model="formData.password2"
                :type="showPassword2 ? 'text' : 'password'"
                required
                placeholder="Confirmez votre mot de passe"
                autocomplete="new-password"
              />
              <button
                type="button"
                class="toggle-password"
                @click="showPassword2 = !showPassword2"
                aria-label="Afficher/Masquer le mot de passe"
              >
                <svg v-if="!showPassword2" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                <svg v-else viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <line x1="1" y1="1" x2="23" y2="23" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </button>
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
            <template v-else>
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2"/>
                <circle cx="8.5" cy="7" r="4" stroke="currentColor" stroke-width="2"/>
                <line x1="20" y1="8" x2="20" y2="14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                <line x1="23" y1="11" x2="17" y2="11" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
              <span>Créer mon compte</span>
            </template>
          </button>
        </form>

        <div class="divider">
          <span>Déjà inscrit ?</span>
        </div>

        <div class="footer">
          <router-link to="/login" class="link-button">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4M10 17l5-5-5-5M15 12H3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <span>Se connecter</span>
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
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Rajdhani:wght@300;400;500;600;700&family=Inter:wght@300;400;500;600;700&display=swap');

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
  background: linear-gradient(135deg, #0a0a12 0%, #0f0f1a 50%, #1a1a2e 100%);
  padding: 2rem 1rem;
  position: relative;
  overflow: hidden;
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
  opacity: 0.4;
  animation: float 10s ease-in-out infinite;
}

.orb-1 {
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, rgba(242, 148, 0, 0.3) 0%, transparent 70%);
  top: -100px;
  right: -100px;
  animation-delay: 0s;
}

.orb-2 {
  width: 300px;
  height: 300px;
  background: radial-gradient(circle, rgba(0, 142, 207, 0.3) 0%, transparent 70%);
  bottom: -50px;
  left: -50px;
  animation-delay: -3s;
}

.orb-3 {
  width: 200px;
  height: 200px;
  background: radial-gradient(circle, rgba(162, 56, 130, 0.3) 0%, transparent 70%);
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  animation-delay: -6s;
}

@keyframes float {
  0%, 100% { transform: translateY(0) scale(1); }
  50% { transform: translateY(-30px) scale(1.05); }
}

.register-container {
  width: 100%;
  max-width: 560px;
  animation: fadeInUp 0.6s ease-out;
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

/* Header avec Logo */
.header {
  text-align: center;
  margin-bottom: 2rem;
}

.logo-container {
  width: 90px;
  height: 90px;
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

.logo-ring.inner {
  width: 70%;
  height: 70%;
  border-top-color: #008ecf;
  border-left-color: #008ecf;
  animation: spin 2s linear infinite reverse;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.logo-icon {
  width: 50px;
  height: 50px;
  background: linear-gradient(135deg, rgba(242, 148, 0, 0.2) 0%, rgba(0, 142, 207, 0.2) 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(242, 148, 0, 0.3);
}

.logo-icon svg {
  width: 28px;
  height: 28px;
  color: #F29400;
}

.header h1 {
  font-family: 'Orbitron', sans-serif;
  font-size: 2.2rem;
  font-weight: 800;
  color: white;
  margin-bottom: 0.25rem;
  letter-spacing: 3px;
  text-shadow: 0 0 30px rgba(242, 148, 0, 0.5);
}

.header h2 {
  font-family: 'Rajdhani', sans-serif;
  font-size: 1.2rem;
  font-weight: 500;
  color: #F29400;
  margin-bottom: 0.5rem;
  letter-spacing: 2px;
  text-transform: uppercase;
}

.subtitle {
  font-family: 'Inter', sans-serif;
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.6);
  font-weight: 400;
}

/* Carte d'inscription */
.register-card {
  background: rgba(15, 15, 25, 0.8);
  backdrop-filter: blur(20px);
  padding: 2rem;
  border-radius: 20px;
  border: 1px solid rgba(242, 148, 0, 0.2);
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
  background: linear-gradient(135deg, rgba(242, 148, 0, 0.2) 0%, rgba(242, 148, 0, 0.05) 100%);
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

.card-header h3 {
  font-family: 'Rajdhani', sans-serif;
  color: white;
  font-size: 1.4rem;
  font-weight: 600;
  margin-bottom: 0.25rem;
}

.info-text {
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.85rem;
}

/* Formulaire */
.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.form-group {
  margin-bottom: 1.25rem;
}

label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
  color: rgba(255, 255, 255, 0.8);
  font-family: 'Rajdhani', sans-serif;
  font-weight: 600;
  font-size: 0.9rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

label svg {
  width: 16px;
  height: 16px;
  color: #F29400;
  flex-shrink: 0;
}

.input-wrapper {
  position: relative;
}

input, select {
  width: 100%;
  padding: 0.875rem 1rem;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  font-family: 'Inter', sans-serif;
  font-size: 0.95rem;
  color: white;
  transition: all 0.3s ease;
}

input::placeholder {
  color: rgba(255, 255, 255, 0.3);
}

input:focus, select:focus {
  outline: none;
  border-color: #F29400;
  background: rgba(242, 148, 0, 0.05);
  box-shadow: 0 0 20px rgba(242, 148, 0, 0.15);
}

/* Select styling */
.select-wrapper {
  position: relative;
}

select {
  appearance: none;
  cursor: pointer;
  padding-right: 2.5rem;
}

select option {
  background: #1a1a2e;
  color: white;
  padding: 0.5rem;
}

.select-arrow {
  position: absolute;
  right: 1rem;
  top: 50%;
  transform: translateY(-50%);
  width: 18px;
  height: 18px;
  color: rgba(255, 255, 255, 0.5);
  pointer-events: none;
  transition: color 0.3s ease;
}

.select-wrapper:focus-within .select-arrow {
  color: #F29400;
}

/* Password input */
.password-wrapper input {
  padding-right: 3rem;
}

.toggle-password {
  position: absolute;
  right: 0.75rem;
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
  transition: color 0.3s ease;
}

.toggle-password:hover {
  color: #F29400;
}

.toggle-password svg {
  width: 18px;
  height: 18px;
}

/* Bouton principal */
.btn-submit {
  width: 100%;
  padding: 1rem;
  background: linear-gradient(135deg, #F29400 0%, #e53212 100%);
  color: white;
  border: none;
  border-radius: 12px;
  font-family: 'Rajdhani', sans-serif;
  font-size: 1.1rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  margin-top: 0.5rem;
  box-shadow: 0 4px 20px rgba(242, 148, 0, 0.3);
}

.btn-submit svg {
  width: 20px;
  height: 20px;
}

.btn-submit:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 30px rgba(242, 148, 0, 0.4);
}

.btn-submit:active:not(:disabled) {
  transform: translateY(0);
}

.btn-submit:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Divider */
.divider {
  text-align: center;
  margin: 1.5rem 0;
  position: relative;
}

.divider::before,
.divider::after {
  content: '';
  position: absolute;
  top: 50%;
  width: 38%;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
}

.divider::before {
  left: 0;
}

.divider::after {
  right: 0;
}

.divider span {
  padding: 0 1rem;
  color: rgba(255, 255, 255, 0.4);
  font-family: 'Rajdhani', sans-serif;
  font-size: 0.9rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 1px;
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
  padding: 0.875rem 2rem;
  background: transparent;
  border: 1px solid rgba(0, 142, 207, 0.5);
  border-radius: 10px;
  color: #008ecf;
  text-decoration: none;
  font-family: 'Rajdhani', sans-serif;
  font-weight: 600;
  font-size: 1rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  transition: all 0.3s ease;
}

.link-button svg {
  width: 18px;
  height: 18px;
}

.link-button:hover {
  background: rgba(0, 142, 207, 0.1);
  border-color: #008ecf;
  box-shadow: 0 0 20px rgba(0, 142, 207, 0.3);
  transform: translateY(-2px);
}

/* Footer de la page */
.page-footer {
  text-align: center;
  color: rgba(255, 255, 255, 0.4);
  font-family: 'Inter', sans-serif;
  font-size: 0.8rem;
}

/* Bouton Accueil */
.home-button {
  position: fixed;
  top: 1.5rem;
  left: 1.5rem;
  width: 50px;
  height: 50px;
  background: rgba(15, 15, 25, 0.8);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(242, 148, 0, 0.3);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  text-decoration: none;
  transition: all 0.3s ease;
  z-index: 100;
}

.home-button svg {
  width: 22px;
  height: 22px;
  color: #F29400;
  transition: all 0.3s ease;
}

.home-button:hover {
  background: rgba(242, 148, 0, 0.1);
  border-color: #F29400;
  box-shadow: 0 0 20px rgba(242, 148, 0, 0.3);
  transform: translateY(-2px);
}

/* Responsive */
@media (max-width: 640px) {
  .register-page {
    padding: 1rem;
  }

  .header h1 {
    font-size: 1.8rem;
  }

  .header h2 {
    font-size: 1rem;
  }

  .register-card {
    padding: 1.5rem;
  }

  .form-row {
    grid-template-columns: 1fr;
  }

  .card-header {
    flex-direction: column;
    text-align: center;
  }

  .logo-container {
    width: 70px;
    height: 70px;
  }

  .logo-icon {
    width: 40px;
    height: 40px;
  }

  .logo-icon svg {
    width: 22px;
    height: 22px;
  }

  .home-button {
    top: 1rem;
    left: 1rem;
    width: 44px;
    height: 44px;
  }

  .home-button svg {
    width: 18px;
    height: 18px;
  }
}

@media (max-width: 380px) {
  .header h1 {
    font-size: 1.5rem;
    letter-spacing: 2px;
  }

  .register-card {
    padding: 1.25rem;
  }

  input, select {
    padding: 0.75rem;
  }

  .btn-submit {
    padding: 0.875rem;
    font-size: 1rem;
  }
}
</style>
