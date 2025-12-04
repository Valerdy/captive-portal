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
  promotion_id: null as number | null,
  matricule: '',
  password: '',
  password2: ''
})
const errorMessage = ref('')
const showPassword = ref(false)
const showPassword2 = ref(false)

// Charger les promotions au montage
onMounted(async () => {
  try {
    await promotionStore.fetchPromotions()
  } catch (error) {
    console.error('Erreur lors du chargement des promotions:', error)
  }
})

async function handleRegister() {
  errorMessage.value = ''

  // Validation côté client
  if (!formData.value.first_name || !formData.value.last_name ||
      !formData.value.promotion_id || !formData.value.matricule ||
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
        <p class="subtitle">Complétez votre inscription</p>
      </div>

      <!-- Carte d'inscription -->
      <div class="register-card">
        <h3>Inscription</h3>
        <p class="info-text">Utilisez les informations fournies par l'administration</p>

        <form @submit.prevent="handleRegister">
          <div class="form-row">
            <div class="form-group">
              <label for="first_name">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <circle cx="12" cy="7" r="4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                Prénom *
              </label>
              <input
                id="first_name"
                v-model="formData.first_name"
                type="text"
                required
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
                Nom *
              </label>
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

          <div class="form-row">
            <div class="form-group">
              <label for="promotion">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M22 10v6M2 10l10-5 10 5-10 5z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M6 12v5c3 3 9 3 12 0v-5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                Promotion *
              </label>
              <select
                id="promotion"
                v-model="formData.promotion_id"
                required
                class="form-select"
              >
                <option :value="null" disabled>Sélectionnez votre promotion</option>
                <option
                  v-for="promo in promotionStore.promotions.filter(p => p.is_active)"
                  :key="promo.id"
                  :value="promo.id"
                >
                  {{ promo.code }} - {{ promo.name }}
                </option>
              </select>
            </div>
            <div class="form-group">
              <label for="matricule">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <rect x="3" y="4" width="18" height="18" rx="2" ry="2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <line x1="16" y1="2" x2="16" y2="6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <line x1="8" y1="2" x2="8" y2="6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <line x1="3" y1="10" x2="21" y2="10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                Matricule *
              </label>
              <input
                id="matricule"
                v-model="formData.matricule"
                type="text"
                required
                placeholder="Votre matricule"
                autocomplete="off"
              />
            </div>
          </div>

          <div class="form-group">
            <label for="password">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M7 11V7a5 5 0 0 1 10 0v4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              Mot de passe *
            </label>
            <div class="password-input-wrapper">
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
              </svg>
              Confirmation du mot de passe *
            </label>
            <div class="password-input-wrapper">
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

          <button type="submit" :disabled="authStore.isLoading" class="btn-primary">
            <LoadingSpinner v-if="authStore.isLoading" size="small" color="white" />
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
            Déjà inscrit ? Se connecter
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
  background: linear-gradient(135deg, #dc2626 0%, #f97316 50%, #ff6b35 100%);
  padding: 1rem;
}

.register-container {
  width: 100%;
  max-width: 600px;
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

/* Carte d'inscription */
.register-card {
  background: white;
  padding: 2.5rem;
  border-radius: 20px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  margin-bottom: 1.5rem;
}

.register-card h3 {
  color: #dc2626;
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
  text-align: center;
  font-weight: 700;
}

.info-text {
  text-align: center;
  color: #666;
  font-size: 0.9rem;
  margin-bottom: 2rem;
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
  color: #f97316;
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
  border-color: #f97316;
  background: white;
  box-shadow: 0 0 0 3px rgba(249, 115, 22, 0.1);
}

input::placeholder {
  color: #999;
}

/* Select dropdown */
.form-select {
  width: 100%;
  padding: 1rem;
  border: 2px solid #e0e0e0;
  border-radius: 12px;
  font-size: 1rem;
  transition: all 0.3s ease;
  background: #f8f8f8;
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%23666' d='M6 9L1 4h10z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 1rem center;
  padding-right: 3rem;
}

.form-select:focus {
  outline: none;
  border-color: #f97316;
  background-color: white;
  box-shadow: 0 0 0 3px rgba(249, 115, 22, 0.1);
}

.form-select:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Password input with toggle */
.password-input-wrapper {
  position: relative;
}

.password-input-wrapper input {
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
  color: #999;
  transition: color 0.3s ease;
}

.toggle-password:hover {
  color: #f97316;
}

.toggle-password svg {
  width: 20px;
  height: 20px;
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
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
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
