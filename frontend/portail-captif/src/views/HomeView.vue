<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const showVerifyModal = ref(false)
const matricule = ref('')
const verifyLoading = ref(false)
const verifyMessage = ref('')
const verifyError = ref('')

function openVerifyModal() {
  showVerifyModal.value = true
  matricule.value = ''
  verifyMessage.value = ''
  verifyError.value = ''
}

function closeVerifyModal() {
  showVerifyModal.value = false
}

async function verifyAccount() {
  if (!matricule.value.trim()) {
    verifyError.value = 'Veuillez entrer votre matricule'
    return
  }

  verifyLoading.value = true
  verifyError.value = ''
  verifyMessage.value = ''

  try {
    // Simuler une vérification API - à remplacer par un vrai appel API
    await new Promise(resolve => setTimeout(resolve, 1500))

    // Logique de vérification à implémenter
    verifyMessage.value = 'Compte vérifié avec succès ! Votre compte est actif.'

  } catch (error) {
    verifyError.value = 'Erreur lors de la vérification. Veuillez réessayer.'
  } finally {
    verifyLoading.value = false
  }
}

function goToInternet() {
  window.open('http://portail.local', '_blank')
}

function goToLogin() {
  router.push('/login')
}
</script>

<template>
  <div class="home-page">
    <!-- Image de fond -->
    <div class="image-background"></div>

    <div class="content">
      <!-- Logo et Titre -->
      <div class="header-section">
        <div class="logo-main">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M2 17L12 22L22 17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M2 12L12 17L22 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
        <h1>UCAC-ICAM</h1>
        <h2>Portail Captif Réseau</h2>
        <p class="subtitle">Bienvenue sur le portail d'accès Internet</p>
      </div>

      <!-- Boutons d'action -->
      <div class="action-buttons">
        <button @click="goToLogin" class="btn btn-primary">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4M10 17l5-5-5-5M15 12H3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          Se connecter
        </button>

        <button @click="openVerifyModal" class="btn btn-secondary">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M22 4L12 14.01l-3-3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          Vérifier son compte
        </button>

        <button @click="goToInternet" class="btn btn-accent">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <line x1="2" y1="12" x2="22" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          Aller sur Internet
        </button>
      </div>

      <!-- Footer -->
      <div class="footer">
        <p>&copy; 2024 UCAC-ICAM - Portail d'accès réseau sécurisé</p>
      </div>
    </div>

    <!-- Modal de vérification -->
    <Teleport to="body">
      <div v-if="showVerifyModal" class="modal-overlay" @click="closeVerifyModal">
        <div class="modal-content" @click.stop>
          <button @click="closeVerifyModal" class="modal-close">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </button>

          <div class="modal-header">
            <div class="modal-icon">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M22 4L12 14.01l-3-3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
            <h3>Vérification du compte</h3>
            <p>Entrez votre matricule pour vérifier l'état de votre compte</p>
          </div>

          <div class="modal-body">
            <div class="form-group">
              <label for="matricule">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2"/>
                  <circle cx="8.5" cy="7" r="4" stroke="currentColor" stroke-width="2"/>
                  <line x1="20" y1="8" x2="20" y2="14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                  <line x1="23" y1="11" x2="17" y2="11" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                </svg>
                Matricule
              </label>
              <input
                id="matricule"
                v-model="matricule"
                type="text"
                placeholder="Ex: UCAC2024001"
                @keyup.enter="verifyAccount"
                :disabled="verifyLoading"
              />
            </div>

            <div v-if="verifyMessage" class="success-message">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                <path d="M22 4L12 14.01l-3-3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              {{ verifyMessage }}
            </div>

            <div v-if="verifyError" class="error-message">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                <line x1="15" y1="9" x2="9" y2="15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                <line x1="9" y1="9" x2="15" y2="15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
              {{ verifyError }}
            </div>

            <button
              @click="verifyAccount"
              :disabled="verifyLoading"
              class="btn btn-primary btn-full"
            >
              <span v-if="verifyLoading">Vérification en cours...</span>
              <span v-else>Vérifier</span>
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.home-page {
  min-height: 100vh;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

/* Image de fond */
.image-background {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, rgba(220, 38, 38, 0.9) 0%, rgba(17, 24, 39, 0.95) 50%, rgba(249, 115, 22, 0.9) 100%),
              url('https://images.unsplash.com/photo-1562774053-701939374585?q=80&w=2000') center/cover;
  z-index: 0;
}

/* Contenu principal */
.content {
  position: relative;
  z-index: 1;
  text-align: center;
  padding: 2rem;
  max-width: 800px;
  width: 100%;
  animation: fadeInUp 0.8s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(40px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Header Section */
.header-section {
  margin-bottom: 4rem;
  color: white;
}

.logo-main {
  width: 120px;
  height: 120px;
  margin: 0 auto 2rem;
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 3px solid rgba(255, 255, 255, 0.3);
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.4);
  animation: pulse 3s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.4);
  }
  50% {
    transform: scale(1.05);
    box-shadow: 0 15px 60px rgba(220, 38, 38, 0.6);
  }
}

.logo-main svg {
  width: 60px;
  height: 60px;
  color: white;
}

.header-section h1 {
  font-size: 4rem;
  font-weight: 900;
  margin-bottom: 1rem;
  text-shadow: 3px 3px 6px rgba(0, 0, 0, 0.5);
  letter-spacing: 3px;
  background: linear-gradient(135deg, #fff 0%, #f97316 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.header-section h2 {
  font-size: 1.75rem;
  font-weight: 600;
  margin-bottom: 1rem;
  opacity: 0.95;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
}

.subtitle {
  font-size: 1.1rem;
  opacity: 0.9;
  font-weight: 300;
}

/* Boutons d'action */
.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  margin-bottom: 3rem;
}

.btn {
  padding: 1.5rem 2.5rem;
  border: none;
  border-radius: 16px;
  font-size: 1.25rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.4s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  backdrop-filter: blur(10px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
}

.btn svg {
  width: 24px;
  height: 24px;
}

.btn-primary {
  background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
  color: white;
  border: 2px solid rgba(255, 255, 255, 0.2);
}

.btn-primary:hover {
  background: linear-gradient(135deg, #b91c1c 0%, #991b1b 100%);
  transform: translateY(-4px) scale(1.02);
  box-shadow: 0 12px 32px rgba(220, 38, 38, 0.5);
}

.btn-secondary {
  background: linear-gradient(135deg, rgba(107, 114, 128, 0.9) 0%, rgba(75, 85, 99, 0.9) 100%);
  color: white;
  border: 2px solid rgba(255, 255, 255, 0.2);
}

.btn-secondary:hover {
  background: linear-gradient(135deg, rgba(75, 85, 99, 0.95) 0%, rgba(55, 65, 81, 0.95) 100%);
  transform: translateY(-4px) scale(1.02);
  box-shadow: 0 12px 32px rgba(107, 114, 128, 0.5);
}

.btn-accent {
  background: linear-gradient(135deg, #f97316 0%, #ea580c 100%);
  color: white;
  border: 2px solid rgba(255, 255, 255, 0.2);
}

.btn-accent:hover {
  background: linear-gradient(135deg, #ea580c 0%, #c2410c 100%);
  transform: translateY(-4px) scale(1.02);
  box-shadow: 0 12px 32px rgba(249, 115, 22, 0.5);
}

/* Footer */
.footer {
  color: white;
  font-size: 0.95rem;
  opacity: 0.8;
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.5);
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.75);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 1rem;
  animation: fadeIn 0.3s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.modal-content {
  background: white;
  border-radius: 24px;
  padding: 2.5rem;
  max-width: 500px;
  width: 100%;
  position: relative;
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.5);
  animation: slideUp 0.4s ease-out;
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

.modal-close {
  position: absolute;
  top: 1.5rem;
  right: 1.5rem;
  background: #f3f4f6;
  border: none;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
}

.modal-close svg {
  width: 20px;
  height: 20px;
  color: #6b7280;
}

.modal-close:hover {
  background: #dc2626;
  transform: rotate(90deg);
}

.modal-close:hover svg {
  color: white;
}

.modal-header {
  text-align: center;
  margin-bottom: 2rem;
}

.modal-icon {
  width: 80px;
  height: 80px;
  margin: 0 auto 1.5rem;
  background: linear-gradient(135deg, #dc2626 0%, #f97316 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-icon svg {
  width: 40px;
  height: 40px;
  color: white;
}

.modal-header h3 {
  color: #111827;
  font-size: 1.75rem;
  margin-bottom: 0.75rem;
  font-weight: 800;
}

.modal-header p {
  color: #6b7280;
  font-size: 1rem;
}

.modal-body .form-group {
  margin-bottom: 1.5rem;
}

.modal-body label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
  color: #111827;
  font-weight: 600;
  font-size: 1rem;
}

.modal-body label svg {
  width: 20px;
  height: 20px;
  color: #f97316;
}

.modal-body input {
  width: 100%;
  padding: 1.125rem;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  font-size: 1.1rem;
  transition: all 0.3s ease;
  background: #f9fafb;
  text-align: center;
  font-weight: 600;
  letter-spacing: 1px;
}

.modal-body input:focus {
  outline: none;
  border-color: #f97316;
  background: white;
  box-shadow: 0 0 0 4px rgba(249, 115, 22, 0.1);
}

.modal-body input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.success-message {
  background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
  border: 2px solid #34d399;
  color: #065f46;
  padding: 1rem;
  border-radius: 12px;
  margin-bottom: 1.5rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-weight: 600;
}

.success-message svg {
  width: 24px;
  height: 24px;
  flex-shrink: 0;
  color: #059669;
}

.error-message {
  background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
  border: 2px solid #f87171;
  color: #991b1b;
  padding: 1rem;
  border-radius: 12px;
  margin-bottom: 1.5rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-weight: 600;
}

.error-message svg {
  width: 24px;
  height: 24px;
  flex-shrink: 0;
  color: #dc2626;
}

.btn-full {
  width: 100%;
}

/* Responsive */
@media (max-width: 768px) {
  .header-section h1 {
    font-size: 2.5rem;
  }

  .header-section h2 {
    font-size: 1.3rem;
  }

  .logo-main {
    width: 100px;
    height: 100px;
  }

  .logo-main svg {
    width: 50px;
    height: 50px;
  }

  .btn {
    padding: 1.25rem 2rem;
    font-size: 1.1rem;
  }

  .modal-content {
    padding: 2rem 1.5rem;
  }
}

@media (max-width: 480px) {
  .content {
    padding: 1rem;
  }

  .header-section h1 {
    font-size: 2rem;
  }

  .header-section h2 {
    font-size: 1.1rem;
  }

  .subtitle {
    font-size: 0.95rem;
  }

  .logo-main {
    width: 80px;
    height: 80px;
  }

  .logo-main svg {
    width: 40px;
    height: 40px;
  }

  .btn {
    padding: 1.125rem 1.5rem;
    font-size: 1rem;
  }

  .btn svg {
    width: 20px;
    height: 20px;
  }
}
</style>
