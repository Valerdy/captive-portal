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
        <div class="btn-wrapper">
          <button @click="goToLogin" class="btn btn-primary" title="Se connecter">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4M10 17l5-5-5-5M15 12H3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
          <span class="btn-label">Se connecter</span>
        </div>

        <div class="btn-wrapper">
          <button @click="openVerifyModal" class="btn btn-secondary" title="Vérifier son compte">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M22 4L12 14.01l-3-3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
          <span class="btn-label">Vérifier compte</span>
        </div>

        <div class="btn-wrapper">
          <button @click="goToInternet" class="btn btn-accent" title="Aller sur Internet">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <line x1="2" y1="12" x2="22" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
          <span class="btn-label">Aller sur Internet</span>
        </div>
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
  height: 100vh;
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
  background: url('https://images.unsplash.com/photo-1562774053-701939374585?q=80&w=2000') center/cover;
  z-index: 0;
  animation: zoomImage 20s ease-in-out infinite alternate;
}

.image-background::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.4);
}

@keyframes zoomImage {
  0% {
    transform: scale(1);
  }
  100% {
    transform: scale(1.1);
  }
}

/* Contenu principal */
.content {
  position: relative;
  z-index: 1;
  text-align: center;
  padding: 1.5rem 2rem;
  max-width: 900px;
  width: 100%;
  animation: fadeInUp 0.8s ease-out;
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-height: 100vh;
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
  margin-bottom: 2rem;
  color: white;
}

.logo-main {
  width: 80px;
  height: 80px;
  margin: 0 auto 1rem;
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
  width: 40px;
  height: 40px;
  color: white;
}

.header-section h1 {
  font-size: 2.5rem;
  font-weight: 900;
  margin-bottom: 0.5rem;
  text-shadow: 3px 3px 6px rgba(0, 0, 0, 0.5);
  letter-spacing: 2px;
  background: linear-gradient(135deg, #fff 0%, #f97316 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.header-section h2 {
  font-size: 1.35rem;
  font-weight: 600;
  margin-bottom: 0.4rem;
  opacity: 0.95;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
}

.subtitle {
  font-size: 1rem;
  opacity: 0.9;
  font-weight: 300;
}

/* Boutons d'action */
.action-buttons {
  display: flex;
  flex-direction: row;
  justify-content: center;
  align-items: center;
  gap: 2.5rem;
  margin-bottom: 1.5rem;
}

.btn-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
}

.btn {
  width: 100px;
  height: 100px;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.4s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  box-shadow:
    0 8px 16px rgba(0, 0, 0, 0.4),
    0 12px 28px rgba(0, 0, 0, 0.3),
    inset 0 -8px 16px rgba(0, 0, 0, 0.3),
    inset 0 8px 16px rgba(255, 255, 255, 0.2);
}

.btn::before {
  content: '';
  position: absolute;
  top: 15%;
  left: 20%;
  width: 40%;
  height: 30%;
  background: rgba(255, 255, 255, 0.4);
  border-radius: 50%;
  filter: blur(12px);
  transform: rotate(-45deg);
}

.btn svg {
  width: 36px;
  height: 36px;
  position: relative;
  z-index: 1;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3));
}

.btn-label {
  color: white;
  font-size: 0.95rem;
  font-weight: 600;
  text-align: center;
  text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.5);
}

.btn-primary {
  background: radial-gradient(circle at 30% 30%, #ef4444, #dc2626 50%, #991b1b);
  color: white;
}

.btn-primary:hover {
  background: radial-gradient(circle at 30% 30%, #f87171, #ef4444 50%, #b91c1c);
  transform: translateY(-8px) scale(1.08);
  box-shadow:
    0 15px 35px rgba(220, 38, 38, 0.6),
    0 20px 45px rgba(220, 38, 38, 0.4),
    inset 0 -10px 20px rgba(0, 0, 0, 0.4),
    inset 0 10px 20px rgba(255, 255, 255, 0.25);
}

.btn-secondary {
  background: radial-gradient(circle at 30% 30%, #9ca3af, #6b7280 50%, #374151);
  color: white;
}

.btn-secondary:hover {
  background: radial-gradient(circle at 30% 30%, #d1d5db, #9ca3af 50%, #4b5563);
  transform: translateY(-8px) scale(1.08);
  box-shadow:
    0 15px 35px rgba(107, 114, 128, 0.6),
    0 20px 45px rgba(107, 114, 128, 0.4),
    inset 0 -10px 20px rgba(0, 0, 0, 0.4),
    inset 0 10px 20px rgba(255, 255, 255, 0.25);
}

.btn-accent {
  background: radial-gradient(circle at 30% 30%, #fb923c, #f97316 50%, #c2410c);
  color: white;
}

.btn-accent:hover {
  background: radial-gradient(circle at 30% 30%, #fdba74, #fb923c 50%, #ea580c);
  transform: translateY(-8px) scale(1.08);
  box-shadow:
    0 15px 35px rgba(249, 115, 22, 0.6),
    0 20px 45px rgba(249, 115, 22, 0.4),
    inset 0 -10px 20px rgba(0, 0, 0, 0.4),
    inset 0 10px 20px rgba(255, 255, 255, 0.25);
}

/* Footer */
.footer {
  color: white;
  font-size: 0.8rem;
  opacity: 0.8;
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.5);
  margin-top: 0.75rem;
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
@media (max-width: 900px) and (max-height: 700px) {
  .content {
    padding: 1rem 1.5rem;
  }

  .header-section {
    margin-bottom: 1.5rem;
  }

  .header-section h1 {
    font-size: 2rem;
  }

  .header-section h2 {
    font-size: 1.15rem;
  }

  .logo-main {
    width: 70px;
    height: 70px;
    margin-bottom: 0.75rem;
  }

  .logo-main svg {
    width: 35px;
    height: 35px;
  }

  .action-buttons {
    gap: 2rem;
    margin-bottom: 1rem;
  }

  .btn {
    width: 85px;
    height: 85px;
  }

  .btn svg {
    width: 32px;
    height: 32px;
  }

  .btn-label {
    font-size: 0.85rem;
  }

  .footer {
    font-size: 0.75rem;
    margin-top: 0.5rem;
  }
}

@media (max-width: 768px) {
  .content {
    padding: 1.25rem 1.5rem;
  }

  .header-section {
    margin-bottom: 1.5rem;
  }

  .header-section h1 {
    font-size: 2rem;
  }

  .header-section h2 {
    font-size: 1.15rem;
  }

  .logo-main {
    width: 70px;
    height: 70px;
    margin-bottom: 0.75rem;
  }

  .logo-main svg {
    width: 35px;
    height: 35px;
  }

  .action-buttons {
    gap: 2rem;
    margin-bottom: 1.25rem;
  }

  .btn {
    width: 85px;
    height: 85px;
  }

  .btn svg {
    width: 32px;
    height: 32px;
  }

  .btn-label {
    font-size: 0.85rem;
  }

  .modal-content {
    padding: 2rem 1.5rem;
  }
}

@media (max-width: 600px) {
  .content {
    padding: 1rem;
  }

  .header-section {
    margin-bottom: 1.25rem;
  }

  .header-section h1 {
    font-size: 1.75rem;
  }

  .header-section h2 {
    font-size: 1rem;
  }

  .subtitle {
    font-size: 0.85rem;
  }

  .logo-main {
    width: 60px;
    height: 60px;
    margin-bottom: 0.6rem;
  }

  .logo-main svg {
    width: 30px;
    height: 30px;
  }

  .action-buttons {
    gap: 1.5rem;
    margin-bottom: 1rem;
  }

  .btn {
    width: 75px;
    height: 75px;
  }

  .btn svg {
    width: 28px;
    height: 28px;
  }

  .btn-label {
    font-size: 0.8rem;
  }

  .footer {
    font-size: 0.7rem;
    margin-top: 0.5rem;
  }
}

@media (max-width: 450px) {
  .content {
    padding: 0.75rem;
  }

  .header-section {
    margin-bottom: 1rem;
  }

  .header-section h1 {
    font-size: 1.5rem;
    letter-spacing: 1px;
  }

  .header-section h2 {
    font-size: 0.95rem;
  }

  .subtitle {
    font-size: 0.8rem;
  }

  .logo-main {
    width: 55px;
    height: 55px;
    margin-bottom: 0.5rem;
  }

  .logo-main svg {
    width: 28px;
    height: 28px;
  }

  .action-buttons {
    gap: 1.25rem;
    margin-bottom: 0.75rem;
  }

  .btn {
    width: 70px;
    height: 70px;
  }

  .btn svg {
    width: 26px;
    height: 26px;
  }

  .btn-label {
    font-size: 0.75rem;
  }

  .footer {
    font-size: 0.65rem;
  }
}

@media (max-width: 380px) {
  .header-section h1 {
    font-size: 1.35rem;
  }

  .header-section h2 {
    font-size: 0.9rem;
  }

  .subtitle {
    font-size: 0.75rem;
  }

  .action-buttons {
    gap: 1rem;
  }

  .btn {
    width: 65px;
    height: 65px;
  }

  .btn svg {
    width: 24px;
    height: 24px;
  }

  .btn-label {
    font-size: 0.7rem;
  }
}
</style>
