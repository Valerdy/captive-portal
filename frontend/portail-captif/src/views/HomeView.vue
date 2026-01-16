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
    await new Promise(resolve => setTimeout(resolve, 1500))
    verifyMessage.value = 'Compte verifie avec succes ! Votre compte est actif.'
  } catch {
    verifyError.value = 'Erreur lors de la verification. Veuillez reessayer.'
  } finally {
    verifyLoading.value = false
  }
}

function goToInternet() {
  window.open('http://portail.local', '_blank')
}

function goToRegister() {
  router.push('/register')
}

function goToLogin() {
  router.push('/login')
}

function goToAdminLogin() {
  router.push('/admin/login')
}
</script>

<template>
  <div class="home-page">
    <!-- Animated Background -->
    <div class="bg-animated">
      <div class="grid-overlay"></div>
      <div class="gradient-orb orb-1"></div>
      <div class="gradient-orb orb-2"></div>
      <div class="gradient-orb orb-3"></div>
      <div class="scan-line"></div>
    </div>

    <!-- Admin Button -->
    <button @click="goToAdminLogin" class="admin-btn" title="Administration">
      <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z" stroke="currentColor" stroke-width="2"/>
        <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" stroke="currentColor" stroke-width="2"/>
      </svg>
      <span>Admin</span>
    </button>

    <!-- Main Content -->
    <div class="content">
      <!-- Logo Section -->
      <div class="logo-section animate-fadeInUp">
        <div class="logo-container">
          <div class="logo-ring ring-1"></div>
          <div class="logo-ring ring-2"></div>
          <div class="logo-ring ring-3"></div>
          <div class="logo-icon">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M2 17L12 22L22 17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M2 12L12 17L22 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
        </div>
        <h1 class="title">
          <span class="title-main">UCAC-ICAM</span>
          <span class="title-glow">UCAC-ICAM</span>
        </h1>
        <h2 class="subtitle">Portail Captif Reseau</h2>
        <p class="tagline">Systeme d'authentification securise</p>
      </div>

      <!-- Action Cards -->
      <div class="action-grid animate-fadeInUp stagger-2">
        <!-- Login Card -->
        <button @click="goToLogin" class="action-card">
          <div class="card-glow"></div>
          <div class="card-icon orange">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4M10 17l5-5-5-5M15 12H3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <span class="card-label">Connexion</span>
          <span class="card-desc">Acceder a votre compte</span>
          <div class="card-arrow">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M5 12h14M12 5l7 7-7 7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
        </button>

        <!-- Register Card -->
        <button @click="goToRegister" class="action-card">
          <div class="card-glow blue"></div>
          <div class="card-icon blue">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <circle cx="8.5" cy="7" r="4" stroke="currentColor" stroke-width="2"/>
              <line x1="20" y1="8" x2="20" y2="14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              <line x1="23" y1="11" x2="17" y2="11" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </div>
          <span class="card-label">Inscription</span>
          <span class="card-desc">Creer un nouveau compte</span>
          <div class="card-arrow">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M5 12h14M12 5l7 7-7 7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
        </button>

        <!-- Verify Card -->
        <button @click="openVerifyModal" class="action-card">
          <div class="card-glow magenta"></div>
          <div class="card-icon magenta">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M22 4L12 14.01l-3-3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <span class="card-label">Verification</span>
          <span class="card-desc">Verifier votre compte</span>
          <div class="card-arrow">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M5 12h14M12 5l7 7-7 7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
        </button>

        <!-- Internet Card -->
        <button @click="goToInternet" class="action-card">
          <div class="card-glow green"></div>
          <div class="card-icon green">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
              <line x1="2" y1="12" x2="22" y2="12" stroke="currentColor" stroke-width="2"/>
              <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" stroke="currentColor" stroke-width="2"/>
            </svg>
          </div>
          <span class="card-label">Internet</span>
          <span class="card-desc">Acceder au reseau</span>
          <div class="card-arrow">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M5 12h14M12 5l7 7-7 7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
        </button>
      </div>

      <!-- Footer -->
      <div class="footer animate-fadeInUp stagger-3">
        <div class="status-indicator">
          <span class="status-dot"></span>
          <span>Systeme operationnel</span>
        </div>
        <p>&copy; 2024 UCAC-ICAM - Portail Captif Securise</p>
      </div>
    </div>

    <!-- Verify Modal -->
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
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                <path d="M22 4L12 14.01l-3-3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
            <h3>Verification du compte</h3>
            <p>Entrez votre matricule pour verifier l'etat de votre compte</p>
          </div>

          <div class="modal-body">
            <div class="input-group">
              <label class="input-label">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2"/>
                  <circle cx="12" cy="7" r="4" stroke="currentColor" stroke-width="2"/>
                </svg>
                Matricule
              </label>
              <input
                v-model="matricule"
                type="text"
                class="input"
                placeholder="Ex: UCAC2024001"
                @keyup.enter="verifyAccount"
                :disabled="verifyLoading"
              />
            </div>

            <div v-if="verifyMessage" class="alert alert-success">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                <path d="M22 4L12 14.01l-3-3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              {{ verifyMessage }}
            </div>

            <div v-if="verifyError" class="alert alert-error">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                <line x1="15" y1="9" x2="9" y2="15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                <line x1="9" y1="9" x2="15" y2="15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
              {{ verifyError }}
            </div>

            <button @click="verifyAccount" :disabled="verifyLoading" class="btn-verify">
              <span v-if="verifyLoading" class="spinner"></span>
              <span v-else>Verifier</span>
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.home-page {
  min-height: 100vh;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  background: url('/image-bg.jpg') no-repeat center center fixed;
  background-size: cover;
}

/* Overlay sombre sur l'image de fond */
.home-page::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(5, 5, 8, 0.85);
  z-index: 0;
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
    linear-gradient(rgba(242, 148, 0, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(242, 148, 0, 0.03) 1px, transparent 1px);
  background-size: 60px 60px;
  animation: gridMove 20s linear infinite;
}

@keyframes gridMove {
  0% { transform: translateY(0); }
  100% { transform: translateY(60px); }
}

.gradient-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.4;
  animation: orbFloat 8s ease-in-out infinite;
}

.orb-1 {
  width: 600px;
  height: 600px;
  background: radial-gradient(circle, #F29400 0%, transparent 70%);
  top: -200px;
  right: -200px;
  animation-delay: 0s;
}

.orb-2 {
  width: 500px;
  height: 500px;
  background: radial-gradient(circle, #008ecf 0%, transparent 70%);
  bottom: -150px;
  left: -150px;
  animation-delay: 2s;
}

.orb-3 {
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, #a23882 0%, transparent 70%);
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  animation-delay: 4s;
}

@keyframes orbFloat {
  0%, 100% { transform: scale(1) translate(0, 0); opacity: 0.4; }
  50% { transform: scale(1.1) translate(20px, -20px); opacity: 0.6; }
}

.scan-line {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 2px;
  background: linear-gradient(90deg, transparent, #F29400, transparent);
  animation: scanMove 4s linear infinite;
}

@keyframes scanMove {
  0% { top: 0; opacity: 0; }
  10% { opacity: 1; }
  90% { opacity: 1; }
  100% { top: 100%; opacity: 0; }
}

/* Admin Button */
.admin-btn {
  position: fixed;
  top: 2rem;
  right: 2rem;
  z-index: 100;
  background: rgba(10, 10, 15, 0.9);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(242, 148, 0, 0.3);
  border-radius: 12px;
  padding: 0.75rem 1.5rem;
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
  letter-spacing: 0.05em;
}

.admin-btn svg {
  width: 20px;
  height: 20px;
  animation: rotate 10s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.admin-btn:hover {
  background: rgba(242, 148, 0, 0.1);
  border-color: #F29400;
  box-shadow: 0 0 30px rgba(242, 148, 0, 0.3);
  transform: translateY(-2px);
}

.admin-btn:hover svg {
  animation-duration: 2s;
}

/* Content */
.content {
  position: relative;
  z-index: 1;
  text-align: center;
  padding: 2rem;
  max-width: 1000px;
  width: 100%;
}

/* Logo Section */
.logo-section {
  margin-bottom: 3rem;
}

.logo-container {
  position: relative;
  width: 140px;
  height: 140px;
  margin: 0 auto 2rem;
}

.logo-ring {
  position: absolute;
  border-radius: 50%;
  border: 2px solid transparent;
}

.ring-1 {
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  border-color: rgba(242, 148, 0, 0.3);
  animation: ringRotate 10s linear infinite;
}

.ring-2 {
  top: 10px;
  left: 10px;
  width: calc(100% - 20px);
  height: calc(100% - 20px);
  border-color: rgba(0, 142, 207, 0.3);
  animation: ringRotate 8s linear infinite reverse;
}

.ring-3 {
  top: 20px;
  left: 20px;
  width: calc(100% - 40px);
  height: calc(100% - 40px);
  border-color: rgba(162, 56, 130, 0.3);
  animation: ringRotate 6s linear infinite;
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
  width: 80px;
  height: 80px;
  background: linear-gradient(135deg, rgba(242, 148, 0, 0.2) 0%, rgba(162, 56, 130, 0.2) 100%);
  backdrop-filter: blur(10px);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(242, 148, 0, 0.3);
}

.logo-icon svg {
  width: 40px;
  height: 40px;
  color: #F29400;
}

.title {
  position: relative;
  font-family: 'Orbitron', sans-serif;
  font-size: 3.5rem;
  font-weight: 900;
  letter-spacing: 0.15em;
  margin-bottom: 0.5rem;
}

.title-main {
  position: relative;
  z-index: 1;
  background: linear-gradient(135deg, #ffffff 0%, #F29400 50%, #008ecf 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.title-glow {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  color: #F29400;
  filter: blur(20px);
  opacity: 0.5;
  z-index: 0;
}

.subtitle {
  font-family: 'Rajdhani', sans-serif;
  font-size: 1.5rem;
  font-weight: 600;
  color: #008ecf;
  text-transform: uppercase;
  letter-spacing: 0.2em;
  margin-bottom: 0.5rem;
}

.tagline {
  font-family: 'Inter', sans-serif;
  font-size: 1rem;
  color: #636362;
  letter-spacing: 0.05em;
}

/* Action Grid */
.action-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1.5rem;
  margin-bottom: 3rem;
}

.action-card {
  position: relative;
  background: rgba(20, 20, 30, 0.6);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  padding: 2rem 1.5rem;
  cursor: pointer;
  transition: all 0.4s ease;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  overflow: hidden;
  text-align: center;
}

.card-glow {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: radial-gradient(circle at center, rgba(242, 148, 0, 0.1) 0%, transparent 70%);
  opacity: 0;
  transition: opacity 0.4s ease;
}

.card-glow.blue {
  background: radial-gradient(circle at center, rgba(0, 142, 207, 0.1) 0%, transparent 70%);
}

.card-glow.magenta {
  background: radial-gradient(circle at center, rgba(162, 56, 130, 0.1) 0%, transparent 70%);
}

.card-glow.green {
  background: radial-gradient(circle at center, rgba(0, 207, 93, 0.1) 0%, transparent 70%);
}

.action-card:hover .card-glow {
  opacity: 1;
}

.card-icon {
  width: 70px;
  height: 70px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  z-index: 1;
  transition: all 0.4s ease;
}

.card-icon svg {
  width: 32px;
  height: 32px;
  color: white;
}

.card-icon.orange {
  background: linear-gradient(135deg, #F29400 0%, #cc7a00 100%);
  box-shadow: 0 0 30px rgba(242, 148, 0, 0.4);
}

.card-icon.blue {
  background: linear-gradient(135deg, #008ecf 0%, #006699 100%);
  box-shadow: 0 0 30px rgba(0, 142, 207, 0.4);
}

.card-icon.magenta {
  background: linear-gradient(135deg, #a23882 0%, #7a2962 100%);
  box-shadow: 0 0 30px rgba(162, 56, 130, 0.4);
}

.card-icon.green {
  background: linear-gradient(135deg, #00cf5d 0%, #00a648 100%);
  box-shadow: 0 0 30px rgba(0, 207, 93, 0.4);
}

.card-label {
  font-family: 'Rajdhani', sans-serif;
  font-size: 1.25rem;
  font-weight: 700;
  color: white;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  position: relative;
  z-index: 1;
}

.card-desc {
  font-family: 'Inter', sans-serif;
  font-size: 0.85rem;
  color: #636362;
  position: relative;
  z-index: 1;
}

.card-arrow {
  position: absolute;
  bottom: 1rem;
  right: 1rem;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.05);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transform: translateX(-10px);
  transition: all 0.4s ease;
}

.card-arrow svg {
  width: 16px;
  height: 16px;
  color: #F29400;
}

.action-card:hover {
  transform: translateY(-8px);
  border-color: rgba(242, 148, 0, 0.3);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
}

.action-card:hover .card-icon {
  transform: scale(1.1);
}

.action-card:hover .card-arrow {
  opacity: 1;
  transform: translateX(0);
}

/* Footer */
.footer {
  color: #636362;
  font-size: 0.9rem;
}

.status-indicator {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: rgba(0, 207, 93, 0.1);
  border: 1px solid rgba(0, 207, 93, 0.3);
  border-radius: 20px;
  margin-bottom: 1rem;
  font-size: 0.85rem;
  color: #00cf5d;
}

.status-dot {
  width: 8px;
  height: 8px;
  background: #00cf5d;
  border-radius: 50%;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(0.8); }
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
  animation: fadeIn 0.3s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.modal-content {
  background: linear-gradient(135deg, rgba(20, 20, 30, 0.95) 0%, rgba(10, 10, 15, 0.95) 100%);
  backdrop-filter: blur(30px);
  border: 1px solid rgba(242, 148, 0, 0.2);
  border-radius: 24px;
  padding: 2.5rem;
  max-width: 450px;
  width: 100%;
  position: relative;
  box-shadow: 0 0 60px rgba(242, 148, 0, 0.1);
  animation: slideUp 0.4s ease-out;
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(40px); }
  to { opacity: 1; transform: translateY(0); }
}

.modal-close {
  position: absolute;
  top: 1.5rem;
  right: 1.5rem;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  color: #636362;
}

.modal-close svg {
  width: 20px;
  height: 20px;
}

.modal-close:hover {
  background: rgba(229, 50, 18, 0.2);
  border-color: #e53212;
  color: #e53212;
  transform: rotate(90deg);
}

.modal-header {
  text-align: center;
  margin-bottom: 2rem;
}

.modal-icon {
  width: 80px;
  height: 80px;
  margin: 0 auto 1.5rem;
  background: linear-gradient(135deg, #a23882 0%, #7a2962 100%);
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 0 40px rgba(162, 56, 130, 0.4);
}

.modal-icon svg {
  width: 40px;
  height: 40px;
  color: white;
}

.modal-header h3 {
  font-family: 'Rajdhani', sans-serif;
  font-size: 1.75rem;
  font-weight: 700;
  color: white;
  margin-bottom: 0.5rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.modal-header p {
  color: #636362;
  font-size: 0.95rem;
}

.modal-body .input-group {
  margin-bottom: 1.5rem;
}

.modal-body .input-label {
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

.modal-body .input-label svg {
  width: 18px;
  height: 18px;
  color: #a23882;
}

.modal-body .input {
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
  text-align: center;
  font-weight: 600;
  letter-spacing: 0.1em;
}

.modal-body .input::placeholder {
  color: #636362;
}

.modal-body .input:focus {
  border-color: #a23882;
  background: rgba(162, 56, 130, 0.05);
  box-shadow: 0 0 20px rgba(162, 56, 130, 0.2);
}

.alert {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem;
  border-radius: 12px;
  margin-bottom: 1.5rem;
  font-weight: 500;
}

.alert svg {
  width: 24px;
  height: 24px;
  flex-shrink: 0;
}

.alert-success {
  background: rgba(0, 207, 93, 0.1);
  border: 1px solid rgba(0, 207, 93, 0.3);
  color: #00cf5d;
}

.alert-error {
  background: rgba(229, 50, 18, 0.1);
  border: 1px solid rgba(229, 50, 18, 0.3);
  color: #e53212;
}

.btn-verify {
  width: 100%;
  padding: 1rem 2rem;
  font-family: 'Rajdhani', sans-serif;
  font-size: 1.1rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: white;
  background: linear-gradient(135deg, #a23882 0%, #7a2962 100%);
  border: none;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.btn-verify:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 0 30px rgba(162, 56, 130, 0.5);
}

.btn-verify:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.spinner {
  width: 24px;
  height: 24px;
  border: 3px solid rgba(255, 255, 255, 0.2);
  border-top-color: white;
  border-radius: 50%;
  animation: rotate 1s linear infinite;
}

/* Responsive */
@media (max-width: 900px) {
  .action-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .admin-btn {
    top: 1rem;
    right: 1rem;
    padding: 0.6rem 1rem;
    font-size: 0.85rem;
  }

  .title {
    font-size: 2.5rem;
  }

  .subtitle {
    font-size: 1.2rem;
  }

  .logo-container {
    width: 120px;
    height: 120px;
  }

  .logo-icon {
    width: 60px;
    height: 60px;
  }

  .logo-icon svg {
    width: 30px;
    height: 30px;
  }
}

@media (max-width: 600px) {
  .action-grid {
    grid-template-columns: 1fr;
    gap: 1rem;
  }

  .action-card {
    flex-direction: row;
    padding: 1.5rem;
    text-align: left;
  }

  .card-icon {
    width: 60px;
    height: 60px;
  }

  .card-icon svg {
    width: 28px;
    height: 28px;
  }

  .title {
    font-size: 2rem;
  }

  .subtitle {
    font-size: 1rem;
    letter-spacing: 0.1em;
  }
}

@media (max-width: 400px) {
  .title {
    font-size: 1.6rem;
  }

  .content {
    padding: 1rem;
  }
}
</style>
